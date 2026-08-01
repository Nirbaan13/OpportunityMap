"""Run Alembic migrations (used on API startup so prod does not depend on manual Actions)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_done = False


def run_migrations() -> None:
    """Upgrade the database to the latest Alembic revision.

    Safe to call repeatedly: already-applied revisions are no-ops.
    Postgres advisory locks prevent concurrent upgrades from stomping each other.
    """
    from alembic import command
    from alembic.config import Config

    # migrate.py lives at backend/app/core/migrate.py → backend root is parents[2]
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    # env.py reads DATABASE_URL / settings; keep script location absolute for Vercel.
    config.set_main_option("script_location", str(backend_root / "alembic"))
    logger.info("Running alembic upgrade head…")
    command.upgrade(config, "head")
    logger.info("Database schema is at head.")


def ensure_migrations() -> None:
    """Run migrations once per process (cold start). Thread-safe."""
    global _done
    if _done:
        return
    with _lock:
        if _done:
            return
        run_migrations()
        _done = True
