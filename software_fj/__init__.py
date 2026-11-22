"""Sistema de gestión en memoria para Software FJ."""

# Expone la fachada principal como parte de la interfaz pública del paquete.
from software_fj.core.gestor_sistema import GestorSoftwareFJ

# Limita los nombres disponibles al importar el paquete.
__all__ = ["GestorSoftwareFJ"]
