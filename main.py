from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from pydantic import BaseModel

import numpy as np
import pickle

from models import Student, AcademicRecord, Prediction
from db import SessionLocal

# ================= APP =================
app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= STATIC =================
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ================= DB =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= MODEL =================
try:
    with open("dropout_model.pkl", "rb") as f:
        model = pickle.load(f)
except:
    model = None

# ================= SCHEMAS =================
class StudentCreate(BaseModel):
    name: str
    age: int
    gender: str
    income: int
    attendance: int

class AcademicCreate(BaseModel):
    student_id: int
    attendance: float
    marks: float

class PredictionInput(BaseModel):
    attendance: float
    marks: float
    age: int
    gender: int
    income: int

# ================= FRONTEND =================
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    return templates.TemplateResponse("add_student.html", {"request": request})

# ================= API =================

# ✅ CREATE STUDENT (FIXED)
@app.post("/students")
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    new_student = Student(
        name=data.name,
        age=data.age,
        gender=data.gender,
        attendance=data.attendance,
        income=data.income
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


# ✅ ADD ACADEMIC
@app.post("/academic")
def add_academic(record: AcademicCreate, db: Session = Depends(get_db)):
    new_record = AcademicRecord(
        student_id=record.student_id,
        attendance=record.attendance,
        marks=record.marks
    )

    db.add(new_record)
    db.commit()

    return {"message": "Academic added"}


# ✅ PREDICT
@app.post("/predict/{student_id}")
def predict(student_id: int, data: PredictionInput, db: Session = Depends(get_db)):

    features = np.array([[data.attendance, data.marks, data.age, data.gender, data.income]])

    if model:
        risk_score = model.predict_proba(features)[0][1]
    else:
        risk_score = (
            (1 - data.attendance / 100) * 0.4 +
            (1 - data.marks / 100) * 0.4 +
            (0.2 if data.income < 3000 else 0)
        )

    risk_score = round(min(max(risk_score, 0), 1), 2)

    risk_level = "High" if risk_score > 0.7 else "Medium" if risk_score > 0.4 else "Low"

    new_prediction = Prediction(
        student_id=student_id,
        risk_score=risk_score,
        risk_level=risk_level
    )

    db.add(new_prediction)
    db.commit()

    return {"risk": risk_level, "score": risk_score}


# ✅ FETCH STUDENTS (FOR FRONTEND)
@app.get("/students")
def get_students(db: Session = Depends(get_db)):

    students = db.query(Student).all()
    result = []

    for s in students:

        academic = db.query(AcademicRecord).filter(
            AcademicRecord.student_id == s.id
        ).first()

        prediction = db.query(Prediction).filter(
            Prediction.student_id == s.id
        ).first()

        result.append({
            "id": s.id,
            "name": s.name,
            "age": s.age,
            "attendance": academic.attendance if academic else 0,
            "marks": academic.marks if academic else 0,
            "risk": prediction.risk_level if prediction else "Low"
        })

    return result