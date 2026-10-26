# PI_2026_IUD: Proyecto Integrado III -Analitica de datos 
Severidad de los accidentes de tránsito en Australia Occidental (2019–2023)

Integrantes: 

Juan Felipe Valencia Renteria,
Cristian Mateo Piedrahita Arango,
Diego Alejandro Barros Ballestas.


Institución Universitaria Digital de Antioquia (Medellín, Antioquia). Octubre de 2026.

Caso de estudio real con registros públicos de accidentes de tránsito de Main Roads Western Australia. Este repositorio contiene el entorno para cargar los datos y el material de apoyo del informe de documento inicial del proyecto (Etapa 1).

## Propósito

Describir cómo se distribuye la severidad (`SEVERITY`) de los accidentes de tránsito registrados en Australia Occidental entre 2019 y 2023, según el tipo de calzada, la presencia de intersección, la franja horaria y los tipos de vehículos involucrados, para identificar en qué condiciones se concentran los desenlaces más graves, ccon el fin de apoyar en la mejora de iniciativas de seguridad vial.


## Necesidad

Las entidades de seguridad vial cuentan con un registro extenso de accidentes, pero no con una lectura que relacione la gravedad de los accidentes con las condiciones en que ocurren. Necesitan saber si los accidentes más graves se concentran en ciertos tipos de calzada, en intersecciones o tramos, en determinadas horas del día o cuando participan ciertos tipos de vehículos, para orientar la priorización de acciones de infraestructura, control y prevención.

**Pregunta clave:** ¿Cómo se distribuye la severidad (`SEVERITY`) de los accidentes registrados entre 2019 y 2023 según el tipo de calzada, la presencia de intersección, la franja horaria y los tipos de vehículos involucrados?

## Dataset

| Característica | Detalle |
|---|---|
| Identificador | `kalley/WA_Crash` |
| Enlace | https://huggingface.co/datasets/kalley/WA_Crash |
| Origen declarado | Main Roads Western Australia (Data WA) |
| Formato y tamaño | CSV, 29,9 MB |
| Filas y columnas | 127.102 filas, 26 columnas (una partición, `train`) |
| Licencia declarada | Apache 2.0 (confirmar las condiciones de origen en Data WA) |
| Unidad de análisis | Un accidente registrado (`ACC_ID`) |

Variables usadas para responder la pregunta:

| Dimensión | Variable |
|---|---|
| Resultado | `SEVERITY` |
| Tipo de calzada | `CWAY` |
| Presencia de intersección | `ACCIDENT_TYPE` (apoyo: `INTERSECTION_NO`, `INTERSECTION_DESC`) |
| Franja horaria | `CRASH_TIME` (se deriva de la hora en formato HHMM) |
| Periodo | `CRASH_DATE` (texto día/mes/año; se filtra 2019–2023) |
| Tipos de vehículos | `TOTAL_BIKE_INVOLVED`, `TOTAL_TRUCK_INVOLVED`, `TOTAL_HEAVY_TRUCK_INVOLVED`, `TOTAL_MOTOR_CYCLE_INVOLVED`, `TOTAL_OTHER_VEHICLES_INVOLVED` (complemento: `TOTAL_PEDESTRIANS_INVOLVED`) |

Repositorio de referencia: un notebook ejecutable por clase que deja un resumen `.txt` en `reportes/`.

## Pasos de ejecución

```bash
cd /workspaces/RP_AD2026Q4
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyarrow openpyxl  # opcional: parquet y xlsx
python scripts/build_notebooks.py   # opcional: regenerar notebooks
jupyter lab
```

En Bash, el entorno virtual debe activarse con `source` (o con un punto):

```bash
source .venv/bin/activate
# equivalente:
. .venv/bin/activate
```

No se debe ejecutar `.venv/bin/activate` directamente, porque `activate` es
un script que modifica la sesión actual de la terminal. Cuando se activa
correctamente, el prompt muestra `(.venv)`.

Cada notebook termina con `report.save()`, que escribe `reportes/<carpeta>/<notebook>.txt`.

## Autenticación en Hugging Face

Para descargar datasets públicos normalmente no se necesita un token. Si el
dataset es privado o requiere aceptación de condiciones de uso, configura un
token de Hugging Face siguiendo estos pasos.

### 1. Crear un token

1. Inicia sesión en [Hugging Face](https://huggingface.co/).
2. Abre [Settings > Access Tokens](https://huggingface.co/settings/tokens).
3. Selecciona **Create new token**.
4. Asigna un nombre descriptivo, por ejemplo `RP_AD2026Q4`.
5. Selecciona el permiso mínimo necesario: **Read**.
6. Presiona **Create token** y copia el token. Normalmente comienza por
   `hf_`.

Guarda el token de forma segura y no lo incluyas en el código fuente.

### 2. Instalar la CLI e iniciar sesión

Con el entorno virtual activado, instala o actualiza la librería de Hugging
Face:

```bash
python -m pip install --upgrade huggingface_hub
```

Inicia sesión desde la terminal:

```bash
hf auth login
```

Cuando la terminal solicite el token, pégalo y presiona **Enter**. Es normal
que no se muestren caracteres mientras lo escribes o pegas.

La sesión queda guardada localmente para que `HFDatasetLoader` pueda usarla
automáticamente. Comprueba que la autenticación funcionó:

```bash
hf auth whoami
```

Si tu instalación usa la CLI antigua, el comando equivalente es:

```bash
huggingface-cli login
```

### 3. Cargar el dataset autenticado

Después de iniciar sesión, no es necesario pasar el token al constructor:

```python
from rp_utils import HFDatasetLoader

loader = HFDatasetLoader(
    "Fast_Food_Restaurants",
    filename="datos/fast_food.csv",
)
df = loader.load()
```

No escribas tokens directamente en archivos Python ni los subas a GitHub.
Si un token se expone accidentalmente, revócalo desde [Access
Tokens](https://huggingface.co/settings/tokens) y crea uno nuevo.

## Carga de un dataset como DataFrame

`HFDatasetLoader` recibe el identificador del dataset, descarga la división
indicada y devuelve un `pandas.DataFrame`. `filename` y `file_type` son
opcionales; si se proporciona `filename`, el DataFrame también se guarda en
`csv`, `json`, `parquet` o `xlsx`.

```python
from rp_utils import HFDatasetLoader

loader = HFDatasetLoader(
    "Fast_Food_Restaurants",
    filename="datos/fast_food.csv",
)
df = loader.load()
```

Para ejecutar este ejemplo manualmente, crea un archivo `prueba_loader.py` en
la raíz del proyecto con el código anterior y ejecuta:

```bash
PYTHONPATH=src python prueba_loader.py
```

También se puede ejecutar directamente desde la terminal:

```bash
PYTHONPATH=src python -c '
from rp_utils import HFDatasetLoader

df = HFDatasetLoader(
    "Fast_Food_Restaurants",
    filename="datos/fast_food.csv",
).load()

print(df.head())
'
```

También se puede indicar el formato explícitamente:

```python
loader = HFDatasetLoader(
    "Fast_Food_Restaurants",
    filename="datos/fast_food",
    file_type="parquet",
)
df = loader.load()
```

# Estructura de archivos

```text
PI_2026_IUD/
├── .github/
│   └── workflows/        # flujos de GitHub Actions
├── src/                  # código fuente; incluye el módulo rp_utils (HFDatasetLoader)
├── datos/                # (se genera al ejecutar) copia local del dataset
├── .gitignore
├── README.md             # este archivo
└── requirements.txt      # dependencias de Python
