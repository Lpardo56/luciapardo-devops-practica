/*
 * Práctica 2 - Tienda Online
 * Autora: Lucía Pardo
 *
 * app.js - Lógica del frontend de la Tienda Online.
 *
 * Estructura del fichero:
 *   1. CONFIGURACIÓN       -> dirección de la API (API_URL)
 *   2. ACCESO A LA API     -> TODAS las peticiones HTTP (fetch) están aquí
 *   3. PINTAR LA INTERFAZ  -> convierten el JSON recibido en HTML
 *   4. EVENTOS             -> qué pasa al pulsar botones / enviar formularios
 *
 * El frontend NO conoce TiendaService ni los modelos: solo habla con la API
 * mediante HTTP y JSON.
 */

// ============================================================================
// 1. CONFIGURACIÓN
// ============================================================================
const API_POR_DEFECTO = "http://localhost:8000";
let API_URL = leerApiGuardada() || API_POR_DEFECTO;

function leerApiGuardada() {
  try { return localStorage.getItem("tienda_api_url"); } catch { return null; }
}
function guardarApi(url) {
  try { localStorage.setItem("tienda_api_url", url); } catch { /* sin almacenamiento */ }
}

// ============================================================================
// 2. ACCESO A LA API
// ============================================================================
/**
 * Hace una petición HTTP a la API y devuelve el JSON de la respuesta.
 * - Envía el cuerpo como JSON si se indica.
 * - Si el código HTTP no es 2xx lanza un Error con el mensaje "detail" de FastAPI.
 * - Si la respuesta es 204 (No Content) devuelve null.
 */
async function peticion(metodo, ruta, cuerpo = null) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== null) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }

  let respuesta;
  try {
    respuesta = await fetch(API_URL + ruta, opciones);
  } catch {
    throw new Error(`No se puede conectar con la API en ${API_URL}`);
  }

  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    throw new Error(`HTTP ${respuesta.status}: ${mensajeDeError(datos)}`);
  }
  return datos;
}

/** FastAPI devuelve {"detail": "texto"} o, en errores de validación (422), {"detail": [ {...}, ... ]}. */
function mensajeDeError(datos) {
  if (!datos || !datos.detail) return "Error desconocido";
  if (Array.isArray(datos.detail)) {
    return datos.detail
      .map(e => `${(e.loc || []).filter(x => x !== "body").join(".")}: ${e.msg}`.replace(/^: /, ""))
      .join(" · ");
  }
  return datos.detail;
}

/** Una función por endpoint de la API. */
const api = {
  estado:          ()         => peticion("GET",    "/"),
  listarProductos: ()         => peticion("GET",    "/productos"),
  crearProducto:   (producto) => peticion("POST",   "/productos", producto),
  eliminarProducto:(id)       => peticion("DELETE", `/productos/${id}`),
  listarUsuarios:  ()         => peticion("GET",    "/usuarios"),
  crearUsuario:    (usuario)  => peticion("POST",   "/usuarios", usuario),
  crearPedido:     (pedido)   => peticion("POST",   "/pedidos", pedido),
  pedidosDeUsuario:(id)       => peticion("GET",    `/usuarios/${id}/pedidos`),
};

