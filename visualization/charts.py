"""Chart generation using matplotlib / seaborn (saved as PNG files)."""

import io
import base64
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns

from app.config import settings

logger = logging.getLogger(__name__)

# Visual style
DARK_BG = "#1a1a2e"
CARD_BG = "#16213e"
ACCENT = "#0f3460"
TEXT_COLOR = "#e0e0e0"
GRID_COLOR = "#2a2a4a"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "axes.titlecolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "grid.color": GRID_COLOR,
    "legend.facecolor": CARD_BG,
    "legend.edgecolor": GRID_COLOR,
    "legend.labelcolor": TEXT_COLOR,
})

ATTACK_PALETTE = {
    "Normal Traffic": "#28a745",
    "DDoS/DoS Attack": "#dc3545",
    "Port Scan": "#fd7e14",
    "Brute Force": "#ffc107",
    "Botnet": "#9b59b6",
    "Web Attack": "#17a2b8",
    "Other Attack": "#6c757d",
}

DEFAULT_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
]


def _save_fig(fig, prefix: str = "chart") -> str:
    """Save figure to static/charts, return relative URL path."""
    fname = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    path = settings.CHARTS_DIR / fname
    fig.savefig(path, bbox_inches="tight", dpi=100, facecolor=DARK_BG)
    plt.close(fig)
    return f"/static/charts/{fname}"


# ── 1. Attack distribution (pie + bar side-by-side) ──────────────────────────

def chart_attack_distribution(attack_counts: Dict[str, int]) -> str:
    labels = list(attack_counts.keys())
    values = list(attack_counts.values())
    colors = [ATTACK_PALETTE.get(l, DEFAULT_COLORS[i % len(DEFAULT_COLORS)]) for i, l in enumerate(labels)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor(DARK_BG)

    # Pie
    wedges, texts, autotexts = ax1.pie(
        values, labels=None, colors=colors,
        autopct="%1.1f%%", startangle=140,
        pctdistance=0.8, wedgeprops={"edgecolor": DARK_BG, "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color(TEXT_COLOR)
    ax1.set_title("Распределение типов трафика", fontsize=13, pad=15)
    ax1.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)

    # Bar
    bars = ax2.barh(labels, values, color=colors, edgecolor=DARK_BG, linewidth=0.8)
    ax2.set_xlabel("Количество записей", fontsize=10)
    ax2.set_title("Детальная статистика", fontsize=13, pad=15)
    ax2.grid(axis="x", alpha=0.3)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{val:,}", va="center", fontsize=9)

    plt.tight_layout(pad=2)
    return _save_fig(fig, "distribution")


# ── 2. Confusion matrix heatmap ───────────────────────────────────────────────

def chart_confusion_matrix(cm: List[List[int]], class_names: List[str], model_name: str) -> str:
    cm_arr = np.array(cm)
    fig, ax = plt.subplots(figsize=(max(8, len(class_names) * 1.4), max(6, len(class_names) * 1.2)))
    fig.patch.set_facecolor(DARK_BG)

    sns.heatmap(
        cm_arr, annot=True, fmt="d", cmap="Blues",
        xticklabels=class_names, yticklabels=class_names,
        ax=ax, linewidths=0.5, linecolor=GRID_COLOR,
        cbar_kws={"shrink": 0.8},
    )
    ax.set_xlabel("Предсказанный класс", fontsize=11)
    ax.set_ylabel("Истинный класс", fontsize=11)
    ax.set_title(f"Матрица ошибок — {model_name}", fontsize=13, pad=12)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout(pad=1.5)
    return _save_fig(fig, "confusion")


# ── 3. Model comparison bar chart ────────────────────────────────────────────

def chart_model_comparison(metrics: Dict[str, dict]) -> str:
    model_names = list(metrics.keys())
    metric_keys = ["accuracy", "precision", "recall", "f1_score"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1-Score"]
    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"]

    x = np.arange(len(model_names))
    width = 0.18

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(DARK_BG)

    for i, (key, label, color) in enumerate(zip(metric_keys, metric_labels, colors)):
        vals = [metrics[m].get(key, 0) for m in model_names]
        bars = ax.bar(x + i * width, vals, width, label=label, color=color, alpha=0.9, edgecolor=DARK_BG)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(model_names, fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Значение метрики", fontsize=11)
    ax.set_title("Сравнение моделей машинного обучения", fontsize=13, pad=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout(pad=1.5)
    return _save_fig(fig, "comparison")


# ── 4. Training time comparison ───────────────────────────────────────────────

def chart_training_time(metrics: Dict[str, dict]) -> str:
    names = list(metrics.keys())
    times = [metrics[m].get("training_time", 0) for m in names]
    colors = [DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i in range(len(names))]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)

    bars = ax.bar(names, times, color=colors, edgecolor=DARK_BG, linewidth=0.8)
    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                f"{t:.2f}s", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Время обучения (сек)", fontsize=11)
    ax.set_title("Время обучения моделей", fontsize=13, pad=12)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout(pad=1.5)
    return _save_fig(fig, "training_time")


# ── 5. Feature importance (Random Forest / XGBoost) ──────────────────────────

def chart_feature_importance(model, feature_names: List[str], model_name: str, top_n: int = 20) -> Optional[str]:
    if not hasattr(model, "feature_importances_"):
        return None

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]
    top_features = [feature_names[i] for i in indices]
    top_values = [importances[i] for i in indices]

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.35)))
    fig.patch.set_facecolor(DARK_BG)

    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top_features)))
    ax.barh(top_features[::-1], top_values[::-1], color=colors[::-1], edgecolor=DARK_BG)
    ax.set_xlabel("Важность признака", fontsize=11)
    ax.set_title(f"Топ-{top_n} признаков — {model_name}", fontsize=13, pad=12)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout(pad=1.5)
    return _save_fig(fig, "feature_importance")


