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


# Filtro por Estado/Provincia (Ciudad)
estado_seleccionado = st.selectbox(
    "Seleccione un estado/ciudad:",
    options=["Todos"] + list(fact_sale_full["City"].unique()),  # Agregamos "Todos" como opción
    index=0  # Establecemos "Todos" como la opción predeterminada
)





# Filtro por Rango de Fechas (Slider), Convertimos las fechas a datetime.date para el slider
fecha_minima = fact_sale_full["Invoice Date Key"].min().date()  # Convertimos a date
fecha_maxima = fact_sale_full["Invoice Date Key"].max().date()  # Convertimos a date

fecha_inicio, fecha_fin = st.slider(
    "Seleccione un rango de fechas", 
    min_value=fecha_minima,
    max_value=fecha_maxima,
    value=(fecha_minima, fecha_maxima)  # Definimos el rango inicial
)


# Filtramos los datos según los filtros seleccionados
if estado_seleccionado == "Todos":
    # Si se selecciona "Todos", no filtramos por ciudad
    datos_filtrados = fact_sale_full[
        (fact_sale_full["Invoice Date Key"].dt.date >= fecha_inicio) &
        (fact_sale_full["Invoice Date Key"].dt.date <= fecha_fin)
    ]
else:
    # Si se selecciona una ciudad específica, filtramos por la ciudad seleccionada
    datos_filtrados = fact_sale_full[
        (fact_sale_full["City"] == estado_seleccionado) &
        (fact_sale_full["Invoice Date Key"].dt.date >= fecha_inicio) &
        (fact_sale_full["Invoice Date Key"].dt.date <= fecha_fin)
    ]

# Calculamos los percentiles para la segmentación (esto ahora se hace sobre los datos filtrados)
percentil_20 = datos_filtrados["Total Including Tax"].quantile(0.20)
percentil_80 = datos_filtrados["Total Including Tax"].quantile(0.80)
datos_filtrados["Segmento Gasto"] = pd.cut(
    datos_filtrados["Total Including Tax"],
    bins=[-float('inf'), percentil_20, percentil_80, float('inf')],
    labels=["Bajo", "Intermedio", "Alto"]
)

# KPIs calculados usando los datos filtrados
valor_total_compras = datos_filtrados["Total Including Tax"].sum()
ticket_promedio = datos_filtrados["Total Including Tax"].mean()
frecuencia_compra = int(
    datos_filtrados.groupby(datos_filtrados["Invoice Date Key"].dt.to_period("M"))["Sale Key"]
    .count()
    .mean()
)

# Creamos tres columnas para mostrar los KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Valor Total de Compras", value=f"${valor_total_compras:,.2f}")
with col2:
    st.metric(label="Ticket Promedio", value=f"${ticket_promedio:,.2f}")
with col3:
    st.metric(label="Frecuencia de Compras", value=f"{frecuencia_compra:,.2f}")


# Gráfico de Porcentaje de Clientes por Segmento
col1, col2 = st.columns(2)

# Gráfico de Valor Total de Compras por Segmento
with col1:
    valor_total_por_segmento = datos_filtrados.groupby("Segmento Gasto")["Total Including Tax"].sum().reset_index().rename(columns={"Total Including Tax": "Valor Total"})
    valor_total_por_segmento = valor_total_por_segmento.sort_values(by="Valor Total", ascending=False)
    st.markdown("### Valor Total de Compras por Segmento (Ordenado)")
    st.bar_chart(data=valor_total_por_segmento.set_index("Segmento Gasto")["Valor Total"], use_container_width=True)

# Gráfico de Porcentaje de Clientes por Segmento
# Gráfico de Porcentaje de Clientes por Segmento
with col2:
    # Calculamos el porcentaje de clientes por segmento en relación con el total general de clientes
    porcentaje_clientes_por_segmento = datos_filtrados.groupby("Segmento Gasto")["Sale Key"].nunique().reset_index()
    total_clientes = len(fact_sale["Sale Key"].unique())  # Total de clientes basado en las ventas (Sale Key)
    porcentaje_clientes_por_segmento["Porcentaje"] = (
        porcentaje_clientes_por_segmento["Sale Key"] / total_clientes) * 100
    porcentaje_clientes_por_segmento = porcentaje_clientes_por_segmento.sort_values(by="Porcentaje", ascending=False)

    st.markdown("### Porcentaje de Clientes por Segmento")
    st.bar_chart(data=porcentaje_clientes_por_segmento.set_index("Segmento Gasto")["Porcentaje"], use_container_width=True)


   




# Tabla con las métricas clave por segmento
kpis_por_segmento = (
    datos_filtrados.groupby("Segmento Gasto")
    .agg(
        Valor_Total_Compras=("Total Including Tax", "sum"),
        Ticket_Promedio=("Total Including Tax", "mean"),
        Frecuencia_Compras=("Sale Key", lambda x: x.nunique())
    )
    .reset_index()
)

# Mostramos la tabla con las métricas clave en Streamlit
st.markdown("### Tabla con las Métricas Clave por Segmento")
st.dataframe(kpis_por_segmento)