// ============================================================================
// 3. PINTAR LA INTERFAZ
// ============================================================================
const $ = (sel) => document.querySelector(sel);
const euros = (n) => n.toLocaleString("es-ES", { style: "currency", currency: "EUR" });
const escapar = (txt) => String(txt ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Datos cargados desde la API (se usan para los desplegables y el total estimado)
let productos = [];
let usuarios = [];
let lineasPedido = []; // [{producto_id, cantidad}]

function aviso(texto, tipo = "") {
  const el = document.createElement("div");
  el.className = `aviso ${tipo}`;
  el.textContent = texto;
  $("#avisos").appendChild(el);
  setTimeout(() => el.remove(), tipo === "error" ? 6000 : 3500);
}

function pintarProductos() {
  const tbody = $("#tabla-productos");
  if (!productos.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="vacio">No hay productos. Crea el primero con el formulario.</td></tr>`;
    return;
  }
  tbody.innerHTML = productos.map(p => {
    let detalles = "-";
    if (p.tipo === "electronico") detalles = `Garantía: ${p.meses_garantia} meses`;
    if (p.tipo === "ropa") detalles = `Talla ${escapar(p.talla)} · ${escapar(p.color)}`;
    return `<tr>
      <td>${p.id}</td>
      <td>${escapar(p.nombre)}</td>
      <td><span class="chip ${p.tipo}">${p.tipo}</span></td>
      <td>${detalles}</td>
      <td class="num">${euros(p.precio)}</td>
      <td class="num ${p.stock === 0 ? "sin-stock" : ""}">${p.stock}</td>
      <td><button class="btn btn-peligro" data-eliminar="${p.id}" title="Eliminar">Eliminar</button></td>
    </tr>`;
  }).join("");
}

function pintarUsuarios() {
  const tbody = $("#tabla-usuarios");
  if (!usuarios.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="vacio">No hay usuarios registrados.</td></tr>`;
  } else {
    tbody.innerHTML = usuarios.map(u => `<tr>
      <td>${u.id}</td>
      <td>${escapar(u.nombre)}</td>
      <td>${escapar(u.email)}</td>
      <td>${u.es_admin ? '<span class="chip admin">Administrador</span>' : '<span class="chip">Cliente</span>'}</td>
      <td>${u.es_admin ? "" : `<button class="btn-enlace" data-ver-pedidos="${u.id}">Ver pedidos</button>`}</td>
    </tr>`).join("");
  }
  pintarDesplegablesUsuarios();
}

function pintarDesplegablesUsuarios() {
  const clientes = usuarios.filter(u => !u.es_admin);
  const anteriorPedido = $("#pedido-cliente").value;
  const anteriorConsulta = $("#consulta-usuario").value;

  $("#pedido-cliente").innerHTML = clientes.length
    ? clientes.map(u => `<option value="${u.id}">#${u.id} · ${escapar(u.nombre)}</option>`).join("")
    : `<option value="">(no hay clientes)</option>`;
  $("#consulta-usuario").innerHTML = usuarios.length
    ? usuarios.map(u => `<option value="${u.id}">#${u.id} · ${escapar(u.nombre)}${u.es_admin ? " (admin)" : ""}</option>`).join("")
    : `<option value="">(no hay usuarios)</option>`;

  if (clientes.some(u => String(u.id) === anteriorPedido)) $("#pedido-cliente").value = anteriorPedido;
  if (usuarios.some(u => String(u.id) === anteriorConsulta)) $("#consulta-usuario").value = anteriorConsulta;
}

function pintarDesplegableProductos() {
  const sel = $("#pedido-producto");
  const anterior = sel.value;
  sel.innerHTML = productos.length
    ? productos.map(p => `<option value="${p.id}" ${p.stock === 0 ? "disabled" : ""}>
        ${escapar(p.nombre)} · ${euros(p.precio)} (stock ${p.stock})</option>`).join("")
    : `<option value="">(no hay productos)</option>`;
  if (productos.some(p => String(p.id) === anterior)) sel.value = anterior;
}

function pintarLineasPedido() {
  const ul = $("#lineas-pedido");
  if (!lineasPedido.length) {
    ul.innerHTML = `<li class="vacio">Añade productos al pedido</li>`;
    $("#total-pedido").textContent = euros(0);
    return;
  }
  let total = 0;
  ul.innerHTML = lineasPedido.map((l, i) => {
    const p = productos.find(x => x.id === l.producto_id);
    const subtotal = p ? p.precio * l.cantidad : 0;
    total += subtotal;
    return `<li>
      <span>${escapar(p ? p.nombre : "Producto #" + l.producto_id)} × ${l.cantidad}</span>
      <span>${euros(subtotal)} <button type="button" class="btn btn-peligro" data-quitar-linea="${i}" title="Quitar">X</button></span>
    </li>`;
  }).join("");
  $("#total-pedido").textContent = euros(total);
}

function pintarPedidos(pedidos, usuarioId) {
  const cont = $("#lista-pedidos");
  if (!pedidos.length) {
    cont.innerHTML = `<p class="vacio">El usuario #${usuarioId} no tiene pedidos.</p>`;
    return;
  }
  cont.innerHTML = pedidos.map(ped => `
    <article class="pedido">
      <header>
        <strong>Pedido #${ped.id}</strong>
        <span>${new Date(ped.fecha).toLocaleString("es-ES")} · ${escapar(ped.nombre_cliente)}</span>
      </header>
      <table>${ped.items.map(it => `<tr>
          <td>${escapar(it.nombre_producto)}</td>
          <td class="num">${it.cantidad} × ${euros(it.precio_unitario)}</td>
          <td class="num">${euros(it.subtotal)}</td></tr>`).join("")}
      </table>
      <div class="total-pedido">Total: ${euros(ped.total)}</div>
    </article>`).join("");
}

// ============================================================================
// 4. EVENTOS Y CARGA DE DATOS
// ============================================================================
async function cargarProductos() {
  try {
    productos = await api.listarProductos();          // GET /productos
    pintarProductos();
    pintarDesplegableProductos();
    pintarLineasPedido();
  } catch (e) { aviso(e.message, "error"); }
}

async function cargarUsuarios() {
  try {
    usuarios = await api.listarUsuarios();            // GET /usuarios
    pintarUsuarios();
  } catch (e) { aviso(e.message, "error"); }
}

async function comprobarConexion() {
  const estado = $("#estado-api");
  try {
    await api.estado();                               // GET /
    estado.textContent = "conectado";
    estado.className = "estado ok";
    await Promise.all([cargarProductos(), cargarUsuarios()]);
  } catch (e) {
    estado.textContent = "sin conexión";
    estado.className = "estado error";
    aviso(e.message, "error");
  }
}

async function verPedidos(usuarioId) {
  try {
    const pedidos = await api.pedidosDeUsuario(usuarioId);   // GET /usuarios/{id}/pedidos
    pintarPedidos(pedidos, usuarioId);
  } catch (e) {
    $("#lista-pedidos").innerHTML = "";
    aviso(e.message, "error");
  }
}

function activarPestana(idPanel) {
  document.querySelectorAll(".pestana").forEach(b => b.classList.toggle("activa", b.dataset.panel === idPanel));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("activo", p.id === idPanel));
}

