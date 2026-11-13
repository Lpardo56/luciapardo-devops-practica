# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""
main.py - Punto de entrada y capa de exposición (API REST) de la tienda online.

Aquí solo se definen los endpoints: reciben y validan los datos con los
esquemas Pydantic, llaman a TiendaService (lógica de negocio) y convierten
el resultado / los errores en respuestas HTTP.

Arrancar el servidor:
    uvicorn main:app --reload                         # solo este equipo (localhost)
    uvicorn main:app --host 0.0.0.0 --port 8000       # accesible desde otros equipos de la red
Documentación interactiva: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from Services.Tienda_service import (
    TiendaService,
    RecursoNoEncontradoError,
    EmailDuplicadoError,
    StockInsuficienteError,
    OperacionNoValidaError,
)
from schemas import (
    UsuarioCreate, UsuarioRead,
    ProductoCreate, ProductoRead,
    PedidoCreate, PedidoRead,
)

app = FastAPI(
    title="Tienda Online API",
    description="API REST de la tienda online (Práctica 2). Gestiona usuarios, productos y pedidos.",
    version="1.0.0",
)

# CORS: permite que el frontend (abierto desde otro origen, p. ej. http://localhost:5500
# o directamente como fichero) pueda hacer peticiones a la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Única instancia del servicio: todos los clientes (docs, script Python, frontend)
# trabajan sobre los mismos datos en memoria.
tienda = TiendaService()

# Respuestas de error documentadas en /docs
R404 = {404: {"description": "Recurso no encontrado"}}


@app.get("/", tags=["General"], summary="Comprobar que la API está en marcha")
def raiz():
    return {"mensaje": "API de la Tienda Online funcionando", "docs": "/docs"}


# =============================================================================
# USUARIOS
# =============================================================================
@app.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    summary="Crear un usuario",
    responses={409: {"description": "Email ya registrado"}, 400: {"description": "Datos no válidos"}},
)
def crear_usuario(datos: UsuarioCreate):
    try:
        usuario = tienda.registrar_usuario(
            nombre=datos.nombre,
            email=datos.email,
            tipo=datos.tipo,
            direccion_postal=datos.direccion_postal,
        )
    except EmailDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except OperacionNoValidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UsuarioRead.desde_modelo(usuario)


@app.get("/usuarios", response_model=list[UsuarioRead], tags=["Usuarios"], summary="Listar usuarios")
def listar_usuarios():
    return [UsuarioRead.desde_modelo(u) for u in tienda.listar_usuarios()]


@app.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRead,
    tags=["Usuarios"],
    summary="Obtener un usuario por id",
    responses=R404,
)
def obtener_usuario(usuario_id: int):
    try:
        usuario = tienda.obtener_usuario(usuario_id)
    except RecursoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return UsuarioRead.desde_modelo(usuario)


@app.get(
    "/usuarios/{cliente_id}/pedidos",
    response_model=list[PedidoRead],
    tags=["Pedidos"],
    summary="Historial de pedidos de un cliente",
    responses=R404,
)
def pedidos_de_cliente(cliente_id: int):
    try:
        pedidos = tienda.obtener_pedidos_cliente(cliente_id)
    except RecursoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [PedidoRead.desde_modelo(p) for p in pedidos]


# =============================================================================
# PRODUCTOS
# =============================================================================
@app.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
    summary="Crear un producto (genérico, electrónico o ropa)",
    responses={400: {"description": "Datos no válidos"}},
)
def crear_producto(datos: ProductoCreate):
    try:
        producto = tienda.crear_producto(
            tipo=datos.tipo,
            nombre=datos.nombre,
            precio=datos.precio,
            stock=datos.stock,
            meses_garantia=datos.meses_garantia,
            talla=datos.talla,
            color=datos.color,
        )
    except OperacionNoValidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProductoRead.desde_modelo(producto)


@app.get("/productos", response_model=list[ProductoRead], tags=["Productos"], summary="Listar productos")
def listar_productos():
    return [ProductoRead.desde_modelo(p) for p in tienda.listar_productos()]


@app.get(
    "/productos/{producto_id}",
    response_model=ProductoRead,
    tags=["Productos"],
    summary="Obtener un producto por id",
    responses=R404,
)
def obtener_producto(producto_id: int):
    try:
        producto = tienda.obtener_producto(producto_id)
    except RecursoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return ProductoRead.desde_modelo(producto)


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
    summary="Eliminar un producto",
    responses=R404,
)
def eliminar_producto(producto_id: int):
    try:
        tienda.eliminar_producto(producto_id)
    except RecursoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    # 204 No Content: se ha borrado correctamente y no se devuelve cuerpo


# =============================================================================
# PEDIDOS
# =============================================================================
@app.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
    summary="Crear un pedido",
    responses={
        404: {"description": "Cliente o producto no encontrado"},
        409: {"description": "Stock insuficiente"},
        400: {"description": "Operación no válida (p. ej. el usuario es administrador)"},
    },
)
def crear_pedido(datos: PedidoCreate):
    try:
        pedido = tienda.realizar_pedido(
            cliente_id=datos.cliente_id,
            items=[(item.producto_id, item.cantidad) for item in datos.items],
        )
    except RecursoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockInsuficienteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except OperacionNoValidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return PedidoRead.desde_modelo(pedido)


if __name__ == "__main__":
    # Permite arrancar también con:  python main.py
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
