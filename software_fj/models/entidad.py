"""Entidad abstracta de la aplicación."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4


class EntidadSistema(ABC):
    """Base común con identidad, creación y estado activo."""

    def __init__(self, prefijo: str, activa: bool = True) -> None:
        # Todas las entidades comparten un ID único, fecha de alta y estado activo.
        self.__id = f"{prefijo}-{uuid4().hex[:10].upper()}"
        self.__fecha_creacion = datetime.now()
        self.__activa = activa

    @property
    def id(self) -> str:
        """Identificador inmutable."""
        return self.__id

    @property
    def fecha_creacion(self) -> datetime:
        """Fecha de creación inmutable."""
        return self.__fecha_creacion

    @property
    def activa(self) -> bool:
        """Indica si la entidad está activa."""
        return self.__activa

    def activar(self) -> None:
        """Activa la entidad."""
        self.__activa = True

    def desactivar(self) -> None:
        """Desactiva la entidad."""
        self.__activa = False

    @abstractmethod
    def validar(self) -> bool:
        """Verifica la integridad del objeto."""

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Devuelve una descripción legible."""

    @abstractmethod
    def a_diccionario(self) -> dict[str, object]:
        """Serializa datos para reportes en memoria."""

    def __str__(self) -> str:
        return self.obtener_resumen()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r})"

    def __eq__(self, otro: object) -> bool:
        # Dos entidades se consideran iguales solo si comparten identificador.
        return isinstance(otro, EntidadSistema) and self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)
