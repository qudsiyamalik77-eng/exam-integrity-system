from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services.explainability import generate_explanation

router = APIRouter()

FLAGGED_THRESHOLD = 50.0  # suspicion_score >= this is considered flagged


def _session_summary(session_obj, score_obj):
    return {
        "session_id": session_obj.id,
        "candidate_id": session_obj.candidate_id,
        "candidate_name": session_obj.candidate.name if session_obj.candidate else None,
        "candidate_email": session_obj.candidate.email if session_obj.candidate else None,
        "exam_name": session_obj.exam_name,
        "status": session_obj.status,
        "mentor_decision": session_obj.mentor_decision,
        "integrity_score": score_obj.integrity_score if score_obj else None,
        "suspicion_score": score_obj.suspicion_score if score_obj else None,
        "confidence_score": score_obj.confidence_score if score_obj else None,
    }


# All sessions with score summary (mentor overview)
@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(models.ExamSession).all()
    result = []
    for s in sessions:
        score = db.query(models.RiskScore).filter(models.RiskScore.session_id == s.id).first()
        result.append(_session_summary(s, score))
    return result


# Only flagged sessions (suspicion_score above threshold)
@router.get("/flagged")
def list_flagged_sessions(db: Session = Depends(get_db)):
    flagged = (
        db.query(models.ExamSession, models.RiskScore)
        .join(models.RiskScore, models.RiskScore.session_id == models.ExamSession.id)
        .filter(models.RiskScore.suspicion_score >= FLAGGED_THRESHOLD)
        .all()
    )
    return [_session_summary(s, score) for s, score in flagged]


# Dashboard Metrics Endpoint (Resolves 404 on /api/dashboard/metrics)
@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_sessions = db.query(models.ExamSession).count()
    submitted_sessions = db.query(models.ExamSession).filter(models.ExamSession.status == "submitted").count()
    
    flagged_count = (
        db.query(models.RiskScore)
        .filter(models.RiskScore.suspicion_score >= FLAGGED_THRESHOLD)
        .count()
    )
    
    return {
        "total_sessions": total_sessions,
        "submitted_sessions": submitted_sessions,
        "flagged_sessions": flagged_count,
        "system_status": "Healthy"
    }


# Full timeline + explanation for one session (for detailed review)
@router.get("/{session_id}/timeline")
def session_timeline(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session_obj:
        return {"error": "Session not found"}

    events = (
        db.query(models.Event)
        .filter(models.Event.session_id == session_id)
        .order_by(models.Event.timestamp)
        .all()
    )
    score = db.query(models.RiskScore).filter(models.RiskScore.session_id == session_id).first()
    explanation = generate_explanation(session_id, db)

    return {
        "candidate": {
            "id": session_obj.candidate.id,
            "name": session_obj.candidate.name,
            "email": session_obj.candidate.email,
        } if session_obj.candidate else None,
        "session": {
            "id": session_obj.id,
            "exam_name": session_obj.exam_name,
            "status": session_obj.status,
            "mentor_decision": session_obj.mentor_decision,
            "start_time": session_obj.start_time,
            "end_time": session_obj.end_time,
        },
        "score": {
            "integrity_score": score.integrity_score if score else None,
            "suspicion_score": score.suspicion_score if score else None,
            "confidence_score": score.confidence_score if score else None,
        } if score else None,
        "events": [
            {
                "event_type": e.event_type,
                "event_metadata": e.event_metadata,
                "timestamp": e.timestamp,
            }
            for e in events
        ],
        "explanation": explanation,
    }