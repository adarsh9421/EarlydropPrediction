from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


# ================= STUDENT =================
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    income = Column(Integer)

    # Relationships
    academic_records = relationship("AcademicRecord", back_populates="student")
    predictions = relationship("Prediction", back_populates="student")


# ================= ACADEMIC =================
class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    attendance = Column(Float)
    marks = Column(Float)

    # Relationship
    student = relationship("Student", back_populates="academic_records")


# ================= PREDICTION =================
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    risk_score = Column(Float)
    risk_level = Column(String)

    # Relationship
    student = relationship("Student", back_populates="predictions")