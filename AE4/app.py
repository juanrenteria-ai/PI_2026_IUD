from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Severidad de accidentes | Australia Occidental",
    page_icon="🚦",
    layout="wide",
)

# Las rutas se calculan desde este archivo para que funcionen localmente y en Cloud.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_RESULTADOS = RAIZ_PROYECTO / "AE3" / "resultados"
PERIODO = "2019–2023"


@st.cache_data
def cargar_tabla(nombre_archivo):
    """Lee y almacena en caché una de las tablas publicadas en AE3."""
    ruta = RUTA_RESULTADOS / nombre_archivo
    return pd.read_csv(ruta)


PREGUNTAS = {
    "P1 · Calzada": {
        "archivo": "tabla_calzada.csv",
        "pregunta": "¿Cómo se distribuye la severidad según el tipo de calzada (CWAY)?",
        "lectura": (
            "La calzada única (S) registra la mayor proporción de accidentes graves "
            "(6,77 %), frente a la izquierda (L, 3,89 %) y la derecha (R, 4,23 %). "
            "Esto permite priorizar una revisión descriptiva de los segmentos por tipo "
            "de calzada, sin atribuirles causalidad."
        ),
        "limite": (
            "Los códigos S, L y R describen el tipo de calzada, no las condiciones "
            "completas del tramo ni la exposición al tránsito."
        ),
    },
    "P2 · Intersección": {
        "archivo": "tabla_interseccion.csv",
        "pregunta": "¿Cambia la severidad entre accidentes con y sin intersección registrada?",
        "lectura": (
            "La proporción grave es 4,24 % cuando hay intersección registrada y 6,97 % "
            "cuando no la hay. La diferencia sugiere revisar la calidad y completitud "
            "del registro de intersecciones antes de orientar análisis posteriores."
        ),
        "limite": (
            "“Sin intersección registrada” significa que falta el dato; no confirma "
            "que el accidente ocurriera fuera de una intersección."
        ),
    },
    "P3 · Franja horaria": {
        "archivo": "tabla_franja_horaria.csv",
        "pregunta": "¿En qué franja horaria se concentran los accidentes graves?",
        "lectura": (
            "La tarde reúne el mayor número de accidentes graves (2.822), pero su "
            "proporción es la menor entre las franjas con hora conocida (4,68 %). "
            "La madrugada tiene la mayor proporción entre esas franjas (11,17 %). "
            "“Sin dato” marca 14,68 %, pero corresponde solo a 109 registros. "
            "Volumen y proporción responden preguntas distintas."
        ),
        "limite": (
            "Hay 109 registros sin hora. La comparación no incluye volumen de tránsito "
            "por hora y no permite inferir riesgo."
        ),
    },
    "P4 · Tipo de vehículo": {
        "archivo": "tabla_tipo_vehiculo.csv",
        "pregunta": "¿Qué tipos de vehículos participan y con qué severidad?",
        "lectura": (
            "La motocicleta presenta la mayor proporción grave (33,32 %), seguida por "
            "la bicicleta (15,75 %). Esta comparación puede orientar preguntas de "
            "seguimiento por tipo de vehículo, no conclusiones sobre causas."
        ),
        "limite": (
            "Las categorías no son excluyentes: un accidente puede aparecer en más de "
            "un tipo. “Otros vehículos” agrupa muchos registros y la fila de referencia "
            "se omite del gráfico."
        ),
    },
    "P5 · Año": {
        "archivo": "tabla_anio.csv",
        "pregunta": "¿La proporción de accidentes graves cambió entre 2019 y 2023?",
        "lectura": (
            "La proporción anual varía entre 5,09 % (2023) y 6,17 % (2020), sin una "
            "tendencia sostenida de aumento o disminución en el periodo. Se puede usar "
            "la serie para definir qué cambios conviene estudiar con más contexto."
        ),
        "limite": (
            "Son proporciones descriptivas anuales; no se evaluó significancia "
            "estadística ni se controlaron cambios en exposición o registro."
        ),
    },
    "P6 · Mes": {
        "archivo": "tabla_mes.csv",
        "pregunta": "¿Hay meses con mayor proporción de accidentes graves?",
        "lectura": (
            "Enero tiene la mayor proporción (6,15 %) y junio la menor (4,90 %). "
            "La diferencia puede señalar meses para una revisión más detallada, pero "
            "no demuestra un patrón estacional ni explica sus motivos."
        ),
        "limite": (
            "Cada punto agrupa todos los años. No se comparan años por separado ni se "
            "consideran exposición, cambios de población o variaciones de registro."
        ),
    },
    "P7 · Día de la semana": {
        "archivo": "tabla_dia_semana.csv",
        "pregunta": "¿Son más graves los accidentes en fin de semana?",
        "lectura": (
            "Domingo presenta la mayor proporción diaria (8,23 %), seguido por sábado "
            "(6,65 %). Al agrupar los días, fin de semana alcanza 7,33 % y lunes a "
            "viernes 5,02 %. Es un contraste descriptivo que puede orientar preguntas "
            "de seguimiento."
        ),
        "limite": (
            "La comparación agrupa días de todos los años y no tiene denominadores de "
            "exposición; no permite afirmar que el fin de semana cause mayor gravedad."
        ),
    },
    "P8 · Número de vehículos": {
        "archivo": "tabla_total_vehiculos.csv",
        "pregunta": "¿Aumenta la gravedad cuando participan más vehículos?",
        "lectura": (
            "La mayor proporción grave corresponde a accidentes con 1 vehículo "
            "(11,18 %); con 2 vehículos es 3,27 % y con 3 o más, 5,89 %. "
            "La relación no aumenta de forma monotónica, por lo que más vehículos no "
            "equivale a una mayor proporción grave en estos datos."
        ),
        "limite": (
            "El conteo no incluye peatones y la categoría de cero vehículos debe "
            "interpretarse según la definición de la variable derivada."
        ),
    },
}


