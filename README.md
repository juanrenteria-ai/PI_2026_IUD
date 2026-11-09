# Severidad de accidentes de tránsito en Australia Occidental (2019–2023)

Proyecto Integrador III de Analítica de Datos, Institución Universitaria Digital de Antioquia.

Este README documenta la actividad **AE3: Transformación y enriquecimiento de datos**. Para AE2 (ideación y documentación de la necesidad) véase `AE2/`.

## Integrantes

- Juan Felipe Valencia Renteria
- Cristian Mateo Piedrahita Arango
- Diego Alejandro Barros Ballestas

## Propósito y necesidad

Las entidades de seguridad vial tienen un registro extenso de accidentes, pero no una lectura que relacione la gravedad con las condiciones en que ocurren. Un conteo total no distingue entre una categoría con muchos accidentes leves y otra con pocos accidentes fatales.

**Pregunta principal:** ¿cómo se distribuye la severidad (`SEVERITY`) de los accidentes registrados entre 2019 y 2023 según el tipo de calzada, la presencia de intersección, la franja horaria y los tipos de vehículos involucrados?

El alcance es descriptivo: no hay modelos predictivos, causas ni tasas de riesgo, porque el dataset no incluye datos de exposición (volumen de tránsito).

## Dataset

| Característica | Detalle |
|---|---|
| Identificador | `kalley/WA_Crash` (split `train`) |
| Enlace | https://huggingface.co/datasets/kalley/WA_Crash |
| Tamaño original | 127.102 filas × 26 columnas |
| Origen declarado | Main Roads Western Australia (Data WA) |
| Acceso | Público; no requiere token |

El dataset crudo **no se versiona**: `HFDatasetLoader` lo descarga de Hugging Face en cada ejecución (`.gitignore` excluye `**/WA_Crash.csv`).

## Transformaciones realizadas

El procesamiento está en la clase `PreprocesadorCrash` (`AE3/src/clases_po/preprocesamiento.py`).

| Paso | Regla | Resultado |
|---|---|---|
| Conversión de fecha | `CRASH_DATE` (texto día/mes/año) a fecha | 0 no interpretables |
| Conversión de hora | `CRASH_TIME` (HHMM) a `Int64`; válida si está entre 0000 y 2359 y minutos < 60 | 0 inválidas; los 109 nulos de origen se conservan |
| Conversión de conteos | Columnas `TOTAL_*_INVOLVED` a `Int64`; negativos y no enteros pasan a nulo | 0 afectados |
| Texto | Recorte de espacios al inicio y al final | 0 afectados |
| Filtro de periodo | Conservar 01/01/2019 a 31/12/2023 | 0 excluidos |
| Duplicados | Completos y por `ACC_ID` | 0 |
| Categorías | Variantes de `SEVERITY` y `CWAY`; valores esperados de `SEVERITY` | 0 variantes; 5 categorías esperadas |
| Intersección | Revisar faltantes de `INTERSECTION_NO` e `INTERSECTION_DESC` | 58.979 con ambos nulos; se conservan, no se imputan |
| Selección de columnas | Descartar `X`, `Y`, `ROAD_NO`, `ROAD_NAME`, `COMMON_ROAD_NAME`, `SLK`, `OBJECTID`, `GlobalID` | 26 → 18 columnas |

Resultado: **127.102 filas antes y después** (sin exclusiones). Cinco controles de validación se cumplen: fechas en el periodo, `ACC_ID` único, tipos esperados, horas válidas y categorías de `SEVERITY` esperadas.

## Enriquecimiento realizado

No se une ninguna tabla externa (no hay uniones que multipliquen registros). La clase `Enriquecimiento` (`AE3/src/clases_po/enriquecimiento.py`) agrega 8 variables derivadas (18 → 26 columnas):

