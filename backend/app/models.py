from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("ExamSession", back_populates="candidate")


class ExamSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    exam_name = Column(String, nullable=False)
    question_count = Column(Integer, default=1)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="in_progress")
    answer_text = Column(Text, nullable=True)
    mentor_decision = Column(String, default="pending")

    candidate = relationship("Candidate", back_populates="sessions")
    events = relationship("Event", back_populates="session")
    score = relationship("RiskScore", back_populates="session", uselist=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    event_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ExamSession", back_populates="events")


class RiskScore(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True, nullable=False)
    integrity_score = Column(Float, default=100.0)
    suspicion_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    signals_json = Column(JSON, nullable=True)
    timeline_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ExamSession", back_populates="score")