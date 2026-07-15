import os
import sys
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import normalize_database_url, settings  # noqa: E402
from scraper.config import settings as scraper_settings  # noqa: E402

# Prefer CI/secret env; always normalize for Neon (+psycopg, sslmode).
_raw_url = os.environ.get("DATABASE_URL") or scraper_settings.database_url
settings.database_url = normalize_database_url(_raw_url)

from app.database import Base  # noqa: E402

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
