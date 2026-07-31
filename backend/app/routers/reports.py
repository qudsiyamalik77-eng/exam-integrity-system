from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import os

from app.database import get_db
from app import models

router = APIRouter()

REPORTS_DIR = "generated_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


@router.get("/{session_id}/pdf")
def generate_report(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    candidate = db.query(models.Candidate).filter(models.Candidate.id == session.candidate_id).first()
    score = db.query(models.RiskScore).filter(models.RiskScore.session_id == session_id).first()

    file_path = os.path.join(REPORTS_DIR, f"integrity_report_session_{session_id}.pdf")

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def line(text, size=11, gap=0.7):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(2 * cm, y, text)
        y -= gap * cm

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "AI Exam Integrity Report")
    y -= 1.2 * cm

    line(f"Candidate Name: {candidate.name if candidate else 'Unknown'}")
    line(f"Candidate Email: {candidate.email if candidate else 'Unknown'}")
    line(f"Exam: {session.exam_name}")
    line(f"Session ID: {session.id}")
    line(f"Status: {session.status}")
    line(f"Mentor Decision: {session.mentor_decision}")
    y -= 0.4 * cm

    if score:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(2 * cm, y, "Risk Scores")
        y -= 0.9 * cm
        line(f"Integrity Score: {score.integrity_score}")
        line(f"Suspicion Score: {score.suspicion_score}")
        line(f"Confidence Score: {score.confidence_score}")
        y -= 0.4 * cm

        c.setFont("Helvetica-Bold", 13)
        c.drawString(2 * cm, y, "Behavioral Signals")
        y -= 0.9 * cm

        if score.signals_json:
            for signal in score.signals_json:
                line(f"- {signal['name']}: score={signal['score']}, confidence={signal['confidence']}")
                for ev in signal.get("evidence", []):
                    line(f"    • {ev}", size=9, gap=0.5)
                y -= 0.2 * cm
                if y < 3 * cm:
                    c.showPage()
                    y = height - 2 * cm
    else:
        line("No risk score calculated yet for this session.")

    c.save()

    return FileResponse(file_path, media_type="application/pdf", filename=f"integrity_report_{session_id}.pdf")