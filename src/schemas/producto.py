# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""Esquemas Pydantic de Producto (peticiones y respuestas de la API)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from models.Producto import Producto, ProductoElectronico, ProductoRopa


class ProductoCreate(BaseModel):
    """
    Datos para crear un producto. Los atributos extra dependen del tipo:
      - electronico -> meses_garantia
      - ropa        -> talla y color
      - generico    -> ninguno
    """

    tipo: Literal["generico", "electronico", "ropa"] = "generico"
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Portátil Lenovo"])
    precio: float = Field(..., gt=0, examples=[799.99])
    stock: int = Field(..., ge=0, examples=[10])
    meses_garantia: Optional[int] = Field(None, ge=0, examples=[24])
    talla: Optional[str] = Field(None, min_length=1, max_length=10, examples=["M"])
    color: Optional[str] = Field(None, min_length=1, max_length=30, examples=["Azul"])

    @model_validator(mode="after")
    def comprobar_atributos_segun_tipo(self):
        if self.tipo == "electronico":
            if self.meses_garantia is None:
                raise ValueError("Los productos electrónicos necesitan 'meses_garantia'")
            if self.talla is not None or self.color is not None:
                raise ValueError("Un producto electrónico no tiene talla ni color")
        elif self.tipo == "ropa":
            if not self.talla or not self.color:
                raise ValueError("Los productos de ropa necesitan 'talla' y 'color'")
            if self.meses_garantia is not None:
                raise ValueError("Un producto de ropa no tiene meses de garantía")
        else:  # generico
            if any(v is not None for v in (self.meses_garantia, self.talla, self.color)):
                raise ValueError("Un producto genérico no admite meses_garantia, talla ni color")
        return self


class ProductoRead(BaseModel):
    """Datos de un producto que devuelve la API."""

    id: int
    tipo: Literal["generico", "electronico", "ropa"]
    nombre: str
    precio: float
    stock: int
    meses_garantia: Optional[int] = None
    talla: Optional[str] = None
    color: Optional[str] = None

    @classmethod
    def desde_modelo(cls, producto: Producto) -> "ProductoRead":
        datos = dict(
            id=producto.id,
            tipo=producto.tipo,
            nombre=producto.nombre,
            precio=producto.precio,
            stock=producto.stock,
        )
        if isinstance(producto, ProductoElectronico):
            datos["meses_garantia"] = producto.meses_garantia
        elif isinstance(producto, ProductoRopa):
            datos["talla"] = producto.talla
            datos["color"] = producto.color
        return cls(**datos)
