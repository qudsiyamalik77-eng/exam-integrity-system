from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session as DBSession

from app.models import Event, ExamSession, RiskScore
from app.services.similarity import max_similarity_against_peers


@dataclass
class SignalResult:
    name: str
    score: float
    weight: float
    confidence: float
    evidence: List[str] = field(default_factory=list)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _safe_stdev(values: List[float]) -> float:
    return pstdev(values) if len(values) > 1 else 0.0


def _filter(events: List[Event], event_type: str) -> List[Event]:
    return [e for e in events if e.event_type == event_type]


def _meta(e: Event, key: str, default=None):
    return (e.event_metadata or {}).get(key, default)


def detect_tab_switching(events: List[Event]) -> SignalResult:
    switches = _filter(events, "tab_switch") + _filter(events, "blur")
    count = len(switches)
    score = _clamp((count / 15) * 100)
    confidence = _clamp(min(count, 5) / 5, 0, 1)

    evidence = [f"{count} tab-switch/blur events detected"]
    if len(switches) > 1:
        gaps = [(switches[i].timestamp - switches[i-1].timestamp).total_seconds()
                for i in range(1, len(switches))]
        evidence.append(f"avg gap between switches: {mean(gaps):.1f}s")

    return SignalResult("tab_switching", score, weight=0.15, confidence=confidence, evidence=evidence)


def detect_copy_paste(events: List[Event]) -> SignalResult:
    pastes = _filter(events, "paste")
    copies = _filter(events, "copy")
    large_pastes = [p for p in pastes if _meta(p, "char_count", 0) > 50]

    raw = len(pastes) * 8 + len(large_pastes) * 12
    score = _clamp(raw)
    confidence = _clamp(min(len(pastes) + len(copies), 5) / 5, 0, 1)

    evidence = [f"{len(pastes)} paste, {len(copies)} copy events",
                f"{len(large_pastes)} large paste(s) (>50 chars)"]

    return SignalResult("copy_paste", score, weight=0.20, confidence=confidence, evidence=evidence)


def detect_typing_pattern(events: List[Event]) -> SignalResult:
    keys = _filter(events, "keydown")
    if len(keys) < 10:
        return SignalResult("typing_pattern", 0, weight=0.15, confidence=0.1,
                             evidence=["Insufficient keystroke data"])

    intervals = [(keys[i].timestamp - keys[i-1].timestamp).total_seconds()
                 for i in range(1, len(keys))]
    intervals = [i for i in intervals if i >= 0]

    avg_interval = mean(intervals) if intervals else 0
    stdev_interval = _safe_stdev(intervals)
    cv = stdev_interval / avg_interval if avg_interval > 0 else 0

    evidence = [f"avg keystroke interval: {avg_interval:.3f}s", f"CV: {cv:.2f}"]

    if cv < 0.15:
        score = 80
        evidence.append("Typing rhythm unusually mechanical/consistent")
    elif cv > 2.0:
        score = 40
        evidence.append("Typing rhythm unusually erratic")
    else:
        score = 10

    confidence = _clamp(min(len(keys), 100) / 100, 0, 1)
    return SignalResult("typing_pattern", score, weight=0.15, confidence=confidence, evidence=evidence)


def detect_mouse_activity(events: List[Event]) -> SignalResult:
    moves = _filter(events, "mousemove")
    if len(moves) < 5:
        return SignalResult("mouse_activity", 30, weight=0.10, confidence=0.2,
                             evidence=["Very little mouse activity recorded"])

    gaps = [(moves[i].timestamp - moves[i-1].timestamp).total_seconds()
            for i in range(1, len(moves))]
    long_gaps = [g for g in gaps if g > 30]
    score = _clamp(len(long_gaps) * 10)
    confidence = _clamp(min(len(moves), 50) / 50, 0, 1)

    evidence = [f"{len(long_gaps)} inactivity gap(s) > 30s", f"total mouse events: {len(moves)}"]
    return SignalResult("mouse_activity", score, weight=0.10, confidence=confidence, evidence=evidence)


def detect_submission_speed(events: List[Event], question_count: int) -> SignalResult:
    submits = _filter(events, "submit")
    starts = _filter(events, "assessment_start")

    if not submits or not starts:
        return SignalResult("submission_speed", 0, weight=0.10, confidence=0.1,
                             evidence=["Missing start/submit timestamps"])

    duration = (submits[0].timestamp - starts[0].timestamp).total_seconds()
    expected_min_seconds = max(question_count, 1) * 20

    evidence = [f"total duration: {duration:.0f}s", f"expected minimum: {expected_min_seconds:.0f}s"]

    if duration < expected_min_seconds * 0.5:
        score = 90
        evidence.append("Submission far too fast for question count")
    elif duration < expected_min_seconds * 0.8:
        score = 50
        evidence.append("Submission faster than expected")
    else:
        score = 5

    return SignalResult("submission_speed", score, weight=0.10, confidence=0.7, evidence=evidence)


