from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List


class EmployeeBase(BaseModel):
    email: EmailStr
    name: str
    department: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    xhandler: Optional[str] = None
    linkedin: Optional[str] = None
    bio: Optional[str] = None
    contact_number: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    department: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    xhandler: Optional[str] = None
    linkedin: Optional[str] = None
    bio: Optional[str] = None
    contact_number: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    is_present: bool = False
    status: str = "absent"
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    is_present: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    is_present_today: bool
    today_attendance_status: str
    today_check_in_time: Optional[datetime]

    class Config:
        from_attributes = True


class EmployeeWithAttendance(EmployeeResponse):
    attendance_records: List[AttendanceResponse] = []

    class Config:
        from_attributes = True


class CheckInRequest(BaseModel):
    notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    notes: Optional[str] = None


class MarkAbsentRequest(BaseModel):
    notes: Optional[str] = None