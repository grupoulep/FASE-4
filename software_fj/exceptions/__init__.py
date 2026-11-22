"""Excepciones públicas del sistema."""

# Reexporta los errores de dominio para facilitar su importación.
from software_fj.exceptions.errores import (
    CalculoInconsistenteError,
    DatosInvalidosError,
    EntidadNoEncontradaError,
    ErrorPersistenciaLogError,
    OperacionNoPermitidaError,
    ParametroFaltanteError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)

# Declara explícitamente la API pública del subpaquete.
__all__ = [
    "CalculoInconsistenteError",
    "DatosInvalidosError",
    "EntidadNoEncontradaError",
    "ErrorPersistenciaLogError",
    "OperacionNoPermitidaError",
    "ParametroFaltanteError",
    "ReservaInvalidaError",
    "ServicioNoDisponibleError",
    "SoftwareFJError",
]
