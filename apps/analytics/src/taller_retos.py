"""Taller en clase: Actividad Guiada en Parejas - 4 retos con customer_credit_transactions."""
import pandas as pd
from src.db_connector import extract_raw_data, extract_raw_data_in_chunks

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)


def reto_1_conteo_por_region():
    """RETO 1: Agrupar clientes usando agregación SQL GROUP BY region."""
    query = """
        SELECT region, COUNT(*) AS total_clientes
        FROM customer_credit_transactions
        GROUP BY region
        ORDER BY total_clientes DESC;
    """
    df = extract_raw_data(query)
    print("\n=== RETO 1: Conteo por Región ===")
    print(df)
    return df


def reto_2_perfil_de_riesgo():
    """RETO 2: Extraer únicamente clientes con puntaje crítico: credit_score < 650."""
    query = """
        SELECT customer_id, age, credit_score, has_defaulted, region
        FROM customer_credit_transactions
        WHERE credit_score < 650;
    """
    df = extract_raw_data(query)
    print("\n=== RETO 2: Perfil de Riesgo (credit_score < 650) ===")
    print(df)
    return df


def reto_3_filtro_y_orden():
    """RETO 3: Filtrar clientes de Costa ordenados descendentemente por ingreso anual."""
    query = """
        SELECT customer_id, region, annual_income, credit_score
        FROM customer_credit_transactions
        WHERE region = 'Costa'
        ORDER BY annual_income DESC;
    """
    df = extract_raw_data(query)
    print("\n=== RETO 3: Filtro y Orden (Costa, por annual_income DESC) ===")
    print(df)
    return df


def reto_4_reconstruccion():
    """RETO 4: Consolidar 3 chunks con pd.concat() y validar los 9 registros."""
    query = "SELECT * FROM customer_credit_transactions ORDER BY transaction_id;"
    chunks = list(extract_raw_data_in_chunks(query, chunk_size=3))

    print(f"\n=== RETO 4: Reconstrucción ===")
    print(f"Número de chunks obtenidos: {len(chunks)}")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {len(chunk)} filas")

    df_reconstructed = pd.concat(chunks, ignore_index=True)
    print(f"\nDataFrame reconstruido: {len(df_reconstructed)} filas totales")
    assert len(df_reconstructed) == 9, "La reconstrucción no tiene 9 registros"
    print("Validación OK: 9 registros confirmados tras la reconstrucción.")
    return df_reconstructed


if __name__ == "__main__":
    reto_1_conteo_por_region()
    reto_2_perfil_de_riesgo()
    reto_3_filtro_y_orden()
    reto_4_reconstruccion()
