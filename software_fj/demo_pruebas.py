"""Demostración funcional y de resiliencia del sistema.

Creadores:
    Jerson Stiven Lopez Rengifo
    Didier Yohan Salazar Miranda
"""

from datetime import datetime, timedelta
from typing import Callable

from software_fj.core.gestor_sistema import GestorSoftwareFJ
from software_fj.exceptions.errores import (
    CalculoInconsistenteError,
    DatosInvalidosError,
    OperacionNoPermitidaError,
    ParametroFaltanteError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from software_fj.models.cliente import Cliente
from software_fj.models.reserva import EstadoReserva
from software_fj.models.servicio import Servicio
from software_fj.models.servicios_especializados import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    ReservaSala,
)


def _datos_demo() -> tuple[GestorSoftwareFJ, list[Cliente], list[Servicio]]:
    """Construye el catálogo mínimo usado por la demostración."""
    # Crea dos clientes y seis servicios que cubren las tres líneas de negocio.
    gestor = GestorSoftwareFJ()
    clientes = [
        Cliente("Jerson Lopez", "CC1001", "jerson@example.com", "+573001112233"),
        Cliente(
            "Didier Miranda", "NIT2002", "didier@example.com", "+573004445566",
            "FJ Labs", "CORPORATIVO",
        ),
    ]
    for cliente in clientes:
        gestor.registrar_cliente(cliente)
    servicios: list[Servicio] = [
        ReservaSala(
            "SALA1", "Sala Norte", "Junta ejecutiva", 120000,
            12, "Piso 2", True, 35000,
        ),
        ReservaSala(
            "SALA2", "Auditorio", "Eventos", 250000,
            80, "Piso 1", True, 80000,
        ),
        AlquilerEquipo(
            "EQ1", "Portátil", "Equipo portátil", 25000,
            "Portátil", "FJ Pro 14", 8, 100000, 2500,
        ),
        AlquilerEquipo(
            "EQ2", "Proyector", "Proyección HD", 40000,
            "Proyector", "Beam 4K", 4, 60000, 4000,
        ),
        AsesoriaEspecializada(
            "AS1", "Arquitectura", "Diseño de sistemas", 180000,
            "Arquitectura de software", "Jerson Lopez", "ARQUITECTO", "REMOTA",
        ),
        AsesoriaEspecializada(
            "AS2", "Ciberseguridad", "Evaluación preventiva", 150000,
            "Ciberseguridad", "Didier Miranda", "SENIOR", "PRESENCIAL", False, 50000,
        ),
    ]
    for servicio in servicios:
        gestor.registrar_servicio(servicio)
    return gestor, clientes, servicios


def _esperar_error(
    etiqueta: str, accion: Callable[[], object], esperado: type[SoftwareFJError],
    gestor: GestorSoftwareFJ,
) -> int:
    """Ejecuta un escenario y registra el resultado sin detener la demo."""
    try:
        # Cada caso debe producir la excepción indicada para contar como aprobado.
        accion()
    except esperado as exc:
        gestor.logs.registrar_error(exc, f"demo/{etiqueta}")
        print(f"[OK] {etiqueta}: {type(exc).__name__} (capturado y registrado)")
        return 1
    except Exception as exc:
        gestor.logs.registrar_error(exc, f"demo/{etiqueta}/inesperado")
        print(f"[FALLO] {etiqueta}: ocurrió {type(exc).__name__}: {exc}")
        return 0
    print(f"[FALLO] {etiqueta}: no se produjo la excepción esperada.")
    return 0


