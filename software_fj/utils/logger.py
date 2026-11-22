"""Registro estructurado y exclusivo de eventos en archivo de texto."""

from datetime import datetime
from pathlib import Path
import traceback

from software_fj.exceptions.errores import ErrorPersistenciaLogError


class GestorLogs:
    """Escribe eventos en ``logs/software_fj.log`` y permite leerlos."""

    def __init__(self, ruta: str | Path | None = None) -> None:
        # Por defecto el log vive en la raíz del proyecto; se puede inyectar otra ruta.
        raiz = Path(__file__).resolve().parents[2]
        self._ruta = (
            Path(ruta) if ruta is not None else raiz / "logs" / "software_fj.log"
        )

    def registrar_evento(
        self, nivel: str, operacion: str, mensaje: str, detalles: str = ""
    ) -> None:
        """Registra un evento con timestamp y nivel explícito."""
        # Se valida el nivel antes de escribir para mantener un formato uniforme.
        nivel_normalizado = nivel.upper()
        if nivel_normalizado not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"Nivel de log no permitido: {nivel}")
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detalle = f" | {detalles}" if detalles else ""
        linea = f"[{marca}] [{nivel_normalizado}] [{operacion}] {mensaje}{detalle}\n"
        archivo = None
        try:
            # La carpeta y el archivo se crean al primer evento que se registra.
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            archivo = self._ruta.open("a", encoding="utf-8")
            archivo.write(linea)
            archivo.flush()
        except OSError as exc:
            raise ErrorPersistenciaLogError(
                f"No fue posible escribir en {self._ruta}.",
                "ERROR_ESCRITURA_LOG",
                str(exc),
            ) from exc
        finally:
            # El archivo se cierra aun cuando la escritura haya producido un error.
            if archivo is not None:
                try:
                    archivo.close()
                except OSError as exc:
                    raise ErrorPersistenciaLogError(
                        f"No fue posible cerrar {self._ruta}.",
                        "ERROR_CIERRE_LOG",
                        str(exc),
                    ) from exc

    def registrar_advertencia(self, operacion: str, mensaje: str) -> None:
        """Registra una advertencia."""
        self.registrar_evento("WARNING", operacion, mensaje)

    def registrar_error(self, excepcion: BaseException, contexto: str) -> None:
        """Registra el error, su causa y una traza resumida."""
        # Se conserva la causa encadenada y se compacta la traza para una línea de log.
        causa = excepcion.__cause__
        traza = " ".join(
            "".join(
                traceback.format_exception(
                    type(excepcion), excepcion, excepcion.__traceback__
                )
            ).split()
        )
        detalle = f"{type(excepcion).__name__}: {excepcion}"
        if causa is not None:
            detalle += f" | Causa original: {type(causa).__name__}: {causa}"
        if traza:
            detalle += f" | Traza: {traza}"
        self.registrar_evento("ERROR", contexto, str(excepcion), detalle)

    def leer_ultimos_logs(self, n: int) -> list[str]:
        """Lee las últimas n entradas del archivo de log."""
        # Rechaza cantidades inválidas antes de intentar acceder al archivo.
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError("n debe ser un entero no negativo.")
        archivo = None
        try:
            archivo = self._ruta.open("r", encoding="utf-8")
            return archivo.readlines()[-n:] if n else []
        except OSError as exc:
            raise ErrorPersistenciaLogError(
                f"No fue posible leer {self._ruta}.",
                "ERROR_LECTURA_LOG",
                str(exc),
            ) from exc
        finally:
            if archivo is not None:
                archivo.close()