// --- Configuración de la API -------------------------------------------------
$("#api-url").value = API_URL;
$("#form-api").addEventListener("submit", (ev) => {
  ev.preventDefault();
  API_URL = ($("#api-url").value.trim() || API_POR_DEFECTO).replace(/\/+$/, "");
  $("#api-url").value = API_URL;
  guardarApi(API_URL);
  comprobarConexion();
});

// --- Pestañas y botones generales --------------------------------------------
document.querySelectorAll(".pestana").forEach(b =>
  b.addEventListener("click", () => activarPestana(b.dataset.panel)));

document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("button");
  if (!el) return;

  if (el.dataset.recargar === "productos") cargarProductos();
  if (el.dataset.recargar === "usuarios") cargarUsuarios();

  // Eliminar producto -> DELETE /productos/{id}
  if (el.dataset.eliminar) {
    const id = Number(el.dataset.eliminar);
    const p = productos.find(x => x.id === id);
    el.disabled = true;
    try {
      await api.eliminarProducto(id);
      lineasPedido = lineasPedido.filter(l => l.producto_id !== id);
      aviso(`Producto "${p ? p.nombre : id}" eliminado`, "ok");
      await cargarProductos();
    } catch (e) { aviso(e.message, "error"); el.disabled = false; }
  }

  // Ver pedidos desde la tabla de usuarios
  if (el.dataset.verPedidos) {
    activarPestana("panel-pedidos");
    $("#consulta-usuario").value = el.dataset.verPedidos;
    verPedidos(el.dataset.verPedidos);
  }

  if (el.dataset.quitarLinea !== undefined) {
    lineasPedido.splice(Number(el.dataset.quitarLinea), 1);
    pintarLineasPedido();
  }
});

