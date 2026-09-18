from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import APIPermission, APIVersion, MockAPI, RequestLog, RequestSchema, ResponseTemplate, User
from ..schemas import MockAPICreate, MockAPIEdit, MockAPIOut, MockAPIStatusUpdate, VersionCreate
from ..security import current_user
from ..services.cache import invalidate

router = APIRouter(prefix="/apis", tags=["mock APIs"])

@router.get("", response_model=list[MockAPIOut])
def list_apis(skip: int = 0, limit: int = Query(20, le=100), method: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(MockAPI).filter_by(owner_id=user.id)
    if method: query = query.filter(MockAPI.method == method.upper())
    return query.order_by(MockAPI.created_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=MockAPIOut, status_code=201)
def create_api(payload: MockAPICreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    path = payload.path.rstrip("/") or "/"
    duplicate = db.query(MockAPI).join(APIVersion).filter(MockAPI.owner_id == user.id, MockAPI.path == path, MockAPI.method == payload.method.upper(), APIVersion.version == payload.version).first()
    if duplicate: raise HTTPException(409, "An API with this method, path, and version already exists")
    api = MockAPI(owner_id=user.id, name=payload.name, path=path, method=payload.method.upper(), is_private=payload.is_private, auth_required=payload.auth_required, response_delay_ms=payload.response_delay_ms)
    db.add(api); db.flush()
    db.add(APIVersion(mock_api_id=api.id, version=payload.version))
    db.add(RequestSchema(mock_api_id=api.id, body_schema=payload.body_schema, required_headers=payload.required_headers, required_params=payload.required_params))
    db.add_all([ResponseTemplate(mock_api_id=api.id, scenario=r.scenario.lower(), status_code=r.status_code, headers=r.headers, body=r.body) for r in payload.responses])
    db.commit(); db.refresh(api); invalidate(f"dashboard:{user.id}")
    return api

@router.get("/{api_id}", response_model=MockAPIOut)
def get_api(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    return api

@router.patch("/{api_id}", response_model=MockAPIOut)
def update_api(api_id: int, payload: MockAPIEdit, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    path = payload.path.rstrip("/") or "/"
    api.name, api.path, api.method = payload.name, path, payload.method.upper()
    api.is_private, api.auth_required, api.response_delay_ms = payload.is_private, payload.auth_required, payload.response_delay_ms
    db.commit(); db.refresh(api); invalidate(f"dashboard:{user.id}")
    return api

@router.patch("/{api_id}/status", response_model=MockAPIOut)
def update_api_status(api_id: int, payload: MockAPIStatusUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    api.is_active = payload.is_active
    db.commit(); db.refresh(api); invalidate(f"dashboard:{user.id}")
    return api

@router.post("/{api_id}/clone", response_model=MockAPIOut, status_code=201)
def clone_api(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    source = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not source: raise HTTPException(404, "Mock API not found")
    clone = MockAPI(owner_id=user.id, name=f"{source.name} (copy)", path=f"{source.path}-copy", method=source.method, is_active=False, is_private=source.is_private, auth_required=source.auth_required, response_delay_ms=source.response_delay_ms)
    db.add(clone); db.flush()
    version = db.query(APIVersion).filter_by(mock_api_id=source.id, is_current=True).first()
    db.add(APIVersion(mock_api_id=clone.id, version=version.version if version else "v1"))
    schema = db.query(RequestSchema).filter_by(mock_api_id=source.id).first()
    if schema: db.add(RequestSchema(mock_api_id=clone.id, body_schema=schema.body_schema, required_headers=schema.required_headers, required_params=schema.required_params))
    templates = db.query(ResponseTemplate).filter_by(mock_api_id=source.id).all()
    db.add_all([ResponseTemplate(mock_api_id=clone.id, scenario=x.scenario, status_code=x.status_code, headers=x.headers, body=x.body) for x in templates])
    db.commit(); db.refresh(clone); invalidate(f"dashboard:{user.id}")
    return clone

@router.get("/{api_id}/versions")
def list_versions(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    return [{"id": x.id, "version": x.version, "is_current": x.is_current} for x in db.query(APIVersion).filter_by(mock_api_id=api_id).all()]

@router.post("/{api_id}/versions", status_code=201)
def create_version(api_id: int, payload: VersionCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    if db.query(APIVersion).filter_by(mock_api_id=api_id, version=payload.version).first(): raise HTTPException(409, "Version already exists")
    if payload.make_current: db.query(APIVersion).filter_by(mock_api_id=api_id).update({"is_current": False})
    version = APIVersion(mock_api_id=api_id, version=payload.version, is_current=payload.make_current)
    db.add(version); db.commit(); db.refresh(version)
    return {"id": version.id, "version": version.version, "is_current": version.is_current}

@router.delete("/{api_id}", status_code=204)
def delete_api(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    db.query(ResponseTemplate).filter_by(mock_api_id=api.id).delete()
    db.query(RequestSchema).filter_by(mock_api_id=api.id).delete()
    db.query(APIVersion).filter_by(mock_api_id=api.id).delete()
    db.query(APIPermission).filter_by(mock_api_id=api.id).delete()
    db.query(RequestLog).filter_by(mock_api_id=api.id).delete()
    db.delete(api); db.commit(); invalidate(f"dashboard:{user.id}")
