from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.database import get_db
from employees.models import Employees, Attendance
from employees.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeWithAttendance,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    CheckInRequest, CheckOutRequest, MarkAbsentRequest , EmployeeInsight
)
from datetime import datetime, date
from typing import Optional, List

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    existing_employee = db.query(Employees).filter(Employees.email == employee.email).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_employee = Employees(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    department: Optional[str] = Query(None, description="Filter by department"),
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    present_today: Optional[bool] = Query(None, description="Filter by today's presence"),
    db: Session = Depends(get_db)
):
    query = db.query(Employees)
    if department:
        query = query.filter(Employees.department.ilike(f"%{department}%"))
    
    if country:
        query = query.filter(Employees.country.ilike(f"%{country}%"))
    
    if state:
        query = query.filter(Employees.state.ilike(f"%{state}%"))
    
    if search:
        query = query.filter(
            or_(
                Employees.name.ilike(f"%{search}%"),
                Employees.email.ilike(f"%{search}%")
            )
        )
    
    if present_today is not None:
        today = date.today()
        if present_today:
            query = query.join(Attendance).filter(
                and_(
                    Attendance.date == today,
                    Attendance.is_present == True
                )
            )
        else:
            subquery = db.query(Attendance.employee_id).filter(
                and_(
                    Attendance.date == today,
                    Attendance.is_present == True
                )
            ).subquery()
            query = query.filter(~Employees.id.in_(subquery))
    
    employees = query.offset(skip).limit(limit).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeWithAttendance)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.get("/employee_insights", response_model=EmployeeInsight)
def get_employee_insights(db: Session = Depends(get_db)):
    today = date.today()

    total_employees = db.query(Employees).count()

    present_employees = db.query(Attendance).filter(
        Attendance.date == today,
        Attendance.is_present == True
    ).count()

    absent_employees = total_employees - present_employees

    return {
        "total_employees": total_employees,
        "present_employees": present_employees,
        "absent_employees": absent_employees
    }

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee_update.email and employee_update.email != employee.email:
        existing_employee = db.query(Employees).filter(Employees.email == employee_update.email).first()
        if existing_employee:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    update_data = employee_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.query(Attendance).filter(Attendance.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}


# Attendance Management
@router.post("/{employee_id}/check-in", response_model=AttendanceResponse)
def check_in_employee(employee_id: int, request: CheckInRequest, db: Session = Depends(get_db)):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    today = date.today()
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        )
    ).first()
    
    if existing_attendance:
        if existing_attendance.is_present:
            raise HTTPException(status_code=400, detail="Employee already checked in today")
        else:
            existing_attendance.check_in_time = datetime.now()
            existing_attendance.is_present = True
            existing_attendance.status = "present"
            existing_attendance.notes = request.notes
            existing_attendance.updated_at = datetime.now()
            db.commit()
            db.refresh(existing_attendance)
            return existing_attendance
    else:
        attendance = Attendance(
            employee_id=employee_id,
            date=today,
            check_in_time=datetime.now(),
            is_present=True,
            status="present",
            notes=request.notes
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance


@router.post("/{employee_id}/check-out", response_model=AttendanceResponse)
def check_out_employee(employee_id: int, request: CheckOutRequest, db: Session = Depends(get_db)):
    today = date.today()
    
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance:
        raise HTTPException(status_code=404, detail="No check in record found for today")
    
    if not attendance.is_present:
        raise HTTPException(status_code=400, detail="Employee is not checked in")
    
    if attendance.check_out_time:
        raise HTTPException(status_code=400, detail="Employee already checked out")
    
    attendance.check_out_time = datetime.now()
    if request.notes:
        attendance.notes = f"{attendance.notes or ''} | Check-out: {request.notes}"
    attendance.updated_at = datetime.now()
    
    db.commit()
    db.refresh(attendance)
    return attendance


@router.post("/{employee_id}/mark-absent")
def mark_employee_absent(employee_id: int, notes: Optional[str] = None, db: Session = Depends(get_db)):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    today = date.today()
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        )
    ).first()
    
    if existing_attendance:
        existing_attendance.is_present = False
        existing_attendance.status = "absent"
        existing_attendance.check_in_time = None
        existing_attendance.check_out_time = None
        existing_attendance.notes = notes
        existing_attendance.updated_at = datetime.now()
    else:
        attendance = Attendance(
            employee_id=employee_id,
            date=today,
            is_present=False,
            status="absent",
            notes=notes
        )
        db.add(attendance)
    
    db.commit()
    return {"message": "Employee marked as apsent"}


@router.get("/{employee_id}/attendance", response_model=List[AttendanceResponse])
def get_employee_attendance(
    employee_id: int,
    start_date: Optional[date] = Query(None, description="Start date for attendance recrods"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    status: Optional[str] = Query(None, description="Filter by status persent, absent, late, half day"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    employee = db.query(Employees).filter(Employees.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    if status:
        query = query.filter(Attendance.status == status)
    
    attendance_records = query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    return attendance_records


@router.get("/attendance/today", response_model=List[AttendanceResponse])
def get_today_attendance(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    today = date.today()
    query = db.query(Attendance).filter(Attendance.date == today)
    
    if status:
        query = query.filter(Attendance.status == status)
    attendance_records = query.offset(skip).limit(limit).all()
    return attendance_records