# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
Modelo de dominio para los pedidos (Práctica 1).

Cada línea guarda una "foto" del nombre y del precio del producto en el
momento de la compra, para que el historial no cambie si después se
modifica o se elimina el producto.
"""

from datetime import datetime

from models.Producto import Producto
from models.Usuario import Cliente


class LineaPedido:
    """Una línea del pedido: un producto y la cantidad comprada."""

    def __init__(self, producto: Producto, cantidad: int):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        self.producto_id = producto.id
        self.nombre_producto = producto.nombre
        self.precio_unitario = producto.precio
        self.cantidad = cantidad

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)


class Pedido:
    """Pedido realizado por un cliente."""

    def __init__(self, id: int, cliente: Cliente, lineas: list[LineaPedido], fecha: datetime | None = None):
        if not lineas:
            raise ValueError("Un pedido debe tener al menos una línea")
        self.id = id
        self.cliente = cliente
        self.lineas = lineas
        self.fecha = fecha or datetime.now()

    def calcular_total(self) -> float:
        return round(sum(linea.subtotal for linea in self.lineas), 2)

    @property
    def total(self) -> float:
        return self.calcular_total()

    def mostrar_info(self) -> str:
        detalle = "\n".join(
            f"   - {l.nombre_producto} x{l.cantidad} = {l.subtotal:.2f} €" for l in self.lineas
        )
        return (
            f"Pedido {self.id} ({self.fecha:%d/%m/%Y %H:%M}) - {self.cliente.nombre}\n"
            f"{detalle}\n   TOTAL: {self.total:.2f} €"
        )

    def __str__(self) -> str:
        return self.mostrar_info()
