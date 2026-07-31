from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/candidates", response_model=schemas.CandidateResponse)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Candidate).filter(models.Candidate.email == candidate.email).first()
    if existing:
        return existing
    new_candidate = models.Candidate(name=candidate.name, email=candidate.email)
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    return new_candidate


@router.get("/candidates", response_model=list[schemas.CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).all()


@router.post("/", response_model=schemas.SessionResponse)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == session.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    new_session = models.ExamSession(
        candidate_id=session.candidate_id,
        exam_name=session.exam_name,
        question_count=session.question_count or 1,
        status="in_progress"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.get("/{session_id}", response_model=schemas.SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/", response_model=list[schemas.SessionResponse])
def get_all_sessions(db: Session = Depends(get_db)):
    return db.query(models.ExamSession).all()


@router.put("/{session_id}", response_model=schemas.SessionResponse)
def update_session(session_id: int, update: schemas.SessionUpdate, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.answer_text is not None:
        session.answer_text = update.answer_text
    if update.status is not None:
        session.status = update.status
        if update.status == "submitted":
            session.end_time = datetime.utcnow()

    db.commit()
    db.refresh(session)
    return session


@router.put("/{session_id}/decision", response_model=schemas.SessionResponse)
def update_mentor_decision(session_id: int, decision: schemas.MentorDecisionUpdate, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.mentor_decision = decision.mentor_decision
    session.status = "reviewed"
    db.commit()
    db.refresh(session)
    return session


# --- NAYA SUBMISSION ENDPOINT FRONTEND KE LIYE ---
@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_exam_session(payload: dict, db: Session = Depends(get_db)):
    """
    Frontend se aane wala exam data (responses, warnings, student name) 
    yahan receive hoga aur logs/database mein process hoga.
    """
    try:
        student_name = payload.get("student_name", "Unknown Student")
        warnings = payload.get("warnings", 0)
        responses = payload.get("responses", {})
        
        print(f"--- Assessment Submitted ---")
        print(f"Student: {student_name}")
        print(f"Warnings / Violations: {warnings}")
        print(f"Answers Data: {responses}")

        # Yahan aap chahein toh session ko database mein 'submitted' mark kar sakte hain
        return {
            "status": "success",
            "message": "Exam successfully submitted and recorded.",
            "student_name": student_name,
            "warnings_recorded": warnings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))