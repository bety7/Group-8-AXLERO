"""Central configuration, read from environment / .env at the repo root."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

CUBE_API_URL = os.getenv("CUBE_API_URL", "http://localhost:4000/cubejs-api").rstrip("/")
CUBEJS_API_SECRET = os.getenv("CUBEJS_API_SECRET", "change-me")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

# ---- Cost governance ----
MAX_QUERIES_PER_QUESTION = int(os.getenv("MAX_QUERIES_PER_QUESTION", "6"))
MAX_ROWS = int(os.getenv("MAX_ROWS", "500"))
DEFAULT_ROW_LIMIT = int(os.getenv("DEFAULT_ROW_LIMIT", "200"))
DEFAULT_DATE_RANGE = os.getenv("DEFAULT_DATE_RANGE", "last 12 months")
MAX_MEASURES = 6
MAX_DIMENSIONS = 3
MAX_RANGE_DAYS = 5 * 366
MAX_FILTER_VALUES = 50

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
