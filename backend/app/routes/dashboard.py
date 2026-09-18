from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MockAPI, RequestLog, User
from ..security import current_user
from ..services.cache import get_json, set_json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(current_user)):
    cache_key = f"dashboard:{user.id}"
    if cached := get_json(cache_key): return cached
    owned = db.query(MockAPI.id).filter_by(owner_id=user.id)
    total = owned.count()
    log_filter = RequestLog.mock_api_id.in_(owned)
    requests = db.query(RequestLog).filter(log_filter)
    most_used = db.query(RequestLog.path, RequestLog.method, func.count(RequestLog.id).label("count")).filter(log_filter).group_by(RequestLog.path, RequestLog.method).order_by(func.count(RequestLog.id).desc()).limit(5).all()
    total_requests = requests.count()
    error_requests = requests.filter(RequestLog.response_status >= 400).count()
    method_distribution = db.query(MockAPI.method, func.count(MockAPI.id).label("count")).filter(MockAPI.owner_id == user.id).group_by(MockAPI.method).order_by(func.count(MockAPI.id).desc()).all()
    recent = requests.order_by(RequestLog.created_at.desc()).limit(8).all()
    result = {
        "total_mock_apis": total,
        "active_apis": db.query(MockAPI).filter(MockAPI.owner_id == user.id, MockAPI.is_active.is_(True)).count(),
        "total_requests": total_requests,
        "error_requests": error_requests,
        "success_rate": round(((total_requests - error_requests) / total_requests * 100) if total_requests else 0, 1),
        "average_response_time_ms": round(requests.with_entities(func.avg(RequestLog.response_time_ms)).scalar() or 0, 2),
        "most_used_endpoints": [{"path": x.path, "method": x.method, "count": x.count} for x in most_used],
        "method_distribution": [{"method": x.method, "count": x.count} for x in method_distribution],
        "recent_requests": [{"id": x.id, "method": x.method, "path": x.path, "status": x.response_status, "response_time_ms": x.response_time_ms, "timestamp": x.created_at} for x in recent],
    }
    set_json(cache_key, result)
    return result
