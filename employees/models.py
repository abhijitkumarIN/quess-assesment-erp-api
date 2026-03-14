from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Time
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime, date
from typing import Dict, Any


class Employees(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    xhandler = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # Relationship to attendance records
    attendance_records = relationship("Attendance", back_populates="employee")
    
    @property
    def is_present_today(self):
        """Check if employee is present today"""
        today = date.today()
        today_attendance = next(
            (record for record in self.attendance_records if record.date == today), 
            None
        )
        return today_attendance.is_present if today_attendance else False
    
    @property
    def today_attendance_status(self):
        """Get today's attendance status"""
        today = date.today()
        today_attendance = next(
            (record for record in self.attendance_records if record.date == today), 
            None
        )
        return today_attendance.status if today_attendance else "absent"
    
    @property
    def today_check_in_time(self):
        """Get today's check-in time"""
        today = date.today()
        today_attendance = next(
            (record for record in self.attendance_records if record.date == today), 
            None
        )
        return today_attendance.check_in_time if today_attendance else None


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    is_present = Column(Boolean, default=False)
    status = Column(String, default="absent")  # present, absent, late, half_day
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to employee
    employee = relationship("Employees", back_populates="attendance_records")