# Severidad de accidentes de tránsito en Australia Occidental (2019–2023)

Proyecto Integrador de Analítica de Datos de la Institución Universitaria
Digital de Antioquia. Esta entrega contiene el código y los recursos
reproducibles de la actividad AE2: «Ideación, diseño y documentación de la
necesidad».

## Propósito y necesidad

Las entidades de seguridad vial necesitan relacionar la severidad de los
accidentes con las condiciones en que ocurren para orientar la priorización de
acciones de infraestructura, control y prevención.

**Pregunta de análisis:** ¿cómo se distribuye la severidad (SEVERITY) de los accidentes registrados entre 2019 y 2023 según el tipo de calzada, la presencia de intersección, la franja horaria y los tipos de vehículos involucrados?

## Integrantes

- Juan Felipe Valencia Renteria
- Cristian Mateo Piedrahita Arango
- Diego Alejandro Barros Ballestas

## Dataset

- **Identificador:** `kalley/WA_Crash`
- **Enlace:** <https://huggingface.co/datasets/kalley/WA_Crash>
- **Split:** `train` (dataset completo; no es muestra)
- **Licencia declarada en Hugging Face:** Apache 2.0
- **Autenticación:** el dataset público no requiere token.

El notebook descarga el dataset mediante `datasets` al ejecutarse y lo convierte
a un DataFrame de pandas. No se versiona una copia CSV; Hugging Face conserva la
caché local de la descarga. La licencia aquí indicada es la declarada en la
ficha del dataset.

## Estructura del repositorio

```text
PI_2026_IUD/
├── .github/
│   └── workflows/                 # Ejecución automática de AE2
├── AE2/
│   ├── documento/                 # Ubicación reservada para el documento del equipo
│   ├── notebooks/
│   │   └── Semana_1SINC.ipynb     # Notebook ejecutado
│   ├── resultados/
│   │   ├── resumen_dataframe.txt
│   │   ├── resumen_dataframe_metadata.txt
│   │   └── *_transformado.txt
│   └── src/
│       └── clases_po/             # Carga de Hugging Face y generación de reportes
├── .gitignore
├── README.md
└── requirements.txt
```

El DataFrame completo del split alimenta `resumen_dataframe.txt` y
`resumen_dataframe_metadata.txt`. Las salidas del ejercicio de transformaciones
se conservan por separado y llevan el sufijo `_transformado`.

## Ejecución local

Se requiere Python 3.11. Desde la raíz del repositorio, crea y activa un entorno
virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En macOS/Linux, activa el entorno con:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ejecuta el notebook desde la raíz:

```bash
jupyter nbconvert --to notebook --execute --inplace AE2/notebooks/Semana_1SINC.ipynb --ExecutePreprocessor.timeout=1800
```

También puede ejecutarse desde la carpeta del notebook:

```bash
cd AE2/notebooks
jupyter nbconvert --to notebook --execute --inplace Semana_1SINC.ipynb --ExecutePreprocessor.timeout=1800
```

El notebook crea o actualiza los reportes UTF-8 en `AE2/resultados/` en cada
ejecución. La salida de actividad `resumen_dataframe.txt` incluye la fecha de
generación, el identificador, split, indicación de dataset completo, dimensiones,
tipos de columnas y nulos por columna.

## GitHub Actions

El workflow de AE2 se ejecuta al recibir cambios en `main`: configura Python
3.11, instala las dependencias declaradas aquí y ejecuta el notebook completo.
Luego añade y confirma en `main` el notebook ejecutado y los archivos `.txt`
generados. El CSV descargado no se versiona. La ejecución automática puede
actualizar los outputs del notebook y los reportes cada vez que se ejecuta.
