# Práctica 2 - Tienda Online (API REST con FastAPI)

Autora: Lucía Pardo

En esta práctica he convertido la tienda online de la Práctica 1 en una API REST con FastAPI.
La lógica de negocio sigue estando en las clases de dominio y en TiendaService, y la API se
puede usar desde la documentación /docs, desde un cliente en Python hecho con requests y
desde un frontend web.

## Estructura del proyecto

- models/: clases de la Práctica 1
  - Producto.py: Producto, ProductoElectronico y ProductoRopa
  - Usuario.py: Usuario, Cliente y Administrador
  - Pedido.py: Pedido y LineaPedido
- Services/
  - Tienda_service.py: clase TiendaService y las excepciones de la tienda
- schemas/: esquemas Pydantic
  - usuario.py: UsuarioCreate y UsuarioRead
  - producto.py: ProductoCreate y ProductoRead
  - pedido.py: PedidoItemCreate, PedidoCreate, PedidoItemRead y PedidoRead
- main.py: aplicación FastAPI con todos los endpoints
- cliente/cliente_api.py: cliente en Python con requests
- frontend/: index.html, styles.css y app.js
- requirements.txt

## Instalación

Hace falta Python 3.10 o superior. Desde la carpeta Tienda_online:

```
python -m venv .venv
.venv\Scripts\activate        (en Windows)
source .venv/bin/activate     (en Mac o Linux)
pip install -r requirements.txt
```

## Cómo arrancar la API

Desde la carpeta Tienda_online:

```
uvicorn main:app --reload
```

Para que se pueda acceder desde otros ordenadores de la red:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

También se puede arrancar con `python main.py`.

La documentación está en http://localhost:8000/docs

Los datos se guardan en memoria, así que se pierden al parar el servidor.

## Parte 1: Esquemas y endpoints

### Esquemas

- UsuarioCreate: nombre, email, tipo ("cliente" o "admin") y direccion_postal. La dirección es
  obligatoria si el usuario es cliente y el email se valida con una expresión regular.
- UsuarioRead: id, nombre, email y es_admin.
- ProductoCreate: tipo ("generico", "electronico" o "ropa"), nombre, precio (mayor que 0) y
  stock (0 o más). Si es electrónico tiene que llevar meses_garantia y si es ropa tiene que
  llevar talla y color. Si se mandan atributos que no son del tipo da error.
- ProductoRead: id, tipo, nombre, precio, stock y los atributos opcionales según el tipo.
- PedidoItemCreate: producto_id y cantidad.
- PedidoCreate: cliente_id y la lista de items (mínimo uno).
- PedidoItemRead: producto_id, nombre_producto, cantidad, precio_unitario y subtotal.
- PedidoRead: id, fecha, cliente_id, nombre_cliente, total e items.

Los esquemas de salida tienen un método desde_modelo() que pasa el objeto de la tienda al
esquema que se devuelve.

### Endpoints

Usuarios:
- POST /usuarios: crea un usuario. Devuelve 201. Si el email ya existe devuelve 409.
- GET /usuarios: lista de usuarios. Devuelve 200.
- GET /usuarios/{usuario_id}: un usuario. Devuelve 200, o 404 si no existe.

Productos:
- POST /productos: crea un producto. Devuelve 201.
- GET /productos: lista de productos. Devuelve 200.
- GET /productos/{producto_id}: un producto. Devuelve 200, o 404 si no existe.
- DELETE /productos/{producto_id}: borra un producto. Devuelve 204, o 404 si no existe.

Pedidos:
- POST /pedidos: crea un pedido. Devuelve 201. Si no existe el cliente o algún producto
  devuelve 404, si no hay stock suficiente 409, y si el usuario es administrador 400.
- GET /usuarios/{cliente_id}/pedidos: pedidos de un cliente. Devuelve 200, o 404 si no existe.

Si los datos enviados no cumplen los esquemas, FastAPI devuelve 422 automáticamente.

TiendaService lanza sus propias excepciones (RecursoNoEncontradoError, EmailDuplicadoError,
StockInsuficienteError y OperacionNoValidaError) y en main.py se capturan y se convierten en
HTTPException con el código que corresponde.

Al crear un pedido primero se comprueba todo (que exista el cliente, que existan los productos
y que haya stock) y solo después se descuenta el stock, para que si falla una línea no se quede
el stock a medias. Cada línea del pedido guarda el nombre y el precio que tenía el producto al
comprarlo, así el historial no cambia aunque luego se borre el producto.

## Parte 2

### 1. Cliente Python con requests

