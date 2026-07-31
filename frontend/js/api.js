const API_BASE_URL = "http://localhost:8000/api";

async function apiRequest(endpoint, method = "GET", data = null) {
    const options = {
        method: method,
        headers: { "Content-Type": "application/json" }
    };
    if (data) options.body = JSON.stringify(data);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("API Request Failed:", error);
        return null;
    }
}

// ---------- Candidate ----------
async function createCandidate(name, email) {
    return await apiRequest("/sessions/candidates", "POST", { name, email });
}

// ---------- Session ----------
async function createSession(candidateId, examName, questionCount = 10) {
    return await apiRequest("/sessions/", "POST", {
        candidate_id: candidateId,
        exam_name: examName,
        question_count: questionCount
    });
}

async function updateSession(sessionId, data) {
    return await apiRequest(`/sessions/${sessionId}`, "PUT", data);
}

// ---------- Events ----------
async function logEvent(sessionId, eventType, metadata = null) {
    return await apiRequest("/events/", "POST", {
        session_id: sessionId,
        event_type: eventType,
        event_metadata: metadata
    });
}

// ---------- Scoring ----------
async function calculateScore(sessionId) {
    return await apiRequest(`/scoring/${sessionId}/calculate`, "POST");
}

async function getScore(sessionId) {
    return await apiRequest(`/scoring/${sessionId}`, "GET");
}