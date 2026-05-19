"""REST API endpoints for statistics and dashboard data."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud

router = APIRouter(prefix="/api", tags=["statistics"])


@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """Return dashboard-level aggregated statistics."""
    stats = crud.get_dashboard_stats(db)
    analyses = crud.get_all_analyses(db, limit=10)
    return {
        "summary": stats,
        "recent_analyses": [
            {
                "id": a.id,
                "date": a.analysis_date.isoformat(),
                "total_records": a.total_records,
                "attack_count": a.attack_count,
                "best_model": a.best_model,
                "best_accuracy": a.best_accuracy,
            }
            for a in analyses
        ],
    }


@router.get("/statistics/models")
def get_model_stats(db: Session = Depends(get_db)):
    """Return aggregated model metrics across all analyses."""
    from database.models import MLMetric
    from sqlalchemy import func

    rows = (
        db.query(
            MLMetric.model_name,
            func.avg(MLMetric.accuracy).label("avg_accuracy"),
            func.avg(MLMetric.f1_score).label("avg_f1"),
            func.avg(MLMetric.training_time).label("avg_time"),
            func.count(MLMetric.id).label("runs"),
        )
        .group_by(MLMetric.model_name)
        .all()
    )
    return [
        {
            "model": r.model_name,
            "avg_accuracy": round(r.avg_accuracy or 0, 4),
            "avg_f1": round(r.avg_f1 or 0, 4),
            "avg_training_time": round(r.avg_time or 0, 3),
            "total_runs": r.runs,
        }
        for r in rows
    ]
