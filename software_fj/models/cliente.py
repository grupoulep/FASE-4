"""Modelo de cliente con datos encapsulados y validados."""

import re

from software_fj.exceptions.errores import DatosInvalidosError
from software_fj.models.entidad import EntidadSistema
from software_fj.utils.validadores import correo, requerido, telefono, texto


class Cliente(EntidadSistema):
    """Cliente con categoría comercial y beneficio asociado."""

    # Tabla de solo lectura: cada categoría obtiene su descuento correspondiente.
    _DESCUENTOS = {"ESTANDAR": 0.0, "CORPORATIVO": 5.0, "VIP": 10.0}

    def __init__(
        self, nombre_completo: str, documento: str, correo_electronico: str,
        telefono_contacto: str, empresa: str | None = None,
        categoria: str = "ESTANDAR",
    ) -> None:
        super().__init__("CLI")
        # Los campos privados se inicializan y luego pasan por setters validados.
        self.__nombre_completo = ""
        self.__documento = ""
        self.__correo = ""
        self.__telefono = ""
        self.__empresa: str | None = None
        self.__categoria = "ESTANDAR"
        self.nombre_completo = nombre_completo
        self.documento = documento
        self.correo = correo_electronico
        self.telefono = telefono_contacto
        self.empresa = empresa
        self.categoria = categoria

    @property
    def nombre_completo(self) -> str:
        """Devuelve el nombre completo del cliente."""
        return self.__nombre_completo

    @nombre_completo.setter
    def nombre_completo(self, valor: str) -> None:
        """Valida y actualiza el nombre completo."""
        # El nombre debe ser legible y no contener cifras.
        nombre = texto(valor, "nombre completo", 3)
        if any(caracter.isdigit() for caracter in nombre):
            raise DatosInvalidosError(
                "El nombre no puede contener números.", "NOMBRE_INVALIDO"
            )
        self.__nombre_completo = nombre

    @property
    def documento(self) -> str:
        """Devuelve el documento normalizado."""
        return self.__documento

    @documento.setter
    def documento(self, valor: str) -> None:
        """Valida y normaliza el documento."""
        # Se aceptan letras, cifras, puntos y guiones; se guarda en mayúsculas.
        resultado = texto(valor, "documento")
        if not re.fullmatch(r"[A-Za-z0-9.-]{3,30}", resultado):
            raise DatosInvalidosError(
                "El documento debe ser alfanumérico.", "DOCUMENTO_INVALIDO"
            )
        self.__documento = resultado.upper()

    @property
    def correo(self) -> str:
        """Devuelve el correo electrónico."""
        return self.__correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """Valida y actualiza el correo electrónico."""
        self.__correo = correo(valor)

    @property
    def telefono(self) -> str:
        """Devuelve el teléfono de contacto."""
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        """Valida y actualiza el teléfono."""
        self.__telefono = telefono(valor)

    @property
    def empresa(self) -> str | None:
        """Devuelve la empresa, si fue indicada."""
        return self.__empresa

    @empresa.setter
    def empresa(self, valor: str | None) -> None:
        """Valida y actualiza la empresa opcional."""
        # Una empresa vacía se normaliza a None porque el dato es opcional.
        if valor is not None and not isinstance(valor, str):
            raise DatosInvalidosError("La empresa debe ser texto.", "EMPRESA_INVALIDA")
        self.__empresa = valor.strip() if valor and valor.strip() else None

    @property
    def categoria(self) -> str:
        """Devuelve la categoría comercial."""
        return self.__categoria

    @categoria.setter
    def categoria(self, valor: str) -> None:
        """Valida y actualiza la categoría."""
        # Solo se permiten las categorías registradas en la tabla de descuentos.
        requerido(valor, "categoría")
        if not isinstance(valor, str) or valor.upper() not in self._DESCUENTOS:
            raise DatosInvalidosError("Categoría no permitida.", "CATEGORIA_INVALIDA")
        self.__categoria = valor.upper()

    def descuento_categoria(self) -> float:
        """Devuelve el porcentaje de descuento comercial."""
        return self._DESCUENTOS[self.categoria]

    def validar(self) -> bool:
        """Revalida los datos personales del cliente."""
        self.nombre_completo = self.nombre_completo
        self.documento = self.documento
        self.correo = self.correo
        self.telefono = self.telefono
        return True

    def obtener_resumen(self) -> str:
        """Devuelve una descripción breve del cliente."""
        return f"{self.nombre_completo} ({self.documento}) - {self.categoria}"

    def a_diccionario(self) -> dict[str, object]:
        """Devuelve los datos públicos para reportes en memoria."""
        return {
            "id": self.id,
            "nombre": self.nombre_completo,
            "documento": self.documento,
            "correo": self.correo,
            "telefono": self.telefono,
            "empresa": self.empresa,
            "categoria": self.categoria,
            "activa": self.activa,
        }
