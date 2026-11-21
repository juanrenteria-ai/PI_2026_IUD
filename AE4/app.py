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


def aplicar_estilos():
    """Aplica la identidad visual de la aplicación con CSS propio."""
    st.markdown(
        """
        <style>
        :root {
            --petroleo: #123B4A;
            --ambar: #D28A16;
            --tinta: #203541;
            --borde: #D8E2E8;
            --fondo-suave: #F1F5F7;
        }

        [data-testid="stAppViewContainer"] {
            background: #F8FAFB;
            color: var(--tinta);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--petroleo);
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.25rem;
            font-weight: 700;
        }

        h2 {
            margin-top: 1.8rem;
            font-size: 1.45rem;
        }

        [data-testid="stMetric"] {
            min-height: 112px;
            padding: 1rem 1.1rem;
            background: #FFFFFF;
            border: 1px solid var(--borde);
            border-left: 4px solid var(--ambar);
            border-radius: 12px;
            box-shadow: 0 3px 12px rgba(18, 59, 74, 0.07);
        }

        [data-testid="stMetricLabel"] p {
            color: #536873;
            font-size: 0.9rem;
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: var(--petroleo);
            font-weight: 700;
            font-size: clamp(1.25rem, 2.1vw, 1.85rem);
            line-height: 1.2;
        }

        [data-testid="stSidebar"] {
            background: var(--fondo-suave);
            border-right: 1px solid var(--borde);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] p {
            color: var(--petroleo);
        }

        .hero {
            margin-bottom: 1.5rem;
            padding: 2rem 2.2rem;
            color: #FFFFFF;
            background: var(--petroleo);
            border-left: 6px solid var(--ambar);
            border-radius: 14px;
            box-shadow: 0 8px 22px rgba(18, 59, 74, 0.14);
        }

        .hero-kicker {
            margin: 0 0 0.5rem;
            color: #F4C66D;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .hero h1 {
            margin: 0;
            color: #FFFFFF;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
        }

        .hero-subtitle {
            margin: 0.55rem 0 0;
            color: #E5EEF2;
            font-size: 1.05rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid var(--borde);
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            color: #536873;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            color: var(--petroleo);
        }

        .app-footer {
            margin-top: 3rem;
            padding: 1.2rem 0 0.3rem;
            color: #536873;
            border-top: 1px solid var(--borde);
            font-size: 0.86rem;
            line-height: 1.7;
        }

        .app-footer strong {
            color: var(--petroleo);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def configurar_idioma_del_navegador():
    """Evita que el navegador traduzca el documento de Streamlit."""
    if not st.session_state.get("idioma_navegador_configurado", False):
        st.components.v1.html(
            """
            <script>
            window.parent.document.documentElement.lang = "es";
            window.parent.document.documentElement.setAttribute("translate", "no");
            if (!window.parent.document.head.querySelector(
                'meta[name="google"][content="notranslate"]'
            )) {
                const meta = window.parent.document.createElement("meta");
                meta.name = "google";
                meta.content = "notranslate";
                window.parent.document.head.appendChild(meta);
            }
            </script>
            """,
            height=0,
        )
        st.session_state["idioma_navegador_configurado"] = True


def aplicar_estilo_grafico(figura, datos, es_linea, indice_destacado):
    """Uniforma la paleta, tipografía, ejes y rejilla de todos los gráficos."""
    colores = [
        "#B7473D" if indice == indice_destacado else "#78909C"
        for indice in datos.index
    ]

    if es_linea:
        figura.update_traces(
            line={"color": "#78909C", "width": 3},
            marker={
                "color": colores,
                "size": 10,
                "line": {"color": "#FFFFFF", "width": 1.5},
            },
        )
    else:
        figura.update_traces(
            marker={
                "color": colores,
                "line": {"color": "#FFFFFF", "width": 1},
            }
        )

    figura.update_layout(
        font={"family": "Arial, sans-serif", "size": 14, "color": "#203541"},
        title={"font": {"size": 20, "color": "#123B4A"}, "x": 0.02},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 24, "r": 24, "t": 70, "b": 35},
        hoverlabel={"bgcolor": "#FFFFFF", "font": {"color": "#203541"}},
        xaxis={
            "title": "Año" if es_linea else "Categoría",
            "showgrid": False,
            "automargin": True,
            "tickfont": {"size": 13},
        },
        yaxis={
            "title": "Accidentes graves (% de accidentes de la categoría)",
            "showgrid": True,
            "gridcolor": "#E2E9ED",
            "zeroline": False,
            "ticksuffix": "%",
            "automargin": True,
        },
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )


configurar_idioma_del_navegador()
aplicar_estilos()


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
    datos_para_destacar = datos
    if nombre.startswith("P3"):
        # Los registros sin hora siguen en la gráfica, pero no compiten por el destacado.
        datos_para_destacar = datos[
            datos[columna_categoria].astype(str).str.casefold() != "sin dato"
        ]
    indice_mayor = datos_para_destacar["Graves (% de la fila)"].idxmax()
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
    es_linea = nombre.startswith("P5")
    aplicar_estilo_grafico(figura, datos, es_linea, indice_mayor)

    pestanas = st.tabs(["Gráfico", "Interpretación", "Limitaciones"])
    with pestanas[0]:
        st.plotly_chart(figura, width="stretch")
        if nombre.startswith("P3"):
            cantidad_sin_hora = int(
                datos.loc[
                    datos[columna_categoria].astype(str).str.casefold() == "sin dato",
                    "Accidentes (n)",
                ].sum()
            )
            st.caption(
                f"“Sin dato” se mantiene visible: son {formato_entero(cantidad_sin_hora)} "
                "registros sin hora y por eso no se destaca."
            )
    with pestanas[1]:
        st.write(configuracion["lectura"])
    with pestanas[2]:
        st.info(configuracion["limite"])


def mostrar_inicio():
    resumen = obtener_resumen()
    accidentes = int(resumen["Accidentes (n)"])
    graves = int(resumen["Fatal (n)"] + resumen["Hospital (n)"])
    porcentaje_grave = graves / accidentes * 100

    st.markdown(
        """
        <section class="hero">
            <p class="hero-kicker">Proyecto Integrador · AE4</p>
            <h1>Severidad de accidentes de tránsito</h1>
            <p class="hero-subtitle">
                Australia Occidental · Periodo de análisis: <strong>2019–2023</strong>
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
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

    primera_fila = st.columns(2)
    primera_fila[0].metric("Accidentes", formato_entero(accidentes))
    primera_fila[1].metric("Accidentes graves", formato_entero(graves))
    segunda_fila = st.columns(2)
    segunda_fila[0].metric("Graves (%)", f"{porcentaje_grave:.2f} %")
    segunda_fila[1].metric("Periodo analizado", PERIODO)
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

st.markdown(
    """
    <footer class="app-footer">
        <strong>Proyecto Integrador de Analítica de Datos</strong><br>
        Juan Felipe Valencia Renteria · Cristian Mateo Piedrahita Arango ·
        Diego Alejandro Barros Ballestas<br>
        Institución Universitaria Digital de Antioquia · Fuente:
        kalley/WA_Crash, Main Roads Western Australia (Data WA)
    </footer>
    """,
    unsafe_allow_html=True,
)
