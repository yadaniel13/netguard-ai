"""Report generation service (CSV and JSON exports)."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Optional

from database import crud
from database.database import SessionLocal

logger = logging.getLogger(__name__)


def generate_csv_report(analysis_id: int) -> bytes:
    """Generate a CSV report for a given analysis."""
    db = SessionLocal()
    try:
        analysis = crud.get_analysis_result(db, analysis_id)
        if not analysis:
            raise ValueError(f"Анализ {analysis_id} не найден.")

        metrics = crud.get_metrics_for_analysis(db, analysis_id)
        stats = crud.get_stats_for_analysis(db, analysis_id)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["NetGuard AI — Отчёт об анализе трафика"])
        writer.writerow(["Дата анализа", analysis.analysis_date.strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Всего записей", analysis.total_records])
        writer.writerow(["Нормальный трафик", analysis.normal_count])
        writer.writerow(["Атаки обнаружено", analysis.attack_count])
        writer.writerow(["Лучшая модель", analysis.best_model])
        writer.writerow(["Точность (accuracy)", f"{analysis.best_accuracy:.4f}"])
        writer.writerow(["Время обработки (с)", analysis.processing_time])
        writer.writerow([])

        writer.writerow(["=== СТАТИСТИКА АТАК ==="])
        writer.writerow(["Тип атаки", "Количество", "Процент (%)"])
        for s in stats:
            writer.writerow([s.attack_type, s.count, f"{s.percentage:.2f}"])
        writer.writerow([])

        writer.writerow(["=== МЕТРИКИ МОДЕЛЕЙ ==="])
        writer.writerow(["Модель", "Accuracy", "Precision", "Recall", "F1-Score", "Время обучения (с)", "Лучшая"])
        for m in metrics:
            writer.writerow([
                m.model_name,
                f"{m.accuracy:.4f}",
                f"{m.precision:.4f}",
                f"{m.recall:.4f}",
                f"{m.f1_score:.4f}",
                f"{m.training_time:.3f}",
                "Да" if m.is_best else "Нет",
            ])

        return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    finally:
        db.close()


def generate_json_report(analysis_id: int) -> bytes:
    """Generate a JSON report for a given analysis."""
    db = SessionLocal()
    try:
        analysis = crud.get_analysis_result(db, analysis_id)
        if not analysis:
            raise ValueError(f"Анализ {analysis_id} не найден.")

        metrics = crud.get_metrics_for_analysis(db, analysis_id)
        stats = crud.get_stats_for_analysis(db, analysis_id)

        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "analysis": {
                "id": analysis.id,
                "date": analysis.analysis_date.isoformat(),
                "total_records": analysis.total_records,
                "normal_count": analysis.normal_count,
                "attack_count": analysis.attack_count,
                "best_model": analysis.best_model,
                "best_accuracy": analysis.best_accuracy,
                "processing_time": analysis.processing_time,
            },
            "attack_statistics": [
                {"type": s.attack_type, "count": s.count, "percentage": s.percentage}
                for s in stats
            ],
            "model_metrics": [
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
        }
        return json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
    finally:
        db.close()
