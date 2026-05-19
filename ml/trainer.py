"""Model training: Logistic Regression, Random Forest, XGBoost."""

import logging
import time
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_REGISTRY = {
    "Logistic Regression": lambda n_classes: LogisticRegression(
        max_iter=500, random_state=settings.RANDOM_STATE, n_jobs=-1
    ),
    "Random Forest": lambda n_classes: RandomForestClassifier(
        n_estimators=settings.N_ESTIMATORS,
        random_state=settings.RANDOM_STATE,
        n_jobs=-1,
    ),
    "XGBoost": lambda n_classes: XGBClassifier(
        n_estimators=settings.N_ESTIMATORS,
        random_state=settings.RANDOM_STATE,
        eval_metric="mlogloss",
        n_jobs=-1,
    ),
}


def train_all_models(
    X: np.ndarray,
    y: np.ndarray,
    analysis_id: int,
) -> Tuple[Dict, np.ndarray, np.ndarray]:
    """
    Train all registered models, save them to disk.
    Returns (results_dict, X_test, y_test).
    """
    n_classes = len(np.unique(y))
    unique, counts = np.unique(y, return_counts=True)
    can_stratify = bool((counts >= 2).all())
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=settings.TEST_SIZE,
        random_state=settings.RANDOM_STATE,
        stratify=y if can_stratify else None,
    )
    results: Dict[str, dict] = {}

    for name, factory in MODEL_REGISTRY.items():
        logger.info("Training %s …", name)
        model = factory(n_classes)
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0

        path = settings.MODELS_DIR / f"{_slug(name)}_{analysis_id}.pkl"
        joblib.dump(model, path)

        results[name] = {
            "model": model,
            "training_time": round(elapsed, 3),
            "path": str(path),
        }
        logger.info("  %s trained in %.2f s → %s", name, elapsed, path)

    return results, X_test, y_test


def load_model(model_name: str, analysis_id: int):
    """Load a previously saved model from disk."""
    path = settings.MODELS_DIR / f"{_slug(model_name)}_{analysis_id}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Модель не найдена: {path}")
    return joblib.load(path)


def get_latest_models() -> Dict[str, object]:
    """Load the most recently trained version of each model type."""
    models_dir = Path(settings.MODELS_DIR)
    loaded: Dict[str, object] = {}
    for name in MODEL_REGISTRY:
        pattern = f"{_slug(name)}_*.pkl"
        candidates = sorted(models_dir.glob(pattern))
        if candidates:
            loaded[name] = joblib.load(candidates[-1])
    return loaded


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")
