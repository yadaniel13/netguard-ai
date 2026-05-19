"""Inference pipeline: run predictions with the best available model."""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.preprocessor import TrafficPreprocessor, load_and_validate_csv
from ml.trainer import get_latest_models

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Wraps preprocessor + model for end-to-end CSV → predictions flow.
    Used after training is complete to classify new traffic samples.
    """

    def __init__(self, preprocessor: TrafficPreprocessor, model, model_name: str):
        self.preprocessor = preprocessor
        self.model = model
        self.model_name = model_name

    def predict(self, df: pd.DataFrame) -> Tuple[List[str], List[float]]:
        """
        Returns (predicted_labels, confidence_scores).
        confidence_scores are the max class probability if model supports it.
        """
        X = self.preprocessor.transform(df)
        y_num = self.model.predict(X)
        labels = self.preprocessor.decode_labels(y_num)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)
            confidence = probs.max(axis=1).tolist()
        else:
            confidence = [1.0] * len(labels)

        return labels, confidence

    def predict_csv(self, csv_path: str) -> pd.DataFrame:
        """Load CSV, predict, return dataframe with a 'prediction' column."""
        df = load_and_validate_csv(csv_path)
        labels, confidence = self.predict(df)
        df["prediction"] = labels
        df["confidence"] = [round(c, 4) for c in confidence]
        return df
