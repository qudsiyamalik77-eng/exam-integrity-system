import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./exam_integrity.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-later")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Risk scoring thresholds (tweak these later based on testing)
    TAB_SWITCH_WEIGHT: float = 5.0
    PASTE_WEIGHT: float = 8.0
    FOCUS_LOSS_WEIGHT: float = 4.0
    SPEED_ANOMALY_WEIGHT: float = 10.0
    SIMILARITY_WEIGHT: float = 15.0

settings = Settings()