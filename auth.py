from fastapi import HTTPException
from sqlalchemy.orm import Session
import bcrypt
from models import Employee, Login
from schemas import EmployeeCreate, EmployeeLogin
from datetime import datetime

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def register_user(db: Session, employee: EmployeeCreate):
    # Add password match validation
    if employee.password != employee.repassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    existing_employee = db.query(Employee).filter(Employee.email == employee.email).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_employee = Employee(
        name=employee.name,
        email=employee.email,
        password=get_password_hash(employee.password),
        role=employee.role
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

def login_user(db: Session, employee: EmployeeLogin):
    db_employee = db.query(Employee).filter(Employee.email == employee.email).first()
    if not db_employee or not verify_password(employee.password, db_employee.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Optional: Track login
    login_entry = Login(
        employee_id=db_employee.id,
        login_status=True,
        login_timestamp=datetime.now()
    )
    db.add(login_entry)
    db.commit()

    return db_employee