from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import APIPermission, MockAPI, User
from ..schemas import PermissionCreate
from ..security import current_user

router = APIRouter(prefix="/apis/{api_id}/permissions", tags=["API permissions"])

def owned_api(api_id: int, db: Session, user: User):
    api = db.query(MockAPI).filter_by(id=api_id, owner_id=user.id).first()
    if not api: raise HTTPException(404, "Mock API not found")
    return api

@router.get("")
def list_permissions(api_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    rows = db.query(APIPermission, User.email).join(User, User.id == APIPermission.user_id).filter(APIPermission.mock_api_id == api_id).all()
    return [{"id": permission.id, "user_id": permission.user_id, "email": email} for permission, email in rows]

@router.post("", status_code=201)
def grant_permission(api_id: int, payload: PermissionCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    invited = db.query(User).filter_by(email=payload.email).first()
    if not invited: raise HTTPException(404, "User must register before access can be granted")
    if db.query(APIPermission).filter_by(mock_api_id=api_id, user_id=invited.id).first(): raise HTTPException(409, "User already has access")
    permission = APIPermission(mock_api_id=api_id, user_id=invited.id); db.add(permission); db.commit(); db.refresh(permission)
    return {"id": permission.id, "user_id": invited.id, "email": invited.email}

@router.delete("/{permission_id}", status_code=204)
def revoke_permission(api_id: int, permission_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    owned_api(api_id, db, user)
    permission = db.query(APIPermission).filter_by(id=permission_id, mock_api_id=api_id).first()
    if not permission: raise HTTPException(404, "Permission not found")
    db.delete(permission); db.commit()
