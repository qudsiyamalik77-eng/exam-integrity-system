from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()


# Log a new event (called constantly from frontend JS during exam)
@router.post("/", response_model=schemas.EventResponse)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == event.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    new_event = models.Event(
        session_id=event.session_id,
        event_type=event.event_type,
        event_metadata=event.event_metadata
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


# Get all events for a session (used for timeline)
@router.get("/session/{session_id}", response_model=list[schemas.EventResponse])
def get_session_events(session_id: int, db: Session = Depends(get_db)):
    events = db.query(models.Event).filter(models.Event.session_id == session_id).order_by(models.Event.timestamp).all()
    return events