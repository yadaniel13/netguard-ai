"""Model evaluation: metrics, confusion matrix, ROC curves."""

import logging
from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize

logger = logging.getLogger(__name__)


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_names: List[str],
) -> dict:
    """
    Compute accuracy, precision, recall, F1 and optionally AUC.
    Returns a flat metrics dict ready for DB storage and display.
    """
    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))

    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )

    # Per-class report (for detailed view)
    report = classification_report(
        y_test, y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # ROC-AUC (macro, one-vs-rest)
    try:
        classes = np.unique(y_test)
        y_bin = label_binarize(y_test, classes=classes)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)
            if y_bin.shape[1] == 1:
                auc = roc_auc_score(y_test, y_prob[:, 1])
            else:
                auc = float(roc_auc_score(y_bin, y_prob, multi_class="ovr", average="macro"))
        else:
            auc = None
    except Exception:
        auc = None

    return {
        "accuracy": round(acc, 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "auc": round(auc, 4) if auc is not None else None,
        "confusion_matrix": cm.tolist(),
        "class_report": report,
        "y_pred": y_pred.tolist(),
        "y_test": y_test.tolist(),
    }


def evaluate_all_models(
    trained_results: Dict[str, dict],
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_names: List[str],
) -> Dict[str, dict]:
    """Evaluate every model in the training results dict."""
    evaluation: Dict[str, dict] = {}
    for name, info in trained_results.items():
        logger.info("Evaluating %s …", name)
        metrics = evaluate_model(info["model"], X_test, y_test, class_names)
        metrics["training_time"] = info["training_time"]
        evaluation[name] = metrics
    return evaluation


def find_best_model(evaluation: Dict[str, dict]) -> str:
    """Return the name of the model with highest F1-score."""
    return max(evaluation, key=lambda n: evaluation[n]["f1_score"])
