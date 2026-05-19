"""REST API endpoints for running and retrieving analysis."""

import logging
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud
from services.analysis_service import run_analysis
from services.file_service import get_upload_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze/{file_id}")
def start_analysis(file_id: int, db: Session = Depends(get_db)):
    """Trigger analysis for an uploaded file (runs synchronously for simplicity)."""
    db_file = crud.get_uploaded_file(db, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    if db_file.status == "processing":
        raise HTTPException(status_code=409, detail="Анализ уже выполняется.")

    csv_path = str(get_upload_path(db_file.filename))

    try:
        analysis_id = run_analysis(file_id, csv_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {exc}")

    return {"analysis_id": analysis_id, "status": "done"}


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Return full analysis result."""
    analysis = crud.get_analysis_result(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
    metrics = crud.get_metrics_for_analysis(db, analysis_id)
    stats = crud.get_stats_for_analysis(db, analysis_id)
    return {
        "id": analysis.id,
        "file_id": analysis.file_id,
        "analysis_date": analysis.analysis_date.isoformat(),
        "total_records": analysis.total_records,
        "normal_count": analysis.normal_count,
        "attack_count": analysis.attack_count,
        "best_model": analysis.best_model,
        "best_accuracy": analysis.best_accuracy,
        "processing_time": analysis.processing_time,
        "charts": {
            "distribution": analysis.chart_distribution,
            "confusion": analysis.chart_confusion,
            "roc": analysis.chart_roc,
            "comparison": analysis.chart_comparison,
        },
        "ml_metrics": [
            {
                "model": m.model_name,
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
                "training_time": m.training_time,
                "is_best": bool(m.is_best),
            }
            for m in metrics
        ],
        "attack_statistics": [
            {"type": s.attack_type, "count": s.count, "percentage": s.percentage}
            for s in stats
        ],
    }


@router.get("/analyses")
def list_analyses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all analysis results."""
    analyses = crud.get_all_analyses(db, skip=skip, limit=limit)
    return [
        {
            "id": a.id,
            "file_id": a.file_id,
            "date": a.analysis_date.isoformat(),
            "total_records": a.total_records,
            "best_model": a.best_model,
            "best_accuracy": a.best_accuracy,
        }
        for a in analyses
    ]
