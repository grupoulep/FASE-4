"""Jerarquía de errores de dominio de Software FJ."""

# Los errores especializados permiten diferenciar fallos de validación,
# reglas del negocio, reservas, cálculos y escritura de logs.
class SoftwareFJError(Exception):
    """Error base con código estable y detalles opcionales."""

    def __init__(
        self, mensaje: str, codigo_error: str = "SOFTWARE_FJ_ERROR",
        detalles: object = None,
    ) -> None:
        # Estos campos conservan un mensaje legible, un código y el detalle técnico.
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        self.detalles = detalles
        super().__init__(mensaje)


# Cada subclase da a las capas superiores una forma precisa de tratar el error.
class DatosInvalidosError(SoftwareFJError):
    """Dato con tipo o formato no admitido."""


class ParametroFaltanteError(SoftwareFJError):
    """Falta un parámetro obligatorio."""


class OperacionNoPermitidaError(SoftwareFJError):
    """La operación contradice una regla de negocio."""


class ReservaInvalidaError(SoftwareFJError):
    """La reserva o su transición no es válida."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio o recurso no puede reservarse."""


class CalculoInconsistenteError(SoftwareFJError):
    """Un importe o parámetro financiero es inconsistente."""


class EntidadNoEncontradaError(SoftwareFJError):
    """No se encontró la entidad solicitada."""


class ErrorPersistenciaLogError(SoftwareFJError):
    """No fue posible leer o escribir el archivo de logs."""
