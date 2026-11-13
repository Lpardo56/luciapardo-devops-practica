# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""Esquemas Pydantic de Pedido (peticiones y respuestas de la API)."""

from datetime import datetime

from pydantic import BaseModel, Field

from models.Pedido import Pedido, LineaPedido


class PedidoItemCreate(BaseModel):
    """Una línea del pedido al crearlo: qué producto y cuántas unidades."""

    producto_id: int = Field(..., ge=1, examples=[1])
    cantidad: int = Field(..., ge=1, examples=[2])


class PedidoCreate(BaseModel):
    """Datos para crear un pedido."""

    cliente_id: int = Field(..., ge=1, examples=[1])
    items: list[PedidoItemCreate] = Field(..., min_length=1)


class PedidoItemRead(BaseModel):
    """Una línea del pedido tal y como la devuelve la API."""

    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    @classmethod
    def desde_modelo(cls, linea: LineaPedido) -> "PedidoItemRead":
        return cls(
            producto_id=linea.producto_id,
            nombre_producto=linea.nombre_producto,
            cantidad=linea.cantidad,
            precio_unitario=linea.precio_unitario,
            subtotal=linea.subtotal,
        )


class PedidoRead(BaseModel):
    """Pedido completo devuelto por la API."""

    id: int
    fecha: datetime
    cliente_id: int
    nombre_cliente: str
    total: float
    items: list[PedidoItemRead]

    @classmethod
    def desde_modelo(cls, pedido: Pedido) -> "PedidoRead":
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente_id=pedido.cliente.id,
            nombre_cliente=pedido.cliente.nombre,
            total=pedido.total,
            items=[PedidoItemRead.desde_modelo(l) for l in pedido.lineas],
        )