def detect_answer_similarity(
    candidate_answer: Optional[str],
    peer_answers: Optional[List[str]],
) -> SignalResult:
    if not candidate_answer or not peer_answers:
        return SignalResult("answer_similarity", 0, weight=0.15, confidence=0.0,
                             evidence=["Similarity check not run (no peer answers available)"])

    similarity, _ = max_similarity_against_peers(candidate_answer, peer_answers)
    score = _clamp(similarity * 100)
    evidence = [f"max cosine similarity with peer answers: {similarity:.2f}"]

    return SignalResult("answer_similarity", score, weight=0.15, confidence=0.9, evidence=evidence)


def detect_multi_device(events: List[Event]) -> SignalResult:
    device_events = _filter(events, "device_fingerprint")
    ip_events = _filter(events, "ip_info")

    unique_devices = {_meta(e, "fingerprint") for e in device_events if _meta(e, "fingerprint")}
    unique_ips = {_meta(e, "ip") for e in ip_events if _meta(e, "ip")}
    vpn_flags = [e for e in ip_events if _meta(e, "is_vpn_or_proxy")]

    score = 0.0
    evidence = []

    if len(unique_devices) > 1:
        score += 50
        evidence.append(f"{len(unique_devices)} distinct device fingerprints in one session")
    if len(unique_ips) > 1:
        score += 30
        evidence.append(f"{len(unique_ips)} distinct IPs used")
    if vpn_flags:
        score += 20
        evidence.append("VPN/proxy indicator flagged on at least one IP")
    if not evidence:
        evidence = ["Single device/IP, no VPN flags"]

    confidence = 0.8 if (device_events or ip_events) else 0.2
    return SignalResult("multi_device_vpn", _clamp(score), weight=0.10, confidence=confidence, evidence=evidence)


NOTABLE_TYPES = {"tab_switch", "blur", "paste", "copy", "submit",
                  "assessment_start", "device_fingerprint", "ip_info"}


def build_timeline(events: List[Event]) -> List[Dict[str, Any]]:
    timeline = []
    for e in sorted(events, key=lambda x: x.timestamp):
        if e.event_type in NOTABLE_TYPES:
            timeline.append({
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "metadata": e.event_metadata or {},
            })
    return timeline


def calculate_and_save_risk_report(
    db: DBSession,
    session_id: int,
    candidate_answer: Optional[str] = None,
    peer_answers: Optional[List[str]] = None,
) -> RiskScore:
    session_obj = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if session_obj is None:
        raise ValueError(f"Session {session_id} not found")

    events = db.query(Event).filter(Event.session_id == session_id).all()

    signals = [
        detect_tab_switching(events),
        detect_copy_paste(events),
        detect_typing_pattern(events),
        detect_mouse_activity(events),
        detect_submission_speed(events, session_obj.question_count or 1),
        detect_answer_similarity(candidate_answer, peer_answers),
        detect_multi_device(events),
    ]

    weighted_sum = 0.0
    weight_total = 0.0
    for s in signals:
        effective_weight = s.weight * (0.5 + 0.5 * s.confidence)
        weighted_sum += s.score * effective_weight
        weight_total += effective_weight

    suspicion_score = _clamp(weighted_sum / weight_total) if weight_total > 0 else 0.0
    integrity_score = _clamp(100 - suspicion_score)

    max_possible_weight = sum(s.weight for s in signals)
    confidence_score = _clamp((weight_total / max_possible_weight) * 100) if max_possible_weight > 0 else 0.0

    timeline = build_timeline(events)

    existing = db.query(RiskScore).filter(RiskScore.session_id == session_id).first()
    if existing:
        existing.integrity_score = round(integrity_score, 1)
        existing.suspicion_score = round(suspicion_score, 1)
        existing.confidence_score = round(confidence_score, 1)
        existing.signals_json = [
            {"name": s.name, "score": round(s.score, 1), "weight": s.weight,
             "confidence": round(s.confidence, 2), "evidence": s.evidence}
            for s in signals
        ]
        existing.timeline_json = timeline
        existing.generated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    new_score = RiskScore(
        session_id=session_id,
        integrity_score=round(integrity_score, 1),
        suspicion_score=round(suspicion_score, 1),
        confidence_score=round(confidence_score, 1),
        signals_json=[
            {"name": s.name, "score": round(s.score, 1), "weight": s.weight,
             "confidence": round(s.confidence, 2), "evidence": s.evidence}
            for s in signals
        ],
        timeline_json=timeline,
        generated_at=datetime.utcnow(),
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return new_score