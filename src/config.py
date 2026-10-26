import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CORPUS_DIR = DATA_DIR / "corpus"
INDEX_DIR = DATA_DIR / "index"
QUARANTINE_DIR = DATA_DIR / "quarantine"

class Settings(BaseModel):
    # App Settings
    APP_NAME: str = "Health Insurance Pre-Authorisation Desk"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # LLM & Mode
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "stub")  # "stub", "gemini", or "ollama"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")

    # Agent Loop Bounds (A1)
    MAX_AGENT_STEPS: int = int(os.getenv("MAX_AGENT_STEPS", "6"))
    MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "8"))
    WALL_CLOCK_TIMEOUT_SEC: float = float(os.getenv("WALL_CLOCK_TIMEOUT_SEC", "25.0"))

    # Resilience & Circuit Breaker (A5)
    CIRCUIT_BREAKER_FAIL_THRESHOLD: int = int(os.getenv("CB_FAIL_THRESHOLD", "3"))
    CIRCUIT_BREAKER_RESET_TIMEOUT_SEC: float = float(os.getenv("CB_RESET_TIMEOUT_SEC", "30.0"))
    CALL_TIMEOUT_SEC: float = float(os.getenv("CALL_TIMEOUT_SEC", "8.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    # Service Level Objective (D6)
    SLO_P95_SECONDS: float = float(os.getenv("SLO_P95_SECONDS", "2.5"))  # Target p95 in stub mode

    # Rate Limiting & Caching (D7)
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL_SEC: int = int(os.getenv("CACHE_TTL_SEC", "3600"))

    # Prompt Version (L2)
    ACTIVE_PROMPT_VERSION: str = os.getenv("ACTIVE_PROMPT_VERSION", "v2")

settings = Settings()
