"""Implementaciones polimórficas de las líneas de servicio."""

from software_fj.exceptions.errores import (
    DatosInvalidosError,
    OperacionNoPermitidaError,
    ServicioNoDisponibleError,
)
from software_fj.models.servicio import Servicio
from software_fj.utils.validadores import booleano, entero, numero, texto


class ReservaSala(Servicio):
    """Reserva de espacios con aforo y paquete audiovisual."""

    def __init__(
        self, codigo: str, nombre: str, descripcion: str, tarifa_base: float,
        capacidad_maxima: int, ubicacion: str, tiene_audiovisual: bool = False,
        tarifa_audiovisual: float = 0.0,
    ) -> None:
        super().__init__(codigo, nombre, descripcion, tarifa_base)
        # Aforo, ubicación y equipo propio determinan disponibilidad y costo.
        self.__capacidad_maxima = entero(capacidad_maxima, "capacidad máxima", 1)
        self.__ubicacion = texto(ubicacion, "ubicación")
        self.__tiene_audiovisual = booleano(tiene_audiovisual, "tiene audiovisual")
        self.__tarifa_audiovisual = numero(tarifa_audiovisual, "tarifa audiovisual", 0)

    @property
    def capacidad_maxima(self) -> int:
        """Devuelve el aforo permitido."""
        return self.__capacidad_maxima

    @property
    def ubicacion(self) -> str:
        """Devuelve la ubicación física de la sala."""
        return self.__ubicacion

    @property
    def tiene_audiovisual(self) -> bool:
        """Indica si la sala incluye equipo audiovisual."""
        return self.__tiene_audiovisual

    @property
    def tarifa_audiovisual(self) -> float:
        """Devuelve el cargo por el paquete audiovisual."""
        return self.__tarifa_audiovisual

    def validar_parametros(self, **kwargs: object) -> bool:
        """Valida aforo y disponibilidad audiovisual."""
        asistentes = entero(kwargs.get("asistentes"), "asistentes", 1)
        if asistentes > self.capacidad_maxima:
            raise ServicioNoDisponibleError(
                "La cantidad de asistentes supera el aforo.", "AFORO_EXCEDIDO"
            )
        requiere = kwargs.get("requiere_audiovisual", False)
        booleano(requiere, "requiere_audiovisual")
        if requiere and not self.tiene_audiovisual:
            raise ServicioNoDisponibleError(
                "La sala no dispone de equipo audiovisual.", "AUDIOVISUAL_NO_DISPONIBLE"
            )
        return True

    def describir_servicio(self) -> str:
        """Describe capacidad, ubicación y equipamiento."""
        equipo = "audiovisual" if self.tiene_audiovisual else "sin audiovisual"
        return (
            f"Sala {self.nombre}: aforo {self.capacidad_maxima}, {self.ubicacion}, "
            f"{equipo}; ${self.tarifa_base:.2f}/hora"
        )

    def calcular_costo_base(self, duracion: float, **kwargs: object) -> float:
        """Calcula tarifa, audiovisual y recargo por alta ocupación."""
        # En una cotización genérica se asume una persona y sin equipo adicional.
        kwargs.setdefault("asistentes", 1)
        kwargs.setdefault("requiere_audiovisual", False)
        self.validar_parametros(**kwargs)
        costo = self.tarifa_base * duracion
        # Añade el paquete opcional y el recargo logístico al superar 80% del aforo.
        if kwargs.get("requiere_audiovisual", False):
            costo += self.tarifa_audiovisual
        asistentes = int(kwargs["asistentes"])
        if asistentes > self.capacidad_maxima * 0.8:
            costo *= 1.15
        return costo