// --- Productos ---------------------------------------------------------------
function actualizarCamposProducto() {
  const tipo = $("#producto-tipo").value;
  document.querySelectorAll("#form-producto .extra").forEach(div => {
    const visible = div.dataset.tipo === tipo;
    div.hidden = !visible;
    div.querySelectorAll("input").forEach(i => { i.required = visible; });
  });
}
$("#producto-tipo").addEventListener("change", actualizarCamposProducto);

// Crear producto -> POST /productos
$("#form-producto").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  const producto = {
    tipo: f.get("tipo"),
    nombre: f.get("nombre").trim(),
    precio: Number(f.get("precio")),
    stock: Number(f.get("stock")),
  };
  if (producto.tipo === "electronico") producto.meses_garantia = Number(f.get("meses_garantia"));
  if (producto.tipo === "ropa") {
    producto.talla = f.get("talla").trim();
    producto.color = f.get("color").trim();
  }
  try {
    const creado = await api.crearProducto(producto);
    aviso(`Producto "${creado.nombre}" creado con id ${creado.id}`, "ok");
    ev.target.reset();
    actualizarCamposProducto();
    await cargarProductos();
  } catch (e) { aviso(e.message, "error"); }
});

// --- Usuarios ----------------------------------------------------------------
function actualizarCampoDireccion() {
  const esCliente = $("#usuario-tipo").value === "cliente";
  $("#campo-direccion").hidden = !esCliente;
  $("#campo-direccion input").required = esCliente;
}
$("#usuario-tipo").addEventListener("change", actualizarCampoDireccion);

// Crear usuario -> POST /usuarios
$("#form-usuario").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  const usuario = {
    nombre: f.get("nombre").trim(),
    email: f.get("email").trim(),
    tipo: f.get("tipo"),
    direccion_postal: f.get("tipo") === "cliente" ? f.get("direccion_postal").trim() : null,
  };
  try {
    const creado = await api.crearUsuario(usuario);
    aviso(`Usuario "${creado.nombre}" creado con id ${creado.id}`, "ok");
    ev.target.reset();
    actualizarCampoDireccion();
    await cargarUsuarios();
  } catch (e) { aviso(e.message, "error"); }
});

// --- Pedidos -----------------------------------------------------------------
$("#btn-anadir-linea").addEventListener("click", () => {
  const productoId = Number($("#pedido-producto").value);
  const cantidad = Number($("#pedido-cantidad").value);
  if (!productoId) return aviso("Selecciona un producto", "error");
  if (!Number.isInteger(cantidad) || cantidad < 1) return aviso("La cantidad debe ser un entero mayor que 0", "error");

  const existente = lineasPedido.find(l => l.producto_id === productoId);
  if (existente) existente.cantidad += cantidad;
  else lineasPedido.push({ producto_id: productoId, cantidad });
  $("#pedido-cantidad").value = 1;
  pintarLineasPedido();
});

// Crear pedido -> POST /pedidos
$("#form-pedido").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const clienteId = Number($("#pedido-cliente").value);
  if (!clienteId) return aviso("Selecciona un cliente", "error");
  if (!lineasPedido.length) return aviso("Añade al menos un producto al pedido", "error");

  try {
    const pedido = await api.crearPedido({ cliente_id: clienteId, items: lineasPedido });
    aviso(`Pedido #${pedido.id} creado · Total ${euros(pedido.total)}`, "ok");
    lineasPedido = [];
    await cargarProductos();                     // el stock ha cambiado
    $("#consulta-usuario").value = String(clienteId);
    verPedidos(clienteId);
  } catch (e) { aviso(e.message, "error"); }
});

// Consultar pedidos -> GET /usuarios/{id}/pedidos
$("#btn-ver-pedidos").addEventListener("click", () => {
  const id = $("#consulta-usuario").value;
  if (!id) return aviso("Selecciona un usuario", "error");
  verPedidos(id);
});

// --- Inicio ------------------------------------------------------------------
actualizarCamposProducto();
actualizarCampoDireccion();
pintarLineasPedido();
comprobarConexion();
