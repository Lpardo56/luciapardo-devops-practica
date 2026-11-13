# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
cliente_api.py - Cliente Python de la API REST de la tienda (Práctica 2, parte 2).

Es un programa INDEPENDIENTE del servidor: no importa TiendaService, ni los
modelos, ni nada de main.py. Toda la comunicación es mediante peticiones HTTP
con la librería requests.

Uso:
    python cliente_api.py                               # usa BASE_URL por defecto (localhost)
    python cliente_api.py http://192.168.1.34:8000      # API de otro equipo de la red
    (también se puede usar la variable de entorno TIENDA_API_URL)
"""

import os
import sys
import time

import requests

# -----------------------------------------------------------------------------
# Dirección de la API: cambiar aquí (o por argumento / variable de entorno)
# -----------------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
TIMEOUT = 5  # segundos


class ErrorAPI(Exception):
    """La API ha respondido con un código distinto al esperado."""

    def __init__(self, respuesta: requests.Response):
        self.status_code = respuesta.status_code
        try:
            self.detalle = respuesta.json().get("detail", respuesta.text)
            if isinstance(self.detalle, list):  # errores de validación (422) de Pydantic
                self.detalle = "; ".join(err.get("msg", str(err)) for err in self.detalle)
        except ValueError:
            self.detalle = respuesta.text
        super().__init__(f"HTTP {self.status_code}: {self.detalle}")


def comprobar(respuesta: requests.Response, esperado: int):
    """Comprueba el código de estado y devuelve el JSON de la respuesta."""
    print(f"   {respuesta.request.method} {respuesta.url} -> {respuesta.status_code}")
    if respuesta.status_code != esperado:
        raise ErrorAPI(respuesta)
    if respuesta.status_code == 204 or not respuesta.content:
        return None
    return respuesta.json()


# -----------------------------------------------------------------------------
# Funciones que llaman a cada endpoint
# -----------------------------------------------------------------------------
def estado_api():
    return comprobar(requests.get(f"{BASE_URL}/", timeout=TIMEOUT), 200)


def crear_usuario(nombre, email, tipo="cliente", direccion_postal=None):
    datos = {"nombre": nombre, "email": email, "tipo": tipo, "direccion_postal": direccion_postal}
    return comprobar(requests.post(f"{BASE_URL}/usuarios", json=datos, timeout=TIMEOUT), 201)


def listar_usuarios():
    return comprobar(requests.get(f"{BASE_URL}/usuarios", timeout=TIMEOUT), 200)


def obtener_usuario(usuario_id):
    return comprobar(requests.get(f"{BASE_URL}/usuarios/{usuario_id}", timeout=TIMEOUT), 200)


def crear_producto(datos: dict):
    return comprobar(requests.post(f"{BASE_URL}/productos", json=datos, timeout=TIMEOUT), 201)


def listar_productos():
    return comprobar(requests.get(f"{BASE_URL}/productos", timeout=TIMEOUT), 200)


def obtener_producto(producto_id):
    return comprobar(requests.get(f"{BASE_URL}/productos/{producto_id}", timeout=TIMEOUT), 200)


def eliminar_producto(producto_id):
    return comprobar(requests.delete(f"{BASE_URL}/productos/{producto_id}", timeout=TIMEOUT), 204)


def crear_pedido(cliente_id, items: list[tuple[int, int]]):
    datos = {
        "cliente_id": cliente_id,
        "items": [{"producto_id": pid, "cantidad": cant} for pid, cant in items],
    }
    return comprobar(requests.post(f"{BASE_URL}/pedidos", json=datos, timeout=TIMEOUT), 201)


def pedidos_de_usuario(cliente_id):
    return comprobar(requests.get(f"{BASE_URL}/usuarios/{cliente_id}/pedidos", timeout=TIMEOUT), 200)


# -----------------------------------------------------------------------------
# Funciones para mostrar los datos de forma legible
# -----------------------------------------------------------------------------
def mostrar_usuario(u):
    rol = "Administrador" if u["es_admin"] else "Cliente"
    print(f"     #{u['id']:<3} {u['nombre']:<22} {u['email']:<32} {rol}")


def mostrar_producto(p):
    extra = ""
    if p["tipo"] == "electronico":
        extra = f"garantía {p['meses_garantia']} meses"
    elif p["tipo"] == "ropa":
        extra = f"talla {p['talla']}, {p['color']}"
    print(f"     #{p['id']:<3} {p['nombre']:<24} {p['tipo']:<12} {p['precio']:>9.2f} €  "
          f"stock {p['stock']:<4} {extra}")


def mostrar_pedido(ped):
    print(f"     Pedido #{ped['id']} - {ped['fecha'][:19].replace('T', ' ')} - "
          f"cliente #{ped['cliente_id']} ({ped['nombre_cliente']})")
    for it in ped["items"]:
        print(f"        - {it['nombre_producto']:<24} x{it['cantidad']:<3} "
              f"{it['precio_unitario']:>8.2f} € = {it['subtotal']:>9.2f} €")
    print(f"        TOTAL: {ped['total']:.2f} €")


def titulo(texto):
    print(f"\n=== {texto} " + "=" * max(0, 60 - len(texto)))


# -----------------------------------------------------------------------------
# Flujo de prueba
# -----------------------------------------------------------------------------
def main():
    print(f"Cliente de la Tienda Online -> {BASE_URL}")

    titulo("0. Comprobar conexión con la API")
    try:
        print("  ", estado_api()["mensaje"])
    except requests.exceptions.RequestException as e:
        print(f"   No se puede conectar con {BASE_URL}: {e}")
        print("   ¿Está el servidor arrancado? ¿Es correcta la IP / el puerto? ¿Firewall?")
        sys.exit(1)

    # Sufijo para que los emails no se repitan si el script se ejecuta varias veces
    sufijo = int(time.time())

    titulo("1. Crear usuarios")
    cliente = crear_usuario("Lucía Pardo", f"lucia.{sufijo}@correo.com", "cliente",
                            "Calle Real 12, 40001 Segovia")
    print(f"   Creado cliente #{cliente['id']}: {cliente['nombre']}")
    admin = crear_usuario("Admin Tienda", f"admin.{sufijo}@tienda.com", "admin")
    print(f"   Creado administrador #{admin['id']}: {admin['nombre']}")

    titulo("2. Consultar la lista de usuarios")
    for u in listar_usuarios():
        mostrar_usuario(u)

    titulo("3. Crear productos")
    portatil = crear_producto({"tipo": "electronico", "nombre": "Portátil Lenovo",
                               "precio": 799.99, "stock": 5, "meses_garantia": 24})
    camiseta = crear_producto({"tipo": "ropa", "nombre": "Camiseta básica",
                               "precio": 12.5, "stock": 30, "talla": "M", "color": "Azul"})
    taza = crear_producto({"tipo": "generico", "nombre": "Taza de cerámica",
                           "precio": 6.0, "stock": 15})
    for p in (portatil, camiseta, taza):
        print(f"   Creado producto #{p['id']}: {p['nombre']} ({p['tipo']})")

    titulo("4. Consultar la lista de productos")
    for p in listar_productos():
        mostrar_producto(p)

    titulo("5. Crear un pedido para el cliente")
    pedido = crear_pedido(cliente["id"], [(portatil["id"], 1), (camiseta["id"], 3), (taza["id"], 2)])
    mostrar_pedido(pedido)

    titulo("6. Consultar los pedidos del cliente")
    for ped in pedidos_de_usuario(cliente["id"]):
        mostrar_pedido(ped)

    titulo("7. Comprobar que el stock se ha actualizado")
    print(f"   Stock del portátil: {portatil['stock']} -> {obtener_producto(portatil['id'])['stock']}")

    titulo("8. Comprobación de errores (se esperan códigos 4xx)")
    pruebas = [
        ("Pedido con más unidades que stock (409)", lambda: crear_pedido(cliente["id"], [(taza["id"], 999)])),
        ("Pedido de un cliente inexistente (404)", lambda: crear_pedido(99999, [(taza["id"], 1)])),
        ("Pedido hecho por un administrador (400)", lambda: crear_pedido(admin["id"], [(taza["id"], 1)])),
        ("Email repetido (409)", lambda: crear_usuario("Otra", cliente["email"], "cliente", "C/ Falsa 1")),
        ("Electrónico sin garantía (422)", lambda: crear_producto({"tipo": "electronico", "nombre": "X",
                                                                    "precio": 10, "stock": 1})),
        ("Usuario inexistente (404)", lambda: obtener_usuario(99999)),
    ]
    for descripcion, prueba in pruebas:
        try:
            prueba()
            print(f"   [!] {descripcion}: la API NO devolvió error")
        except ErrorAPI as e:
            print(f"   OK  {descripcion}: HTTP {e.status_code} - {e.detalle}")

    titulo("9. Eliminar un producto")
    eliminar_producto(taza["id"])
    try:
        obtener_producto(taza["id"])
    except ErrorAPI as e:
        print(f"   Producto #{taza['id']} eliminado (ahora devuelve HTTP {e.status_code})")

    print("\nFlujo completado correctamente.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    elif os.getenv("TIENDA_API_URL"):
        BASE_URL = os.environ["TIENDA_API_URL"]
    BASE_URL = BASE_URL.rstrip("/")

    try:
        main()
    except ErrorAPI as e:
        print(f"\nError inesperado de la API -> {e}")
        sys.exit(1)
