from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# Serverless (Vercel): no persistent connections. Local/Docker: default pool.
_engine_kwargs: dict = {"pool_pre_ping": True}
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
