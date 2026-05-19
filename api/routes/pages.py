"""HTML page routes rendered with Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud

router = APIRouter()
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    stats = crud.get_dashboard_stats(db)
    recent = crud.get_all_analyses(db, limit=5)
    return templates.TemplateResponse(
        request, "index.html",
        {"stats": stats, "recent_analyses": recent},
    )


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(request, "upload.html", {})


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request, db: Session = Depends(get_db)):
    analyses = crud.get_all_analyses(db, limit=100)
    files = crud.get_all_uploaded_files(db, limit=100)
    return templates.TemplateResponse(
        request, "history.html",
        {"analyses": analyses, "files": files},
    )


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
def analysis_detail(request: Request, analysis_id: int, db: Session = Depends(get_db)):
    analysis = crud.get_analysis_result(db, analysis_id)
    if not analysis:
        return templates.TemplateResponse(
            request, "index.html",
            {"error": f"Анализ #{analysis_id} не найден.",
             "stats": crud.get_dashboard_stats(db),
             "recent_analyses": []},
        )
    metrics = crud.get_metrics_for_analysis(db, analysis_id)
    stats = crud.get_stats_for_analysis(db, analysis_id)
    return templates.TemplateResponse(
        request, "analysis.html",
        {"analysis": analysis, "metrics": metrics, "stats": stats},
    )


@router.get("/models", response_class=HTMLResponse)
def models_page(request: Request, db: Session = Depends(get_db)):
    analyses = crud.get_all_analyses(db, limit=1)
    metrics = []
    analysis = None
    if analyses:
        analysis = analyses[0]
        metrics = crud.get_metrics_for_analysis(db, analysis.id)
    return templates.TemplateResponse(
        request, "models.html",
        {"metrics": metrics, "analysis": analysis},
    )
