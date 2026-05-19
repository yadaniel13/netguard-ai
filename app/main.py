"""
NetGuard AI — Главный модуль FastAPI приложения.
Система интеллектуальной фильтрации сетевого трафика.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, BASE_DIR
from database.database import init_db
from api.routes import pages, upload, analysis, statistics, reports

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    init_db()
    logger.info("Database initialised.")
    _seed_demo_data()
    yield


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Система интеллектуальной фильтрации сетевого трафика на основе МО",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(pages.router)
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(statistics.router)
app.include_router(reports.router)


def _seed_demo_data():
    """Generate and analyse sample data on first launch so the dashboard is not empty."""
    from database.database import SessionLocal
    from database import crud

    db = SessionLocal()
    try:
        if crud.get_dashboard_stats(db)["total_analyses"] > 0:
            return
    finally:
        db.close()

    logger.info("No analyses found — generating demo dataset …")
    try:
        from scripts.generate_sample_data import generate_sample_dataset
        sample_path = settings.DATASETS_DIR / "sample_traffic.csv"
        generate_sample_dataset(str(sample_path), n_rows=5000)

        # Register as uploaded file
        import shutil
        dest = settings.UPLOAD_DIR / "demo_traffic.csv"
        shutil.copy(sample_path, dest)

        db = SessionLocal()
        try:
            db_file = crud.create_uploaded_file(
                db, "demo_traffic.csv", "sample_traffic.csv",
                dest.stat().st_size, 5000,
            )
            file_id = db_file.id
        finally:
            db.close()

        from services.analysis_service import run_analysis
        run_analysis(file_id, str(dest))
        logger.info("Demo analysis complete.")
    except Exception as exc:
        logger.error("Demo seed failed: %s", exc, exc_info=True)
