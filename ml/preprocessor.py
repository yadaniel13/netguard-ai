"""Data preprocessing pipeline for network traffic CSV files."""

import logging
import re
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

from app.config import settings

logger = logging.getLogger(__name__)


def _normalize_column_name(name: str) -> str:
    """Convert column name to lowercase snake_case."""
    name = name.strip().lower()
    name = re.sub(r"[/\-\s]+", "_", name)
    name = re.sub(r"[^\w]", "", name)
    return name


def _detect_label_column(df: pd.DataFrame) -> Optional[str]:
    """Find the label/target column in the dataframe."""
    for col in df.columns:
        for candidate in settings.LABEL_COLUMN_NAMES:
            if col.strip().lower() == candidate.strip().lower():
                return col
    for col in df.columns:
        if "label" in col.lower() or "attack" in col.lower() or "class" in col.lower():
            return col
    return None


def _map_attack_labels(series: pd.Series) -> pd.Series:
    """Map raw dataset labels to unified attack category names."""
    return series.map(lambda x: settings.ATTACK_LABELS.get(str(x).strip(), str(x).strip()))


class TrafficPreprocessor:
    """
    Transforms raw network-traffic CSV data into a numeric feature matrix
    ready for scikit-learn / XGBoost training or inference.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns: list = []
        self.label_column: Optional[str] = None
        self.is_fitted: bool = False

    # ── public API ────────────────────────────────────────────────────────────

    def fit_transform(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Clean, encode and scale the dataframe.
        Returns (X, y, feature_names).
        """
        df = self._clean(df)
        self.label_column = _detect_label_column(df)
        if self.label_column is None:
            raise ValueError("Не найден столбец с метками (label / attack_type / class).")

        y_raw = _map_attack_labels(df[self.label_column])

        # Drop classes with fewer than 5 samples — too rare to split/train on
        counts = y_raw.value_counts()
        valid = counts[counts >= 5].index
        if len(valid) < len(counts):
            removed = counts[counts < 5].to_dict()
            logger.warning("Removing rare classes (< 5 samples): %s", removed)
            mask = y_raw.isin(valid)
            y_raw = y_raw[mask].reset_index(drop=True)
            df = df[mask].reset_index(drop=True)

        if len(y_raw) < 20:
            raise ValueError(
                f"После фильтрации редких классов осталось только {len(y_raw)} строк. "
                "Загрузите датасет с большим количеством записей (минимум 20 на класс)."
            )

        X = df.drop(columns=[self.label_column])
        X = self._select_numeric(X)
        self.feature_columns = list(X.columns)

        X_scaled = self.scaler.fit_transform(X)
        y_encoded = self.label_encoder.fit_transform(y_raw)
        self.is_fitted = True
        logger.info("Preprocessor fitted: %d features, %d classes", len(self.feature_columns), len(self.label_encoder.classes_))
        return X_scaled, y_encoded, self.feature_columns

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform new data using the already fitted scaler."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transform().")
        df = self._clean(df)

        # Drop label column if present
        label_col = _detect_label_column(df)
        if label_col:
            df = df.drop(columns=[label_col])

        # Align columns
        X = self._select_numeric(df)
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0.0
        X = X[self.feature_columns]
        return self.scaler.transform(X)

    def get_label_names(self) -> list:
        """Return human-readable class names."""
        if not self.is_fitted:
            return []
        return list(self.label_encoder.classes_)

    def decode_labels(self, y: np.ndarray) -> list:
        """Convert numeric predictions back to string labels."""
        return list(self.label_encoder.inverse_transform(y))

    # ── private helpers ───────────────────────────────────────────────────────

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.drop_duplicates()
        df = df.replace([np.inf, -np.inf], np.nan)
        threshold = len(df) * 0.5
        df = df.dropna(axis=1, thresh=int(threshold))
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                fill = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
                df[col] = df[col].fillna(fill)
        return df

    def _select_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only numeric columns and drop near-zero-variance columns."""
        df = df.select_dtypes(include=[np.number]).copy()
        zero_var = df.columns[df.std() == 0]
        df = df.drop(columns=zero_var)
        for col in df.columns:
            lo, hi = df[col].quantile(0.01), df[col].quantile(0.99)
            df[col] = df[col].clip(lo, hi)
        return df


def load_and_validate_csv(path: str) -> pd.DataFrame:
    """Load CSV, do basic validation, return DataFrame."""
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:
        raise ValueError(f"Не удалось прочитать CSV: {exc}") from exc

    if df.empty:
        raise ValueError("CSV файл пустой.")
    if len(df.columns) < 3:
        raise ValueError("CSV содержит менее 3 столбцов. Проверьте формат файла.")
    if len(df) < 20:
        raise ValueError(
            f"CSV содержит только {len(df)} строк. Минимум — 20 строк для обучения моделей. "
            "Загрузите файл с реальными данными трафика."
        )

    logger.info("CSV loaded: %d rows × %d columns", len(df), len(df.columns))
    return df