class AlquilerEquipo(Servicio):
    """Alquiler con inventario interno y opciones de seguro."""

    def __init__(
        self, codigo: str, nombre: str, descripcion: str, tarifa_base: float,
        tipo_equipo: str, marca_modelo: str, stock_total: int,
        deposito_garantia: float = 0.0, tarifa_seguro_hora: float = 0.0,
    ) -> None:
        super().__init__(codigo, nombre, descripcion, tarifa_base)
        # El inventario comienza completamente disponible y cambia al confirmar
        # o cancelar reservas.
        self.__tipo_equipo = texto(tipo_equipo, "tipo de equipo")
        self.__marca_modelo = texto(marca_modelo, "marca/modelo")
        self.__stock_total = entero(stock_total, "stock total", 1)
        self.__stock_disponible = self.__stock_total
        self.__deposito_garantia = numero(deposito_garantia, "depósito", 0)
        self.__tarifa_seguro_hora = numero(tarifa_seguro_hora, "tarifa de seguro", 0)

    @property
    def tipo_equipo(self) -> str:
        """Devuelve la clase de equipo."""
        return self.__tipo_equipo

    @property
    def marca_modelo(self) -> str:
        """Devuelve marca y modelo del equipo."""
        return self.__marca_modelo

    @property
    def stock_total(self) -> int:
        """Devuelve la cantidad total registrada."""
        return self.__stock_total

    @property
    def stock_disponible(self) -> int:
        """Devuelve las unidades disponibles para reservar."""
        return self.__stock_disponible

    @property
    def deposito_garantia(self) -> float:
        """Devuelve el depósito por unidad."""
        return self.__deposito_garantia

    @property
    def tarifa_seguro_hora(self) -> float:
        """Devuelve el cargo del seguro por unidad y hora."""
        return self.__tarifa_seguro_hora

    def reservar_unidades(self, cantidad: int) -> None:
        """Retira unidades disponibles de manera atómica."""
        unidades = entero(cantidad, "cantidad", 1)
        # Se comprueba el stock antes de modificarlo para no dejar cantidades negativas.
        if unidades > self.stock_disponible:
            raise ServicioNoDisponibleError(
                "No hay unidades suficientes en inventario.", "STOCK_INSUFICIENTE"
            )
        self.__stock_disponible -= unidades

    def liberar_unidades(self, cantidad: int) -> None:
        """Devuelve unidades sin superar el stock total."""
        unidades = entero(cantidad, "cantidad", 1)
        # Evita devolver unidades más de una vez y exceder el total del inventario.
        if self.stock_disponible + unidades > self.stock_total:
            raise ServicioNoDisponibleError(
                "La liberación excedería el inventario total.", "STOCK_INCONSISTENTE"
            )
        self.__stock_disponible += unidades

    def validar_parametros(self, **kwargs: object) -> bool:
        """Valida cantidad de unidades y opción de seguro."""
        cantidad = entero(kwargs.get("cantidad"), "cantidad", 1)
        if cantidad > self.stock_disponible:
            raise ServicioNoDisponibleError(
                "No hay unidades suficientes en inventario.", "STOCK_INSUFICIENTE"
            )
        booleano(kwargs.get("incluir_seguro", False), "incluir_seguro")
        return True

    def describir_servicio(self) -> str:
        """Describe el equipo y la disponibilidad del inventario."""
        return (
            f"Equipo {self.tipo_equipo} {self.marca_modelo}: "
            f"{self.stock_disponible}/{self.stock_total} disponibles; "
            f"${self.tarifa_base:.2f}/hora"
        )

    def calcular_costo_base(self, duracion: float, **kwargs: object) -> float:
        """Calcula renta, seguro y depósito con descuento prolongado."""
        # Los valores por defecto sirven para cotizar; al confirmar se exigen
        # los parámetros específicos de este alquiler.
        kwargs.setdefault("cantidad", 1)
        kwargs.setdefault("incluir_seguro", False)
        self.validar_parametros(**kwargs)
        cantidad = int(kwargs["cantidad"])
        costo = self.tarifa_base * duracion * cantidad
        if kwargs.get("incluir_seguro", False):
            costo += self.tarifa_seguro_hora * duracion * cantidad
        costo += self.deposito_garantia * cantidad
        # Los alquileres de ocho horas o más reciben un descuento automático del 10%.
        if duracion >= 8:
            costo *= 0.9
        return costo


