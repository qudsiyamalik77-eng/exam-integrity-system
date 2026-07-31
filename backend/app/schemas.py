from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# ---------- Candidate ----------
class CandidateCreate(BaseModel):
    name: str
    email: str


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Session ----------
class SessionCreate(BaseModel):
    candidate_id: int
    exam_name: str
    question_count: Optional[int] = 1


class SessionUpdate(BaseModel):
    answer_text: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    candidate_id: int
    exam_name: str
    question_count: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    mentor_decision: str

    class Config:
        from_attributes = True


# ---------- Event ----------
class EventCreate(BaseModel):
    session_id: int
    event_type: str
    event_metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    id: int
    session_id: int
    event_type: str
    event_metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ---------- Risk Score ----------
class RiskScoreResponse(BaseModel):
    id: int
    session_id: int
    integrity_score: float
    suspicion_score: float
    confidence_score: float
    signals_json: Optional[List[Dict[str, Any]]] = None
    timeline_json: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime

    class Config:
        from_attributes = True


# ---------- Mentor Decision ----------
class MentorDecisionUpdate(BaseModel):
    mentor_decision: str