# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
Modelos de dominio para los usuarios de la tienda (Práctica 1).

Jerarquía:
    - Usuario (clase base)
    - Cliente: hereda de Usuario, tiene direccion_postal y puede hacer pedidos
    - Administrador: hereda de Usuario, gestiona la tienda
"""


class Usuario:
    """Usuario base de la tienda."""

    def __init__(self, id: int, nombre: str, email: str):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del usuario no puede estar vacío")
        if not email or "@" not in email:
            raise ValueError("El email no es válido")

        self.id = id
        self.nombre = nombre.strip()
        self.email = email.strip().lower()

    def es_admin(self) -> bool:
        return False

    def mostrar_info(self) -> str:
        return f"[{self.id}] {self.nombre} <{self.email}>"

    def __str__(self) -> str:
        return self.mostrar_info()


class Cliente(Usuario):
    """Cliente de la tienda: tiene dirección postal y puede realizar pedidos."""

    def __init__(self, id: int, nombre: str, email: str, direccion_postal: str):
        super().__init__(id, nombre, email)
        if not direccion_postal or not direccion_postal.strip():
            raise ValueError("El cliente necesita una dirección postal")
        self.direccion_postal = direccion_postal.strip()

    def mostrar_info(self) -> str:
        return f"{super().mostrar_info()} | Cliente | {self.direccion_postal}"


class Administrador(Usuario):
    """Administrador de la tienda."""

    def es_admin(self) -> bool:
        return True

    def mostrar_info(self) -> str:
        return f"{super().mostrar_info()} | Administrador"
