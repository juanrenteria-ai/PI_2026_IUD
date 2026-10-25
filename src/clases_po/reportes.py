"""Generación de reportes de DataFrames."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


class Reportes:
    """Imprime y guarda un resumen legible de un DataFrame."""

    def generar_reporte(self, df: pd.DataFrame) -> str:
        """Genera el contenido textual del reporte."""
        self._validar_dataframe(df)
        numericas = df.select_dtypes(include="number")
        lineas = [
            "REPORTE DEL DATAFRAME",
            "=" * 60,
            f"Filas: {len(df)}",
            f"Columnas: {len(df.columns)}",
            f"Duplicados: {int(df.duplicated().sum())}",
            "",
            "Columnas y tipos:",
            *[f"- {columna}: {tipo}" for columna, tipo in df.dtypes.items()],
            "",
            "Valores nulos por columna:",
            *[f"- {columna}: {cantidad}" for columna, cantidad in df.isna().sum().items()],
        ]

        if not numericas.empty:
            lineas += [
                "",
                "Estadísticas numéricas:",
                numericas.describe().round(3).to_string(),
            ]

        return "\n".join(lineas) + "\n"

    def reporte_descriptivo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Devuelve tipo, límites y conteos descriptivos para cada columna."""
        self._validar_dataframe(df)
        metadatos = []

        for columna in df.columns:
            serie = df[columna]
            registro = {
                "columna": columna,
                "tipo": str(serie.dtype),
                "valores_nulos": int(serie.isna().sum()),
                "valores_unicos": int(serie.nunique(dropna=True)),
                "valor_minimo": None,
                "valor_maximo": None,
                "longitud_minima": None,
                "longitud_maxima": None,
            }

            if pd.api.types.is_numeric_dtype(serie.dtype):
                registro["valor_minimo"] = serie.min()
                registro["valor_maximo"] = serie.max()
            else:
                longitudes = serie.dropna().astype("string").str.len()
                if not longitudes.empty:
                    registro["longitud_minima"] = int(longitudes.min())
                    registro["longitud_maxima"] = int(longitudes.max())

            metadatos.append(registro)

        return pd.DataFrame(metadatos)

    def imprimir_reporte(self, df: pd.DataFrame) -> None:
        """Imprime en la consola el reporte del DataFrame."""
        print(self.generar_reporte(df), end="")

    def guardar_reporte(self, df: pd.DataFrame, ruta: str | Path) -> Path:
        """Guarda el reporte en un archivo de texto y devuelve su ruta."""
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.generar_reporte(df), encoding="utf-8")
        return path

    def guardar_reporte_metadata(
        self, metadata: pd.DataFrame, ruta: str | Path
    ) -> Path:
        """Guarda la metadata descriptiva como una tabla de texto."""
        self._validar_dataframe(metadata)
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(metadata.to_string(index=False) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _validar_dataframe(df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df debe ser un pandas.DataFrame.")