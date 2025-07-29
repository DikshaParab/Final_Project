from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    role = Column(Boolean, nullable=False)  # 'admin' or 'employee'

    # Explicit relationships with foreign_keys
    attendance = relationship("Attendance", back_populates="employee", 
                            foreign_keys="Attendance.employee_id", cascade="all, delete-orphan")
    
    leaves = relationship("LeaveRequest", back_populates="employee", 
                         foreign_keys="LeaveRequest.employee_id", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role
        }
    
class Login(Base):
    __tablename__ = "login"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    login_timestamp = Column(DateTime, nullable=False, default=func.now())
    login_status = Column(Boolean, nullable=False)
    employee = relationship("Employee", foreign_keys=[employee_id])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "login_timestamp": self.login_timestamp,
            "login_status": self.login_status
        }

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, default=datetime.now)
    in_time = Column(DateTime)
    out_time = Column(DateTime)

    employee = relationship("Employee", back_populates="attendance", 
                          foreign_keys=[employee_id])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.date,
            "in_time": self.in_time,
            "out_time": self.out_time
        }
    
class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # 'pending', 'approved', 'rejected'
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="leaves", 
                          foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approved_by])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": self.reason,
            "status": self.status,
            "approved_by": self.approved_by
        }   