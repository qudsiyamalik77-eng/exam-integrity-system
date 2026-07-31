document.addEventListener("DOMContentLoaded", () => {
    const candidateId = localStorage.getItem("candidateId") || "EMP-102";

    // Track Tab Switching / Visibility Changes
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            sendEvent("tab_switch", "Student navigated away from the assessment tab.");
        }
    });

    // Track Window Blur (Focus Lost)
    window.addEventListener("blur", () => {
        sendEvent("window_blur", "Student lost window focus.");
    });

    // Track Copy/Paste Abuse
    document.addEventListener("copy", () => {
        sendEvent("copy_event", "Clipboard copy action intercepted.");
    });

    document.addEventListener("paste", () => {
        sendEvent("paste_event", "External text paste action intercepted.");
    });

    function sendEvent(eventType, description) {
        const payload = {
            candidate_id: candidateId,
            event_type: eventType,
            description: description,
            timestamp: new Date().toISOString()
        };

        // Send to Backend API
        apiRequest('/log-event', 'POST', payload);
        console.warn(`[INTEGRITY ALERT] ${eventType}: ${description}`);
    }
});