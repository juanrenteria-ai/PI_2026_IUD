
"""Enriquecimiento del conjunto WA_Crash y tablas de respuesta a las preguntas de negocio.
 
Todas las variables derivadas se calculan con reglas deterministas sobre las
columnas ya transformadas por ``PreprocesadorCrash``; no se combina ninguna
otra tabla, por lo que no hay uniones que puedan multiplicar registros.
"""
from __future__ import annotations
 
import io
from pathlib import Path
 
import pandas as pd
 
from .llm_nvidia import ClienteNvidia, LLMNoDisponible
 
 
class Enriquecimiento:
    """Agrega variables derivadas, construye tablas por pregunta y las exporta."""
 
    SEVERIDADES = ("Fatal", "Hospital", "Medical", "PDO Major", "PDO Minor")
    SEVERIDAD_GRAVE = ("Fatal", "Hospital")
    DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    MESES = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
        "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    )
    FRANJAS = ("Madrugada", "Mañana", "Tarde", "Noche", "Sin dato")
    COLUMNAS_VEHICULOS = {
        "TOTAL_BIKE_INVOLVED": "Bicicleta",
        "TOTAL_TRUCK_INVOLVED": "Camión",
        "TOTAL_HEAVY_TRUCK_INVOLVED": "Camión pesado",
        "TOTAL_MOTOR_CYCLE_INVOLVED": "Motocicleta",
        "TOTAL_OTHER_VEHICLES_INVOLVED": "Otros vehículos",
    }
    NUEVAS_VARIABLES = (
        "ANIO",
        "MES",
        "DIA_SEMANA",
        "ES_FIN_DE_SEMANA",
        "FRANJA_HORARIA",
        "ESTADO_INTERSECCION",
        "TOTAL_VEHICULOS_INVOLUCRADOS",
        "ES_GRAVE",
    )
    FILAS_POR_IMAGEN = 6
    CON_INTERSECCION = "Con intersección registrada"
    SIN_INTERSECCION = "Sin intersección registrada"
 
    # ------------------------------------------------------------------ variables
    def catalogo_variables(self) -> pd.DataFrame:
        """Documenta fórmula, significado y utilidad de cada variable derivada."""
        filas = [
            (
                "ANIO",
                "CRASH_DATE.year",
                "Año calendario del accidente (2019–2023).",
                "Permite revisar si la distribución de severidad cambia entre años "
                "y si un patrón es estable en el tiempo.",
            ),
            (
                "MES",
                "CRASH_DATE.month (1 = enero … 12 = diciembre)",
                "Mes del año en que ocurrió el accidente.",
                "Detecta estacionalidad en la severidad (por ejemplo, meses con más "
                "accidentes graves) para planear campañas de prevención.",
            ),
            (
                "DIA_SEMANA",
                "Nombre del día según CRASH_DATE.dayofweek (Lunes … Domingo)",
                "Día de la semana del accidente.",
                "Identifica los días con mayor concentración de accidentes graves "
                "para orientar el control en vía.",
            ),
            (
                "ES_FIN_DE_SEMANA",
                "1 si DIA_SEMANA es Sábado o Domingo; 0 en otro caso",
                "Indicador de accidente ocurrido en fin de semana.",
                "Resume en un solo indicador la comparación entre días laborales y "
                "fin de semana.",
            ),
            (
                "FRANJA_HORARIA",
                "hora = CRASH_TIME // 100; Madrugada 00–05, Mañana 06–11, "
                "Tarde 12–17, Noche 18–23; 'Sin dato' si CRASH_TIME es nulo",
                "Tramo del día en que ocurrió el accidente.",
                "Responde directamente la pregunta por franja horaria y focaliza "
                "los horarios de control y prevención.",
            ),
            (
                "ESTADO_INTERSECCION",
                "'Con intersección registrada' si INTERSECTION_NO o INTERSECTION_DESC "
                "no son nulos; 'Sin intersección registrada' en otro caso",
                "Si el accidente tiene una intersección asociada en el registro.",
                "Responde la pregunta por presencia de intersección. Se contrasta con "
                "ACCIDENT_TYPE; 'sin registro' no prueba por sí solo que no exista.",
            ),
            (
                "TOTAL_VEHICULOS_INVOLUCRADOS",
                "TOTAL_BIKE + TOTAL_TRUCK + TOTAL_HEAVY_TRUCK + TOTAL_MOTOR_CYCLE + "
                "TOTAL_OTHER_VEHICLES (sin peatones); nulo si algún sumando es nulo",
                "Cantidad de vehículos que participaron en el accidente.",
                "Mide la complejidad del evento y permite ver si más vehículos "
                "se asocian a mayor severidad.",
            ),
            (
                "ES_GRAVE",
                "1 si SEVERITY es Fatal u Hospital; 0 en otro caso",
                "Indicador de accidente con víctimas fatales o que requirieron hospital.",
                "Permite calcular una tasa de gravedad comparable entre categorías "
                "de calzada, intersección, franja y vehículos.",
            ),
        ]
        return pd.DataFrame(
            filas, columns=["variable", "formula_o_regla", "significado", "utilidad"]
        )
 
    def preguntas_adicionales(self) -> pd.DataFrame:
        """Preguntas derivadas de la necesidad, ligadas a las variables nuevas."""
        filas = [
            ("P1", "¿Cómo se distribuye la severidad según el tipo de calzada (CWAY)?",
             "ES_GRAVE", "tabla_calzada"),
            ("P2", "¿Cambia la severidad entre accidentes con y sin intersección registrada?",
             "ESTADO_INTERSECCION, ES_GRAVE", "tabla_interseccion"),
            ("P3", "¿En qué franja horaria se concentran los accidentes graves?",
             "FRANJA_HORARIA, ES_GRAVE", "tabla_franja_horaria"),
            ("P4", "¿Qué tipos de vehículos participan en accidentes y con qué severidad?",
             "ES_GRAVE", "tabla_tipo_vehiculo"),
            ("P5", "¿La proporción de accidentes graves cambió entre 2019 y 2023?",
             "ANIO, ES_GRAVE", "tabla_anio"),
            ("P6", "¿Hay meses con mayor proporción de accidentes graves?",
             "MES, ES_GRAVE", "tabla_mes"),
            ("P7", "¿Son más graves los accidentes en fin de semana que en días laborales?",
             "DIA_SEMANA, ES_FIN_DE_SEMANA, ES_GRAVE", "tabla_dia_semana"),
            ("P8", "¿Aumenta la gravedad cuando participan más vehículos?",
             "TOTAL_VEHICULOS_INVOLUCRADOS, ES_GRAVE", "tabla_total_vehiculos"),
        ]
        return pd.DataFrame(
            filas, columns=["id", "pregunta", "variables", "tabla"]
        )
 
    def agregar_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Devuelve una copia de ``df`` con las ocho variables derivadas."""
        requeridas = {
            "CRASH_DATE", "CRASH_TIME", "SEVERITY", "INTERSECTION_NO",
            "INTERSECTION_DESC", *self.COLUMNAS_VEHICULOS,
        }
        faltantes = requeridas - set(df.columns)
        if faltantes:
            raise KeyError(f"Faltan columnas requeridas: {sorted(faltantes)}")
 
        resultado = df.copy(deep=True)
        fecha = pd.to_datetime(resultado["CRASH_DATE"])
        resultado["ANIO"] = fecha.dt.year.astype("Int64")
        resultado["MES"] = fecha.dt.month.astype("Int64")
        resultado["DIA_SEMANA"] = fecha.dt.dayofweek.map(
            dict(enumerate(self.DIAS))
        ).astype("string")
        resultado["ES_FIN_DE_SEMANA"] = fecha.dt.dayofweek.ge(5).astype("int64")
 
        hora = (pd.to_numeric(resultado["CRASH_TIME"], errors="coerce") // 100)
        franja = pd.Series(pd.NA, index=resultado.index, dtype="string")
        # fillna(False): una condición nula en mask() se trataría como verdadera.
        franja = franja.mask(hora.between(0, 5).fillna(False).astype(bool), "Madrugada")
        franja = franja.mask(hora.between(6, 11).fillna(False).astype(bool), "Mañana")
        franja = franja.mask(hora.between(12, 17).fillna(False).astype(bool), "Tarde")
        franja = franja.mask(hora.between(18, 23).fillna(False).astype(bool), "Noche")
        resultado["FRANJA_HORARIA"] = franja.fillna("Sin dato").astype("string")
 
        con_interseccion = resultado["INTERSECTION_NO"].notna() | resultado[
            "INTERSECTION_DESC"
        ].notna()
        resultado["ESTADO_INTERSECCION"] = pd.Series(
            self.SIN_INTERSECCION, index=resultado.index, dtype="string"
        ).mask(con_interseccion, self.CON_INTERSECCION)
 
        vehiculos = resultado[list(self.COLUMNAS_VEHICULOS)].astype("Int64")
        resultado["TOTAL_VEHICULOS_INVOLUCRADOS"] = vehiculos.sum(
            axis=1, skipna=False
        ).astype("Int64")
 
        severidad = self._severidad_canonica(resultado["SEVERITY"])
        resultado["ES_GRAVE"] = severidad.isin(self.SEVERIDAD_GRAVE).astype("int64")
        return resultado
 
    def contrastar_interseccion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cruza ESTADO_INTERSECCION con ACCIDENT_TYPE para sustentar la regla."""
        if "ACCIDENT_TYPE" not in df.columns:
            raise KeyError("Se requiere ACCIDENT_TYPE para el contraste.")
        cruce = pd.crosstab(
            df["ESTADO_INTERSECCION"], df["ACCIDENT_TYPE"].fillna("Sin dato"),
            margins=True, margins_name="Total",
        )
        cruce.columns.name = None
        cruce.index.name = "ESTADO_INTERSECCION"
        return cruce.reset_index()
 
    # --------------------------------------------------------------------- tablas
    def tabla_calzada(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._tabla_severidad(df["CWAY"].astype("string"), df, "Tipo de calzada (CWAY)")
 
    def tabla_interseccion(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._tabla_severidad(
            df["ESTADO_INTERSECCION"], df, "Estado de intersección",
            orden=[self.CON_INTERSECCION, self.SIN_INTERSECCION],
        )
 
    def tabla_franja_horaria(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._tabla_severidad(
            df["FRANJA_HORARIA"], df, "Franja horaria", orden=list(self.FRANJAS)
        )
 
    def tabla_anio(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._tabla_severidad(df["ANIO"].astype("string"), df, "Año")
 
    def tabla_mes(self, df: pd.DataFrame) -> pd.DataFrame:
        etiquetas = df["MES"].map(
            {i + 1: f"{i + 1:02d} - {m}" for i, m in enumerate(self.MESES)}
        ).astype("string")
        return self._tabla_severidad(etiquetas, df, "Mes")
 
    def tabla_dia_semana(self, df: pd.DataFrame) -> pd.DataFrame:
        etiquetas = df["DIA_SEMANA"]
        return self._tabla_severidad(
            etiquetas, df, "Día de la semana", orden=list(self.DIAS)
        )
 
    def tabla_total_vehiculos(self, df: pd.DataFrame) -> pd.DataFrame:
        total = df["TOTAL_VEHICULOS_INVOLUCRADOS"]
        etiquetas = pd.Series("Sin dato", index=df.index, dtype="string")
        etiquetas = etiquetas.mask(total.eq(0).fillna(False), "0 vehículos")
        etiquetas = etiquetas.mask(total.eq(1).fillna(False), "1 vehículo")
        etiquetas = etiquetas.mask(total.eq(2).fillna(False), "2 vehículos")
        etiquetas = etiquetas.mask(total.ge(3).fillna(False), "3 o más vehículos")
        return self._tabla_severidad(
            etiquetas, df, "Vehículos involucrados",
            orden=["0 vehículos", "1 vehículo", "2 vehículos", "3 o más vehículos", "Sin dato"],
        )
 
    def tabla_tipo_vehiculo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tabla por tipo de vehículo. Las filas NO son excluyentes.
 
        Un accidente puede involucrar varios tipos, por lo que los porcentajes
        de la columna ``% del total de accidentes`` no suman 100.
        """
        severidad = self._severidad_canonica(df["SEVERITY"])
        total_general = len(df)
        filas = []
        for columna, etiqueta in self.COLUMNAS_VEHICULOS.items():
            mascara = df[columna].gt(0).fillna(False).astype(bool)
            filas.append(
                self._fila_resumen(etiqueta, severidad[mascara], total_general)
            )
        filas.append(
            self._fila_resumen("Todos los accidentes (referencia)", severidad, total_general)
        )
        resultado = pd.DataFrame(filas)
        return resultado.rename(columns={"categoria": "Tipo de vehículo"})
 
    def construir_tablas(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Genera todas las tablas, indexadas por el nombre de archivo."""
        return {
            "tabla_calzada": self.tabla_calzada(df),
            "tabla_interseccion": self.tabla_interseccion(df),
            "tabla_franja_horaria": self.tabla_franja_horaria(df),
            "tabla_tipo_vehiculo": self.tabla_tipo_vehiculo(df),
            "tabla_anio": self.tabla_anio(df),
            "tabla_mes": self.tabla_mes(df),
            "tabla_dia_semana": self.tabla_dia_semana(df),
            "tabla_total_vehiculos": self.tabla_total_vehiculos(df),
        }
 
    # ------------------------------------------------------------- interpretación
    LIMITACIONES = {
        "tabla_calzada": "No hay datos de tránsito ni de longitud de cada tipo de calzada; "
        "un mayor número de accidentes puede reflejar más exposición y no más riesgo.",
        "tabla_interseccion": "'Sin intersección registrada' significa que el dato falta; "
        "se contrasta con ACCIDENT_TYPE, pero no se verifica en terreno.",
        "tabla_franja_horaria": "Las franjas tienen distinta duración efectiva de tráfico; "
        "sin volumen horario no se puede hablar de riesgo, solo de registros. "
        "Las horas nulas se agrupan en 'Sin dato'.",
        "tabla_tipo_vehiculo": "Las filas no son excluyentes (un accidente puede involucrar "
        "varios tipos), por eso los porcentajes del total no suman 100. "
        "'Otros vehículos' agrupa tipos no detallados en el dataset.",
        "tabla_anio": "El periodo incluye años afectados por cambios de movilidad; "
        "la comparación entre años es descriptiva.",
        "tabla_mes": "Con cinco años por mes, un solo año atípico puede mover el resultado; "
        "no se controla el clima ni el volumen de viajes.",
        "tabla_dia_semana": "Los fines de semana tienen otro patrón de viajes; "
        "sin exposición no se puede afirmar que sean más peligrosos.",
        "tabla_total_vehiculos": "Suma bicicletas, camiones, camiones pesados, motos y otros "
        "vehículos; no incluye peatones. Los accidentes con 0 vehículos registrados "
        "pueden ser casos con solo peatones o datos incompletos.",
    }
 
    def interpretar_tabla(
        self, nombre: str, tabla: pd.DataFrame, minimo_accidentes: int = 100
    ) -> str:
        """Texto corto con hallazgos calculados de la propia tabla y sus limitaciones."""
        categoria = tabla.columns[0]
        cuerpo = tabla[~tabla[categoria].astype(str).str.contains("referencia|^Total$", regex=True)]
        referencia = tabla[tabla[categoria].astype(str).str.contains("referencia|^Total$", regex=True)]
        tasa_global = float(referencia["Graves (% de la fila)"].iloc[-1])
        candidatas = cuerpo[
            (cuerpo["Accidentes (n)"] >= minimo_accidentes)
            & (~cuerpo[categoria].astype(str).eq("Sin dato"))
        ]
        partes = [f"Tasa global de accidentes graves (Fatal + Hospital): {tasa_global:.2f} %."]
        if not candidatas.empty:
            mayor = candidatas.loc[candidatas["Accidentes (n)"].idxmax()]
            alta = candidatas.loc[candidatas["Graves (% de la fila)"].idxmax()]
            baja = candidatas.loc[candidatas["Graves (% de la fila)"].idxmin()]
            partes.append(
                f"Mayor volumen: {mayor[categoria]} con {int(mayor['Accidentes (n)']):,} "
                f"accidentes ({mayor['% del total de accidentes']:.2f} % del total)."
            )
            partes.append(
                f"Mayor proporción de graves: {alta[categoria]} con "
                f"{alta['Graves (% de la fila)']:.2f} %; la menor: {baja[categoria]} con "
                f"{baja['Graves (% de la fila)']:.2f} % (categorías con al menos "
                f"{minimo_accidentes} accidentes)."
            )
        partes.append(f"Limitaciones: {self.LIMITACIONES.get(nombre, '')}")
        return " ".join(partes)
 
    # ---------------------------------------------------------------- verificación
    def verificar_tablas(
        self, df: pd.DataFrame, tablas: dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Comprueba totales y porcentajes; lanza AssertionError si algo no cuadra."""
        total = len(df)
        resultados = []
        for nombre, tabla in tablas.items():
            col_total = "Accidentes (n)"
            col_pct_total = "% del total de accidentes"
            severidades_n = [f"{s} (n)" for s in self.SEVERIDADES]
            severidades_pct = [f"{s} (% de la fila)" for s in self.SEVERIDADES]
 
            cuerpo = tabla[~tabla.iloc[:, 0].astype(str).str.contains("referencia|^Total$", regex=True)]
            es_excluyente = nombre != "tabla_tipo_vehiculo"
 
            suma_severidad = tabla[severidades_n].sum(axis=1)
            assert (suma_severidad == tabla[col_total]).all(), (
                f"{nombre}: la suma por severidad no coincide con el total de cada fila."
            )
            pct_filas = tabla[severidades_pct].sum(axis=1)
            assert (pct_filas.sub(100).abs() <= 0.1).all(), (
                f"{nombre}: los porcentajes por fila no suman 100 %."
            )
            if es_excluyente:
                assert int(cuerpo[col_total].sum()) == total, (
                    f"{nombre}: los totales no suman {total}."
                )
                assert abs(float(cuerpo[col_pct_total].sum()) - 100) <= 0.1 * max(len(cuerpo), 1), (
                    f"{nombre}: el % del total no suma 100 %."
                )
            else:
                assert int(tabla.iloc[-1][col_total]) == total
            resultados.append(
                {
                    "tabla": nombre,
                    "filas": len(tabla),
                    "total_accidentes": int(cuerpo[col_total].sum()) if es_excluyente else total,
                    "excluyente": "Sí" if es_excluyente else "No (un accidente puede estar en varias filas)",
                    "estado": "OK",
                }
            )
        return pd.DataFrame(resultados)
 
    def verificar_exportacion(
        self,
        df: pd.DataFrame,
        tablas: dict[str, pd.DataFrame],
        carpeta: str | Path,
    ) -> pd.DataFrame:
        """Relee los archivos exportados y confirma que coinciden con la memoria."""
        carpeta = Path(carpeta)
        resultados = []
        leido = pd.read_csv(carpeta / "WA_Crash_enriquecido.csv", low_memory=False)
        assert len(leido) == len(df), "El CSV enriquecido no tiene las mismas filas."
        assert list(leido.columns) == list(df.columns), "Las columnas del CSV difieren."
        assert leido.isna().sum().to_dict() == df.isna().sum().to_dict(), (
            "Los nulos del CSV enriquecido difieren de los del DataFrame."
        )
        resultados.append({"archivo": "WA_Crash_enriquecido.csv", "estado": "OK", "filas": len(leido)})
        for nombre, tabla in tablas.items():
            csv = pd.read_csv(carpeta / f"{nombre}.csv")
            pd.testing.assert_frame_equal(
                csv, tabla.reset_index(drop=True), check_dtype=False, check_exact=False
            )
            texto = (carpeta / f"{nombre}.txt").read_text(encoding="utf-8")
            assert f"Total de filas: {len(tabla)}" in texto, f"{nombre}.txt incompleto."
            resultados.append({"archivo": f"{nombre}.csv/.txt", "estado": "OK", "filas": len(csv)})
        return pd.DataFrame(resultados)
 
    # ------------------------------------------------------------------ exportación
    def exportar_resultados(
        self,
        df: pd.DataFrame,
        tablas: dict[str, pd.DataFrame],
        carpeta: str | Path,
    ) -> list[Path]:
        """Escribe el dataset enriquecido y, por tabla, un CSV y un TXT."""
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        preguntas = self.preguntas_adicionales().set_index("tabla")["pregunta"].to_dict()
        rutas = []
 
        ruta = carpeta / "WA_Crash_enriquecido.csv"
        df.to_csv(ruta, index=False)
        rutas.append(ruta)
 
        for nombre, tabla in tablas.items():
            ruta_csv = carpeta / f"{nombre}.csv"
            tabla.to_csv(ruta_csv, index=False)
            ruta_txt = carpeta / f"{nombre}.txt"
            pregunta = preguntas.get(nombre, "")
            ruta_txt.write_text(
                f"TABLA: {nombre}\nPregunta: {pregunta}\n"
                f"Total de filas: {len(tabla)}\n"
                f"{'=' * 60}\n{tabla.to_string(index=False)}\n\n"
                f"Interpretación: {self.interpretar_tabla(nombre, tabla)}\n",
                encoding="utf-8",
            )
            rutas.extend([ruta_csv, ruta_txt])
        return rutas
 
    # ----------------------------------------------------------------- LLM (Nemotron)
    def validar_tabla_con_llm(
        self, nombre: str, tabla: pd.DataFrame, cliente: ClienteNvidia
    ) -> dict[str, object]:
        """Dibuja la tabla como imagen y comprueba que Nemotron Parse la lea igual.
 
        Es un control independiente de lectura; no genera ni modifica cifras.
        Nunca lanza excepciones: si el modelo no está disponible devuelve el
        motivo para que el flujo continúe.
        """
        esperadas = self._cifras_enteras(tabla)
        base = {"tabla": nombre, "cifras_esperadas": len(esperadas)}
        if not cliente.disponible():
            return {**base, "cifras_leidas": 0, "coincidencia_pct": None,
                    "estado": "Omitida: sin API_KEY_NVIDIA"}
        leidas: set[int] = set()
        # Las tablas altas se leen peor: se envían en bloques de pocas filas.
        bloques = [
            tabla.iloc[i : i + self.FILAS_POR_IMAGEN]
            for i in range(0, len(tabla), self.FILAS_POR_IMAGEN)
        ]
        try:
            for numero, bloque in enumerate(bloques, start=1):
                titulo = nombre if len(bloques) == 1 else f"{nombre} ({numero}/{len(bloques)})"
                markdown = cliente.extraer_markdown(self._tabla_a_png(bloque, titulo))
                leidas |= {
                    int(v)
                    for v in ClienteNvidia.numeros_en_texto(markdown)
                    if float(v).is_integer()
                }
        except LLMNoDisponible as error:
            return {**base, "cifras_leidas": 0, "coincidencia_pct": None,
                    "estado": f"Omitida: {error}"}
        except Exception as error:  # noqa: BLE001 - el control no debe romper el flujo
            return {**base, "cifras_leidas": 0, "coincidencia_pct": None,
                    "estado": f"Omitida: error inesperado ({type(error).__name__})"}
 
        encontradas = sum(1 for valor in esperadas if valor in leidas)
        porcentaje = round(100 * encontradas / len(esperadas), 2) if esperadas else None
        estado = "Coincide" if porcentaje is not None and porcentaje >= 95 else "Revisar"
        return {**base, "cifras_leidas": len(leidas), "coincidencia_pct": porcentaje,
                "estado": f"{estado} (modelo: {cliente.modelo_usado})"}
 
    def validar_tablas_con_llm(
        self, tablas: dict[str, pd.DataFrame], cliente: ClienteNvidia
    ) -> pd.DataFrame:
        return pd.DataFrame(
            [self.validar_tabla_con_llm(n, t, cliente) for n, t in tablas.items()]
        )
 
    # -------------------------------------------------------------------- privados
    @classmethod
    def _severidad_canonica(cls, serie: pd.Series) -> pd.Series:
        mapa = {s.upper(): s for s in cls.SEVERIDADES}
        texto = serie.astype("string").str.strip().str.upper()
        return texto.map(mapa).astype("string")
 
    def _fila_resumen(
        self, etiqueta: str, severidad: pd.Series, total_general: int
    ) -> dict[str, object]:
        total = len(severidad)
        fila: dict[str, object] = {
            "categoria": etiqueta,
            "Accidentes (n)": total,
            "% del total de accidentes": round(100 * total / total_general, 2) if total_general else 0.0,
        }
        conteos = severidad.value_counts()
        for sev in self.SEVERIDADES:
            fila[f"{sev} (n)"] = int(conteos.get(sev, 0))
        for sev in self.SEVERIDADES:
            fila[f"{sev} (% de la fila)"] = (
                round(100 * int(conteos.get(sev, 0)) / total, 2) if total else 0.0
            )
        graves = sum(int(conteos.get(s, 0)) for s in self.SEVERIDAD_GRAVE)
        fila["Graves (n)"] = graves
        fila["Graves (% de la fila)"] = round(100 * graves / total, 2) if total else 0.0
        return fila
 
    def _tabla_severidad(
        self,
        categorias: pd.Series,
        df: pd.DataFrame,
        nombre_categoria: str,
        orden: list[str] | None = None,
    ) -> pd.DataFrame:
        severidad = self._severidad_canonica(df["SEVERITY"])
        etiquetas = categorias.astype("string").fillna("Sin dato")
        valores = list(orden) if orden else sorted(etiquetas.unique())
        extra = [v for v in etiquetas.unique() if v not in valores]
        total_general = len(df)
        filas = []
        for valor in [*valores, *sorted(extra)]:
            mascara = etiquetas.eq(valor)
            if not mascara.any():
                continue
            filas.append(self._fila_resumen(valor, severidad[mascara], total_general))
        filas.append(self._fila_resumen("Total", severidad, total_general))
        return pd.DataFrame(filas).rename(columns={"categoria": nombre_categoria})
 
    @staticmethod
    def _cifras_enteras(tabla: pd.DataFrame) -> list[int]:
        columnas_n = [c for c in tabla.columns if str(c).endswith("(n)")]
        valores = tabla[columnas_n].to_numpy().ravel()
        return sorted({int(v) for v in valores if int(v) >= 10})
 
    @staticmethod
    def _tabla_a_png(tabla: pd.DataFrame, titulo: str) -> bytes:
        import matplotlib
 
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
 
        legible = tabla.copy()
        for columna in legible.columns:
            if str(columna).endswith("(n)"):
                legible[columna] = legible[columna].map(lambda v: f"{int(v):,}")
        figura, eje = plt.subplots(figsize=(16.64, 2.0 + 0.5 * len(legible)), dpi=100)
        eje.axis("off")
        eje.set_title(titulo, fontsize=14)
        tabla_dibujada = eje.table(
            cellText=legible.astype(str).values,
            colLabels=list(legible.columns),
            loc="center",
        )
        tabla_dibujada.auto_set_font_size(False)
        tabla_dibujada.set_fontsize(8)
        tabla_dibujada.scale(1, 1.6)
        memoria = io.BytesIO()
        figura.savefig(memoria, format="png", bbox_inches="tight")
        plt.close(figura)
        return memoria.getvalue()
 