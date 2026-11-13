# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
Modelos de dominio para los productos de la tienda (Práctica 1).

Jerarquía:
    - Producto (clase base)
    - ProductoElectronico: hereda de Producto y añade meses_garantia
    - ProductoRopa: hereda de Producto y añade talla y color
"""


class Producto:
    """Producto genérico de la tienda."""

    def __init__(self, id: int, nombre: str, precio: float, stock: int):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor que 0")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo")

        self.id = id
        self.nombre = nombre.strip()
        self.precio = float(precio)
        self.stock = int(stock)

    @property
    def tipo(self) -> str:
        return "generico"

    def hay_stock(self, cantidad: int) -> bool:
        """Indica si hay unidades suficientes para servir 'cantidad'."""
        return cantidad <= self.stock

    def reducir_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        if not self.hay_stock(cantidad):
            raise ValueError(
                f"Stock insuficiente para '{self.nombre}' "
                f"(disponible: {self.stock}, solicitado: {cantidad})"
            )
        self.stock -= cantidad

    def aumentar_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        self.stock += cantidad

    def mostrar_info(self) -> str:
        return f"[{self.id}] {self.nombre} - {self.precio:.2f} € (stock: {self.stock})"

    def __str__(self) -> str:
        return self.mostrar_info()


class ProductoElectronico(Producto):
    """Producto electrónico: añade los meses de garantía."""

    def __init__(self, id: int, nombre: str, precio: float, stock: int, meses_garantia: int):
        super().__init__(id, nombre, precio, stock)
        if meses_garantia is None or meses_garantia < 0:
            raise ValueError("Los meses de garantía deben ser un número >= 0")
        self.meses_garantia = int(meses_garantia)

    @property
    def tipo(self) -> str:
        return "electronico"

    def mostrar_info(self) -> str:
        return f"{super().mostrar_info()} | Garantía: {self.meses_garantia} meses"


class ProductoRopa(Producto):
    """Prenda de ropa: añade talla y color."""

    def __init__(self, id: int, nombre: str, precio: float, stock: int, talla: str, color: str):
        super().__init__(id, nombre, precio, stock)
        if not talla or not color:
            raise ValueError("La ropa necesita talla y color")
        self.talla = talla.strip().upper()
        self.color = color.strip()

    @property
    def tipo(self) -> str:
        return "ropa"

    def mostrar_info(self) -> str:
        return f"{super().mostrar_info()} | Talla: {self.talla} | Color: {self.color}"
