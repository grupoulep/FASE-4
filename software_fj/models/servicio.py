"""Clase abstracta de servicio y cálculo financiero común."""

import math
from abc import abstractmethod
from typing import overload

from software_fj.exceptions.errores import (
    CalculoInconsistenteError,
    DatosInvalidosError,
    ServicioNoDisponibleError,
)
from software_fj.models.entidad import EntidadSistema
from software_fj.utils.validadores import booleano, numero, texto


class Servicio(EntidadSistema):
    """Servicio tarifado con validación y cálculo extensible."""

    def __init__(
        self, codigo: str, nombre: str, descripcion: str, tarifa_base: float
    ) -> None:
        super().__init__("SRV")
        # Los datos comunes de catálogo se validan antes de crear el servicio.
        self.__codigo = texto(codigo, "código")
        self.__nombre = texto(nombre, "nombre")
        self.__descripcion = texto(descripcion, "descripción")
        self.__tarifa_base = 1.0
        self.tarifa_base = tarifa_base
        self.__disponible = True

    @property
    def codigo(self) -> str:
        """Devuelve el código comercial del servicio."""
        return self.__codigo

    @property
    def nombre(self) -> str:
        """Devuelve el nombre del servicio."""
        return self.__nombre

    @property
    def descripcion(self) -> str:
        """Devuelve la descripción del servicio."""
        return self.__descripcion

    @property
    def tarifa_base(self) -> float:
        """Devuelve la tarifa por unidad de tiempo."""
        return self.__tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        """Valida y actualiza la tarifa base."""
        self.__tarifa_base = numero(valor, "tarifa base", 0, estricto=True)

    @property
    def disponible(self) -> bool:
        """Indica si el servicio puede ofrecerse."""
        return self.__disponible

    @disponible.setter
    def disponible(self, valor: bool) -> None:
        """Actualiza el indicador de disponibilidad."""
        self.__disponible = booleano(valor, "disponible")

    @abstractmethod
    def validar_parametros(self, **kwargs: object) -> bool:
        """Valida parámetros propios requeridos para reservar."""
        # Cada servicio concreto define sus datos obligatorios y reglas.

    @abstractmethod
    def describir_servicio(self) -> str:
        """Devuelve descripción polimórfica del servicio."""
        # Las subclases describen su catálogo con sus propios atributos.

    @abstractmethod
    def calcular_costo_base(self, duracion: float, **kwargs: object) -> float:
        """Calcula el costo específico antes de impuestos/descuentos."""
        # El cálculo base se delega a la implementación especializada.

    # @overload ayuda al verificador de tipos; Python ejecuta la implementación
    # única definida más abajo con valores opcionales y parámetros nombrados.
    @overload
    def calcular_costo(self, duracion: float) -> float:
        """Sobrecarga para cotización base."""
        ...

    @overload
    def calcular_costo(self, duracion: float, tasa_impuesto: float) -> float:
        """Sobrecarga para cotización con impuesto."""
        ...

    @overload
    def calcular_costo(
        self, duracion: float, tasa_impuesto: float,
        descuento_porcentaje: float,
    ) -> float:
        """Sobrecarga para cotización con impuesto y descuento porcentual."""
        ...

    @overload
    def calcular_costo(
        self, duracion: float, tasa_impuesto: float = ...,
        descuento_porcentaje: float = ..., descuento_fijo: float = ...,
        recargo_adicional: float = ..., **parametros_servicio: object,
    ) -> float:
        """Sobrecarga integral con parámetros específicos del servicio."""
        ...

    def calcular_costo(
        self, duracion: float, tasa_impuesto: float = 0.0,
        descuento_porcentaje: float = 0.0, descuento_fijo: float = 0.0,
        recargo_adicional: float = 0.0, **parametros_servicio: object,
    ) -> float:
        """Calcula el total con recargos, descuentos e impuesto."""
        try:
            # Normaliza y valida los importes antes de operar con ellos.
            horas = numero(duracion, "duración")
            impuesto = numero(tasa_impuesto, "tasa de impuesto")
            porcentaje = numero(descuento_porcentaje, "descuento porcentual")
            fijo = numero(descuento_fijo, "descuento fijo")
            recargo = numero(recargo_adicional, "recargo adicional")
            if horas <= 0:
                raise CalculoInconsistenteError(
                    "La duración debe ser positiva.", "DURACION_INVALIDA"
                )
            if impuesto < 0 or impuesto > 1:
                raise CalculoInconsistenteError(
                    "La tasa de impuesto debe estar entre 0 y 1.", "IMPUESTO_INVALIDO"
                )
            if porcentaje < 0 or porcentaje > 100:
                raise CalculoInconsistenteError(
                    "El descuento porcentual debe estar entre 0% y 100%.",
                    "DESCUENTO_INVALIDO",
                )
            if fijo < 0 or recargo < 0:
                raise CalculoInconsistenteError(
                    "Descuentos y recargos deben ser no negativos.",
                    "AJUSTE_INVALIDO",
                )
            # El método especializado aporta el subtotal según el tipo de servicio.
            base = numero(
                self.calcular_costo_base(horas, **parametros_servicio),
                "costo base",
            )
            if base < 0:
                raise CalculoInconsistenteError(
                    "El costo base no puede ser negativo.", "BASE_INVALIDA"
                )
            # Aplica recargo y descuentos antes de calcular el impuesto.
            subtotal_con_recargo = base + recargo
            descuento = subtotal_con_recargo * (porcentaje / 100)
            if fijo > subtotal_con_recargo - descuento:
                raise CalculoInconsistenteError(
                    "El descuento fijo excede el subtotal.", "DESCUENTO_FIJO_INVALIDO"
                )
            neto = subtotal_con_recargo - descuento - fijo
            total = neto * (1 + impuesto)
            if not math.isfinite(total) or total < 0:
                raise CalculoInconsistenteError(
                    "El total calculado no es válido.", "TOTAL_INVALIDO"
                )
            return round(total, 2)
        except CalculoInconsistenteError:
            raise
        except (TypeError, ValueError, ArithmeticError, DatosInvalidosError) as exc:
            # Se transforma el fallo técnico en un error de dominio sin perder su causa.
            raise CalculoInconsistenteError(
                "No fue posible calcular un costo consistente.",
                "ERROR_CALCULO",
                str(exc),
            ) from exc

    def validar(self) -> bool:
        """Verifica que la tarifa del servicio sea válida."""
        if self.tarifa_base <= 0 or not self.disponible:
            return self.tarifa_base > 0
        return True

    def obtener_resumen(self) -> str:
        """Devuelve el resumen polimórfico del servicio."""
        return self.describir_servicio()

    def a_diccionario(self) -> dict[str, object]:
        """Serializa los atributos públicos del servicio."""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tipo": type(self).__name__,
            "tarifa_base": self.tarifa_base,
            "disponible": self.disponible,
            "descripcion": self.descripcion,
        }

    def asegurar_disponible(self) -> None:
        """Impide usar el servicio cuando está inhabilitado."""
        if not self.disponible or not self.activa:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.nombre}' no está disponible.",
                "SERVICIO_NO_DISPONIBLE",
            )