def ejecutar_demo() -> int:
    """Ejecuta flujos de negocio y más de diez escenarios de error."""
    gestor, clientes, servicios = _datos_demo()
    sala, equipo, asesoria = servicios[0], servicios[2], servicios[4]
    assert isinstance(sala, ReservaSala)
    assert isinstance(equipo, AlquilerEquipo)
    # Invoca métodos polimórficos sobre una lista heterogénea de servicios.
    print("=== Catálogo polimórfico ===")
    for servicio in servicios:
        print(
            f"- {servicio.describir_servicio()} | "
            f"cotización base: ${servicio.calcular_costo(1):,.2f}"
        )

    # Muestra cuatro firmas de cálculo en un mismo servicio de salas.
    print("\n=== Variantes de cálculo ===")
    variantes = (
        ("base", {}),
        ("impuesto", {"tasa_impuesto": 0.19}),
        ("impuesto y descuento", {"tasa_impuesto": 0.19, "descuento_porcentaje": 5}),
        (
            "integral",
            {
                "tasa_impuesto": 0.19,
                "descuento_porcentaje": 5,
                "descuento_fijo": 1000,
                "recargo_adicional": 2000,
                "asistentes": 6,
                "requiere_audiovisual": True,
            },
        ),
    )
    for etiqueta, opciones in variantes:
        print(f"{etiqueta}: ${sala.calcular_costo(2, **opciones):,.2f}")

    ahora = datetime.now() + timedelta(days=1)
    # Comprueba el flujo de alquiler exitoso y la disminución de inventario.
    reserva_ok = gestor.crear_reserva(
        clientes[0], equipo, 3, ahora, {"cantidad": 2, "incluir_seguro": True}
    )
    gestor.confirmar_reserva(reserva_ok.id)
    print(f"\nStock tras confirmar alquiler: {equipo.stock_disponible}")
    assert equipo.stock_disponible == 6
    total = gestor.procesar_reserva(reserva_ok.id)
    print(f"Reserva procesada: ${total:,.2f}")

    # Comprueba que cancelar devuelve al inventario las unidades alquiladas.
    reserva_cancelable = gestor.crear_reserva(
        clientes[1], equipo, 2, ahora + timedelta(days=2),
        {"cantidad": 1, "incluir_seguro": False},
    )
    gestor.confirmar_reserva(reserva_cancelable.id)
    gestor.cancelar_reserva(reserva_cancelable.id, "Cambio de agenda")
    assert equipo.stock_disponible == 6
    print(f"Stock tras cancelar alquiler: {equipo.stock_disponible}")

    # Se preparan reservas inválidas que se probarán en la batería de errores.
    reserva_sin_motivo = gestor.crear_reserva(
        clientes[0], sala, 1, ahora + timedelta(days=4), {"asistentes": 2}
    )
    reserva_aforo = gestor.crear_reserva(
        clientes[0], sala, 1, ahora + timedelta(days=5), {"asistentes": 13}
    )
    fallos = [
        (
            "correo mal formado",
            lambda: Cliente("Jerson Lopez", "AA11", "correo", "1234567"),
            DatosInvalidosError,
        ),
        (
            "duración negativa",
            lambda: gestor.crear_reserva(
                clientes[0], sala, -1, ahora, {"asistentes": 2}
            ),
            ReservaInvalidaError,
        ),
        (
            "texto en duración",
            lambda: gestor.crear_reserva(
                clientes[0], sala, "dos", ahora, {"asistentes": 2}
            ),
            ReservaInvalidaError,
        ),
        (
            "parámetro obligatorio vacío",
            lambda: Cliente("", "CC88", "x@example.com", "1234567"),
            ParametroFaltanteError,
        ),
        (
            "documento duplicado",
            lambda: gestor.registrar_cliente(
                Cliente("Didier Miranda", "CC1001", "otro@example.com", "12345678")
            ),
            OperacionNoPermitidaError,
        ),
        (
            "procesar sin confirmar",
            lambda: gestor.procesar_reserva(reserva_cancelable.id),
            ReservaInvalidaError,
        ),
        (
            "cancelar procesada",
            lambda: gestor.cancelar_reserva(reserva_ok.id, "No procede"),
            OperacionNoPermitidaError,
        ),
        (
            "motivo ausente",
            lambda: gestor.cancelar_reserva(reserva_sin_motivo.id, ""),
            ParametroFaltanteError,
        ),
        (
            "desactivar cliente con reserva activa",
            lambda: gestor.desactivar_cliente(clientes[0].id),
            OperacionNoPermitidaError,
        ),
        (
            "exceso de aforo",
            lambda: reserva_aforo.confirmar(),
            ServicioNoDisponibleError,
        ),
        (
            "stock insuficiente",
            lambda: equipo.validar_parametros(
                cantidad=999, incluir_seguro=False
            ),
            ServicioNoDisponibleError,
        ),
        (
            "descuento superior al 100%",
            lambda: sala.calcular_costo(
                1, descuento_porcentaje=101, asistentes=1
            ),
            CalculoInconsistenteError,
        ),
        (
            "impuesto negativo",
            lambda: sala.calcular_costo(
                1, tasa_impuesto=-0.1, asistentes=1
            ),
            CalculoInconsistenteError,
        ),
        (
            "descuento fijo excesivo",
            lambda: sala.calcular_costo(
                1, descuento_fijo=999999, asistentes=1
            ),
            CalculoInconsistenteError,
        ),
        (
            "confirmar reserva cancelada",
            lambda: reserva_cancelable.confirmar(),
            ReservaInvalidaError,
        ),
    ]
    # Continúa con el siguiente caso aunque uno de ellos falle inesperadamente.
    exitos = sum(
        _esperar_error(nombre, accion, esperado, gestor)
        for nombre, accion, esperado in fallos
    )
    if reserva_ok.estado is not EstadoReserva.PROCESADA:
        raise AssertionError("El flujo de procesamiento no finalizó correctamente.")
    # Presenta el resultado agregado de las pruebas y las métricas de negocio.
    print(f"\nEscenarios de error capturados: {exitos}/{len(fallos)}")
    print(f"Resumen: {gestor.resumen_ejecutivo()}")
    return exitos


if __name__ == "__main__":
    ejecutar_demo()
