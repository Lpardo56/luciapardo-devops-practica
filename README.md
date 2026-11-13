# luciapardo-devops-practica

**Autora:** Lucía Pardo

## Descripción

Tienda Online: API REST desarrollada en Python con FastAPI (Práctica 2). Permite gestionar
usuarios (clientes y administradores), productos (genéricos, electrónicos y ropa) y pedidos,
controlando el stock. Incluye un cliente en Python hecho con `requests` y un frontend web en
HTML, CSS y JavaScript.

En este repositorio voy a ir aplicando lo de la asignatura de DevOps: control de versiones
con Git y GitHub (ramas `feature/*`, commits y Pull Requests) y contenerización con Docker.

## Estructura del repositorio

```
.
├── Dockerfile            # imagen de la API
├── .dockerignore         # lo que no se copia al construir la imagen
├── docker-compose.yml    # API + frontend juntos (extra)
├── requirements.txt      # dependencias con versiones fijadas
├── README.md
└── src/                  # código de la Práctica 2
    ├── main.py           # aplicación FastAPI (endpoints)
    ├── models/           # Producto, Usuario, Pedido
    ├── schemas/          # esquemas Pydantic
    ├── Services/         # TiendaService (lógica de negocio)
    ├── cliente/          # cliente en Python con requests
    ├── frontend/         # HTML, CSS, JS + Dockerfile del frontend
    └── README_practica2.md
```

## Ejecución sin Docker

Hace falta Python 3.10 o superior.

```
python -m venv .venv
.venv\Scripts\activate        (en Windows)
source .venv/bin/activate     (en Mac o Linux)
pip install -r requirements.txt
cd src
uvicorn main:app --reload
```

---

## Docker

### Requisitos

Tener instalado Docker Desktop (o Docker Engine) y que esté arrancado. Se puede comprobar con:

```
docker --version
```

### Qué hace el Dockerfile

1. Parte de la imagen `python:3.12-slim`, que ocupa poco.
2. Copia `requirements.txt` y ejecuta `pip install --no-cache-dir -r requirements.txt`. Se copia
   antes que el código para que Docker reutilice esta capa si solo cambia el código.
3. Crea un usuario sin privilegios (`appuser`) para no ejecutar la aplicación como root.
4. Copia el código fuente (`src/`) con `COPY`.
5. Cambia el propietario y los permisos de `/app` para que `appuser` pueda ejecutar el código.
6. Arranca la API con `CMD` usando uvicorn en el puerto indicado por la variable `PORT`.

El fichero `.dockerignore` evita copiar a la imagen cosas que no hacen falta: la carpeta `.git`,
cachés de Python, entornos virtuales, ficheros `.env`, documentación y el frontend (que tiene
su propia imagen).

### 1. Construir la imagen

Desde la raíz del repositorio:

```
docker build -t tienda-online-api:1.0.0 .
```

Para comprobar que se ha creado:

```
docker images tienda-online-api
```

### 2. Ejecutar el contenedor

Ejemplo básico (en segundo plano, puerto 8000):

```
docker run -d --name tienda-api -p 8000:8000 tienda-online-api:1.0.0
```

Ejecutarlo en primer plano para ver los logs (se para con Ctrl+C y se borra al salir):

```
docker run --rm -p 8000:8000 tienda-online-api:1.0.0
```

Cambiando el puerto interno con la variable de entorno `PORT`:

```
docker run -d --name tienda-api -e PORT=9000 -p 9000:9000 tienda-online-api:1.0.0
```

Con más detalle en los logs:

```
docker run -d --name tienda-api -e LOG_LEVEL=debug -p 8000:8000 tienda-online-api:1.0.0
```

Comandos útiles:

```
docker ps                    # ver los contenedores en marcha
docker logs -f tienda-api    # ver los logs
docker stop tienda-api       # parar el contenedor
docker rm tienda-api         # borrarlo
```

### 3. Variables de entorno

| Variable    | Valor por defecto | Para qué sirve                                                  |
|-------------|-------------------|-----------------------------------------------------------------|
| `PORT`      | `8000`            | Puerto en el que escucha uvicorn dentro del contenedor          |
| `LOG_LEVEL` | `info`            | Nivel de logs de uvicorn (`debug`, `info`, `warning`, `error`)  |

