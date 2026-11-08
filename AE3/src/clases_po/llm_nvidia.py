"""Conexión con NVIDIA Nemotron 3.5 Parse (modelo de extracción de documentos).
 
``nvidia/nemotron-3.5-parse`` es un modelo de visión-lenguaje que recibe la
imagen de UNA página y devuelve su contenido en Markdown. No es un modelo de
chat: no redacta conocimiento de negocio a partir de texto. Por eso, en este
proyecto se usa como verificador independiente: cada tabla de resultados se
dibuja como imagen, el modelo la lee y las cifras leídas se comparan con las
cifras reales de la tabla (ver ``Enriquecimiento.validar_tabla_con_llm``).
 
La clave se lee de la variable de entorno ``API_KEY_NVIDIA`` (secreto de
Codespaces o de Actions). Nunca se escribe en el repositorio ni se imprime.
"""
from __future__ import annotations
 
import base64
import json
import os
import re
import urllib.error
import urllib.request
 
 
class LLMNoDisponible(RuntimeError):
    """El modelo no pudo usarse (sin clave, sin red o respuesta inesperada)."""
 
 
class ClienteNvidia:
    """Cliente mínimo para enviar una imagen a Nemotron Parse y leer su Markdown.
 
    Args:
        modelos: identificadores a probar, en orden, en el catálogo de NVIDIA. La
            documentación pública no confirma el id alojado de 3.5, así que si el
            primero responde 404/400/422 se intenta el siguiente.
        url: endpoint de la API alojada de NVIDIA. Si se usa un NIM propio
            (``POST /v1/parse``, multipart) hay que cambiar ``modo``.
        modo: ``"chat"`` (API alojada, formato OpenAI con imagen en base64) o
            ``"nim"`` (contenedor propio, multipart con el campo ``document``).
        prompt: prompt de control de Nemotron Parse. Por defecto solo texto plano,
            sin cajas ni clases, para que la salida no incluya coordenadas.
        timeout: segundos máximos de espera por solicitud.
    """
 
    VARIABLE_CLAVE = "API_KEY_NVIDIA"
    # lista: contenido como partes [texto, imagen]; img: texto con etiqueta <img>
    FORMATOS = ("img", "prompt_img", "lista")
 
    def __init__(
        self,
        modelos: tuple[str, ...] = ("nvidia/nemotron-3.5-parse", "nvidia/nemotron-parse"),
        url: str = "https://integrate.api.nvidia.com/v1/chat/completions",
        modo: str = "chat",
        prompt: str = "</s><s><no_bbox><no_classes><output_plain><predict_text_in_pic>",
        timeout: int = 120,
        api_key: str | None = None,
    ) -> None:
        if modo not in {"chat", "nim"}:
            raise ValueError("modo debe ser 'chat' o 'nim'.")
        self.modelos = tuple(modelos)
        self.modelo_usado: str | None = None
        self._combo: tuple[str, str] | None = None
        self._agotado: LLMNoDisponible | None = None
        self.url = url
        self.modo = modo
        self.prompt = prompt
        self.timeout = timeout
        self._api_key = api_key or os.environ.get(self.VARIABLE_CLAVE)
 
    def disponible(self) -> bool:
        """True si hay una clave configurada (no comprueba la red)."""
        return bool(self._api_key)
 
    def extraer_markdown(self, imagen_png: bytes) -> str:
        """Envía una imagen PNG y devuelve el Markdown que el modelo extrae."""
        if not self.disponible():
            raise LLMNoDisponible(
                f"No se encontró la variable de entorno {self.VARIABLE_CLAVE}."
            )
        if self._agotado is not None:
            raise self._agotado
        combinaciones = (
            [self._combo]
            if self._combo
            else [(m, f) for m in self.modelos for f in self.FORMATOS]
        )
        fallos: list[str] = []
        for modelo, formato in combinaciones:
            if self.modo == "chat":
                cuerpo, cabeceras = self._solicitud_chat(imagen_png, modelo, formato)
            else:
                cuerpo, cabeceras = self._solicitud_multipart(imagen_png)
            peticion = urllib.request.Request(
                self.url, data=cuerpo, headers=cabeceras, method="POST"
            )
            try:
                with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                    texto = respuesta.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as error:
                detalle = self._detalle_error(error)
                fallos.append(f"[{modelo} | {formato}] HTTP {error.code}: {detalle}")
                if error.code in (400, 404, 422) and self.modo == "chat" and not self._combo:
                    continue  # probar la siguiente combinación
                raise LLMNoDisponible(" ; ".join(fallos)) from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                raise LLMNoDisponible(f"No se pudo contactar la API: {error}.") from error
            self.modelo_usado = f"{modelo} ({formato})"
            self._combo = (modelo, formato)
            return self._leer_respuesta(texto)
        self._agotado = LLMNoDisponible(" ; ".join(fallos))
        raise self._agotado
 
    # ------------------------------------------------------------------ privados
    def _solicitud_chat(
        self, imagen_png: bytes, modelo: str, formato: str = "lista"
    ) -> tuple[bytes, dict[str, str]]:
        b64 = base64.b64encode(imagen_png).decode("ascii")
        url_imagen = f"data:image/png;base64,{b64}"
        if formato == "lista":
            contenido: object = [
                {"type": "text", "text": self.prompt},
                {"type": "image_url", "image_url": {"url": url_imagen}},
            ]
        elif formato == "prompt_img":
            contenido = f'{self.prompt}<img src="{url_imagen}" />'
        else:  # "img"
            contenido = f'<img src="{url_imagen}" />'
        carga = {
            "model": modelo,
            "messages": [{"role": "user", "content": contenido}],
            "temperature": 0.0,
            "max_tokens": 4096,
            "stream": False,
        }
        cabeceras = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return json.dumps(carga).encode("utf-8"), cabeceras
 
    @staticmethod
    def _detalle_error(error: urllib.error.HTTPError) -> str:
        """Primeros caracteres del cuerpo del error (no contiene la clave)."""
        try:
            cuerpo = error.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return "sin detalle"
        return re.sub(r"\s+", " ", cuerpo)[:240] or "sin detalle"
 
    def _solicitud_multipart(self, imagen_png: bytes) -> tuple[bytes, dict[str, str]]:
        frontera = "----ae3boundary7d1f"
        partes = (
            f"--{frontera}\r\n"
            'Content-Disposition: form-data; name="document"; filename="tabla.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("utf-8")
        cuerpo = partes + imagen_png + f"\r\n--{frontera}--\r\n".encode("utf-8")
        cabeceras = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": f"multipart/form-data; boundary={frontera}",
            "Accept": "application/json",
        }
        return cuerpo, cabeceras
 
    @staticmethod
    def _leer_respuesta(texto: str) -> str:
        """Extrae el Markdown de la respuesta, tolerando varias formas de salida."""
        try:
            datos = json.loads(texto)
        except json.JSONDecodeError:
            return texto
        if isinstance(datos, dict) and datos.get("choices"):
            mensaje = datos["choices"][0].get("message", {})
            llamadas = mensaje.get("tool_calls") or []
            if llamadas:
                argumentos = llamadas[0].get("function", {}).get("arguments", "")
                try:
                    estructura = json.loads(argumentos)
                except (json.JSONDecodeError, TypeError):
                    return str(argumentos)
                return ClienteNvidia._aplanar(estructura)
            return str(mensaje.get("content") or "")
        return ClienteNvidia._aplanar(datos)
 
    @staticmethod
    def _aplanar(estructura: object) -> str:
        """Une todos los textos de una estructura anidada en un solo string."""
        if isinstance(estructura, str):
            return estructura
        if isinstance(estructura, dict):
            return "\n".join(ClienteNvidia._aplanar(v) for v in estructura.values())
        if isinstance(estructura, list):
            return "\n".join(ClienteNvidia._aplanar(v) for v in estructura)
        return "" if estructura is None else str(estructura)
 
    @staticmethod
    def numeros_en_texto(texto: str) -> list[float]:
        """Devuelve los números que aparecen en un texto (admite 1,234.5 y 12.3)."""
        texto = re.sub(r"<[^>]*>", " ", texto)  # tokens de control y coordenadas
        encontrados = re.findall(r"-?\d[\d,]*\.?\d*", texto)
        valores: list[float] = []
        for item in encontrados:
            limpio = item.replace(",", "").rstrip(".")
            try:
                valores.append(float(limpio))
            except ValueError:
                continue
        return valores
 