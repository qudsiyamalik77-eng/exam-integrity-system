from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import events, sessions, scoring, reports, dashboard

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Exam Integrity & Cheating Detection System",
    description="API for monitoring assessment sessions and detecting suspicious behavior",
    version="1.0.0"
)

# CORS - allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Risk Scoring"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Mentor Dashboard"])

@app.get("/")
def root():
    return {"message": "AI Exam Integrity System API is running", "docs": "/docs"}