La aplicación no usa contraseñas ni claves. Si en el futuro hiciera falta alguna, se pasaría con
`-e` o con un fichero `.env` (que está en el `.gitignore` y en el `.dockerignore`), nunca escrita
en el código.

### 4. Probar que funciona

Con el contenedor arrancado:

**a) Logs del contenedor** (`docker logs tienda-api`). Debería salir algo así:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**b) Endpoint raíz** en el navegador (http://localhost:8000) o con curl:

```
curl http://localhost:8000/
```

Respuesta esperada:

```json
{"mensaje":"API de la Tienda Online funcionando","docs":"/docs"}
```

**c) Documentación interactiva** en http://localhost:8000/docs, donde se pueden probar todos los
endpoints:

| Método | Ruta                              | Qué hace                         |
|--------|-----------------------------------|----------------------------------|
| GET    | `/`                               | Comprueba que la API funciona    |
| POST   | `/usuarios`                       | Crea un usuario                  |
| GET    | `/usuarios`                       | Lista los usuarios               |
| GET    | `/usuarios/{id}`                  | Obtiene un usuario               |
| GET    | `/usuarios/{id}/pedidos`          | Pedidos de un cliente            |
| POST   | `/productos`                      | Crea un producto                 |
| GET    | `/productos`                      | Lista los productos              |
| GET    | `/productos/{id}`                 | Obtiene un producto              |
| DELETE | `/productos/{id}`                 | Borra un producto                |
| POST   | `/pedidos`                        | Crea un pedido                   |

Ejemplo creando un producto con curl (en Mac o Linux; en Windows es más cómodo desde /docs):

```
curl -X POST http://localhost:8000/productos \
  -H "Content-Type: application/json" \
  -d '{"tipo":"electronico","nombre":"Portátil","precio":799.99,"stock":10,"meses_garantia":24}'
```

Devuelve `201` con el producto creado y su `id`.

**d) Prueba completa con el cliente de Python dentro del propio contenedor.** La imagen ya tiene
`requests` instalado, así que se puede lanzar el cliente de la Práctica 2 contra la API:

```
docker exec tienda-api python cliente/cliente_api.py
```

Crea usuarios, productos y un pedido, prueba los errores (stock insuficiente, email repetido, etc.)
y al final debe imprimir:

```
Flujo completado correctamente.
```

### 5. Publicar la imagen en Docker Hub

La imagen está publicada en Docker Hub con mi usuario `lpardo56`:
https://hub.docker.com/r/lpardo56/tienda-online-api

Pasos que he seguido para publicarla:

```
docker login
docker tag tienda-online-api:1.0.0 lpardo56/tienda-online-api:1.0.0
docker tag tienda-online-api:1.0.0 lpardo56/tienda-online-api:latest
docker push lpardo56/tienda-online-api:1.0.0
docker push lpardo56/tienda-online-api:latest
```

Uso dos etiquetas: `1.0.0` para tener una versión fija y `latest` para la última.

### 6. Descargar la imagen (pull) y ejecutarla

Desde cualquier ordenador con Docker, sin necesidad del código:

```
docker pull lpardo56/tienda-online-api:1.0.0
docker run -d --name tienda-api -p 8000:8000 lpardo56/tienda-online-api:1.0.0
```

### 7. Extra: API + frontend con docker-compose

El frontend tiene su propio `Dockerfile` en `src/frontend/`, que sirve los ficheros estáticos con
nginx. El `docker-compose.yml` levanta los dos contenedores a la vez:

```
docker compose up -d --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:8080

El frontend se ejecuta en el navegador y hace las peticiones a `http://localhost:8000`, que es el
puerto que publica el contenedor de la API, así que los dos quedan comunicados. Para pararlo todo:

```
docker compose down
```

---

## Flujo de trabajo con Git

- `main`: rama principal, solo recibe cambios a través de Pull Requests.
- `feature/docker`: rama donde he hecho la contenerización (Dockerfile, .dockerignore,
  requirements con versiones fijadas, docker-compose y documentación). Al terminar se abre un
  Pull Request hacia `main`, se revisa y se fusiona.

Los commits siguen el formato `tipo(ámbito): descripción`, por ejemplo
`feat(docker): primera versión del Dockerfile` o `docs: añade guía de Docker al README`.
