import numpy as np
import pandas as pd

from src.cleaning import (
    clean_inconsistencies,
    impute_column,
    detect_and_cap_outliers,
    run_cleaning_pipeline,
)
from src.db_connector import get_database_engine, extract_raw_data


def test_clean_inconsistencies_normalizes_region_and_invalid_age():
    df = pd.DataFrame({
        "region": [" costa ", "SIERRA", "oriente"],
        "age": [25, 150, 10],
    })
    cleaned = clean_inconsistencies(df)

    assert list(cleaned["region"]) == ["Costa", "Sierra", "Oriente"]
    assert pd.isna(cleaned["age"].iloc[1])
    assert pd.isna(cleaned["age"].iloc[2])
    assert cleaned["age"].iloc[0] == 25


def test_impute_column_mean():
    df = pd.DataFrame({"annual_income": [100.0, 200.0, np.nan]})
    result = impute_column(df, "annual_income", strategy="mean")
    assert result["annual_income"].isna().sum() == 0
    assert result["annual_income"].iloc[2] == 150.0


def test_impute_column_median():
    df = pd.DataFrame({"age": [20.0, 30.0, np.nan, 40.0]})
    result = impute_column(df, "age", strategy="median")
    assert result["age"].isna().sum() == 0
    assert result["age"].iloc[2] == 30.0


def test_impute_column_mode():
    df = pd.DataFrame({"region": ["Costa", "Costa", "Sierra", None]})
    result = impute_column(df, "region", strategy="mode")
    assert result["region"].isna().sum() == 0
    assert result["region"].iloc[3] == "Costa"


def test_detect_and_cap_outliers_reduces_variance_without_dropping_rows():
    df = pd.DataFrame({"annual_income": [40000, 42000, 39000, 41000, 500000]})
    original_len = len(df)
    result = detect_and_cap_outliers(df, columns=["annual_income"])

    assert len(result) == original_len
    assert result["annual_income"].var() < df["annual_income"].var()
    assert result["annual_income"].max() < 500000


def test_run_cleaning_pipeline_creates_clean_table():
    engine = get_database_engine()
    raw_df = extract_raw_data("SELECT * FROM customer_credit_transactions;")

    cleaned_df = run_cleaning_pipeline(raw_df, engine=engine)

    assert not cleaned_df.empty
    assert cleaned_df["age"].isna().sum() == 0
    assert cleaned_df["annual_income"].isna().sum() == 0

    verification_df = extract_raw_data("SELECT * FROM customer_credit_clean;", engine=engine)
    assert len(verification_df) == len(cleaned_df)
