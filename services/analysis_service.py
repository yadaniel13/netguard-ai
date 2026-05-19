"""Core analysis orchestration service."""

import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import pandas as pd

from app.config import settings
from database import crud
from database.database import SessionLocal
from ml.preprocessor import TrafficPreprocessor, load_and_validate_csv, _map_attack_labels, _detect_label_column
from ml.trainer import train_all_models
from ml.evaluator import evaluate_all_models, find_best_model
from visualization.charts import (
    chart_attack_distribution,
    chart_confusion_matrix,
    chart_model_comparison,
    chart_roc_curves,
)

logger = logging.getLogger(__name__)

PREPROCESSOR_PATH = settings.MODELS_DIR / "preprocessor.pkl"


def run_analysis(file_id: int, csv_path: str) -> int:
    """
    Full pipeline: preprocess → train → evaluate → persist.
    Returns analysis_result.id on success, raises on error.
    """
    db = SessionLocal()
    t_start = time.time()
    try:
        crud.update_file_status(db, file_id, "processing")

        # 1. Load data
        df = load_and_validate_csv(csv_path)
        logger.info("File loaded: %d rows", len(df))

        # 2. Preprocess
        preprocessor = TrafficPreprocessor()
        X, y, feature_cols = preprocessor.fit_transform(df)
        joblib.dump(preprocessor, PREPROCESSOR_PATH)

        # 3. Train models
        trained, X_test, y_test = train_all_models(X, y, file_id)

        # 4. Evaluate models
        class_names = preprocessor.get_label_names()
        evaluation = evaluate_all_models(trained, X_test, y_test, class_names)
        best_name = find_best_model(evaluation)
        best_metrics = evaluation[best_name]

        # 5. Build attack statistics from ground-truth labels
        label_col = _detect_label_column(df)
        if label_col:
            mapped = _map_attack_labels(df[label_col])
        else:
            mapped = pd.Series(preprocessor.decode_labels(trained[best_name]["model"].predict(X)))

        attack_counts: Dict[str, int] = mapped.value_counts().to_dict()
        normal_count = attack_counts.get("Normal Traffic", 0)
        attack_count = sum(v for k, v in attack_counts.items() if k != "Normal Traffic")

        # 6. Generate charts
        chart_dist = chart_attack_distribution(attack_counts)

        cm = best_metrics.get("confusion_matrix", [])
        chart_conf = chart_confusion_matrix(cm, class_names, best_name) if cm else None

        flat_metrics = {n: {k: v for k, v in m.items() if isinstance(v, (int, float))} for n, m in evaluation.items()}
        chart_comp = chart_model_comparison(flat_metrics)

        models_for_roc = {n: info["model"] for n, info in trained.items()}
        chart_roc = chart_roc_curves(models_for_roc, X_test, y_test, class_names)

        # 7. Persist results
        processing_time = round(time.time() - t_start, 2)
        analysis = crud.create_analysis_result(
            db,
            file_id=file_id,
            total_records=len(df),
            normal_count=normal_count,
            attack_count=attack_count,
            best_model=best_name,
            best_accuracy=best_metrics["accuracy"],
            processing_time=processing_time,
            chart_distribution=chart_dist,
            chart_confusion=chart_conf,
            chart_roc=chart_roc,
            chart_comparison=chart_comp,
        )

        for attack_type, count in attack_counts.items():
            pct = round(count / len(df) * 100, 2)
            crud.create_attack_statistic(db, analysis.id, attack_type, count, pct)

        for name, metrics in evaluation.items():
            crud.create_ml_metric(
                db,
                analysis_id=analysis.id,
                model_name=name,
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                training_time=metrics.get("training_time", 0.0),
                is_best=(name == best_name),
            )

        crud.update_file_status(db, file_id, "done")
        logger.info("Analysis %d completed in %.2f s", analysis.id, processing_time)
        return analysis.id

    except Exception as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        crud.update_file_status(db, file_id, "error", str(exc))
        raise
    finally:
        db.close()
