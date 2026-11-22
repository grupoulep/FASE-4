"""Ciclo de vida de una reserva."""

from copy import deepcopy
from datetime import datetime
from enum import Enum

from software_fj.exceptions.errores import (
    CalculoInconsistenteError,
    OperacionNoPermitidaError,
    ParametroFaltanteError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from software_fj.models.cliente import Cliente
from software_fj.models.entidad import EntidadSistema
from software_fj.models.servicio import Servicio
from software_fj.models.servicios_especializados import AlquilerEquipo
from software_fj.utils.validadores import numero, texto


class EstadoReserva(Enum):
    """Estados permitidos de una reserva."""

    # El estado limita qué transiciones del ciclo de vida son legales.
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    PROCESADA = "PROCESADA"
    CANCELADA = "CANCELADA"


class Reserva(EntidadSistema):
    """Reserva vinculada a un cliente y a un servicio."""

    def __init__(
        self, cliente: Cliente, servicio: Servicio, duracion_horas: float,
        fecha_programada: datetime,
        parametros_servicio: dict[str, object] | None = None,
    ) -> None:
        super().__init__("RES")
        # Comprueba referencias y datos estructurales antes de aceptar la reserva.
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError(
                "Se requiere un cliente válido.", "CLIENTE_INVALIDO"
            )
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError(
                "Se requiere un servicio válido.", "SERVICIO_INVALIDO"
            )
        self.__cliente = cliente
        self.__servicio = servicio
        self.__duracion_horas = numero(duracion_horas, "duración", 0, estricto=True)
        if not isinstance(fecha_programada, datetime):
            raise ReservaInvalidaError(
                "La fecha programada debe ser datetime.", "FECHA_INVALIDA"
            )
        if (
            parametros_servicio is not None
            and not isinstance(parametros_servicio, dict)
        ):
            raise ReservaInvalidaError(
                "Los parámetros del servicio deben ser un diccionario.",
                "PARAMETROS_INVALIDOS",
            )
        self.__fecha_programada = fecha_programada
        # Se guarda una copia para impedir que el llamador cambie los parámetros
        # de la reserva sin pasar por sus validaciones.
        self.__parametros_servicio = deepcopy(parametros_servicio or {})
        self.__estado = EstadoReserva.PENDIENTE
        self.__costo_total: float | None = None
        self.__desglose_calculo: dict[str, float] = {}
        self.__motivo_cancelacion: str | None = None

    @property
    def cliente(self) -> Cliente:
        """Devuelve el cliente asociado."""
        return self.__cliente

    @property
    def servicio(self) -> Servicio:
        """Devuelve el servicio asociado."""
        return self.__servicio

    @property
    def duracion_horas(self) -> float:
        """Devuelve la duración reservada."""
        return self.__duracion_horas

    @property
    def fecha_programada(self) -> datetime:
        """Devuelve la fecha y hora de inicio."""
        return self.__fecha_programada

    @property
    def parametros_servicio(self) -> dict[str, object]:
        """Devuelve una copia aislada de los parámetros específicos."""
        return deepcopy(self.__parametros_servicio)

    @property
    def estado(self) -> EstadoReserva:
        """Devuelve el estado actual."""
        return self.__estado

    @property
    def costo_total(self) -> float | None:
        """Devuelve el importe liquidado, si existe."""
        return self.__costo_total

    @property
    def desglose_calculo(self) -> dict[str, float]:
        """Devuelve una copia del desglose financiero."""
        return dict(self.__desglose_calculo)

    @property
    def motivo_cancelacion(self) -> str | None:
        """Devuelve el motivo de cancelación, si fue cancelada."""
        return self.__motivo_cancelacion

    def calcular_presupuesto(
        self, tasa_impuesto: float = 0.0, descuento_porcentaje: float = 0.0,
        descuento_fijo: float = 0.0, recargo_adicional: float = 0.0,
    ) -> float:
        """Calcula una cotización provisional con los parámetros propios."""
        try:
            # El cálculo fiscal y el cálculo específico se delegan al servicio.
            return self.__servicio.calcular_costo(
                self.__duracion_horas,
                tasa_impuesto=tasa_impuesto,
                descuento_porcentaje=descuento_porcentaje,
                descuento_fijo=descuento_fijo,
                recargo_adicional=recargo_adicional,
                **self.__parametros_servicio,
            )
        except CalculoInconsistenteError as exc:
            raise ReservaInvalidaError(
                "No fue posible calcular el presupuesto de la reserva.",
                "PRESUPUESTO_INVALIDO",
                str(exc),
            ) from exc

    def confirmar(self) -> None:
        """Valida y confirma una reserva pendiente."""
        # Primero verifica la transición; luego la disponibilidad y los parámetros.
        if self.__estado is not EstadoReserva.PENDIENTE:
            raise ReservaInvalidaError(
                "Solo se puede confirmar una reserva pendiente.",
                "TRANSICION_INVALIDA",
            )
        if not self.__cliente.activa:
            raise ReservaInvalidaError(
                "El cliente está inactivo.", "CLIENTE_INACTIVO"
            )
        try:
            self.__servicio.asegurar_disponible()
            self.__servicio.validar_parametros(**self.__parametros_servicio)
            # El stock solo se descuenta después de superar todas las validaciones.
            if isinstance(self.__servicio, AlquilerEquipo):
                self.__servicio.reservar_unidades(
                    int(self.__parametros_servicio["cantidad"])
                )
        except ServicioNoDisponibleError:
            raise
        except SoftwareFJError as exc:
            raise ReservaInvalidaError(
                "Los parámetros de la reserva no son válidos.",
                "RESERVA_INVALIDA",
                str(exc),
            ) from exc
        self.__estado = EstadoReserva.CONFIRMADA

    def procesar(
        self, tasa_impuesto: float = 0.19, descuento_porcentaje: float = 0.0,
        recargo_adicional: float = 0.0, descuento_fijo: float = 0.0,
    ) -> float:
        """Liquida una reserva confirmada y registra el desglose."""
        # Una reserva solo se liquida después de haber sido confirmada.
        if self.__estado is not EstadoReserva.CONFIRMADA:
            raise ReservaInvalidaError(
                "Solo se puede procesar una reserva confirmada.",
                "TRANSICION_INVALIDA",
            )
        try:
            # Conserva el costo base y obtiene el total con ajustes y tributos.
            base = self.__servicio.calcular_costo_base(
                self.__duracion_horas, **self.__parametros_servicio
            )
            total = self.__servicio.calcular_costo(
                self.__duracion_horas,
                tasa_impuesto=tasa_impuesto,
                descuento_porcentaje=descuento_porcentaje,
                descuento_fijo=descuento_fijo,
                recargo_adicional=recargo_adicional,
                **self.__parametros_servicio,
            )
            if total < 0:
                raise CalculoInconsistenteError("Total negativo.", "TOTAL_INVALIDO")
            subtotal = (base + recargo_adicional) * (
                1 - descuento_porcentaje / 100
            ) - descuento_fijo
            self.__costo_total = total
            # Registra los componentes para que el total pueda explicarse al cliente.
            self.__desglose_calculo = {
                "costo_base": round(base, 2),
                "recargo_adicional": round(recargo_adicional, 2),
                "descuento_porcentual": round(
                    (base + recargo_adicional) * descuento_porcentaje / 100, 2
                ),
                "descuento_fijo": round(descuento_fijo, 2),
                "impuesto": round(total - subtotal, 2),
                "total": total,
            }
            self.__estado = EstadoReserva.PROCESADA
            return total
        except (SoftwareFJError, TypeError, ValueError, ArithmeticError) as exc:
            if isinstance(exc, ReservaInvalidaError):
                raise
            raise ReservaInvalidaError(
                "Falló la liquidación de la reserva.",
                "ERROR_PROCESAMIENTO",
                str(exc),
            ) from exc

    def cancelar(self, motivo: str) -> None:
        """Cancela reserva pendiente/confirmada y devuelve equipo si corresponde."""
        # Solo se revierte una reserva no procesada y con un motivo informado.
        if self.__estado not in {EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA}:
            raise OperacionNoPermitidaError(
                "No se puede cancelar una reserva procesada o cancelada.",
                "CANCELACION_NO_PERMITIDA",
            )
        if motivo is None or not isinstance(motivo, str) or not motivo.strip():
            raise ParametroFaltanteError(
                "Debe indicar un motivo de cancelación.", "MOTIVO_FALTANTE"
            )
        if self.__estado is EstadoReserva.CONFIRMADA and isinstance(
            self.__servicio, AlquilerEquipo
        ):
            # Al cancelar un alquiler confirmado, se restauran las unidades tomadas.
            self.__servicio.liberar_unidades(
                int(self.__parametros_servicio["cantidad"])
            )
        self.__motivo_cancelacion = texto(motivo, "motivo")
        self.__estado = EstadoReserva.CANCELADA

    def validar(self) -> bool:
        """Verifica las referencias y la duración de la reserva."""
        return (
            self.__duracion_horas > 0
            and isinstance(self.__cliente, Cliente)
            and isinstance(self.__servicio, Servicio)
        )

    def obtener_resumen(self) -> str:
        """Devuelve un resumen legible de la reserva."""
        return (
            f"{self.id}: {self.servicio.nombre} para {self.cliente.nombre_completo} "
            f"({self.estado.value}, {self.fecha_programada:%Y-%m-%d %H:%M})"
        )

    def a_diccionario(self) -> dict[str, object]:
        """Serializa la reserva para reportes en memoria."""
        return {
            "id": self.id,
            "cliente_id": self.cliente.id,
            "servicio_id": self.servicio.id,
            "servicio": self.servicio.nombre,
            "duracion_horas": self.duracion_horas,
            "fecha_programada": self.fecha_programada.isoformat(),
            "estado": self.estado.value,
            "costo_total": self.costo_total,
            "parametros_servicio": self.parametros_servicio,
        }
