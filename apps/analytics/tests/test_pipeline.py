import pytest
import pandas as pd
import numpy as np
from src.pipeline import load_and_preprocess_dataset, calculate_feature_metrics, scale_features


def test_load_and_preprocess_dataset():
    X, y = load_and_preprocess_dataset()
    assert not X.empty
    assert len(X) == len(y)
    assert X.isna().sum().sum() == 0


def test_calculate_feature_metrics():
    X, _ = load_and_preprocess_dataset()
    metrics = calculate_feature_metrics(X)
    assert isinstance(metrics, pd.DataFrame)
    assert "mean" in metrics.columns
    assert "std" in metrics.columns


def test_scale_features():
    X, _ = load_and_preprocess_dataset()
    X_scaled = scale_features(X)
    
    # Verificar que es un DataFrame
    assert isinstance(X_scaled, pd.DataFrame)
    
    # Verificar que se mantienen las columnas y el índice
    assert list(X_scaled.columns) == list(X.columns)
    assert list(X_scaled.index) == list(X.index)
    
    # Verificar que los datos están normalizados (media ≈ 0, std ≈ 1)
    for col in X_scaled.columns:
        assert np.isclose(X_scaled[col].mean(), 0, atol=1e-10)
        assert np.isclose(X_scaled[col].std(ddof=0), 1, atol=1e-10)