class AsesoriaEspecializada(Servicio):
    """Asesoría con modalidad, seniority y recargo urgente."""

    # Multiplicador por experiencia del consultor; se usa en el cálculo base.
    _MULTIPLICADORES = {"JUNIOR": 1.0, "SENIOR": 1.35, "ARQUITECTO": 1.75}

    def __init__(
        self, codigo: str, nombre: str, descripcion: str, tarifa_base: float,
        especialidad: str, consultor_asignado: str, nivel_senioridad: str,
        modalidad: str, solo_remota: bool = False, cargo_desplazamiento: float = 0.0,
    ) -> None:
        super().__init__(codigo, nombre, descripcion, tarifa_base)
        # Normaliza y valida los valores enumerados de nivel y modalidad.
        self.__especialidad = texto(especialidad, "especialidad")
        self.__consultor_asignado = texto(consultor_asignado, "consultor")
        self.__nivel_senioridad = self._opcion(
            nivel_senioridad, self._MULTIPLICADORES, "seniority"
        )
        self.__modalidad = self._opcion(
            modalidad, {"REMOTA": 1, "PRESENCIAL": 1}, "modalidad"
        )
        self.__solo_remota = solo_remota
        booleano(solo_remota, "solo_remota")
        self.__cargo_desplazamiento = numero(
            cargo_desplazamiento, "cargo desplazamiento", 0
        )

    @staticmethod
    def _opcion(valor: object, opciones: dict[str, object], nombre: str) -> str:
        resultado = texto(valor, nombre).upper()
        if resultado not in opciones:
            raise DatosInvalidosError(f"{nombre} no válido.", "OPCION_INVALIDA")
        return resultado

    @property
    def especialidad(self) -> str:
        """Devuelve la especialidad de consultoría."""
        return self.__especialidad

    @property
    def consultor_asignado(self) -> str:
        """Devuelve el nombre del consultor."""
        return self.__consultor_asignado

    @property
    def nivel_senioridad(self) -> str:
        """Devuelve el nivel de seniority."""
        return self.__nivel_senioridad

    @property
    def modalidad(self) -> str:
        """Devuelve la modalidad habitual del servicio."""
        return self.__modalidad

    @property
    def solo_remota(self) -> bool:
        """Indica si la asesoría está restringida a modalidad remota."""
        return self.__solo_remota

    def validar_parametros(self, **kwargs: object) -> bool:
        """Valida urgencia y modalidad solicitada."""
        # Una asesoría solo remota no puede aceptar una reserva presencial.
        booleano(kwargs.get("es_urgente", False), "es_urgente")
        modalidad = kwargs.get("modalidad_solicitada", self.modalidad)
        if not isinstance(modalidad, str) or modalidad.upper() not in {
            "REMOTA", "PRESENCIAL"
        }:
            raise DatosInvalidosError(
                "Modalidad solicitada no válida.", "MODALIDAD_INVALIDA"
            )
        if self.solo_remota and modalidad.upper() == "PRESENCIAL":
            raise OperacionNoPermitidaError(
                "Esta asesoría solo está disponible de forma remota.",
                "MODALIDAD_NO_PERMITIDA",
            )
        return True

    def describir_servicio(self) -> str:
        """Describe especialidad, consultor, seniority y modalidad."""
        return (
            f"Asesoría en {self.especialidad} por {self.consultor_asignado} "
            f"({self.nivel_senioridad}, {self.modalidad.lower()}); "
            f"${self.tarifa_base:.2f}/hora"
        )

    def calcular_costo_base(self, duracion: float, **kwargs: object) -> float:
        """Calcula seniority, urgencia y cargo por desplazamiento."""
        self.validar_parametros(**kwargs)
        # La experiencia determina la tarifa; urgencia y modalidad agregan cargos.
        costo = (
            self.tarifa_base * self._MULTIPLICADORES[self.nivel_senioridad] * duracion
        )
        if kwargs.get("es_urgente", False):
            costo *= 1.25
        modalidad = str(kwargs.get("modalidad_solicitada", self.modalidad)).upper()
        if modalidad == "PRESENCIAL":
            costo += self.__cargo_desplazamiento
        return costo