def formato_entero(valor):
    """Presenta conteos con separador de miles usado en español."""
    return f"{int(valor):,}".replace(",", ".")


def obtener_resumen():
    """Obtiene el total general desde la fila Total de la tabla anual."""
    # La fila Total resume los accidentes y conteos de severidad del periodo.
    tabla_anual = cargar_tabla("tabla_anio.csv")
    columna_categoria = tabla_anual.columns[0]
    return tabla_anual.loc[
        tabla_anual[columna_categoria].astype(str).str.casefold() == "total"
    ].iloc[0]


def preparar_datos(nombre_archivo):
    """Quita totales y filas de referencia para graficar solo categorías."""
    datos = cargar_tabla(nombre_archivo).copy()
    columna_categoria = datos.columns[0]
    etiquetas = datos[columna_categoria].astype(str)
    # Se excluye el total y, en P4, la referencia que no es un tipo de vehículo.
    datos = datos[
        (etiquetas.str.casefold() != "total")
        & (~etiquetas.str.contains("referencia", case=False, na=False))
    ].copy()
    datos["Accidentes (n)"] = pd.to_numeric(datos["Accidentes (n)"])
    datos["Graves (n)"] = pd.to_numeric(datos["Graves (n)"])
    datos["Graves (% de la fila)"] = pd.to_numeric(
        datos["Graves (% de la fila)"]
    )
    return datos, columna_categoria