# ── 6. ROC curve (binary or multi-class OvR) ─────────────────────────────────

def chart_roc_curves(
    models_dict: Dict[str, object],
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_names: List[str],
) -> str:
    from sklearn.metrics import roc_curve, auc
    from sklearn.preprocessing import label_binarize

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor(DARK_BG)
    ax.plot([0, 1], [0, 1], "w--", linewidth=0.8, label="Случайная угадайка")

    for (name, model), color in zip(models_dict.items(), DEFAULT_COLORS):
        if not hasattr(model, "predict_proba"):
            continue
        try:
            classes = np.unique(y_test)
            y_bin = label_binarize(y_test, classes=classes)
            y_prob = model.predict_proba(X_test)

            if len(classes) == 2:
                fpr, tpr, _ = roc_curve(y_test, y_prob[:, 1])
                roc_auc = auc(fpr, tpr)
                ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} (AUC = {roc_auc:.3f})")
            else:
                # Macro average
                all_fpr = np.unique(np.concatenate([roc_curve(y_bin[:, i], y_prob[:, i])[0] for i in range(len(classes))]))
                mean_tpr = np.zeros_like(all_fpr)
                for i in range(len(classes)):
                    fpr_i, tpr_i, _ = roc_curve(y_bin[:, i], y_prob[:, i])
                    mean_tpr += np.interp(all_fpr, fpr_i, tpr_i)
                mean_tpr /= len(classes)
                roc_auc = auc(all_fpr, mean_tpr)
                ax.plot(all_fpr, mean_tpr, color=color, lw=2, label=f"{name} (macro AUC = {roc_auc:.3f})")
        except Exception as exc:
            logger.warning("ROC curve failed for %s: %s", name, exc)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.set_title("ROC-кривые моделей", fontsize=13, pad=12)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout(pad=1.5)
    return _save_fig(fig, "roc")