| Variable | Regla |
|---|---|
| `ANIO` | Año de `CRASH_DATE` |
| `MES` | Mes de `CRASH_DATE` (1 a 12) |
| `DIA_SEMANA` | Lunes a Domingo |
| `ES_FIN_DE_SEMANA` | 1 si es sábado o domingo; 0 en otro caso |
| `FRANJA_HORARIA` | `CRASH_TIME // 100`: Madrugada 00–05, Mañana 06–11, Tarde 12–17, Noche 18–23; `Sin dato` si es nula |
| `ESTADO_INTERSECCION` | "Con intersección registrada" si `INTERSECTION_NO` o `INTERSECTION_DESC` no son nulos; en otro caso "Sin intersección registrada" |
| `TOTAL_VEHICULOS_INVOLUCRADOS` | Suma de bicicletas, camiones, camiones pesados, motocicletas y otros vehículos (sin peatones) |
| `ES_GRAVE` | 1 si `SEVERITY` es Fatal u Hospital; 0 en otro caso |

Contraste de `ESTADO_INTERSECCION` con `ACCIDENT_TYPE`: coinciden 127.083 de 127.102 registros (99,99 %); los 19 restantes se conservan sin corregir.

## Preguntas de negocio abordadas

| Id | Pregunta | Tabla |
|---|---|---|
| P1 | ¿Cómo se distribuye la severidad según el tipo de calzada (`CWAY`)? | `tabla_calzada` |
| P2 | ¿Cambia la severidad entre accidentes con y sin intersección registrada? | `tabla_interseccion` |
| P3 | ¿En qué franja horaria se concentran los accidentes graves? | `tabla_franja_horaria` |
| P4 | ¿Qué tipos de vehículos participan y con qué severidad? | `tabla_tipo_vehiculo` |
| P5 | ¿La proporción de accidentes graves cambió entre 2019 y 2023? | `tabla_anio` |
| P6 | ¿Hay meses con mayor proporción de accidentes graves? | `tabla_mes` |
| P7 | ¿Son más graves los accidentes en fin de semana? | `tabla_dia_semana` |
| P8 | ¿Aumenta la gravedad cuando participan más vehículos? | `tabla_total_vehiculos` |

P1 a P4 responden la pregunta principal; P5 a P8 la amplían con las variables derivadas.

## Pasos de ejecución

Requisitos: Python 3.11, Git y conexión a internet.

```bash
git clone https://github.com/juanrenteria-ai/PI_2026_IUD.git
cd PI_2026_IUD
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd AE3/notebooks
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=1800 \
  AE3_Transformacion_Enriquecimiento.ipynb
```

También puede abrirse con `jupyter lab` y ejecutar todas las celdas.

- **`API_KEY_NVIDIA` (opcional):** habilita la verificación independiente de lectura de las tablas con Nemotron Parse. Si no está definida, esa verificación queda como "Omitida" y el resto del flujo continúa. No escriba la clave en el código ni la suba al repositorio.
- **Ejecución automática:** el workflow `.github/workflows/ejecutar-ae3.yml` ejecuta el notebook en cada `push` a `main` que cambie `AE3/**` (excepto `AE3/documento/**`) y confirma los resultados.

## Rutas de salida

Todas las salidas se guardan en `AE3/resultados/`.

| Archivo | Contenido |
|---|---|
| `AE3/resultados/WA_Crash_enriquecido.csv` | **Dataset preparado**: 127.102 filas × 26 columnas |
| `AE3/resultados/resumen_dataframe.txt` | **Archivo descriptivo**: reporte del DataFrame final (filas, columnas, tipos, nulos y estadísticas) |
| `AE3/resultados/resumen_dataframe_metadata.txt` | **Archivo descriptivo (metadata)**: tipo, nulos, valores únicos, mínimo, máximo y longitudes por columna |
| `AE3/resultados/tabla_<nombre>.csv` y `.txt` | Una pareja por cada tabla de resultados (8 tablas) |
| `AE3/resultados/validacion_llm_tablas.csv` | Verificación de lectura de las tablas con Nemotron Parse |

Nombres de tabla: `calzada`, `interseccion`, `franja_horaria`, `tipo_vehiculo`, `anio`, `mes`, `dia_semana`, `total_vehiculos`.

## Tablas de resultados

Distribución general: Fatal 735 (0,58 %), Hospital 6.264 (4,93 %), Medical 16.485 (12,97 %), PDO Major 68.868 (54,18 %), PDO Minor 34.750 (27,34 %). **Graves (Fatal + Hospital): 6.999 (5,51 %).**

Proporción de accidentes graves por categoría (fuente: `AE3/resultados/tabla_*.csv`):

