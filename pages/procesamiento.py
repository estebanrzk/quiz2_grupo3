import pandas as pd
import sqlite3
import streamlit as st

# Especificamos la ruta a la base de datos
ruta_db = r"C:/Users/f/Downloads/quiz2grupo3/quiz2_grupo3/data/WWI_simple.db"

# Establecemos la conexión con la base de datos
try:
    conn = sqlite3.connect(ruta_db)
    print("Conexión exitosa a la base de datos.")

    # Cargamos las tablas en DataFrames
    dim_customer = pd.read_sql_query("SELECT * FROM DimCustomer", conn)
    fact_sale = pd.read_sql_query("SELECT * FROM FactSale", conn)
    dim_city = pd.read_sql_query("SELECT * FROM DimCity", conn)

except sqlite3.Error as e:
    print(f"Error al conectar con la base de datos o cargar tablas: {e}")
finally:
    if conn:
        conn.close()
        print("Conexión cerrada.")

# Realizamos el merge entre fact_sale y dim_customer usando CustomerKey
fact_sale_customer = fact_sale.merge(dim_customer, on="Customer Key", how="left")

# Realizamos el merge entre fact_sale_customer y dim_city usando CityKey
fact_sale_full = fact_sale_customer.merge(dim_city, on="City Key", how="left")

# Convertimos la columna "Total Including Tax" a valores numéricos y las fechas a datetime
fact_sale_full["Total Including Tax"] = pd.to_numeric(fact_sale_full["Total Including Tax"], errors="coerce")
fact_sale_full["Invoice Date Key"] = pd.to_datetime(fact_sale_full["Invoice Date Key"], errors="coerce")

# Filtros en Streamlit
# Filtro por Categoría
categoria_seleccionada = st.selectbox(
    "Seleccione una categoría:",
    options=fact_sale_full["Category"].unique()
)

# Filtro por Estado/Provincia (Ciudad)
estado_seleccionado = st.selectbox(
    "Seleccione un estado/ciudad:",
    options=fact_sale_full["City"].unique()
)

# Filtro por Rango de Fechas
fecha_inicio, fecha_fin = st.date_input(
    "Seleccione un rango de fechas", 
    value=[fact_sale_full["Invoice Date Key"].min(), fact_sale_full["Invoice Date Key"].max()],
    min_value=fact_sale_full["Invoice Date Key"].min(),
    max_value=fact_sale_full["Invoice Date Key"].max()
)

# Filtramos los datos según los filtros seleccionados
datos_filtrados = fact_sale_full[
    (fact_sale_full["Category"] == categoria_seleccionada) &
    (fact_sale_full["City"] == estado_seleccionado) &
    (fact_sale_full["Invoice Date Key"] >= pd.to_datetime(fecha_inicio)) &
    (fact_sale_full["Invoice Date Key"] <= pd.to_datetime(fecha_fin))
]

# Calculamos los percentiles para la segmentación (esto ahora se hace sobre los datos filtrados)
percentil_20 = datos_filtrados["Total Including Tax"].quantile(0.20)
percentil_80 = datos_filtrados["Total Including Tax"].quantile(0.80)
datos_filtrados["Segmento G
