import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "kaspintar-super-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Database configuration: defaults to SQLite, or can use Supabase / PostgreSQL cloud URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'kaspintar.db'}")

# If deployed on Vercel Serverless and using default SQLite, write to /tmp
if os.getenv("VERCEL"):
    if not os.getenv("DATABASE_URL") or DATABASE_URL.startswith("sqlite"):
        DATABASE_URL = "sqlite:////tmp/kaspintar.db"
    UPLOAD_DIR = Path("/tmp/uploads")
else:
    UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Gemini API Key (can be set via .env or through the Admin Panel UI)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Active model supported on Google GenAI API
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
