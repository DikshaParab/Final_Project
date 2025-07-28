from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from schemas import EmployeeCreate, EmployeeLogin
from models import Employee, Attendance, LeaveRequest
from datetime import date, datetime, timedelta
import models, auth
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    repassword: str = Form(...),  
    role: bool = Form(...),
    db: Session = Depends(get_db)
):
    
    # Pass all parameters including repassword
    new_employee = auth.register_user(db, EmployeeCreate(
        name=name, 
        email=email, 
        password=password,
        repassword=repassword,  # Add this
        role=role
    ))
    print(new_employee)
    return RedirectResponse("/", status_code=303)

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    employee = auth.login_user(db, EmployeeLogin(email=email, password=password))
    if employee.role == 1:  # Admin
        return RedirectResponse(f"/dashboard?employee_id={employee.id}", status_code=303)
    else:
        return RedirectResponse(f"/employee/dashboard?employee_id={employee.id}", status_code=303)

# GET endpoint for punch-in page
@app.get("/punch-in", response_class=HTMLResponse)
def punch_in_page(request: Request):
    return templates.TemplateResponse("punchin.html", {"request": request})

# GET endpoint for punch-out page
@app.get("/punch-out", response_class=HTMLResponse)
def punch_out_page(request: Request):
    return templates.TemplateResponse("punchout.html", {"request": request})

# Punch In endpoint
@app.post("/punch-in")
def punch_in(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == email).first()
    if not employee:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid Email"})
    from datetime import date, datetime
    today = date.today()
    # Check if already punched in today
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee.id, Attendance.date == today).first()
    if attendance:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Already punched in today."})
    new_attendance = Attendance(employee_id=employee.id, date=today, punch_in=datetime.now())
    db.add(new_attendance)
    db.commit()
    return templates.TemplateResponse("login.html", {"request": request, "success": "Punched in successfully!"})

# Punch Out endpoint
@app.post("/punch-out")
def punch_out(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == email).first()
    if not employee:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid Email"})
    today = date.today()
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee.id, Attendance.date == today).first()
    if not attendance:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Punch in first before punching out."})
    if attendance.punch_out:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Already punched out today."})
    attendance.punch_out = datetime.now()
    db.commit()
    return templates.TemplateResponse("login.html", {"request": request, "success": "Punched out successfully!"})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or not employee.role:
        return RedirectResponse("/")
    # You can add admin-specific data here if needed
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "employee": employee
    })

@app.get("/employee/dashboard", response_class=HTMLResponse)
def employee_dashboard(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/")

    # Get attendance data with proper date handling
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    attendance_events = [
        {
            "title": "Present",
            "start": record.date.strftime("%Y-%m-%d") if record.date else None
        }
        for record in attendance if record.date
    ]

    # Get leave requests
    leaves = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id).all()

    return templates.TemplateResponse("employee_dashboard.html", {
        "request": request,
        "employee": employee,
        "leaves": leaves,
        "attendance_events": [e for e in attendance_events if e['start']]
    })

def apply_leave(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    employee_id = int(request.query_params.get("employee_id"))
    leave = LeaveRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending"
    )
    db.add(leave)
    db.commit()
    return RedirectResponse(f"/employee/dashboard?employee_id={employee_id}", status_code=303)

# GET endpoint to render the leave application modal page
@app.get("/employee/apply-leave", response_class=HTMLResponse)
def apply_leave_form(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("leave_modal.html", {
        "request": request,
        "employee": employee
    })

# POST endpoint to handle leave application form submission
@app.post("/employee/apply-leave")
def apply_leave(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    # Validation: start_date <= end_date
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        return templates.TemplateResponse("leave_modal.html", {
            "request": request,
            "employee": employee,
            "error": "Invalid date format."
        })
    if start_dt > end_dt:
        return templates.TemplateResponse("leave_modal.html", {
            "request": request,
            "employee": employee,
            "error": "Start date cannot be after end date."
        })
    # Validation: no overlap with existing leaves
    existing_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(["pending", "approved"])
    ).all()
    for leave in existing_leaves:
        leave_start = datetime.strptime(str(leave.start_date), "%Y-%m-%d")
        leave_end = datetime.strptime(str(leave.end_date), "%Y-%m-%d")
        if start_dt <= leave_end and end_dt >= leave_start:
            return templates.TemplateResponse("leave_modal.html", {
                "request": request,
                "employee": employee,
                "error": "Leave dates overlap with an existing leave request."
            })
    # Validation: no overlap with attendance (already present days)
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    present_dates = set([a.date.strftime("%Y-%m-%d") for a in attendance if a.date])
    check_date = start_dt
    while check_date <= end_dt:
        if check_date.strftime("%Y-%m-%d") in present_dates:
            return templates.TemplateResponse("leave_modal.html", {
                "request": request,
                "employee": employee,
                "error": f"You already have attendance marked on {check_date.strftime('%Y-%m-%d')}."
            })
        check_date += timedelta(days=1)
    # If all validations pass, create leave
    leave = LeaveRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending"
    )
    db.add(leave)
    db.commit()
    return templates.TemplateResponse("leave_modal.html", {
        "request": request,
        "employee": employee,
        "success": True
    })

@app.get("/employee/attendance", response_class=HTMLResponse)
def employee_attendance(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/")
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    return templates.TemplateResponse("employee_attendance.html", {
        "request": request,
        "employee": employee,
        "attendance": attendance
    })

@app.get("/employee/leaves", response_class=HTMLResponse)
def employee_leaves(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/")
    leaves = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id).all()
    return templates.TemplateResponse("employee_leaves.html", {
        "request": request,
        "employee": employee,
        "leaves": leaves
    })

@app.get("/employee/profile", response_class=HTMLResponse)
def employee_profile(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/")
    return templates.TemplateResponse("employee_profile.html", {
        "request": request,
        "employee": employee
    })

@app.get("/logout")
def logout():
    # For now, just redirect to login page. Implement session clearing if needed.
    return RedirectResponse("/", status_code=303)