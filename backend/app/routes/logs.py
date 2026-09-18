from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MockAPI, RequestLog, User
from ..security import current_user

router = APIRouter(prefix="/logs", tags=["request history"])

@router.get("")
def list_logs(api_id: int | None = None, status_min: int | None = Query(None, ge=100, le=599), from_date: datetime | None = None, skip: int = 0, limit: int = Query(50, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_ids = db.query(MockAPI.id).filter_by(owner_id=user.id)
    query = db.query(RequestLog).filter(RequestLog.mock_api_id.in_(owned_ids))
    if api_id is not None: query = query.filter(RequestLog.mock_api_id == api_id)
    if status_min is not None: query = query.filter(RequestLog.response_status >= status_min)
    if from_date is not None: query = query.filter(RequestLog.created_at >= from_date)
    total = query.count()
    rows = query.order_by(RequestLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [{"id": x.id, "api_id": x.mock_api_id, "method": x.method, "path": x.path, "params": x.request_params, "body": x.request_body, "status": x.response_status, "response_time_ms": x.response_time_ms, "timestamp": x.created_at} for x in rows]}
