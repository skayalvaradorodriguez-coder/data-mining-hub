# data-mining-hub

Monorepo para la asignatura Minería de Datos (7mo semestre) — Unidad 1 y Unidad 2.

## Arquitectura

- **apps/analytics**: módulo Python contenerizado (pandas, scikit-learn, SQLAlchemy, psycopg2) con pipeline de extracción, preprocesamiento y conexión a fuentes de datos relacionales.
- **PostgreSQL (dm_postgres)**: gestor relacional estándar de industria, con datos semilla de transacciones de crédito de clientes bancarios.
- **CI**: pipeline en GitHub Actions que construye y prueba el módulo analytics en Docker.

## Unidad 2 - Tema 1: Extracción y conexión a fuentes de datos

### Dataset ampliado

Se amplió `init-db/01_init.sql` de 9 a 14 registros, agregando 5 clientes nuevos con nulos intencionales en `age` y `annual_income`, para preparar el terreno al análisis exploratorio de datos (EDA) y limpieza en los siguientes temas.

### Hallazgos del Taller en Parejas (4 retos)

1. **Conteo por región**: la distribución de clientes no es uniforme entre regiones (Costa concentra la mayor cantidad de registros).
2. **Perfil de riesgo (`credit_score < 650`)**: los clientes con `credit_score` nulo (ej. CUST-1008) quedan automáticamente excluidos de este filtro, porque en SQL `NULL < 650` no evalúa a verdadero. Esto demuestra que los valores nulos pueden ocultar registros de riesgo si no se tratan explícitamente antes del análisis.
3. **Filtro y orden (Costa por ingreso anual)**: el ordenamiento descendente funcionó correctamente sobre el subconjunto filtrado por región.
4. **Reconstrucción por chunks**: `extract_raw_data_in_chunks()` particiona correctamente el dataset en bloques del tamaño solicitado, y `pd.concat()` reconstruye el DataFrame original sin pérdida de registros.

### Consistencia validada

El test `test_extract_raw_data_regions` confirma que la suma de los conteos agregados por región (`GROUP BY region`) siempre coincide con el total de filas extraídas sin agrupar — una validación básica de integridad entre la extracción cruda y la extracción agregada.

## Cómo levantar el entorno

```powershell
docker compose down -v
docker compose build analytics
docker compose up -d
docker exec -it dm_analytics pytest -v tests/
```

## Unidad 2 - Tema 3: Limpieza y calidad de datos

Se implementó `apps/analytics/src/cleaning.py` con el pipeline de calidad de datos
(Fase 3 de CRISP-DM): normalización de inconsistencias, imputación de valores
faltantes (media, mediana, moda y KNNImputer) y tratamiento de outliers mediante
acotamiento (capping) mediante el rango intercuartílico (IQR). El resultado se
persiste en la tabla `customer_credit_clean` dentro de PostgreSQL.

### Reflexión: ¿por qué capping y no eliminación de outliers?

En el contexto de riesgo crediticio, eliminar directamente los registros con
`annual_income` o `loan_amount` atípicos implicaría descartar precisamente a los
clientes con perfiles financieros extremos -quienes, en la práctica, suelen ser
los casos más relevantes para un modelo de scoring de crédito (clientes de muy
alto o muy bajo poder adquisitivo). Perder esas observaciones reduce el tamaño
de la muestra, puede sesgar el dataset hacia el cliente "promedio" y le resta al
modelo la capacidad de aprender a distinguir perfiles de riesgo poco comunes
pero reales. El capping, en cambio, preserva el 100% de los registros y la señal
de que ese cliente es atípico (al dejarlo en el límite superior/inferior del IQR),
sin que un solo valor extremo distorsione desproporcionadamente la media y la
varianza del conjunto de entrenamiento.
