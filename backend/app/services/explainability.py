from sqlalchemy.orm import Session
from app import models
from app.config import settings


def _severity(count: int, low_max: int, medium_max: int) -> str:
    if count <= low_max:
        return "low"
    elif count <= medium_max:
        return "medium"
    return "high"


def generate_explanation(session_id: int, db: Session):
    """
    Builds a structured, human-readable breakdown of every signal
    that contributed to a session's risk score.
    """
    events = db.query(models.Event).filter(models.Event.session_id == session_id).all()
    session_obj = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()

    signals = []

    # --- 1. Tab Switching ---
    tab_switch_count = len([e for e in events if e.event_type == "tab_switch"])
    if tab_switch_count > 0:
        severity = _severity(tab_switch_count, low_max=2, medium_max=5)
        weight = min(tab_switch_count * settings.TAB_SWITCH_WEIGHT, 30)
        signals.append({
            "signal": "tab_switch",
            "triggered": True,
            "severity": severity,
            "weight_contributed": round(weight, 2),
            "raw_count": tab_switch_count,
            "explanation": f"Candidate switched tabs {tab_switch_count} time(s), which may indicate checking external resources."
        })

    # --- 2. Paste Events ---
    paste_events = [e for e in events if e.event_type == "paste"]
    if paste_events:
        total_chars = sum((e.event_metadata or {}).get("text_length", 0) for e in paste_events)
        severity = _severity(len(paste_events), low_max=1, medium_max=3)
        weight = min(len(paste_events) * settings.PASTE_WEIGHT, 30)
        signals.append({
            "signal": "paste",
            "triggered": True,
            "severity": severity,
            "weight_contributed": round(weight, 2),
            "raw_count": len(paste_events),
            "explanation": f"Candidate pasted content {len(paste_events)} time(s), totaling {total_chars} characters, which may indicate copying from an external source."
        })

    # --- 3. Focus Loss ---
    focus_loss_count = len([e for e in events if e.event_type == "focus_loss"])
    if focus_loss_count > 0:
        severity = _severity(focus_loss_count, low_max=2, medium_max=5)
        weight = min(focus_loss_count * settings.FOCUS_LOSS_WEIGHT, 20)
        signals.append({
            "signal": "focus_loss",
            "triggered": True,
            "severity": severity,
            "weight_contributed": round(weight, 2),
            "raw_count": focus_loss_count,
            "explanation": f"Window focus was lost {focus_loss_count} time(s), which may indicate switching to another application or device."
        })

    # --- 4. Submission Speed Anomaly ---
    if session_obj and session_obj.start_time and session_obj.end_time:
        duration_seconds = (session_obj.end_time - session_obj.start_time).total_seconds()
        answer_length = len(session_obj.answer_text or "")
        if answer_length > 200 and duration_seconds < 30:
            signals.append({
                "signal": "speed_anomaly",
                "triggered": True,
                "severity": "high",
                "weight_contributed": settings.SPEED_ANOMALY_WEIGHT,
                "raw_count": 1,
                "explanation": f"Candidate submitted {answer_length} characters in only {int(duration_seconds)} seconds, which is unusually fast for manual typing."
            })

    # --- 5. Copy Events ---
    copy_events = [e for e in events if e.event_type == "copy"]
    if copy_events:
        total_copied = sum((e.event_metadata or {}).get("text_length", 0) for e in copy_events)
        severity = _severity(len(copy_events), low_max=1, medium_max=3)
        weight = min(len(copy_events) * settings.COPY_WEIGHT, 20)
        signals.append({
            "signal": "copy",
            "triggered": True,
            "severity": severity,
            "weight_contributed": round(weight, 2),
            "raw_count": len(copy_events),
            "explanation": f"Candidate copied content {len(copy_events)} time(s), totaling {total_copied} characters, which may indicate external material was captured for reuse."
        })

    # --- 6. Mouse Idle ---
    idle_events = [e for e in events if e.event_type == "mouse_idle"]
    if idle_events:
        total_idle = sum((e.event_metadata or {}).get("idle_seconds", 0) for e in idle_events)
        severity = _severity(len(idle_events), low_max=1, medium_max=3)
        weight = min(len(idle_events) * settings.MOUSE_IDLE_WEIGHT, 15)
        signals.append({
            "signal": "mouse_idle",
            "triggered": True,
            "severity": severity,
            "weight_contributed": round(weight, 2),
            "raw_count": len(idle_events),
            "explanation": f"Mouse was idle {len(idle_events)} time(s), totaling {total_idle} seconds, which may indicate the candidate stepped away or consulted another device."
        })

    # --- 7. Similarity placeholder ---
    # Reserved for future cross-candidate similarity comparison.

    if not signals:
        overall_summary = "No suspicious signals were detected during this session."
    else:
        triggered_names = ", ".join(s["signal"] for s in signals)
        overall_summary = f"{len(signals)} signal(s) triggered: {triggered_names}."

    return {
        "session_id": session_id,
        "overall_summary": overall_summary,
        "signals": signals
    }