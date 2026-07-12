from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Employee
from schemas import RoleUpdateRequest
from deps import require_role

router = APIRouter(prefix="/users", tags=["users"])

@router.patch("/{employee_id}/role")
def promote_role(
    employee_id: int,
    data: RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: Employee = Depends(require_role("admin")),
):
    if data.role not in ("department_head", "asset_manager"):
        raise HTTPException(status_code=400, detail="Invalid role")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.role = data.role
    db.commit()
    return {"message": f"{employee.name} promoted to {data.role}"}