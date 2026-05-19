"""CRUD operations for the NetGuard database."""

from typing import Optional
from sqlalchemy.orm import Session
from database.models import UploadedFile, AnalysisResult, MLMetric, AttackStatistic


# ── UploadedFile ──────────────────────────────────────────────────────────────

def create_uploaded_file(
    db: Session,
    filename: str,
    original_filename: str,
    file_size: int,
    row_count: int = 0,
) -> UploadedFile:
    obj = UploadedFile(
        filename=filename,
        original_filename=original_filename,
        file_size=file_size,
        row_count=row_count,
        status="pending",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_uploaded_file(db: Session, file_id: int) -> Optional[UploadedFile]:
    return db.query(UploadedFile).filter(UploadedFile.id == file_id).first()


def get_all_uploaded_files(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(UploadedFile)
        .order_by(UploadedFile.upload_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_file_status(
    db: Session,
    file_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> Optional[UploadedFile]:
    obj = get_uploaded_file(db, file_id)
    if obj:
        obj.status = status
        if error_message:
            obj.error_message = error_message
        db.commit()
        db.refresh(obj)
    return obj


# ── AnalysisResult ────────────────────────────────────────────────────────────

def create_analysis_result(
    db: Session,
    file_id: int,
    total_records: int,
    normal_count: int,
    attack_count: int,
    best_model: str,
    best_accuracy: float,
    processing_time: float,
    chart_distribution: Optional[str] = None,
    chart_confusion: Optional[str] = None,
    chart_roc: Optional[str] = None,
    chart_comparison: Optional[str] = None,
) -> AnalysisResult:
    obj = AnalysisResult(
        file_id=file_id,
        total_records=total_records,
        normal_count=normal_count,
        attack_count=attack_count,
        best_model=best_model,
        best_accuracy=best_accuracy,
        processing_time=processing_time,
        chart_distribution=chart_distribution,
        chart_confusion=chart_confusion,
        chart_roc=chart_roc,
        chart_comparison=chart_comparison,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_analysis_result(db: Session, analysis_id: int) -> Optional[AnalysisResult]:
    return db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()


def get_analyses_for_file(db: Session, file_id: int):
    return db.query(AnalysisResult).filter(AnalysisResult.file_id == file_id).all()


def get_all_analyses(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(AnalysisResult)
        .order_by(AnalysisResult.analysis_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── MLMetric ──────────────────────────────────────────────────────────────────

def create_ml_metric(
    db: Session,
    analysis_id: int,
    model_name: str,
    accuracy: float,
    precision: float,
    recall: float,
    f1_score: float,
    training_time: float,
    is_best: bool = False,
) -> MLMetric:
    obj = MLMetric(
        analysis_id=analysis_id,
        model_name=model_name,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        training_time=training_time,
        is_best=int(is_best),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_metrics_for_analysis(db: Session, analysis_id: int):
    return db.query(MLMetric).filter(MLMetric.analysis_id == analysis_id).all()


# ── AttackStatistic ───────────────────────────────────────────────────────────

def create_attack_statistic(
    db: Session,
    analysis_id: int,
    attack_type: str,
    count: int,
    percentage: float,
) -> AttackStatistic:
    obj = AttackStatistic(
        analysis_id=analysis_id,
        attack_type=attack_type,
        count=count,
        percentage=percentage,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_stats_for_analysis(db: Session, analysis_id: int):
    return db.query(AttackStatistic).filter(AttackStatistic.analysis_id == analysis_id).all()


# ── Dashboard aggregate ───────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total_files = db.query(UploadedFile).count()
    total_analyses = db.query(AnalysisResult).count()
    total_records = db.query(AnalysisResult).with_entities(
        AnalysisResult.total_records
    ).all()
    total_packets = sum(r[0] or 0 for r in total_records)

    attack_stats = db.query(AttackStatistic).all()
    total_attacks = sum(s.count for s in attack_stats if s.attack_type != "Normal Traffic")

    return {
        "total_files": total_files,
        "total_analyses": total_analyses,
        "total_packets": total_packets,
        "total_attacks": total_attacks,
    }
