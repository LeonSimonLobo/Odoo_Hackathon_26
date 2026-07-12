import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import engine, get_db, Base
from models import Department, Employee, AssetCategory, ActivityLog

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AssetFlow API",
    description="Backend API Server for AssetFlow Enterprise Asset & Resource Management System",
    version="1.0.0"
)

# Configure CORS Middleware (crucial for Next.js frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# PYDANTIC SCHEMAS (Request & Response Validation)
# =====================================================================

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_department_id: Optional[int] = None
    department_head_id: Optional[int] = None
    status: str = Field("active", pattern="^(active|inactive)$")

class DepartmentResponse(BaseModel):
    id: int
    name: str
    parent_department_id: Optional[int]
    parent_department_name: Optional[str]
    department_head_id: Optional[int]
    department_head_name: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    schema_attributes: Optional[Dict[str, Any]] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schema_attributes: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    department_id: Optional[int]
    department_name: Optional[str]
    role: str
    status: str
    created_at: str
    
    class Config:
        from_attributes = True

class EmployeeRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(employee|department_head|asset_manager|admin)$")

class EmployeeStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive)$")


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def log_activity(db: Session, employee_id: Optional[int], action: str, details: Dict[str, Any]):
    """Helper to record audit trails of actions"""
    log_entry = ActivityLog(
        employee_id=employee_id,
        action=action,
        details=details
    )
    db.add(log_entry)
    db.commit()


# =====================================================================
# TAB A: DEPARTMENT ENDPOINTS
# =====================================================================

