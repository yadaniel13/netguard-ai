"""REST API endpoints for exporting reports."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud
from services.report_service import generate_csv_report, generate_json_report

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/report/{analysis_id}/csv")
def download_csv(analysis_id: int, db: Session = Depends(get_db)):
    """Download analysis report as CSV."""
    analysis = crud.get_analysis_result(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
    try:
        content = generate_csv_report(analysis_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{analysis_id}.csv"},
    )


@router.get("/report/{analysis_id}/json")
def download_json(analysis_id: int, db: Session = Depends(get_db)):
    """Download analysis report as JSON."""
    analysis = crud.get_analysis_result(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
    try:
        content = generate_json_report(analysis_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=report_{analysis_id}.json"},
    )
