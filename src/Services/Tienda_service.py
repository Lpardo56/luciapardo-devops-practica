# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
TiendaService: lógica de negocio de la tienda (Práctica 1).

Guarda los datos en memoria (diccionarios) y es la ÚNICA clase que usa
main.py para trabajar con usuarios, productos y pedidos. Cuando algo va mal
lanza excepciones propias (TiendaError y subclases) para que la capa de la
API pueda traducirlas al código HTTP adecuado.
"""

from models.Producto import Producto, ProductoElectronico, ProductoRopa
from models.Usuario import Usuario, Cliente, Administrador
from models.Pedido import Pedido, LineaPedido


# ---------------------------------------------------------------------------
# Excepciones de la tienda
# ---------------------------------------------------------------------------
class TiendaError(Exception):
    """Error genérico de la tienda."""


class RecursoNoEncontradoError(TiendaError):
    """No existe el usuario / producto pedido.            -> HTTP 404"""


class EmailDuplicadoError(TiendaError):
    """Ya hay un usuario registrado con ese email.         -> HTTP 409"""


class StockInsuficienteError(TiendaError):
    """No hay unidades suficientes de un producto.         -> HTTP 409"""


class OperacionNoValidaError(TiendaError):
    """Datos u operación no válidos para la lógica de negocio. -> HTTP 400"""


# ---------------------------------------------------------------------------
# Servicio
# ---------------------------------------------------------------------------
class TiendaService:
    TIPOS_USUARIO = ("cliente", "admin")
    TIPOS_PRODUCTO = ("generico", "electronico", "ropa")

    def __init__(self):
        self.usuarios: dict[int, Usuario] = {}
        self.productos: dict[int, Producto] = {}
        self.pedidos: dict[int, Pedido] = {}
        self._siguiente_id_usuario = 1
        self._siguiente_id_producto = 1
        self._siguiente_id_pedido = 1

    # ------------------------------------------------------------- usuarios
    def registrar_usuario(self, nombre: str, email: str, tipo: str = "cliente",
                          direccion_postal: str | None = None) -> Usuario:
        tipo = (tipo or "").lower()
        if tipo not in self.TIPOS_USUARIO:
            raise OperacionNoValidaError(f"Tipo de usuario no válido: '{tipo}'")

        email_normalizado = (email or "").strip().lower()
        if any(u.email == email_normalizado for u in self.usuarios.values()):
            raise EmailDuplicadoError(f"Ya existe un usuario con el email '{email_normalizado}'")

        try:
            if tipo == "cliente":
                usuario = Cliente(self._siguiente_id_usuario, nombre, email, direccion_postal)
            else:
                usuario = Administrador(self._siguiente_id_usuario, nombre, email)
        except ValueError as e:
            raise OperacionNoValidaError(str(e)) from e

        self.usuarios[usuario.id] = usuario
        self._siguiente_id_usuario += 1
        return usuario

    def obtener_usuario(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.get(usuario_id)
        if usuario is None:
            raise RecursoNoEncontradoError(f"No existe ningún usuario con id {usuario_id}")
        return usuario

    def listar_usuarios(self) -> list[Usuario]:
        return list(self.usuarios.values())

    # ------------------------------------------------------------ productos
    def crear_producto(self, tipo: str, nombre: str, precio: float, stock: int,
                       meses_garantia: int | None = None,
                       talla: str | None = None, color: str | None = None) -> Producto:
        tipo = (tipo or "").lower()
        if tipo not in self.TIPOS_PRODUCTO:
            raise OperacionNoValidaError(f"Tipo de producto no válido: '{tipo}'")

        nuevo_id = self._siguiente_id_producto
        try:
            if tipo == "electronico":
                producto = ProductoElectronico(nuevo_id, nombre, precio, stock, meses_garantia)
            elif tipo == "ropa":
                producto = ProductoRopa(nuevo_id, nombre, precio, stock, talla, color)
            else:
                producto = Producto(nuevo_id, nombre, precio, stock)
        except (ValueError, TypeError) as e:
            raise OperacionNoValidaError(str(e)) from e

        self.productos[producto.id] = producto
        self._siguiente_id_producto += 1
        return producto

    def listar_productos(self) -> list[Producto]:
        return list(self.productos.values())

    def obtener_producto(self, producto_id: int) -> Producto:
        producto = self.productos.get(producto_id)
        if producto is None:
            raise RecursoNoEncontradoError(f"No existe ningún producto con id {producto_id}")
        return producto

    def eliminar_producto(self, producto_id: int) -> Producto:
        producto = self.obtener_producto(producto_id)
        del self.productos[producto_id]
        return producto

    # -------------------------------------------------------------- pedidos
    def realizar_pedido(self, cliente_id: int, items: list[tuple[int, int]]) -> Pedido:
        """
        Crea un pedido para un cliente.

        items: lista de tuplas (producto_id, cantidad).
        Primero se comprueba TODO (cliente, productos y stock) y solo después
        se descuenta el stock, para no dejar la tienda a medias si algo falla.
        """
        cliente = self.obtener_usuario(cliente_id)
        if not isinstance(cliente, Cliente):
            raise OperacionNoValidaError("Solo los clientes pueden realizar pedidos")
        if not items:
            raise OperacionNoValidaError("El pedido debe contener al menos un producto")

        # Agrupar por producto (por si el mismo producto aparece en varias líneas)
        cantidades: dict[int, int] = {}
        for producto_id, cantidad in items:
            if cantidad <= 0:
                raise OperacionNoValidaError("Las cantidades deben ser mayores que 0")
            cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

        # 1) Validar existencia y stock
        for producto_id, cantidad in cantidades.items():
            producto = self.obtener_producto(producto_id)
            if not producto.hay_stock(cantidad):
                raise StockInsuficienteError(
                    f"Stock insuficiente para '{producto.nombre}' "
                    f"(disponible: {producto.stock}, solicitado: {cantidad})"
                )

        # 2) Crear líneas y descontar stock
        lineas = []
        for producto_id, cantidad in cantidades.items():
            producto = self.productos[producto_id]
            lineas.append(LineaPedido(producto, cantidad))
            producto.reducir_stock(cantidad)

        pedido = Pedido(self._siguiente_id_pedido, cliente, lineas)
        self.pedidos[pedido.id] = pedido
        self._siguiente_id_pedido += 1
        return pedido

    def obtener_pedidos_cliente(self, cliente_id: int) -> list[Pedido]:
        cliente = self.obtener_usuario(cliente_id)  # lanza 404 si no existe
        return [p for p in self.pedidos.values() if p.cliente.id == cliente.id]
