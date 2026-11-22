"""Interfaz de consola tolerante a errores para Software FJ."""

from datetime import datetime
from typing import Callable

from software_fj.core.gestor_sistema import GestorSoftwareFJ
from software_fj.demo_pruebas import ejecutar_demo
from software_fj.exceptions.errores import SoftwareFJError
from software_fj.models.cliente import Cliente
from software_fj.models.reserva import EstadoReserva
from software_fj.models.servicio import Servicio
from software_fj.models.servicios_especializados import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    ReservaSala,
)


class ConsolaSoftwareFJ:
    """Coordina menús, entradas y manejo centralizado de errores."""

    def __init__(self) -> None:
        # La consola conserva una sola instancia de la fachada durante la sesión.
        self.gestor = GestorSoftwareFJ()
        self._activo = True

    @staticmethod
    def _entrada(mensaje: str) -> str:
        return input(mensaje).strip()

    def _entero(self, mensaje: str, minimo: int = 0) -> int:
        valor = self._entrada(mensaje)
        numero = int(valor)
        if numero < minimo:
            raise ValueError(f"El valor debe ser al menos {minimo}.")
        return numero

    def _ejecutar_seguro(self, accion: Callable[[], object]) -> None:
        """Aísla cada operación para que errores recuperables no cierren el menú."""
        try:
            # Cada submenú queda aislado; los errores se muestran y se registran.
            accion()
        except KeyboardInterrupt:
            self.gestor.logs.registrar_advertencia(
                "consola", "Operación interrumpida por el usuario."
            )
            print("\nOperación interrumpida; regresando al menú.")
        except (SoftwareFJError, ValueError, TypeError, OSError) as exc:
            try:
                self.gestor.logs.registrar_error(exc, "consola")
            except SoftwareFJError as error_log:
                print(f"No se pudo escribir el log: {error_log}")
            print(f"Error: {exc}")
        except Exception as exc:
            try:
                self.gestor.logs.registrar_error(exc, "consola/error_inesperado")
            except SoftwareFJError as error_log:
                print(f"No se pudo escribir el log: {error_log}")
            print(f"Error inesperado; la aplicación continúa: {exc}")

    def ejecutar(self) -> None:
        """Mantiene activo el menú hasta solicitar una salida segura."""
        print("Software FJ - Gestión de servicios corporativos")
        while self._activo:
            try:
                # Cada opción del menú apunta a una acción independiente.
                print(
                    "\n1. Clientes\n2. Servicios\n3. Reservas\n4. Reporte general"
                    "\n5. Últimos logs\n6. Demostración y pruebas\n7. Salir"
                )
                opcion = self._entrada("Opción: ")
                acciones: dict[str, Callable[[], object]] = {
                    "1": self._menu_clientes,
                    "2": self._menu_servicios,
                    "3": self._menu_reservas,
                    "4": self._reporte,
                    "5": self._mostrar_logs,
                    "6": ejecutar_demo,
                    "7": self._salir,
                }
                accion = acciones.get(opcion)
                if accion is None:
                    print("Seleccione una opción entre 1 y 7.")
                    continue
                self._ejecutar_seguro(accion)
            except KeyboardInterrupt:
                print("\nUse la opción 7 para salir de forma segura.")

    def _menu_clientes(self) -> None:
        # Este submenú concentra el alta, consulta y desactivación de clientes.
        print("\nClientes: 1 Registrar | 2 Listar | 3 Buscar | 4 Desactivar")
        opcion = self._entrada("Opción: ")
        if opcion == "1":
            cliente = Cliente(
                self._entrada("Nombre completo: "),
                self._entrada("Documento: "),
                self._entrada("Correo: "),
                self._entrada("Teléfono: "),
                self._entrada("Empresa (opcional): ") or None,
                self._entrada("Categoría [ESTANDAR/CORPORATIVO/VIP] (ESTANDAR): ")
                or "ESTANDAR",
            )
            self.gestor.registrar_cliente(cliente)
            print(f"Registrado: {cliente}")
        elif opcion == "2":
            for cliente in self.gestor.listar_clientes():
                print(f"- {cliente.obtener_resumen()}")
        elif opcion == "3":
            print(self.gestor.buscar_cliente(self._entrada("ID o documento: ")))
        elif opcion == "4":
            self.gestor.desactivar_cliente(self._entrada("ID o documento: "))
            print("Cliente desactivado.")
        else:
            print("Opción de clientes no válida.")

    def _menu_servicios(self) -> None:
        # El tipo elegido determina qué clase de servicio se instancia.
        print(
            "\nServicios: 1 Registrar sala | 2 Registrar equipo | "
            "3 Registrar asesoría"
        )
        print("4 Listar catálogo | 5 Cambiar disponibilidad")
        opcion = self._entrada("Opción: ")
        if opcion == "4":
            # Usa el método polimórfico de cada servicio para mostrar el catálogo.
            for descripcion in self.gestor.listar_descripciones_servicios():
                print(f"- {descripcion}")
            return
        if opcion == "5":
            codigo = self._entrada("ID o código: ")
            disponible = self._entrada("Disponible (s/n): ").lower() == "s"
            self.gestor.cambiar_disponibilidad(codigo, disponible)
            return

        codigo = self._entrada("Código: ")
        nombre = self._entrada("Nombre: ")
        descripcion = self._entrada("Descripción: ")
        tarifa = float(self._entrada("Tarifa base por hora: "))
        if opcion == "1":
            servicio: Servicio = ReservaSala(
                codigo, nombre, descripcion, tarifa,
                self._entero("Aforo máximo: ", 1),
                self._entrada("Ubicación: "),
                self._entrada("¿Tiene audiovisual? (s/n): ").lower() == "s",
                float(self._entrada("Tarifa audiovisual: ") or "0"),
            )
        elif opcion == "2":
            servicio = AlquilerEquipo(
                codigo, nombre, descripcion, tarifa,
                self._entrada("Tipo de equipo: "),
                self._entrada("Marca/modelo: "),
                self._entero("Stock total: ", 1),
                float(self._entrada("Depósito de garantía: ") or "0"),
                float(self._entrada("Seguro por hora: ") or "0"),
            )
        elif opcion == "3":
            servicio = AsesoriaEspecializada(
                codigo, nombre, descripcion, tarifa,
                self._entrada("Especialidad: "),
                self._entrada("Consultor: "),
                self._entrada("Senioridad [JUNIOR/SENIOR/ARQUITECTO]: "),
                self._entrada("Modalidad [REMOTA/PRESENCIAL]: "),
                self._entrada("¿Solo remota? (s/n): ").lower() == "s",
                float(self._entrada("Cargo por desplazamiento: ") or "0"),
            )
        else:
            print("Opción de servicios no válida.")
            return
        self.gestor.registrar_servicio(servicio)
        print(f"Servicio registrado: {servicio.describir_servicio()}")

    def _menu_reservas(self) -> None:
        # Recopila datos generales y parámetros propios del tipo de servicio.
        print(
            "\nReservas: 1 Crear/cotizar | 2 Listar | 3 Confirmar"
            " | 4 Procesar | 5 Cancelar"
        )
        opcion = self._entrada("Opción: ")
        if opcion == "1":
            clientes = self.gestor.listar_clientes()
            servicios = self.gestor.listar_servicios()
            if not clientes or not servicios:
                print("Registre al menos un cliente y un servicio primero.")
                return
            for i, cliente in enumerate(clientes, 1):
                print(f"C{i}. {cliente.obtener_resumen()}")
            cliente = clientes[self._entero("Cliente #: ", 1) - 1]
            for i, servicio in enumerate(servicios, 1):
                print(f"S{i}. {servicio.describir_servicio()}")
            servicio = servicios[self._entero("Servicio #: ", 1) - 1]
            duracion = float(self._entrada("Duración en horas: "))
            fecha = datetime.strptime(
                self._entrada("Fecha/hora (AAAA-MM-DD HH:MM): "),
                "%Y-%m-%d %H:%M",
            )
            parametros: dict[str, object]
            # Cada subtipo necesita datos diferentes para validar una reserva.
            if isinstance(servicio, ReservaSala):
                parametros = {
                    "asistentes": self._entero("Asistentes: ", 1),
                    "requiere_audiovisual":
                        self._entrada("¿Requiere audiovisual? (s/n): ").lower() == "s",
                }
            elif isinstance(servicio, AlquilerEquipo):
                parametros = {
                    "cantidad": self._entero("Unidades: ", 1),
                    "incluir_seguro":
                        self._entrada("¿Incluir seguro? (s/n): ").lower() == "s",
                }
            elif isinstance(servicio, AsesoriaEspecializada):
                parametros = {
                    "es_urgente": self._entrada("¿Urgente? (s/n): ").lower() == "s",
                    "modalidad_solicitada":
                        self._entrada("Modalidad solicitada [REMOTA/PRESENCIAL]: ")
                        or servicio.modalidad,
                }
            else:
                parametros = {}
            reserva = self.gestor.crear_reserva(
                cliente, servicio, duracion, fecha, parametros
            )
            print(f"Reserva {reserva.id} creada.")
            print(f"Cotización sin impuesto: ${reserva.calcular_presupuesto():,.2f}")
            self.gestor.confirmar_reserva(reserva.id)
            print("Reserva confirmada.")
        elif opcion == "2":
            for reserva in self.gestor.listar_reservas():
                print(f"- {reserva.obtener_resumen()}")
        elif opcion == "3":
            self.gestor.confirmar_reserva(self._entrada("ID de reserva: "))
            print("Reserva confirmada.")
        elif opcion == "4":
            total = self.gestor.procesar_reserva(
                self._entrada("ID de reserva: ")
            )
            print(f"Total liquidado: ${total:,.2f}")
        elif opcion == "5":
            self.gestor.cancelar_reserva(
                self._entrada("ID de reserva: "),
                self._entrada("Motivo de cancelación: "),
            )
            print("Reserva cancelada.")
        else:
            print("Opción de reservas no válida.")

    def _reporte(self) -> None:
        # Muestra métricas calculadas en memoria por la fachada del sistema.
        print(self.gestor.resumen_ejecutivo())

    def _mostrar_logs(self) -> None:
        # El acceso a disco de la aplicación se limita a consultar el archivo de log.
        for linea in self.gestor.logs.leer_ultimos_logs(20):
            print(linea.rstrip())

    def _salir(self) -> None:
        # Registra el cierre antes de terminar el bucle principal.
        self.gestor.logs.registrar_evento(
            "INFO", "consola", "Cierre solicitado por el usuario."
        )
        self._activo = False
        print("Sesión finalizada.")


def main() -> None:
    """Punto de entrada protegido de la aplicación."""
    # Construye la interfaz y entrega el control al ciclo del menú.
    ConsolaSoftwareFJ().ejecutar()


if __name__ == "__main__":
    # Evita iniciar la consola cuando este módulo se importa desde otro archivo.
    main()
