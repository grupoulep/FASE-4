"""Fachada de operaciones del sistema en memoria."""

from datetime import datetime, timedelta

from software_fj.exceptions.errores import (
    EntidadNoEncontradaError,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    SoftwareFJError,
)
from software_fj.models.cliente import Cliente
from software_fj.models.reserva import EstadoReserva, Reserva
from software_fj.models.servicio import Servicio
from software_fj.models.servicios_especializados import AlquilerEquipo, ReservaSala
from software_fj.utils.logger import GestorLogs


class GestorSoftwareFJ:
    """Mantiene clientes, servicios y reservas en listas privadas."""

    def __init__(self, gestor_logs: GestorLogs | None = None) -> None:
        # Los datos del negocio viven únicamente en memoria durante la ejecución.
        self.__clientes: list[Cliente] = []
        self.__servicios: list[Servicio] = []
        self.__reservas: list[Reserva] = []
        self.__logs = gestor_logs or GestorLogs()

    @property
    def logs(self) -> GestorLogs:
        """Acceso al gestor de logs para integración de consola."""
        return self.__logs

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        """Valida e incorpora cliente evitando documentos duplicados."""
        try:
            # La validación y la búsqueda de duplicados ocurren antes de mutar la lista.
            if not isinstance(cliente, Cliente):
                raise TypeError("Se esperaba un objeto Cliente.")
            cliente.validar()
            if any(c.documento == cliente.documento for c in self.__clientes):
                raise OperacionNoPermitidaError(
                    "Ya existe un cliente con ese documento.", "DOCUMENTO_DUPLICADO"
                )
        except (SoftwareFJError, TypeError) as exc:
            self.__logs.registrar_error(exc, "registrar_cliente")
            raise
        else:
            # El bloque else solo se alcanza cuando el cliente pasó todas las reglas.
            self.__clientes.append(cliente)
            self.__logs.registrar_evento(
                "INFO", "registrar_cliente", "Cliente registrado.", cliente.id
            )
            return cliente

    def listar_clientes(self) -> list[Cliente]:
        """Devuelve una copia superficial de los clientes registrados."""
        return list(self.__clientes)

    def buscar_cliente(self, identificador: str) -> Cliente:
        """Busca un cliente por ID o documento."""
        encontrado = next(
            (
                c for c in self.__clientes
                if c.id == identificador or c.documento == identificador.upper()
            ),
            None,
        )
        if encontrado is None:
            raise EntidadNoEncontradaError(
                f"No se encontró cliente '{identificador}'.", "CLIENTE_NO_ENCONTRADO"
            )
        return encontrado

    def desactivar_cliente(self, identificador: str) -> None:
        """Desactiva un cliente que no tenga reservas activas."""
        cliente = self.buscar_cliente(identificador)
        # Las reservas pendientes o confirmadas impiden desactivar al cliente.
        activas = [
            r for r in self.__reservas
            if r.cliente == cliente
            and r.estado in {EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA}
        ]
        if activas:
            raise OperacionNoPermitidaError(
                "No se puede desactivar un cliente con reservas activas.",
                "CLIENTE_CON_RESERVAS",
            )
        cliente.desactivar()
        self.__logs.registrar_evento(
            "INFO", "desactivar_cliente", "Cliente desactivado.", cliente.id
        )

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        """Registra servicio con código único."""
        try:
            # Comprueba el tipo, la tarifa y que el código no esté repetido.
            if not isinstance(servicio, Servicio):
                raise TypeError("Se esperaba un objeto Servicio.")
            servicio.validar()
            if any(s.codigo == servicio.codigo for s in self.__servicios):
                raise OperacionNoPermitidaError(
                    "Ya existe un servicio con ese código.", "CODIGO_DUPLICADO"
                )
        except (SoftwareFJError, TypeError) as exc:
            self.__logs.registrar_error(exc, "registrar_servicio")
            raise
        else:
            self.__servicios.append(servicio)
            self.__logs.registrar_evento(
                "INFO", "registrar_servicio", "Servicio registrado.", servicio.codigo
            )
            return servicio

    def listar_servicios(self, tipo: type[Servicio] | None = None) -> list[Servicio]:
        """Devuelve servicios, opcionalmente filtrados por subtipo."""
        return [
            servicio for servicio in self.__servicios
            if tipo is None or isinstance(servicio, tipo)
        ]

    def cambiar_disponibilidad(self, identificador: str, disponible: bool) -> None:
        """Actualiza disponibilidad de un servicio por ID o código."""
        servicio = self.buscar_servicio(identificador)
        servicio.disponible = disponible
        self.__logs.registrar_evento(
            "INFO", "cambiar_disponibilidad",
            f"Disponibilidad establecida en {disponible}.", servicio.codigo,
        )

    def buscar_servicio(self, identificador: str) -> Servicio:
        """Busca un servicio por ID o código."""
        encontrado = next(
            (
                s for s in self.__servicios
                if s.id == identificador or s.codigo == identificador
            ),
            None,
        )
        if encontrado is None:
            raise EntidadNoEncontradaError(
                f"No se encontró servicio '{identificador}'.", "SERVICIO_NO_ENCONTRADO"
            )
        return encontrado

    def crear_reserva(
        self, cliente: Cliente | str, servicio: Servicio | str,
        duracion_horas: float, fecha_programada: datetime,
        parametros_servicio: dict[str, object] | None = None,
    ) -> Reserva:
        """Crea reserva validando referencias y evitando colisión de sala."""
        try:
            # Se permiten referencias directas o búsquedas por ID/documento/código.
            cliente_obj = (
                self.buscar_cliente(cliente) if isinstance(cliente, str) else cliente
            )
            servicio_obj = (
                self.buscar_servicio(servicio)
                if isinstance(servicio, str)
                else servicio
            )
            if (
                cliente_obj not in self.__clientes
                or servicio_obj not in self.__servicios
            ):
                raise EntidadNoEncontradaError(
                    "El cliente o servicio no está registrado.", "ENTIDAD_NO_REGISTRADA"
                )
            reserva = Reserva(
                cliente_obj, servicio_obj, duracion_horas,
                fecha_programada, parametros_servicio,
            )
            if isinstance(servicio_obj, ReservaSala):
                # La colisión se revisa antes de guardar una reserva de sala.
                if self._hay_colision(reserva):
                    raise ReservaInvalidaError(
                        "La sala ya está reservada en ese horario.",
                        "COLISION_HORARIA",
                    )
        except (SoftwareFJError, TypeError, ValueError) as exc:
            self.__logs.registrar_error(exc, "crear_reserva")
            if isinstance(exc, ReservaInvalidaError):
                raise
            raise ReservaInvalidaError(
                "No fue posible crear la reserva.",
                "ERROR_CREACION_RESERVA",
                str(exc),
            ) from exc
        else:
            # Solo se agrega y anuncia la reserva después de completar las reglas.
            self.__reservas.append(reserva)
            self.__logs.registrar_evento(
                "INFO", "crear_reserva", "Reserva creada.", reserva.id
            )
            return reserva

    def _hay_colision(self, propuesta: Reserva) -> bool:
        """Detecta intervalos de reserva superpuestos para la misma sala."""
        inicio = propuesta.fecha_programada
        fin = inicio + timedelta(hours=propuesta.duracion_horas)
        for existente in self.__reservas:
            if existente.servicio != propuesta.servicio or existente.estado not in {
                EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA
            }:
                continue
            otro_inicio = existente.fecha_programada
            otro_fin = otro_inicio + timedelta(hours=existente.duracion_horas)
            if inicio < otro_fin and otro_inicio < fin:
                return True
        return False

    def registrar_reserva(self, reserva: Reserva) -> Reserva:
        """Agrega una reserva previamente creada."""
        if reserva in self.__reservas:
            raise OperacionNoPermitidaError(
                "La reserva ya fue agregada.", "RESERVA_DUPLICADA"
            )
        self.__reservas.append(reserva)
        self.__logs.registrar_evento(
            "INFO", "registrar_reserva", "Reserva creada.", reserva.id
        )
        return reserva

    def confirmar_reserva(self, identificador: str) -> Reserva:
        """Confirma una reserva y registra el resultado."""
        reserva = self.buscar_reserva(identificador)
        try:
            # Se vuelve a comprobar el horario al confirmar, por si hubo cambios
            # después de que se creó la reserva.
            if (
                isinstance(reserva.servicio, ReservaSala)
                and self._hay_colision_excluyendo(reserva)
            ):
                raise ReservaInvalidaError(
                    "La sala ya está reservada en ese horario.", "COLISION_HORARIA"
                )
            reserva.confirmar()
        except SoftwareFJError as exc:
            self.__logs.registrar_error(exc, "confirmar_reserva")
            raise
        else:
            self.__logs.registrar_evento(
                "INFO", "confirmar_reserva", "Reserva confirmada.", reserva.id
            )
            return reserva

    def _hay_colision_excluyendo(self, propuesta: Reserva) -> bool:
        """Comprueba colisiones sin comparar la propuesta consigo misma."""
        inicio = propuesta.fecha_programada
        fin = inicio + timedelta(hours=propuesta.duracion_horas)
        for existente in self.__reservas:
            if existente == propuesta or existente.servicio != propuesta.servicio:
                continue
            if existente.estado not in {
                EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA
            }:
                continue
            otro_inicio = existente.fecha_programada
            otro_fin = otro_inicio + timedelta(hours=existente.duracion_horas)
            if inicio < otro_fin and otro_inicio < fin:
                return True
        return False

    def procesar_reserva(
        self, identificador: str, tasa_impuesto: float = 0.19,
        descuento_porcentaje: float = 0.0, recargo_adicional: float = 0.0,
    ) -> float:
        """Procesa una reserva y registra auditoría aun si falla."""
        reserva = self.buscar_reserva(identificador)
        try:
            # Captura errores de dominio; finally registra el cierre del intento.
            total = reserva.procesar(
                tasa_impuesto, descuento_porcentaje, recargo_adicional
            )
        except SoftwareFJError as exc:
            self.__logs.registrar_error(exc, "procesar_reserva")
            raise
        else:
            self.__logs.registrar_evento(
                "INFO", "procesar_reserva", "Reserva procesada.", reserva.id
            )
            return total
        finally:
            self.__logs.registrar_evento(
                "INFO", "procesar_reserva",
                "Fin de intento de procesamiento.", reserva.id,
            )

    def cancelar_reserva(self, identificador: str, motivo: str) -> None:
        """Cancela una reserva e informa de fallos de dominio."""
        reserva = self.buscar_reserva(identificador)
        try:
            reserva.cancelar(motivo)
        except SoftwareFJError as exc:
            self.__logs.registrar_error(exc, "cancelar_reserva")
            raise
        else:
            self.__logs.registrar_evento(
                "INFO", "cancelar_reserva", "Reserva cancelada.", reserva.id
            )

    def buscar_reserva(self, identificador: str) -> Reserva:
        """Busca una reserva por su identificador único."""
        encontrado = next(
            (r for r in self.__reservas if r.id == identificador), None
        )
        if encontrado is None:
            raise EntidadNoEncontradaError(
                f"No se encontró reserva '{identificador}'.", "RESERVA_NO_ENCONTRADA"
            )
        return encontrado

    def listar_reservas(
        self, cliente_id: str | None = None,
        estado: EstadoReserva | None = None,
    ) -> list[Reserva]:
        """Filtra reservas por cliente y/o estado."""
        return [
            r for r in self.__reservas
            if (cliente_id is None or r.cliente.id == cliente_id)
            and (estado is None or r.estado is estado)
        ]

    def resumen_ejecutivo(self) -> dict[str, object]:
        """Genera estadísticas sin escribir datos de negocio a disco."""
        # Cuenta estados e ingresos solamente desde reservas procesadas.
        por_estado = {
            estado.value: sum(r.estado is estado for r in self.__reservas)
            for estado in EstadoReserva
        }
        ingresos = sum(
            r.costo_total or 0.0 for r in self.__reservas
            if r.estado is EstadoReserva.PROCESADA
        )
        return {
            "total_clientes": len(self.__clientes),
            "clientes_activos": sum(c.activa for c in self.__clientes),
            "servicios_disponibles": sum(
                s.disponible and s.activa for s in self.__servicios
            ),
            "total_servicios": len(self.__servicios),
            "reservas_por_estado": por_estado,
            "ingresos_acumulados": round(ingresos, 2),
        }

    def listar_descripciones_servicios(self) -> list[str]:
        """Presenta catálogo mediante despacho polimórfico."""
        # Cada instancia decide su propia descripción según su tipo concreto.
        return [s.describir_servicio() for s in self.__servicios]
