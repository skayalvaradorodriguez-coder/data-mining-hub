import pytest
import pandas as pd
from sqlalchemy import text
from src.db_connector import get_database_engine, extract_raw_data, extract_raw_data_in_chunks


def test_engine_connection():
    """Valida la conectividad básica con el motor PostgreSQL."""
    engine = get_database_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_extract_raw_data():
    """Valida que los datos crudos se carguen correctamente en un DataFrame."""
    query = "SELECT * FROM customer_credit_transactions;"
    df = extract_raw_data(query)

    assert not df.empty
    assert isinstance(df, pd.DataFrame)
    assert "customer_id" in df.columns
    assert "credit_score" in df.columns
    assert len(df) >= 9


def test_extract_raw_data_in_chunks():
    """Valida que el generador de lotes entregue bloques correctos."""
    query = "SELECT * FROM customer_credit_transactions ORDER BY transaction_id;"
    chunks = list(extract_raw_data_in_chunks(query, chunk_size=3))

    assert len(chunks) >= 3
    assert len(chunks[0]) == 3
    assert isinstance(chunks[0], pd.DataFrame)


def test_extract_raw_data_regions():
    """Valida que el conteo por región (GROUP BY) sea consistente con el total de registros."""
    df_total = extract_raw_data("SELECT * FROM customer_credit_transactions;")
    df_regions = extract_raw_data(
        "SELECT region, COUNT(*) AS total FROM customer_credit_transactions GROUP BY region;"
    )

    assert not df_regions.empty
    assert "region" in df_regions.columns
    assert "total" in df_regions.columns

    # La suma de los conteos por región debe igualar el total de filas
    assert df_regions["total"].sum() == len(df_total)

    # Las regiones presentes en el agregado deben coincidir con las del dataset completo
    assert set(df_regions["region"]) == set(df_total["region"].unique())
