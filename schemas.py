from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ---------- Registration & Login Event Schemas ----------

class RegistrationEvent(BaseModel):
    id: int
    user_id: int
    registration_timestamp: datetime
    registration_status: bool

    class Config:
        from_attributes = True

class LoginEvent(BaseModel):
    id: int
    user_id: int
    login_timestamp: datetime
    login_status: bool

    class Config:
        from_attributes = True

# ---------- User Schemas ----------

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    repassword: str 
    role: bool  # 0 for employee, 1 for admin

class EmployeeLogin(BaseModel):
    email: EmailStr
    password: str

class EmployeeOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: bool

    class Config:
        from_attributes = True

# ---------- Attendance Schemas ----------

class AttendanceCreate(BaseModel):
    in_time: Optional[datetime]
    out_time: Optional[datetime]

class AttendanceOut(BaseModel):
    id: int
    date: datetime
    in_time: Optional[datetime]
    out_time: Optional[datetime]

    class Config:
        from_attributes = True

# ---------- Leave Schemas ----------

class LeaveRequestCreate(BaseModel):
    start_date: datetime
    end_date: datetime
    reason: str

class LeaveRequestOut(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime
    reason: str
    status: str

    class Config:
        from_attributes = True

# ---------- Login Schema (optional) ----------

class LoginOut(BaseModel):
    id: int
    login_timestamp: datetime
    login_status: bool

    class Config:
        from_attributes = True