@app.get("/api/departments", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    response = []
    for dept in departments:
        # Fetch parent name
        parent_name = None
        if dept.parent_department_id:
            parent = db.get(Department, dept.parent_department_id)
            if parent:
                parent_name = parent.name
        
        # Fetch head name
        head_name = None
        if dept.department_head_id:
            head = db.get(Employee, dept.department_head_id)
            if head:
                head_name = head.name

        response.append({
            "id": dept.id,
            "name": dept.name,
            "parent_department_id": dept.parent_department_id,
            "parent_department_name": parent_name,
            "department_head_id": dept.department_head_id,
            "department_head_name": head_name,
            "status": dept.status,
            "created_at": dept.created_at.isoformat(),
            "updated_at": dept.updated_at.isoformat()
        })
    return response

@app.post("/api/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    # 1. Enforce Parent department exists if provided
    if dept_in.parent_department_id:
        parent = db.get(Department, dept_in.parent_department_id)
        if not parent:
            raise HTTPException(status_code=400, detail=f"Parent department with ID {dept_in.parent_department_id} not found.")

    # 2. Enforce Head employee exists if provided
    if dept_in.department_head_id:
        head = db.get(Employee, dept_in.department_head_id)
        if not head:
            raise HTTPException(status_code=400, detail=f"Employee designated as Head (ID {dept_in.department_head_id}) not found.")

    new_dept = Department(
        name=dept_in.name,
        parent_department_id=dept_in.parent_department_id,
        department_head_id=dept_in.department_head_id,
        status=dept_in.status
    )
    
    db.add(new_dept)
    try:
        db.commit()
        db.refresh(new_dept)
        
        # 3. If Head is assigned, auto-promote their role in the Directory
        if new_dept.department_head_id:
            head_emp = db.get(Employee, new_dept.department_head_id)
            if head_emp and head_emp.role != "department_head":
                head_emp.role = "department_head"
                head_emp.department_id = new_dept.id
                db.commit()
        
        log_activity(db, None, "CREATE_DEPARTMENT", {"id": new_dept.id, "name": new_dept.name})
        
        # Build response
        parent_name = db.get(Department, new_dept.parent_department_id).name if new_dept.parent_department_id else None
        head_name = db.get(Employee, new_dept.department_head_id).name if new_dept.department_head_id else None

        return {
            "id": new_dept.id,
            "name": new_dept.name,
            "parent_department_id": new_dept.parent_department_id,
            "parent_department_name": parent_name,
            "department_head_id": new_dept.department_head_id,
            "department_head_name": head_name,
            "status": new_dept.status,
            "created_at": new_dept.created_at.isoformat(),
            "updated_at": new_dept.updated_at.isoformat()
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Department with this name already exists.")

@app.put("/api/departments/{id}", response_model=DepartmentResponse)
def update_department(id: int, dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    dept = db.get(Department, id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    # 1. Enforce Parent department exists and isn't self (prevents infinite loop)
    if dept_in.parent_department_id:
        if dept_in.parent_department_id == id:
            raise HTTPException(status_code=400, detail="A department cannot be its own parent.")
        parent = db.get(Department, dept_in.parent_department_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent department not found.")

    # 2. Enforce Head employee exists
    if dept_in.department_head_id:
        head = db.get(Employee, dept_in.department_head_id)
        if not head:
            raise HTTPException(status_code=400, detail="Employee designated as Head not found.")

    dept.name = dept_in.name
    dept.parent_department_id = dept_in.parent_department_id
    dept.department_head_id = dept_in.department_head_id
    dept.status = dept_in.status

    try:
        db.commit()
        db.refresh(dept)
        
        # 3. If Head is assigned, auto-promote their role in the Directory
        if dept.department_head_id:
            head_emp = db.get(Employee, dept.department_head_id)
            if head_emp and head_emp.role != "department_head":
                head_emp.role = "department_head"
                head_emp.department_id = dept.id
                db.commit()

        log_activity(db, None, "UPDATE_DEPARTMENT", {"id": dept.id, "name": dept.name})

        # Fetch names for response
        parent_name = db.get(Department, dept.parent_department_id).name if dept.parent_department_id else None
        head_name = db.get(Employee, dept.department_head_id).name if dept.department_head_id else None

        return {
            "id": dept.id,
            "name": dept.name,
            "parent_department_id": dept.parent_department_id,
            "parent_department_name": parent_name,
            "department_head_id": dept.department_head_id,
            "department_head_name": head_name,
            "status": dept.status,
            "created_at": dept.created_at.isoformat(),
            "updated_at": dept.updated_at.isoformat()
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Department name already exists in another record.")


# =====================================================================
# TAB B: ASSET CATEGORY ENDPOINTS
# =====================================================================

@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(AssetCategory).all()

@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(cat_in: CategoryCreate, db: Session = Depends(get_db)):
    new_cat = AssetCategory(
        name=cat_in.name,
        description=cat_in.description,
        schema_attributes=cat_in.schema_attributes
    )
    db.add(new_cat)
    try:
        db.commit()
        db.refresh(new_cat)
        log_activity(db, None, "CREATE_CATEGORY", {"id": new_cat.id, "name": new_cat.name})
        return new_cat
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category name already exists.")

@app.put("/api/categories/{id}", response_model=CategoryResponse)
def update_category(id: int, cat_in: CategoryCreate, db: Session = Depends(get_db)):
    cat = db.get(AssetCategory, id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    cat.name = cat_in.name
    cat.description = cat_in.description
    cat.schema_attributes = cat_in.schema_attributes
    
    try:
        db.commit()
        db.refresh(cat)
        log_activity(db, None, "UPDATE_CATEGORY", {"id": cat.id, "name": cat.name})
        return cat
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category name already exists in another record.")


# =====================================================================
# TAB C: EMPLOYEE DIRECTORY & PROMOTIONS (Admin Only)
# =====================================================================

@app.get("/api/employees", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    response = []
    for emp in employees:
        dept_name = None
        if emp.department_id:
            dept = db.get(Department, emp.department_id)
            if dept:
                dept_name = dept.name
        
        response.append({
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "department_id": emp.department_id,
            "department_name": dept_name,
            "role": emp.role,
            "status": emp.status,
            "created_at": emp.created_at.isoformat()
        })
    return response

@app.put("/api/employees/{id}/role", response_model=EmployeeResponse)
def update_employee_role(id: int, role_in: EmployeeRoleUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")

    old_role = emp.role
    emp.role = role_in.role
    db.commit()
    db.refresh(emp)

    log_activity(db, None, "PROMOTE_EMPLOYEE", {
        "id": emp.id, 
        "name": emp.name, 
        "old_role": old_role, 
        "new_role": emp.role
    })

    dept_name = db.get(Department, emp.department_id).name if emp.department_id else None
    return {
        "id": emp.id,
        "name": emp.name,
        "email": emp.email,
        "department_id": emp.department_id,
        "department_name": dept_name,
        "role": emp.role,
        "status": emp.status,
        "created_at": emp.created_at.isoformat()
    }

@app.put("/api/employees/{id}/status", response_model=EmployeeResponse)
def update_employee_status(id: int, status_in: EmployeeStatusUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")

    old_status = emp.status
    emp.status = status_in.status
    db.commit()
    db.refresh(emp)

    log_activity(db, None, "TOGGLE_EMPLOYEE_STATUS", {
        "id": emp.id,
        "name": emp.name,
        "old_status": old_status,
        "new_status": emp.status
    })

    dept_name = db.get(Department, emp.department_id).name if emp.department_id else None
    return {
        "id": emp.id,
        "name": emp.name,
        "email": emp.email,
        "department_id": emp.department_id,
        "department_name": dept_name,
        "role": emp.role,
        "status": emp.status,
        "created_at": emp.created_at.isoformat()
    }


# Root route helper to verify server status
@app.get("/")
def get_root():
    return {
        "status": "online",
        "service": "AssetFlow API",
        "documentation": "/docs"
    }
