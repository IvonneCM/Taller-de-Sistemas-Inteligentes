// Cliente de la API (TASK-037). Sin dependencias.
//
// Sesión: el access token vive SOLO en memoria. El refresh token se guarda en
// sessionStorage (se borra al cerrar la pestaña) para que recargar la página no
// obligue a entrar de nuevo; es el compromiso entre comodidad y exposición a
// XSS, y se documenta en docs/contrato_api.md. Ante un 401 se intenta UN
// refresco y se reintenta la petición una vez.

const BASE = import.meta.env.VITE_API_URL ?? "/api";
const TIEMPO_MAXIMO_MS = 15000;
const CLAVE_REFRESCO = "siptb.refresh";

export class ApiError extends Error {
  constructor(estado, mensaje, { requestId = null, tipo = "http" } = {}) {
    super(mensaje);
    this.name = "ApiError";
    this.estado = estado;
    this.requestId = requestId;
    this.tipo = tipo; // "http" | "red" | "tiempo"
  }
}

let tokens = null; // { acceso, refresco }
let refrescoEnCurso = null;
const oyentes = new Set();

function almacen() {
  try { return window.sessionStorage; } catch { return null; }
}

function emitir(evento) { oyentes.forEach((f) => f(evento)); }

/** Se llama con "sesion-iniciada" o "sesion-vencida" / "sesion-cerrada". */
export function alCambiarSesion(funcion) {
  oyentes.add(funcion);
  return () => oyentes.delete(funcion);
}

function guardar(par) {
  tokens = { acceso: par.access_token, refresco: par.refresh_token };
  try { almacen()?.setItem(CLAVE_REFRESCO, tokens.refresco); } catch { /* sin almacenamiento: solo memoria */ }
}

function olvidar() {
  tokens = null;
  try { almacen()?.removeItem(CLAVE_REFRESCO); } catch { /* nada */ }
}

/** Datos del usuario a partir del JWT. SOLO para mostrar: el servidor decide los permisos. */
export function usuarioDelToken(token = tokens?.acceso) {
  if (!token) return null;
  try {
    const carga = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const datos = JSON.parse(decodeURIComponent(escape(atob(carga))));
    return { id: Number(datos.sub), rol: datos.rol };
  } catch {
    return null;
  }
}

export function haySesion() { return tokens !== null; }

async function conTiempo(url, opciones) {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), TIEMPO_MAXIMO_MS);
  try {
    return await fetch(url, { ...opciones, signal: control.signal });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new ApiError(0, "El servidor tardó demasiado en responder.", { tipo: "tiempo" });
    }
    throw new ApiError(0, "No hay conexión con el servidor.", { tipo: "red" });
  } finally {
    clearTimeout(temporizador);
  }
}

async function leerCuerpo(respuesta) {
  try { return await respuesta.json(); } catch { return null; }
}

function errorDe(respuesta, cuerpo) {
  const requestId = cuerpo?.request_id ?? respuesta.headers.get("x-request-id");
  let mensaje = typeof cuerpo?.detail === "string" ? cuerpo.detail : null;
  if (respuesta.status === 422) mensaje = "Revisa los datos enviados.";
  if (respuesta.status === 403) mensaje = "Tu rol no tiene acceso a esto.";
  if (respuesta.status === 429) {
    const segundos = Number(respuesta.headers.get("retry-after"));
    const minutos = Number.isFinite(segundos) && segundos > 0 ? Math.ceil(segundos / 60) : null;
    mensaje = minutos
      ? `Demasiados intentos fallidos. Vuelve a intentarlo en ${minutos} ${minutos === 1 ? "minuto" : "minutos"}.`
      : "Demasiados intentos fallidos. Vuelve a intentarlo más tarde.";
  }
  if (respuesta.status === 503) mensaje = mensaje ?? "El servicio de datos no está disponible. Intenta de nuevo en unos segundos.";
  if (respuesta.status >= 500 && !mensaje) mensaje = "Ocurrió un error en el servidor.";
  return new ApiError(respuesta.status, mensaje ?? "No se pudo completar la solicitud.", { requestId });
}

function consulta(params) {
  const datos = Object.entries(params ?? {}).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return datos.length ? `?${new URLSearchParams(datos)}` : "";
}

export async function entrar(email, password) {
  const respuesta = await conTiempo(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  const cuerpo = await leerCuerpo(respuesta);
  if (!respuesta.ok) {
    const error = errorDe(respuesta, cuerpo);
    if (respuesta.status === 401) error.message = "Correo o contraseña incorrectos.";
    throw error;
  }
  guardar(cuerpo);
  emitir("sesion-iniciada");
  return usuarioDelToken();
}

/** Intenta recuperar la sesión con el refresh token guardado. */
export async function restaurarSesion() {
  let guardado = null;
  try { guardado = almacen()?.getItem(CLAVE_REFRESCO) ?? null; } catch { /* nada */ }
  if (!guardado) return null;
  tokens = { acceso: null, refresco: guardado };
  try {
    await refrescar();
    return usuarioDelToken();
  } catch {
    olvidar();
    return null;
  }
}

// Un solo refresco a la vez: varias peticiones con 401 comparten la misma promesa.
function refrescar() {
  if (!tokens?.refresco) return Promise.reject(new ApiError(401, "Sesión vencida."));
  if (!refrescoEnCurso) {
    refrescoEnCurso = (async () => {
      const respuesta = await conTiempo(`${BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: tokens.refresco }),
      });
      const cuerpo = await leerCuerpo(respuesta);
      if (!respuesta.ok) throw errorDe(respuesta, cuerpo);
      guardar(cuerpo);
    })().finally(() => { refrescoEnCurso = null; });
  }
  return refrescoEnCurso;
}

export async function salir() {
  const refresco = tokens?.refresco;
  olvidar();
  emitir("sesion-cerrada");
  if (refresco) {
    // Mejor esfuerzo: si falla, el token vence solo.
    try {
      await conTiempo(`${BASE}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresco }),
      });
    } catch { /* nada */ }
  }
}

/** GET autenticado con refresco y un reintento ante 401. */
export async function pedir(ruta, { params, _reintento = false } = {}) {
  if (!tokens) throw new ApiError(401, "Inicia sesión para continuar.");
  if (!tokens.acceso) await refrescar();
  const respuesta = await conTiempo(`${BASE}${ruta}${consulta(params)}`, {
    headers: { Authorization: `Bearer ${tokens.acceso}` },
  });
  if (respuesta.status === 401 && !_reintento) {
    try {
      await refrescar();
    } catch {
      olvidar();
      emitir("sesion-vencida");
      throw new ApiError(401, "Tu sesión venció. Vuelve a entrar.");
    }
    return pedir(ruta, { params, _reintento: true });
  }
  const cuerpo = await leerCuerpo(respuesta);
  if (!respuesta.ok) {
    if (respuesta.status === 401) {
      olvidar();
      emitir("sesion-vencida");
    }
    throw errorDe(respuesta, cuerpo);
  }
  return cuerpo;
}

// Solo para pruebas.
export function _reiniciar() {
  tokens = null;
  refrescoEnCurso = null;
  oyentes.clear();
  try { almacen()?.removeItem(CLAVE_REFRESCO); } catch { /* nada */ }
}
