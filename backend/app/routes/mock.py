import asyncio, time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jsonschema import ValidationError, validate
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import APIPermission, APIVersion, MockAPI, RequestLog, RequestSchema, ResponseTemplate, User
from ..security import current_user
from ..services.cache import invalidate

router = APIRouter(prefix="/mock", tags=["dynamic mock execution"])

def api_for_request(path: str, method: str, version: str, db: Session):
    # Registered paths may contain FastAPI-like tokens, e.g. /products/{id}.
    candidates = db.query(MockAPI).join(APIVersion).filter(MockAPI.method == method, MockAPI.is_active.is_(True), APIVersion.version == version).all()
    incoming = "/" + path.strip("/")
    for api in candidates:
        expected, values = api.path.strip("/").split("/"), incoming.strip("/").split("/")
        if len(expected) == len(values) and all(a == b or (a.startswith("{") and a.endswith("}")) for a, b in zip(expected, values)): return api
    raise HTTPException(404, "Mock endpoint not found")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def execute(path: str, request: Request, version: str = "v1", scenario: str = "success", db: Session = Depends(get_db)):
    started = time.perf_counter(); api = api_for_request(path, request.method, version, db)
    if api.is_private or api.auth_required:
        try: actor = current_user(request.headers.get("authorization") and type("C", (), {"credentials": request.headers["authorization"].replace("Bearer ", "")})(), db)
        except HTTPException: raise HTTPException(401, "Mock API authentication required")
        allowed = actor.id == api.owner_id or db.query(APIPermission).filter_by(mock_api_id=api.id, user_id=actor.id).first()
        if not allowed: raise HTTPException(403, "You do not have access to this private mock API")
    schema = db.query(RequestSchema).filter_by(mock_api_id=api.id).first()
    body = None
    try: body = await request.json()
    except Exception: pass
    if schema:
        missing = [key for key in (schema.required_headers or {}) if key.lower() not in request.headers]
        if missing: raise HTTPException(422, {"message": "Missing required headers", "headers": missing})
        if schema.body_schema:
            try: validate(body, schema.body_schema)
            except ValidationError as error: raise HTTPException(422, {"message": "Request body validation failed", "detail": error.message})
    template = db.query(ResponseTemplate).filter_by(mock_api_id=api.id, scenario=scenario.lower()).first() or db.query(ResponseTemplate).filter_by(mock_api_id=api.id, scenario="success").first()
    if not template: raise HTTPException(500, "No response template configured")
    if api.response_delay_ms: await asyncio.sleep(api.response_delay_ms / 1000)
    elapsed = int((time.perf_counter() - started) * 1000)
    db.add(RequestLog(mock_api_id=api.id, method=request.method, path=request.url.path, request_params=dict(request.query_params), request_body=body, response_status=template.status_code, response_time_ms=elapsed)); db.commit(); invalidate(f"dashboard:{api.owner_id}")
    return JSONResponse(content=template.body, status_code=template.status_code, headers=template.headers or {})
