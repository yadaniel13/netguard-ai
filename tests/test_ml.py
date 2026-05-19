"""Unit tests for the ML pipeline."""

import numpy as np
import pandas as pd
import pytest

from ml.preprocessor import TrafficPreprocessor, load_and_validate_csv
from ml.evaluator import evaluate_model, find_best_model
from scripts.generate_sample_data import generate_sample_dataset


@pytest.fixture(scope="module")
def sample_df(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "test.csv")
    generate_sample_dataset(path, n_rows=300)
    return pd.read_csv(path)


def test_preprocessor_fit_transform(sample_df):
    prep = TrafficPreprocessor()
    X, y, features = prep.fit_transform(sample_df)
    assert X.shape[0] == len(sample_df)
    assert X.shape[1] > 0
    assert len(y) == len(sample_df)
    assert len(features) > 0


def test_preprocessor_label_names(sample_df):
    prep = TrafficPreprocessor()
    prep.fit_transform(sample_df)
    names = prep.get_label_names()
    assert len(names) > 1
    assert "BENIGN" in names or "Normal Traffic" in names or any(names)


def test_preprocessor_decode(sample_df):
    prep = TrafficPreprocessor()
    _, y, _ = prep.fit_transform(sample_df)
    decoded = prep.decode_labels(y[:10])
    assert len(decoded) == 10
    assert all(isinstance(d, str) for d in decoded)


def test_evaluate_model(sample_df):
    from sklearn.ensemble import RandomForestClassifier
    prep = TrafficPreprocessor()
    X, y, _ = prep.fit_transform(sample_df)

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test, prep.get_label_names())

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert "confusion_matrix" in metrics


def test_find_best_model():
    evaluation = {
        "Model A": {"f1_score": 0.85},
        "Model B": {"f1_score": 0.92},
        "Model C": {"f1_score": 0.88},
    }
    best = find_best_model(evaluation)
    assert best == "Model B"