| Pregunta | Categoría | Accidentes (n) | Graves (%) |
|---|---|---:|---:|
| P1 Calzada | S (única) | 69.954 | 6,77 |
| | L (izquierda) | 44.758 | 3,89 |
| | R (derecha) | 12.390 | 4,23 |
| P2 Intersección | Con intersección registrada | 68.123 | 4,24 |
| | Sin intersección registrada | 58.979 | 6,97 |
| P3 Franja horaria | Madrugada | 5.355 | 11,17 |
| | Mañana | 41.208 | 4,78 |
| | Tarde | 60.278 | 4,68 |
| | Noche | 20.152 | 7,91 |
| | Sin dato | 109 | 14,68 |
| P4 Vehículo (no excluyentes) | Motocicleta | 4.334 | 33,32 |
| | Bicicleta | 2.539 | 15,75 |
| | Camión pesado | 2.318 | 8,46 |
| | Camión | 4.530 | 5,32 |
| | Otros vehículos | 118.208 | 4,73 |
| P5 Año | 2019 / 2020 / 2021 / 2022 / 2023 | 26.685 / 22.975 / 26.566 / 25.057 / 25.819 | 5,56 / 6,17 / 5,19 / 5,61 / 5,09 |
| P6 Mes | Enero (máx.) / Junio (mín.) | 9.152 / 11.128 | 6,15 / 4,90 |
| P7 Día | Domingo / Sábado / Lunes a viernes | 11.405 / 15.262 / 100.435 | 8,23 / 6,65 / 4,82–5,32 |
| P8 Total de vehículos | 0 / 1 / 2 / 3 o más | 5.292 / 31.178 / 84.111 / 6.521 | 7,20 / 11,18 / 3,27 / 5,89 |

Lectura breve:

- La gravedad no se reparte de forma homogénea: sube con motocicletas y bicicletas, en la madrugada y la noche, en calzada única, en tramos y en fines de semana.
- Volumen y gravedad no coinciden: la tarde concentra el 47,42 % de los accidentes pero tiene la menor proporción de graves.
- La gravedad no aumenta con más vehículos: el máximo está en los accidentes de un solo vehículo.

## Limitaciones

- Sin datos de exposición no se puede hablar de riesgo, solo de distribución de accidentes registrados.
- "Sin intersección registrada" es un dato faltante y no una verificación en terreno.
- Los tipos de vehículo no son excluyentes; "Otros vehículos" agrupa el 93 % de los accidentes sin detalle.
- La severidad proviene del registro policial y puede subestimar la gravedad de motociclistas, peatones y ciclistas.
- 109 registros no tienen hora (0,09 %).
- Las comparaciones son descriptivas: no se aplicaron pruebas estadísticas.

## Estructura del repositorio

```text
PI_2026_IUD/
├── .github/
│   └── workflows/
│       ├── ejecucion-automatica.yml     # ejecución automática de AE2
│       └── ejecutar-ae3.yml             # ejecución automática de AE3
├── AE2/                                 # ideación y documentación de la necesidad
│   ├── documento/
│   ├── notebooks/Semana_1SINC.ipynb
│   ├── resultados/
│   └── src/clases_po/
├── AE3/                                 # transformación y enriquecimiento
│   ├── documento/                       # (propuesto) informe Word de avance
│   ├── notebooks/
│   │   └── AE3_Transformacion_Enriquecimiento.ipynb
│   ├── resultados/                      # dataset preparado, tablas y reportes
│   └── src/clases_po/
│       ├── hf_loader.py                 # HFDatasetLoader (descarga desde Hugging Face)
│       ├── preprocesamiento.py          # PreprocesadorCrash
│       ├── enriquecimiento.py           # Enriquecimiento
│       ├── reportes.py                  # Reportes descriptivos
│       └── llm_nvidia.py                # ClienteNvidia (verificación de lectura)
├── .gitignore
├── README.md
└── requirements.txt
```


## Fuentes

- Dataset: https://huggingface.co/datasets/kalley/WA_Crash
- Datos de origen: Main Roads Western Australia, https://catalogue.data.wa.gov.au/dataset/mrwa-crash-information-last-5-years-