def mostrar_pregunta(nombre, configuracion):
    datos, columna_categoria = preparar_datos(configuracion["archivo"])
    indice_mayor = datos["Graves (% de la fila)"].idxmax()
    categoria_mayor = datos.loc[indice_mayor]

    st.title(configuracion["pregunta"])
    st.caption(f"{nombre} · Registros descriptivos del periodo {PERIODO}")

    metricas = st.columns(3)
    metricas[0].metric(
        "Proporción grave más alta",
        f'{categoria_mayor["Graves (% de la fila)"]:.2f} %',
        help=f'Categoría: {categoria_mayor[columna_categoria]}',
    )
    metricas[1].metric(
        "Accidentes en esa categoría",
        formato_entero(categoria_mayor["Accidentes (n)"]),
    )
    metricas[2].metric(
        "Accidentes graves en esa categoría",
        formato_entero(categoria_mayor["Graves (n)"]),
    )
    st.caption(
        "Métrica principal: proporción de accidentes graves = "
        "(Fatal + Hospital) ÷ accidentes de la categoría × 100. "
        "Unidad: porcentaje de accidentes de esa categoría. "
        "Los conteos se muestran como número de accidentes."
    )

    # El año tiene orden temporal; las demás preguntas comparan categorías.
    if nombre.startswith("P5"):
        figura = px.line(
            datos,
            x=columna_categoria,
            y="Graves (% de la fila)",
            markers=True,
            text="Graves (% de la fila)",
            custom_data=["Accidentes (n)", "Graves (n)"],
            title=f"Proporción de accidentes graves por año ({PERIODO})",
            labels={
                columna_categoria: "Año",
                "Graves (% de la fila)": "Accidentes graves (% de la categoría)",
            },
        )
    else:
        figura = px.bar(
            datos,
            x=columna_categoria,
            y="Graves (% de la fila)",
            text="Graves (% de la fila)",
            custom_data=["Accidentes (n)", "Graves (n)"],
            title=f"Proporción de accidentes graves por categoría ({PERIODO})",
            labels={
                columna_categoria: "Categoría",
                "Graves (% de la fila)": "Accidentes graves (% de la categoría)",
            },
        )

    figura.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="top center" if nombre.startswith("P5") else "outside",
        hovertemplate=(
            "%{x}<br>Graves: %{y:.2f}%"
            "<br>Accidentes de la categoría: %{customdata[0]:,}"
            "<br>Accidentes graves: %{customdata[1]:,}<extra></extra>"
        ),
    )
    figura.update_layout(
        yaxis_title="Accidentes graves (% de accidentes de la categoría)",
        xaxis_title="Año" if nombre.startswith("P5") else "Categoría",
        yaxis_ticksuffix="%",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    st.plotly_chart(figura, width="stretch")

    st.subheader("Interpretación")
    st.write(configuracion["lectura"])
    st.info(f"**Limitación de esta pregunta:** {configuracion['limite']}")


def mostrar_inicio():
    resumen = obtener_resumen()
    accidentes = int(resumen["Accidentes (n)"])
    graves = int(resumen["Fatal (n)"] + resumen["Hospital (n)"])
    porcentaje_grave = graves / accidentes * 100

    st.title("Severidad de accidentes de tránsito")
    st.subheader("Australia Occidental · 2019–2023")
    st.write(
        "Las entidades de seguridad vial cuentan con muchos registros, pero un "
        "conteo total no distingue entre numerosos accidentes leves y menos "
        "accidentes graves. Esta app relaciona la severidad registrada con "
        "características de los accidentes."
    )
    st.markdown(
        "**Pregunta principal:** ¿Cómo se distribuye la severidad de los accidentes "
        "según el tipo de calzada, la presencia de intersección, la franja horaria "
        "y los tipos de vehículos involucrados?"
    )

    columnas = st.columns(4)
    columnas[0].metric("Accidentes", formato_entero(accidentes))
    columnas[1].metric(
        "Accidentes graves",
        formato_entero(graves),
        f"{porcentaje_grave:.2f} %",
        help="Graves = Fatal + Hospital; porcentaje sobre el total de accidentes.",
    )
    columnas[2].metric("Periodo analizado", PERIODO)
    columnas[3].metric("Fuente", "kalley/WA_Crash")
    st.caption(
        "Fuente original: Main Roads Western Australia (Data WA). "
        "El análisis usa tablas de resultados ya preparadas; no vuelve a procesar "
        "el archivo enriquecido."
    )

    st.subheader("Distribución por severidad")
    severidades = ["Fatal", "Hospital", "Medical", "PDO Major", "PDO Minor"]
    distribucion = pd.DataFrame(
        {
            "Severidad": severidades,
            "Accidentes (n)": [int(resumen[f"{nombre} (n)"]) for nombre in severidades],
        }
    )
    distribucion["Porcentaje del total"] = (
        distribucion["Accidentes (n)"] / accidentes * 100
    ).map(lambda porcentaje: f"{porcentaje:.2f} %")
    st.dataframe(distribucion, hide_index=True, width="stretch")

    st.subheader("Alcance")
    st.write(
        "El análisis es descriptivo. No estima causas, predicciones ni tasas de "
        "riesgo. “Graves” agrupa las categorías Fatal y Hospital."
    )


def mostrar_conclusiones():
    resumen = obtener_resumen()
    accidentes = int(resumen["Accidentes (n)"])
    graves = int(resumen["Fatal (n)"] + resumen["Hospital (n)"])
    porcentaje_grave = graves / accidentes * 100

    st.title("Conclusiones, recomendaciones y limitaciones")
    st.subheader("Conclusiones")
    st.markdown(
        f"- En el periodo se registraron **{formato_entero(accidentes)} accidentes** "
        f"y **{formato_entero(graves)} graves ({porcentaje_grave:.2f} %)**.\n"
        "- El volumen y la proporción de gravedad no son lo mismo: la tarde concentra "
        "el 47,42 % de los accidentes, pero tiene la menor proporción grave entre "
        "las franjas horarias con dato (4,68 %).\n"
        "- Las proporciones más altas aparecen en categorías como motocicleta, "
        "madrugada y domingo; son comparaciones descriptivas, no explicaciones."
    )

    st.subheader("Recomendaciones")
    st.markdown(
        "- Priorizar la revisión de calidad y completitud de variables como "
        "intersección y hora.\n"
        "- Usar estas diferencias para formular análisis posteriores, incorporando "
        "datos de exposición al tránsito antes de hablar de tasas o riesgo.\n"
        "- Presentar juntos conteos y proporciones para no confundir volumen con "
        "gravedad."
    )

    st.subheader("Limitaciones generales")
    st.markdown(
        "- Sin datos de exposición no se pueden calcular tasas de riesgo.\n"
        "- “Sin intersección registrada” representa información faltante.\n"
        "- Los tipos de vehículo no son excluyentes y “Otros vehículos” concentra "
        "la mayoría de registros sin detalle.\n"
        "- La severidad proviene del registro policial y puede subestimar la gravedad "
        "de motociclistas, peatones y ciclistas.\n"
        "- Las comparaciones son descriptivas; no se aplicaron pruebas estadísticas."
    )


st.sidebar.title("Navegación")
opciones = ["Inicio", *PREGUNTAS.keys(), "Conclusiones y límites"]
seccion = st.sidebar.radio("Ir a una sección", opciones)
st.sidebar.caption("Proyecto Integrador · AE4")

if seccion == "Inicio":
    mostrar_inicio()
elif seccion == "Conclusiones y límites":
    mostrar_conclusiones()
else:
    mostrar_pregunta(seccion, PREGUNTAS[seccion])
