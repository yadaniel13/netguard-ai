"""
Standalone script for training models on a provided CSV dataset.
Usage:
    python -m scripts.train_models [path/to/dataset.csv] [n_rows]
"""

import logging
import sys
from pathlib import Path

import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main(csv_path: str, n_rows: int = None):
    import pandas as pd
    from ml.preprocessor import TrafficPreprocessor, load_and_validate_csv
    from ml.trainer import train_all_models
    from ml.evaluator import evaluate_all_models, find_best_model
    from app.config import settings

    logger.info("Loading dataset: %s", csv_path)
    df = load_and_validate_csv(csv_path)
    if n_rows:
        df = df.sample(min(n_rows, len(df)), random_state=42)
    logger.info("Dataset shape: %s", df.shape)

    preprocessor = TrafficPreprocessor()
    X, y, features = preprocessor.fit_transform(df)
    logger.info("Features: %d, Classes: %s", len(features), preprocessor.get_label_names())

    joblib.dump(preprocessor, settings.MODELS_DIR / "preprocessor.pkl")
    logger.info("Preprocessor saved.")

    trained, X_test, y_test = train_all_models(X, y, analysis_id=0)
    evaluation = evaluate_all_models(trained, X_test, y_test, preprocessor.get_label_names())

    best = find_best_model(evaluation)
    logger.info("\n=== RESULTS ===")
    for name, m in evaluation.items():
        marker = " ← BEST" if name == best else ""
        logger.info(
            "%-22s  acc=%.4f  prec=%.4f  rec=%.4f  f1=%.4f  time=%.2fs%s",
            name, m["accuracy"], m["precision"], m["recall"], m["f1_score"],
            m.get("training_time", 0), marker,
        )


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "datasets/sample_traffic.csv"
    rows = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if not Path(path).exists():
        from scripts.generate_sample_data import generate_sample_dataset
        generate_sample_dataset(path, n_rows=rows or 5000)
    main(path, rows)
