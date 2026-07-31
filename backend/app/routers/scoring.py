from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.risk_engine import calculate_and_save_risk_report

router = APIRouter()


@router.post("/{session_id}/calculate", response_model=schemas.RiskScoreResponse)
def calculate_score(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result = calculate_and_save_risk_report(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result


@router.get("/{session_id}", response_model=schemas.RiskScoreResponse)
def get_score(session_id: int, db: Session = Depends(get_db)):
    score = db.query(models.RiskScore).filter(models.RiskScore.session_id == session_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found for this session. Calculate it first.")
    return score