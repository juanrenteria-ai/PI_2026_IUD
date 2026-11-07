"""Transformación y validación del conjunto de accidentes WA_Crash."""
from __future__ import annotations

import pandas as pd


class PreprocesadorCrash:
    """Prepara los datos de accidentes sin modificar el DataFrame recibido."""

    COLUMNAS_CONTEO = (
        "TOTAL_BIKE_INVOLVED",
        "TOTAL_TRUCK_INVOLVED",
        "TOTAL_HEAVY_TRUCK_INVOLVED",
        "TOTAL_MOTOR_CYCLE_INVOLVED",
        "TOTAL_OTHER_VEHICLES_INVOLVED",
        "TOTAL_PEDESTRIANS_INVOLVED",
    )
    COLUMNAS_REQUERIDAS = (
        "ACC_ID",
        "CWAY",
        "INTERSECTION_NO",
        "INTERSECTION_DESC",
        "LONGITUDE",
        "LATITUDE",
        "CRASH_DATE",
        "CRASH_TIME",
        "SEVERITY",
        "EVENT_NATURE",
        "EVENT_TYPE",
        *COLUMNAS_CONTEO,
    )
    COLUMNAS_CONSERVADAS = (
        "ACC_ID",
        "CWAY",
        "INTERSECTION_NO",
        "INTERSECTION_DESC",
        "LONGITUDE",
        "LATITUDE",
        "CRASH_DATE",
        "CRASH_TIME",
        "ACCIDENT_TYPE",
        "SEVERITY",
        "EVENT_NATURE",
        "EVENT_TYPE",
        *COLUMNAS_CONTEO,
    )
    SEVERIDADES_ESPERADAS = {
        "FATAL",
        "HOSPITAL",
        "MEDICAL",
        "PDO MAJOR",
        "PDO MINOR",
    }

    def __init__(self) -> None:
        self._log: list[dict[str, object]] = []
        self._conversion_stats: dict[str, int] = {}

    def diagnosticar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resume tipos, datos presentes y faltantes de cada columna."""
        self._validar_dataframe(df)
        total = len(df)
        filas = []
        for columna in df.columns:
            valores = df[columna].dropna()
            filas.append(
                {
                    "columna": columna,
                    "tipo_actual": str(df[columna].dtype),
                    "no_nulos": int(df[columna].notna().sum()),
                    "nulos": int(df[columna].isna().sum()),
                    "porcentaje_nulos": (
                        round(float(df[columna].isna().sum() / total * 100), 2)
                        if total
                        else 0.0
                    ),
                    "ejemplo": valores.iloc[0] if not valores.empty else None,
                }
            )
        return pd.DataFrame(filas)

    def convertir_tipos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convierte fechas, horas, conteos y texto en una copia del DataFrame."""
        self._validar_dataframe(df)
        resultado = df.copy(deep=True)
        stats: dict[str, int] = {}

        fechas_originales = resultado["CRASH_DATE"]
        fechas = pd.to_datetime(fechas_originales, dayfirst=True, errors="coerce")
        stats["fechas_no_interpretables"] = int(
            (fechas_originales.notna() & fechas.isna()).sum()
        )
        resultado["CRASH_DATE"] = fechas

        horas_originales = resultado["CRASH_TIME"]
        horas_numericas = pd.to_numeric(horas_originales, errors="coerce")
        horas_enteras = horas_numericas.notna() & horas_numericas.mod(1).eq(0)
        horas_candidatas = horas_numericas.where(horas_enteras)
        hhmm = horas_candidatas.fillna(-1).astype("int64")
        horas_validas = (
            horas_enteras
            & hhmm.between(0, 2359)
            & hhmm.mod(100).lt(60)
        )
        stats["horas_invalidas"] = int((horas_originales.notna() & ~horas_validas).sum())
        resultado["CRASH_TIME"] = horas_candidatas.where(horas_validas).astype("Int64")

        for columna in self.COLUMNAS_CONTEO:
            valores_originales = resultado[columna]
            numericos = pd.to_numeric(valores_originales, errors="coerce")
            enteros = numericos.notna() & numericos.mod(1).eq(0)
            stats[f"conteos_invalidos:{columna}"] = int(
                (valores_originales.notna() & ~enteros).sum()
            )
            resultado[columna] = numericos.where(enteros).astype("Int64")

        espacios = 0
        for columna in resultado.select_dtypes(include=["object", "string"]).columns:
            texto = resultado[columna].astype("string")
            limpio = texto.str.strip()
            espacios += int((texto.notna() & texto.ne(limpio)).sum())
            resultado[columna] = limpio
        stats["textos_con_espacios_sobrantes"] = espacios
        self._conversion_stats = stats
        return resultado

    def tratar_calidad(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtros justificados y registra cada control de calidad."""
        self._validar_dataframe(df)
        resultado = df.copy(deep=True)
        self._log = []

        antes = len(resultado)
        fechas_invalidas = int(resultado["CRASH_DATE"].isna().sum())
        resultado = resultado.loc[resultado["CRASH_DATE"].notna()].copy()
        self._registrar(
            "fechas no interpretables",
            "Excluir registros sin fecha interpretable",
            "Sin fecha no es posible asignar el accidente al periodo de análisis; "
            "se eliminan únicamente esas filas.",
            fechas_invalidas,
            antes,
            len(resultado),
        )

        antes = len(resultado)
        fuera_periodo = ~resultado["CRASH_DATE"].between(
            pd.Timestamp("2019-01-01"), pd.Timestamp("2023-12-31 23:59:59.999999")
        )
        afectados = int(fuera_periodo.sum())
        resultado = resultado.loc[~fuera_periodo].copy()
        self._registrar(
            "filtro de periodo",
            "Conservar accidentes entre 2019 y 2023 inclusive",
            "La pregunta de análisis limita el alcance a esos cinco años; "
            f"se excluyen {afectados} registros fuera del periodo.",
            afectados,
            antes,
            len(resultado),
        )

        antes = len(resultado)
        duplicados = int(resultado.duplicated(keep="first").sum())
        resultado = resultado.drop_duplicates(keep="first").copy()
        self._registrar(
            "duplicados completos",
            "Conservar una copia de cada fila idéntica",
            "Las repeticiones exactas no representan registros independientes.",
            duplicados,
            antes,
            len(resultado),
        )

        antes = len(resultado)
        mascara_duplicados_id = resultado["ACC_ID"].notna() & resultado[
            "ACC_ID"
        ].duplicated(keep="first")
        duplicados_id = int(mascara_duplicados_id.sum())
        resultado = resultado.loc[~mascara_duplicados_id].copy()
        self._registrar(
            "duplicados por ACC_ID",
            "Conservar el primer registro de cada identificador de accidente",
            "ACC_ID identifica el accidente; los registros repetidos no se cuentan "
            "como accidentes adicionales y se conserva la primera fila.",
            duplicados_id,
            antes,
            len(resultado),
        )

        ambas_nulas = resultado["INTERSECTION_NO"].isna() & resultado[
            "INTERSECTION_DESC"
        ].isna()
        solo_uno_nulo = resultado["INTERSECTION_NO"].isna() ^ resultado[
            "INTERSECTION_DESC"
        ].isna()
        self._registrar(
            "consistencia de intersección",
            "Revisar el patrón de faltantes de INTERSECTION_NO e INTERSECTION_DESC",
            f"{int(ambas_nulas.sum())} registros tienen ambas variables nulas; "
            f"{int(solo_uno_nulo.sum())} tienen solo una nula. Se conservan todos "
            "los faltantes: no equivalen a ausencia de intersección.",
            int(solo_uno_nulo.sum()),
            len(resultado),
            len(resultado),
        )

        self._registrar(
            "horas inválidas",
            "Invalidar horas fuera de HHMM (0000-2359 y minutos menores que 60)",
            "Las horas inválidas se convierten en nulos; no se imputan y las filas "
            "se conservan. Los nulos originales también se conservan.",
            self._conversion_stats.get("horas_invalidas", 0),
            len(resultado),
            len(resultado),
        )

        texto_espacios = self._conversion_stats.get(
            "textos_con_espacios_sobrantes", 0
        )
        self._registrar(
            "normalización de texto",
            "Eliminar espacios sobrantes al inicio y al final",
            "Se recortan únicamente los valores que contenían espacios periféricos.",
            texto_espacios,
            len(resultado),
            len(resultado),
        )

        for columna in ("SEVERITY", "CWAY"):
            resultado, cambios, variantes = self._normalizar_variantes(
                resultado, columna
            )
            self._registrar(
                f"categorías de {columna}",
                "Revisar variantes por mayúsculas/minúsculas o espacios",
                (
                    f"Variantes agrupadas encontradas: {variantes}; se normalizaron "
                    f"{cambios} valores al valor original más frecuente de cada grupo."
                    if variantes
                    else "No se encontraron categorías duplicadas por mayúsculas, "
                    "minúsculas o espacios; no se normalizaron categorías."
                ),
                cambios,
                len(resultado),
                len(resultado),
            )

        severidades = resultado["SEVERITY"].astype("string").str.strip().str.upper()
        severidades_invalidas = int(
            (severidades.notna() & ~severidades.isin(self.SEVERIDADES_ESPERADAS)).sum()
        )
        self._registrar(
            "valores de SEVERITY",
            "Contrastar categorías con FATAL, HOSPITAL, MEDICAL, PDO MAJOR y PDO MINOR",
            "No se eliminan ni sustituyen categorías desconocidas; se reportan para "
            "revisión y la validación final las marcará.",
            severidades_invalidas,
            len(resultado),
            len(resultado),
        )

        negativos = 0
        for columna in self.COLUMNAS_CONTEO:
            mascara = resultado[columna].lt(0).fillna(False)
            cantidad = int(mascara.sum())
            negativos += cantidad
            resultado.loc[mascara, columna] = pd.NA
            self._registrar(
                f"conteos negativos: {columna}",
                f"Convertir negativos de {columna} en nulos",
                "Un conteo de vehículos/personas no puede ser negativo; se conserva "
                "la fila y se invalida solo el valor imposible.",
                cantidad,
                len(resultado),
                len(resultado),
            )

        conteos_no_convertibles = sum(
            self._conversion_stats.get(f"conteos_invalidos:{columna}", 0)
            for columna in self.COLUMNAS_CONTEO
        )
        self._registrar(
            "conteos no enteros o no numéricos",
            "Invalidar valores de conteo que no sean enteros numéricos",
            "Los valores no interpretables como enteros se registran como nulos; "
            "las filas se conservan.",
            conteos_no_convertibles,
            len(resultado),
            len(resultado),
        )
        return resultado

    def seleccionar_columnas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Conserva las variables de análisis y registra cada descarte."""
        self._validar_dataframe(df)
        resultado = df.copy(deep=True)

        comparaciones = []
        for proyectada, geografica in (("X", "LONGITUDE"), ("Y", "LATITUDE")):
            if proyectada in resultado and geografica in resultado:
                a = pd.to_numeric(resultado[proyectada], errors="coerce")
                b = pd.to_numeric(resultado[geografica], errors="coerce")
                coinciden = a.notna() & b.notna()
                diferencias = (a - b).abs()
                iguales = coinciden & diferencias.le(1e-9)
                max_diferencia = (
                    float(diferencias[coinciden].max())
                    if coinciden.any()
                    else None
                )
                comparaciones.append(
                    f"{proyectada}/{geografica}: {int(iguales.sum())} iguales "
                    f"(tolerancia absoluta 1e-9) de {int(coinciden.sum())} comparables; "
                    f"diferencia absoluta máxima={max_diferencia}"
                )
            else:
                comparaciones.append(
                    f"{proyectada}/{geografica}: comparación no posible por columna ausente"
                )

        descartes = [
            columna for columna in resultado.columns
            if columna not in self.COLUMNAS_CONSERVADAS
        ]
        for columna in descartes:
            criterio = (
                "Se comparó numéricamente con LONGITUDE/LATITUDE: "
                + "; ".join(comparaciones)
                + f". Se descarta {columna} por redundancia y se conservan "
                "LONGITUDE y LATITUDE para visualizaciones posteriores de AE4."
                if columna in {"X", "Y"}
                else (
                    "Identificador técnico de origen sin dimensión analítica."
                    if columna in {"OBJECTID", "GlobalID"}
                    else "Dato vial/localizador no requerido para las dimensiones "
                    "definidas en la pregunta."
                )
            )
            self._registrar(
                f"selección de columnas: {columna}",
                f"Descartar {columna}",
                criterio,
                int(resultado[columna].notna().sum()),
                len(resultado),
                len(resultado),
            )

        conservadas = [c for c in self.COLUMNAS_CONSERVADAS if c in resultado.columns]
        return resultado.loc[:, conservadas].copy()

    def procesar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ejecuta la preparación completa en una copia y retorna datos limpios."""
        self._validar_dataframe(df)
        faltantes = [c for c in self.COLUMNAS_REQUERIDAS if c not in df.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas requeridas de WA_Crash: {faltantes}")
        self._log = []
        self._conversion_stats = {}
        convertido = self.convertir_tipos(df)
        calidad = self.tratar_calidad(convertido)
        return self.seleccionar_columnas(calidad)

    def comparar_antes_despues(
        self, df_original: pd.DataFrame, df_limpio: pd.DataFrame
    ) -> pd.DataFrame:
        """Compara dimensiones, tipos y nulos de cada columna antes y después."""
        self._validar_dataframe(df_original)
        self._validar_dataframe(df_limpio)
        columnas = list(dict.fromkeys([*df_original.columns, *df_limpio.columns]))
        filas = []
        for columna in columnas:
            filas.append(
                {
                    "columna": columna,
                    "filas_antes": len(df_original),
                    "columnas_antes": len(df_original.columns),
                    "tipo_antes": (
                        str(df_original[columna].dtype)
                        if columna in df_original
                        else "descartada"
                    ),
                    "nulos_antes": (
                        int(df_original[columna].isna().sum())
                        if columna in df_original
                        else None
                    ),
                    "filas_despues": len(df_limpio),
                    "columnas_despues": len(df_limpio.columns),
                    "tipo_despues": (
                        str(df_limpio[columna].dtype)
                        if columna in df_limpio
                        else "descartada"
                    ),
                    "nulos_despues": (
                        int(df_limpio[columna].isna().sum())
                        if columna in df_limpio
                        else None
                    ),
                }
            )
        return pd.DataFrame(filas)

    def tabla_log(self) -> pd.DataFrame:
        """Devuelve las decisiones de calidad registradas como tabla."""
        columnas = (
            "paso",
            "regla",
            "criterio/justificación",
            "registros_afectados",
            "filas_antes",
            "filas_despues",
        )
        return pd.DataFrame(self._log, columns=columnas)

    def validar(self, df_limpio: pd.DataFrame) -> bool:
        """Imprime controles del resultado y devuelve si todos se cumplen."""
        self._validar_dataframe(df_limpio)
        controles: list[tuple[str, bool]] = []
        fecha = df_limpio.get("CRASH_DATE")
        controles.append(
            (
                "Fechas completas dentro del periodo 2019-2023",
                bool(
                    fecha is not None
                    and fecha.notna().all()
                    and fecha.between("2019-01-01", "2023-12-31 23:59:59.999999").all()
                ),
            )
        )
        identificador = df_limpio.get("ACC_ID")
        controles.append(
            (
                "ACC_ID único y no nulo",
                bool(
                    identificador is not None
                    and identificador.notna().all()
                    and not identificador.duplicated().any()
                ),
            )
        )
        tipos_correctos = (
            "CRASH_DATE" in df_limpio
            and pd.api.types.is_datetime64_any_dtype(df_limpio["CRASH_DATE"])
            and "CRASH_TIME" in df_limpio
            and str(df_limpio["CRASH_TIME"].dtype) == "Int64"
            and all(
                columna in df_limpio
                and str(df_limpio[columna].dtype) == "Int64"
                for columna in self.COLUMNAS_CONTEO
            )
        )
        controles.append(("Tipos esperados de fechas, horas y conteos", tipos_correctos))

        hora = df_limpio.get("CRASH_TIME")
        horas_validas = bool(
            hora is not None
            and (
                hora.dropna().between(0, 2359)
                & hora.dropna().mod(100).lt(60)
            ).all()
        )
        controles.append(("Horas no nulas válidas en formato HHMM", horas_validas))

        severidad = df_limpio.get("SEVERITY")
        severidades_validas = bool(
            severidad is not None
            and severidad.notna().all()
            and severidad.astype("string").str.strip().str.upper().isin(
                self.SEVERIDADES_ESPERADAS
            ).all()
        )
        controles.append(("Categorías de SEVERITY esperadas", severidades_validas))

        for nombre, correcto in controles:
            print(f"{'✔' if correcto else '✘'} {nombre}")
        return all(correcto for _, correcto in controles)

    def _registrar(
        self,
        paso: str,
        regla: str,
        criterio: str,
        afectados: int,
        filas_antes: int,
        filas_despues: int,
    ) -> None:
        self._log.append(
            {
                "paso": paso,
                "regla": regla,
                "criterio/justificación": criterio,
                "registros_afectados": int(afectados),
                "filas_antes": int(filas_antes),
                "filas_despues": int(filas_despues),
            }
        )

    @staticmethod
    def _normalizar_variantes(
        df: pd.DataFrame, columna: str
    ) -> tuple[pd.DataFrame, int, int]:
        resultado = df.copy()
        valores = resultado[columna].dropna()
        cambios = 0
        variantes = 0
        for _, indices in valores.groupby(
            valores.astype("string").str.strip().str.casefold()
        ).groups.items():
            originales = resultado.loc[indices, columna]
            distintos = originales.drop_duplicates()
            if len(distintos) > 1:
                variantes += 1
                canonico = originales.value_counts().index[0]
                mascara = resultado.index.isin(indices) & resultado[columna].ne(canonico)
                cambios += int(mascara.sum())
                resultado.loc[mascara, columna] = canonico
        return resultado, cambios, variantes

    @staticmethod
    def _validar_dataframe(df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df debe ser un pandas.DataFrame.")