El archivo cliente/cliente_api.py no importa nada del servidor, todo lo hace con peticiones
HTTP. En cada petición comprueba el código de estado y lee el JSON de la respuesta.

Lo que hace:
1. Comprueba que la API responde (GET /).
2. Crea un cliente y un administrador.
3. Consulta la lista de usuarios.
4. Crea tres productos (electrónico, ropa y genérico).
5. Consulta la lista de productos.
6. Crea un pedido para el cliente.
7. Consulta los pedidos del cliente.
8. Comprueba que el stock ha bajado.
9. Prueba algunos errores: stock insuficiente, cliente que no existe, pedido de un administrador,
   email repetido, electrónico sin garantía y usuario que no existe.
10. Borra un producto y comprueba que después da 404.

Para ejecutarlo (con la API arrancada en otra terminal):

```
cd cliente
python cliente_api.py
```

La dirección de la API está en la variable BASE_URL al principio del archivo. También se
puede pasar al ejecutarlo, por ejemplo:

```
python cliente_api.py http://192.168.1.34:8000
```

### 2. Comunicación entre dos equipos

En el ordenador que hace de servidor:
1. Mirar la IP local. En Windows con `ipconfig` (Dirección IPv4), en Mac con
   `ipconfig getifaddr en0` y en Linux con `hostname -I`.
2. Arrancar la API con `uvicorn main:app --host 0.0.0.0 --port 8000`.
3. Si sale el aviso del firewall de Windows, permitir el acceso en red privada.

En el otro ordenador (conectado a la misma red):
1. Abrir en el navegador http://IP_DEL_SERVIDOR:8000/docs y comprobar que sale la documentación.
2. Ejecutar el cliente con la IP del servidor: `python cliente_api.py http://IP_DEL_SERVIDOR:8000`
3. En la terminal del servidor se ve que las peticiones llegan desde la IP del otro ordenador.

La diferencia entre localhost y la IP: localhost siempre es el propio ordenador, así que desde
el segundo equipo localhost:8000 no encuentra la API. Hay que poner la IP del ordenador que la
tiene arrancada. Por eso se arranca con --host 0.0.0.0, porque por defecto uvicorn solo acepta
conexiones del mismo ordenador (127.0.0.1).

Si la red de la universidad no deja conectar los ordenadores entre sí, se puede usar el punto
de acceso de un móvil.

### 3. Frontend

El frontend está hecho con HTML, CSS y JavaScript sin frameworks, con ayuda de IA (lo permite
el enunciado). Tiene tres pestañas:
- Productos: ver la lista, crear productos (los campos cambian según el tipo) y eliminarlos.
- Usuarios: ver la lista y crear usuarios.
- Pedidos: crear un pedido eligiendo cliente, productos y cantidades, y ver los pedidos de un
  usuario.

Para abrirlo, con la API arrancada:

```
cd frontend
python -m http.server 5500
```

y entrar en http://localhost:5500 (también se puede abrir index.html directamente).

En main.py he añadido CORSMiddleware, porque si no el navegador bloquea las peticiones del
frontend a la API al estar en otra dirección.

Para usar la API de otro ordenador se cambia la dirección en el campo "API" de arriba y se
pulsa Conectar.

Dónde se hacen las peticiones a la API: en frontend/app.js, en la parte "2. ACCESO A LA API".
La función peticion() es la única que usa fetch: monta la URL, manda los datos en JSON,
comprueba si la respuesta es correcta y devuelve el JSON. Si hay un error saca el mensaje
"detail" que devuelve FastAPI y lo muestra en un aviso.

El objeto api tiene una función para cada endpoint:
- api.estado(): GET /
- api.listarProductos(): GET /productos
- api.crearProducto(): POST /productos
- api.eliminarProducto(): DELETE /productos/{id}
- api.listarUsuarios(): GET /usuarios
- api.crearUsuario(): POST /usuarios
- api.crearPedido(): POST /pedidos
- api.pedidosDeUsuario(): GET /usuarios/{id}/pedidos

Con las respuestas se pintan las tablas y los desplegables. Por ejemplo, después de crear un
pedido se vuelven a pedir los productos para que se vea el stock actualizado.

## Comprobación final

Con la API arrancada, los tres clientes (/docs, cliente_api.py y el frontend) usan los mismos
endpoints y ven los mismos datos. Por ejemplo, si se crea un producto desde /docs aparece en
el frontend al darle a Recargar, y un pedido hecho con cliente_api.py se puede ver en la
pestaña Pedidos del frontend.
