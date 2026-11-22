"""Validadores estrictos reutilizados por modelos y servicios."""

import math
import re
from typing import TypeVar

from software_fj.exceptions.errores import (
    DatosInvalidosError,
    ParametroFaltanteError,
)

# El tipo genérico conserva el tipo de dato original al validar obligatoriedad.
T = TypeVar("T")


def requerido(valor: T, nombre: str) -> T:
    """Devuelve el valor o informa si falta."""
    # Trata None y texto en blanco como ausencia del argumento.
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ParametroFaltanteError(
            f"El parámetro '{nombre}' es obligatorio.", "PARAMETRO_FALTANTE"
        )
    return valor


def texto(valor: object, nombre: str, minimo: int = 1) -> str:
    """Valida texto no vacío con una longitud mínima."""
    requerido(valor, nombre)
    # Se normalizan espacios exteriores antes de devolver el texto.
    if not isinstance(valor, str) or len(valor.strip()) < minimo:
        raise DatosInvalidosError(
            f"'{nombre}' debe ser texto de al menos {minimo} caracteres.",
            "TEXTO_INVALIDO",
        )
    return valor.strip()


def numero(
    valor: object, nombre: str, minimo: float | None = None,
    estricto: bool = False,
) -> float:
    """Convierte a número finito y valida su límite inferior."""
    requerido(valor, nombre)
    # bool es subtipo de int en Python, pero no se considera importe válido.
    if isinstance(valor, bool):
        raise DatosInvalidosError(f"'{nombre}' debe ser numérico.", "NUMERO_INVALIDO")
    try:
        resultado = float(valor)
    except (TypeError, ValueError) as exc:
        # La excepción original se conserva como causa para facilitar el diagnóstico.
        raise DatosInvalidosError(
            f"'{nombre}' debe ser numérico.", "NUMERO_INVALIDO"
        ) from exc
    if not math.isfinite(resultado):
        raise DatosInvalidosError(f"'{nombre}' debe ser finito.", "NUMERO_INVALIDO")
    if minimo is not None and (
        resultado <= minimo if estricto else resultado < minimo
    ):
        # El modo estricto permite exigir, por ejemplo, tarifas mayores que cero.
        operador = "mayor que" if estricto else "mayor o igual que"
        raise DatosInvalidosError(
            f"'{nombre}' debe ser {operador} {minimo}.", "RANGO_INVALIDO"
        )
    return resultado


def entero(valor: object, nombre: str, minimo: int = 0) -> int:
    """Valida un entero sin aceptar booleanos ni truncar decimales."""
    requerido(valor, nombre)
    if isinstance(valor, bool):
        raise DatosInvalidosError(f"'{nombre}' debe ser entero.", "ENTERO_INVALIDO")
    try:
        convertido = int(valor)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError(
            f"'{nombre}' debe ser entero.", "ENTERO_INVALIDO"
        ) from exc
    if isinstance(valor, float) and not valor.is_integer():
        raise DatosInvalidosError(f"'{nombre}' debe ser entero.", "ENTERO_INVALIDO")
    if isinstance(valor, str) and str(convertido) != valor.strip():
        raise DatosInvalidosError(f"'{nombre}' debe ser entero.", "ENTERO_INVALIDO")
    if convertido < minimo:
        raise DatosInvalidosError(
            f"'{nombre}' no puede ser menor que {minimo}.", "RANGO_INVALIDO"
        )
    return convertido


def booleano(valor: object, nombre: str) -> bool:
    """Valida un booleano real, sin conversiones implícitas."""
    if not isinstance(valor, bool):
        raise DatosInvalidosError(f"'{nombre}' debe ser booleano.", "BOOLEANO_INVALIDO")
    return valor


def correo(valor: object) -> str:
    """Valida un correo electrónico de uso común."""
    resultado = texto(valor, "correo")
    # El patrón exige usuario, dominio y al menos un sufijo de dominio.
    patron = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )
    if not re.fullmatch(patron, resultado):
        raise DatosInvalidosError(
            "El correo no tiene un formato válido.", "CORREO_INVALIDO"
        )
    return resultado.lower()


def telefono(valor: object) -> str:
    """Valida un teléfono con 7 a 15 dígitos, admitiendo prefijo +."""
    resultado = texto(valor, "teléfono")
    if not re.fullmatch(r"\+?[0-9]{7,15}", resultado):
        raise DatosInvalidosError(
            "El teléfono debe contener entre 7 y 15 dígitos.", "TELEFONO_INVALIDO"
        )
    return resultado
