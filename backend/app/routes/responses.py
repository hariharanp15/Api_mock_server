from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MockAPI, ResponseTemplate, User
from ..schemas import ResponseScenario, ResponseTemplateUpdate
from ..security import current_user

router = APIRouter(prefix="/apis/{api_id}/responses", tags=["response scenarios"])

def owned_api(api_id: int, db: Session, user: User) -> MockAPI:
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    return api

def output(template: ResponseTemplate):
    return {"id": template.id, "scenario": template.scenario, "status_code": template.status_code, "headers": template.headers or {}, "body": template.body}

@router.get("")
def list_scenarios(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    return [output(x) for x in db.query(ResponseTemplate).filter_by(mock_api_id=api_id).all()]

@router.post("", status_code=201)
def create_scenario(api_id: int, payload: ResponseScenario, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    existing = db.query(ResponseTemplate).filter_by(mock_api_id=api_id, scenario=payload.scenario.lower()).first()
    if existing: raise HTTPException(409, "A scenario with this name already exists")
    template = ResponseTemplate(mock_api_id=api_id, scenario=payload.scenario.lower(), status_code=payload.status_code, headers=payload.headers, body=payload.body)
    db.add(template); db.commit(); db.refresh(template)
    return output(template)

@router.put("/{template_id}")
def update_scenario(api_id: int, template_id: int, payload: ResponseTemplateUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    template = db.query(ResponseTemplate).filter_by(id=template_id, mock_api_id=api_id).first()
    if not template: raise HTTPException(404, "Response scenario not found")
    template.scenario, template.status_code, template.headers, template.body = payload.scenario.lower(), payload.status_code, payload.headers, payload.body
    db.commit(); db.refresh(template)
    return output(template)

@router.delete("/{template_id}", status_code=204)
def delete_scenario(api_id: int, template_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    template = db.query(ResponseTemplate).filter_by(id=template_id, mock_api_id=api_id).first()
    if not template: raise HTTPException(404, "Response scenario not found")
    db.delete(template); db.commit()
