# main.py - Revised version with fixes and enhancements
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
    return templates.TemplateResponse("/authentication/login.html", {"request": request})

# Only admin can add new employees via dashboard form
@app.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    employee_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(Employee).filter(Employee.id == employee_id).first()
    if not admin or not admin.role:
        return RedirectResponse("/", status_code=303)
    new_employee = auth.register_user(db, EmployeeCreate(
        name=name, email=email, password=password, role=(role == "admin")
    ))
    # After adding, stay on dashboard and show a success message
    total_employees = db.query(Employee).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
    leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").all()
    all_leaves = db.query(LeaveRequest).all()
    return templates.TemplateResponse("/admin/dashboard.html", {
        "request": request,
        "employee": admin,
        "total_employees": total_employees,
        "pending_leaves": pending_leaves,
        "leaves": leaves,
        "all_leaves": all_leaves,
        "add_employee_success": True
    })


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    employee = auth.login_user(db, EmployeeLogin(email=email, password=password))
    if employee.role == 1:
        return RedirectResponse(f"/dashboard?employee_id={employee.id}", status_code=303)
    else:
        return RedirectResponse(f"/employee/dashboard?employee_id={employee.id}", status_code=303)

@app.get("/punch-in", response_class=HTMLResponse)
def punch_in_page(request: Request):
    return templates.TemplateResponse("/authentication/punchin.html", {"request": request})

@app.get("/punch-out", response_class=HTMLResponse)
def punch_out_page(request: Request):
    return templates.TemplateResponse("/authentication/punchout.html", {"request": request})

@app.post("/punch-in")
def punch_in(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == email).first()
    today = date.today()
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee.id, Attendance.date == today).first()
    if attendance:
        return RedirectResponse("/punch-in?error=Already punched in", status_code=303)
    db.add(Attendance(employee_id=employee.id, date=today, punch_in=datetime.now()))
    db.commit()
    return RedirectResponse("/punch-in?success=true", status_code=303)

@app.post("/punch-out")
def punch_out(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == email).first()
    today = date.today()
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee.id, Attendance.date == today).first()
    if not attendance or attendance.punch_out:
        return RedirectResponse("/punch-out?error=Invalid punch out", status_code=303)
    attendance.punch_out = datetime.now()
    db.commit()
    return RedirectResponse("/punch-out?success=true", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or not employee.role:
        return RedirectResponse("/")

    total_employees = db.query(Employee).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
    leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").all()
    all_leaves = db.query(LeaveRequest).all()

    return templates.TemplateResponse("/admin/dashboard.html", {
        "request": request,
        "employee": employee,
        "total_employees": total_employees,
        "pending_leaves": pending_leaves,
        "leaves": leaves,
        "all_leaves": all_leaves
    })

@app.get("/employee/dashboard", response_class=HTMLResponse)
def employee_dashboard(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/")

    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    leaves = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id).all()
    attendance_events = [{"title": "Present", "start": record.date.strftime("%Y-%m-%d")} for record in attendance if record.date]

    return templates.TemplateResponse("/employee/employee_dashboard.html", {
        "request": request,
        "employee": employee,
        "leaves": leaves,
        "attendance_events": attendance_events
    })

@app.get("/employee/apply-leave", response_class=HTMLResponse)
def apply_leave_form(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee or employee.role:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("/employee/leave_modal.html", {"request": request, "employee": employee})

@app.post("/employee/apply-leave")
def submit_leave(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    if start_dt > end_dt:
        return templates.TemplateResponse("/employee/leave_modal.html", {"request": request, "employee": employee, "error": "Start date after end date."})

    # Check overlaps
    existing = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id, LeaveRequest.status.in_(["pending", "approved"])).all()
    for leave in existing:
        if start_dt <= leave.end_date and end_dt >= leave.start_date:
            return templates.TemplateResponse("/employee/leave_modal.html", {"request": request, "employee": employee, "error": "Date overlap with existing leave."})

    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    present_days = {a.date.strftime("%Y-%m-%d") for a in attendance if a.date}
    check_date = start_dt
    while check_date <= end_dt:
        if check_date.strftime("%Y-%m-%d") in present_days:
            return templates.TemplateResponse("/employee/leave_modal.html", {"request": request, "employee": employee, "error": f"Attendance exists on {check_date}"})
        check_date += timedelta(days=1)

    db.add(LeaveRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending"
    ))
    db.commit()
    return templates.TemplateResponse("/employee/leave_modal.html", {"request": request, "employee": employee, "success": True})

@app.get("/employee/attendance", response_class=HTMLResponse)
def employee_attendance(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    attendance = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    return templates.TemplateResponse("/employee/employee_attendance.html", {"request": request, "employee": employee, "attendance": attendance})

@app.get("/employee/leaves", response_class=HTMLResponse)
def employee_leaves(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    leaves = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id).all()
    return templates.TemplateResponse("/employee/employee_leaves.html", {"request": request, "employee": employee, "leaves": leaves})

@app.get("/employee/profile", response_class=HTMLResponse)
def employee_profile(request: Request, db: Session = Depends(get_db)):
    employee_id = int(request.query_params.get("employee_id"))
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    return templates.TemplateResponse("/employee/employee_profile.html", {"request": request, "employee": employee})

@app.get("/logout")
def logout():
    return RedirectResponse("/", status_code=303)