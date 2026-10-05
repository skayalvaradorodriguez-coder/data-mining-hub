"""Pipeline de limpieza y calidad de datos: inconsistencias, imputación y outliers."""
from typing import List, Literal

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

from src.db_connector import get_database_engine, extract_raw_data

MIN_VALID_AGE = 18
MAX_VALID_AGE = 100


def clean_inconsistencies(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la columna 'region' (strip + Title Case) y fuerza a NaN
    las edades que violan reglas de negocio (age > 100 o age < 18)."""
    df = df.copy()

    if "region" in df.columns:
        df["region"] = df["region"].astype(str).str.strip().str.title()
        df.loc[df["region"].isin(["Nan", "None", ""]), "region"] = np.nan

    if "age" in df.columns:
        invalid_age_mask = (df["age"] < MIN_VALID_AGE) | (df["age"] > MAX_VALID_AGE)
        df.loc[invalid_age_mask, "age"] = np.nan

    return df


def impute_column(
    df: pd.DataFrame,
    column: str,
    strategy: Literal["mean", "median", "mode", "knn"] = "mean",
) -> pd.DataFrame:
    """Imputa valores faltantes en 'column' según la estrategia indicada.

    Estrategias soportadas:
      - "mean": media aritmética (variables numéricas continuas).
      - "median": mediana (robusta ante outliers).
      - "mode": moda (variables categóricas).
      - "knn": KNNImputer de Scikit-Learn, usando el resto de columnas
        numéricas para preservar relaciones multivariables.
    """
    df = df.copy()

    if strategy == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif strategy == "median":
        df[column] = df[column].fillna(df[column].median())
    elif strategy == "mode":
        mode_value = df[column].mode(dropna=True)
        if not mode_value.empty:
            df[column] = df[column].fillna(mode_value.iloc[0])
    elif strategy == "knn":
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if column not in numeric_cols:
            raise ValueError(f"KNN solo soporta columnas numéricas; '{column}' no lo es.")
        imputer = KNNImputer(n_neighbors=3)
        df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
    else:
        raise ValueError(f"Estrategia de imputación desconocida: {strategy}")

    return df


def detect_and_cap_outliers(
    df: pd.DataFrame, columns: List[str], factor: float = 1.5
) -> pd.DataFrame:
    """Detecta outliers con el rango intercuartílico (IQR) y los acota (capping)
    en vez de eliminarlos, para preservar la cantidad de registros del dataset."""
    df = df.copy()

    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - factor * iqr
        upper_bound = q3 + factor * iqr
        df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

    return df


def run_cleaning_pipeline(
    df: pd.DataFrame, engine=None, save_table: str = "customer_credit_clean"
) -> pd.DataFrame:
    """Orquesta el pipeline completo: inconsistencias -> imputación -> outliers -> persistencia.
    Guarda el resultado en la tabla `customer_credit_clean` dentro de PostgreSQL."""
    variance_before = df["annual_income"].var()

    df_clean = clean_inconsistencies(df)
    df_clean = impute_column(df_clean, "age", strategy="median")
    df_clean = impute_column(df_clean, "annual_income", strategy="mean")
    df_clean = impute_column(df_clean, "credit_score", strategy="median")
    df_clean = impute_column(df_clean, "region", strategy="mode")
    df_clean = detect_and_cap_outliers(df_clean, columns=["annual_income", "loan_amount"])

    variance_after = df_clean["annual_income"].var()

    print("\n=== Auditoría de Calidad: annual_income ===")
    print(f"Varianza ANTES del tratamiento:   {variance_before:,.2f}")
    print(f"Varianza DESPUÉS del tratamiento: {variance_after:,.2f}")
    print(f"Reducción: {(1 - variance_after / variance_before) * 100:,.1f}%")

    active_engine = engine or get_database_engine()
    df_clean.to_sql(save_table, con=active_engine, if_exists="replace", index=False)
    print(f"\nTabla '{save_table}' guardada en PostgreSQL ({len(df_clean)} registros).")

    return df_clean


if __name__ == "__main__":
    raw_df = extract_raw_data("SELECT * FROM customer_credit_transactions;")
    run_cleaning_pipeline(raw_df)
