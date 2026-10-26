import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError, _reiniciar, alCambiarSesion, entrar, enviarArchivo, haySesion, pedir, restaurarSesion, salir, usuarioDelToken,
} from "../api.js";

// JWT de prueba (sin firma: el cliente solo lee la carga para mostrar el rol).
function jwt(carga) {
  const b64 = (o) => btoa(JSON.stringify(o)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `${b64({ alg: "HS256" })}.${b64(carga)}.firma`;
}
const PAR = { access_token: jwt({ sub: "7", rol: "epidemiologo" }), refresh_token: "refresco-1", token_type: "bearer", expires_in: 1800 };
const PAR_2 = { access_token: jwt({ sub: "7", rol: "epidemiologo", n: 2 }), refresh_token: "refresco-2", token_type: "bearer", expires_in: 1800 };

function responder(estado, cuerpo = null, cabeceras = {}) {
  return Promise.resolve({
    ok: estado >= 200 && estado < 300,
    status: estado,
    headers: { get: (n) => cabeceras[n.toLowerCase()] ?? null },
    json: () => (cuerpo === null ? Promise.reject(new Error("sin cuerpo")) : Promise.resolve(cuerpo)),
  });
}

let fetchSimulado;
beforeEach(() => {
  _reiniciar();
  fetchSimulado = vi.fn();
  vi.stubGlobal("fetch", fetchSimulado);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("entrar", () => {
  it("guarda la sesión, avisa y devuelve el rol", async () => {
    fetchSimulado.mockReturnValueOnce(responder(200, PAR));
    const eventos = [];
    alCambiarSesion((e) => eventos.push(e));

    const usuario = await entrar("a@demo.local", "clave");

    expect(usuario).toEqual({ id: 7, rol: "epidemiologo" });
    expect(haySesion()).toBe(true);
    expect(eventos).toEqual(["sesion-iniciada"]);
    expect(window.sessionStorage.getItem("siptb.refresh")).toBe("refresco-1");
    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe("/api/auth/login");
    expect(opciones.body.get("username")).toBe("a@demo.local"); // formulario, como OAuth2
  });

  it("credenciales incorrectas dan un mensaje claro y no dejan sesión", async () => {
    fetchSimulado.mockReturnValueOnce(responder(401, { detail: "Credenciales invalidas" }));
    await expect(entrar("a@demo.local", "mala")).rejects.toThrow("Correo o contraseña incorrectos.");
    expect(haySesion()).toBe(false);
    expect(window.sessionStorage.getItem("siptb.refresh")).toBeNull();
  });

  it("demasiados intentos: dice cuánto esperar, en minutos, y no deja sesión", async () => {
    fetchSimulado.mockReturnValueOnce(responder(429, { detail: "Demasiados intentos fallidos." }, { "retry-after": "840" }));
    await expect(entrar("a@demo.local", "mala")).rejects.toThrow("Vuelve a intentarlo en 14 minutos.");
    expect(haySesion()).toBe(false);
  });

  it("demasiados intentos sin Retry-After usa un mensaje general", async () => {
    fetchSimulado.mockReturnValueOnce(responder(429, { detail: "x" }));
    await expect(entrar("a@demo.local", "mala")).rejects.toThrow("Vuelve a intentarlo más tarde.");
  });

  it("sin conexión lo dice, sin mostrar detalles técnicos", async () => {
    fetchSimulado.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    const error = await entrar("a@demo.local", "x").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.tipo).toBe("red");
    expect(error.message).toBe("No hay conexión con el servidor.");
  });
});

describe("pedir", () => {
  async function conSesion() {
    fetchSimulado.mockReturnValueOnce(responder(200, PAR));
    await entrar("a@demo.local", "clave");
    fetchSimulado.mockClear();
  }

  it("envía el token y los parámetros, ignorando los vacíos", async () => {
    await conSesion();
    fetchSimulado.mockReturnValueOnce(responder(200, [{ id: 1 }]));

    const datos = await pedir("/alertas", { params: { limite: 50, desde: undefined, texto: "" } });

    expect(datos).toEqual([{ id: 1 }]);
    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe("/api/alertas?limite=50");
    expect(opciones.headers.Authorization).toBe(`Bearer ${PAR.access_token}`);
  });

  it("enviarArchivo hace POST multipart con el token y reintenta con el mismo archivo tras un 401", async () => {
    await conSesion();
    fetchSimulado
      .mockReturnValueOnce(responder(401, { detail: "x" }))
      .mockReturnValueOnce(responder(200, PAR_2))
      .mockReturnValueOnce(responder(400, { detail: "El archivo no es un PDF." }));
    const archivo = new File(["hola"], "b.pdf", { type: "application/pdf" });

    await expect(enviarArchivo("/admin/boletines", archivo)).rejects.toThrow("El archivo no es un PDF.");

    const [url, opciones] = fetchSimulado.mock.calls[2];
    expect(url).toBe("/api/admin/boletines");
    expect(opciones.method).toBe("POST");
    expect(opciones.body.get("archivo")).toBe(archivo);
    expect(opciones.headers.Authorization).toBe(`Bearer ${PAR_2.access_token}`);
  });

  it("sin sesión no llama a la red", async () => {
    await expect(pedir("/zonas/riesgo")).rejects.toMatchObject({ estado: 401 });
    expect(fetchSimulado).not.toHaveBeenCalled();
  });

  it("ante un 401 refresca UNA vez y reintenta con el token nuevo", async () => {
    await conSesion();
    fetchSimulado
      .mockReturnValueOnce(responder(401, { detail: "x" }))   // petición original
      .mockReturnValueOnce(responder(200, PAR_2))             // /auth/refresh
      .mockReturnValueOnce(responder(200, { ok: true }));     // reintento

    expect(await pedir("/zonas/riesgo")).toEqual({ ok: true });

    expect(fetchSimulado.mock.calls[1][0]).toBe("/api/auth/refresh");
    expect(JSON.parse(fetchSimulado.mock.calls[1][1].body)).toEqual({ refresh_token: "refresco-1" });
    expect(fetchSimulado.mock.calls[2][1].headers.Authorization).toBe(`Bearer ${PAR_2.access_token}`);
    expect(window.sessionStorage.getItem("siptb.refresh")).toBe("refresco-2");
  });

  it("varias peticiones con 401 comparten un solo refresco", async () => {
    await conSesion();
    fetchSimulado.mockImplementation((url) => {
      if (url === "/api/auth/refresh") return responder(200, PAR_2);
      const autorizada = fetchSimulado.mock.calls.length > 0 && true;
      return responder(autorizada ? 401 : 200, { detail: "x" });
    });
    // Tras el refresco, el servidor acepta el token nuevo.
    let refrescado = false;
    fetchSimulado.mockImplementation((url, opciones) => {
      if (url === "/api/auth/refresh") { refrescado = true; return responder(200, PAR_2); }
      return refrescado && opciones.headers.Authorization.includes(PAR_2.access_token)
        ? responder(200, { ok: true }) : responder(401, { detail: "x" });
    });

    const resultados = await Promise.all([pedir("/a"), pedir("/b"), pedir("/c")]);

    expect(resultados).toHaveLength(3);
    expect(fetchSimulado.mock.calls.filter(([url]) => url === "/api/auth/refresh")).toHaveLength(1);
  });

  it("si el refresco falla, cierra la sesión y avisa que venció", async () => {
    await conSesion();
    const eventos = [];
    alCambiarSesion((e) => eventos.push(e));
    fetchSimulado
      .mockReturnValueOnce(responder(401, { detail: "x" }))
      .mockReturnValueOnce(responder(401, { detail: "Credenciales invalidas" }));

    await expect(pedir("/zonas/riesgo")).rejects.toThrow("Tu sesión venció. Vuelve a entrar.");

    expect(haySesion()).toBe(false);
    expect(eventos).toContain("sesion-vencida");
    expect(window.sessionStorage.getItem("siptb.refresh")).toBeNull();
  });

  it("no reintenta en bucle: un segundo 401 tras refrescar cierra la sesión", async () => {
    await conSesion();
    fetchSimulado.mockImplementation((url) => (url === "/api/auth/refresh" ? responder(200, PAR_2) : responder(401, { detail: "x" })));
    await expect(pedir("/zonas/riesgo")).rejects.toBeInstanceOf(ApiError);
    expect(fetchSimulado.mock.calls.filter(([url]) => url === "/api/auth/refresh")).toHaveLength(1);
    expect(haySesion()).toBe(false);
  });

  it.each([
    [403, { detail: "x" }, "Tu rol no tiene acceso a esto."],
    [404, { detail: "No existe el municipio 9." }, "No existe el municipio 9."],
    [422, { detail: [{ loc: [], msg: "m", type: "t" }] }, "Revisa los datos enviados."],
    [503, { detail: "El servicio de datos no esta disponible. Intente de nuevo en unos segundos.", request_id: "abc123" }, "El servicio de datos no esta disponible. Intente de nuevo en unos segundos."],
  ])("traduce el estado %i a un mensaje para la persona", async (estado, cuerpo, mensaje) => {
    await conSesion();
    fetchSimulado.mockReturnValueOnce(responder(estado, cuerpo));
    const error = await pedir("/x").catch((e) => e);
    expect(error.estado).toBe(estado);
    expect(error.message).toBe(mensaje);
  });

  it("conserva el código de soporte (request_id) del error", async () => {
    await conSesion();
    fetchSimulado.mockReturnValueOnce(responder(503, { detail: "caída", request_id: "abc123" }));
    const error = await pedir("/x").catch((e) => e);
    expect(error.requestId).toBe("abc123");
  });

  it("un 500 sin detalle no muestra nada técnico", async () => {
    await conSesion();
    fetchSimulado.mockReturnValueOnce(responder(500, null));
    const error = await pedir("/x").catch((e) => e);
    expect(error.message).toBe("Ocurrió un error en el servidor.");
  });

  it("si el servidor no responde a tiempo, corta y lo dice", async () => {
    await conSesion();
    vi.useFakeTimers();
    fetchSimulado.mockImplementationOnce((_, { signal }) => new Promise((_, rechazar) => {
      signal.addEventListener("abort", () => rechazar(Object.assign(new Error("abortado"), { name: "AbortError" })));
    }));

    const promesa = pedir("/zonas/riesgo").catch((e) => e);
    await vi.advanceTimersByTimeAsync(15001);

    const error = await promesa;
    expect(error.tipo).toBe("tiempo");
    expect(error.message).toBe("El servidor tardó demasiado en responder.");
  });
});

describe("restaurarSesion y salir", () => {
  it("recupera la sesión con el refresh token guardado", async () => {
    window.sessionStorage.setItem("siptb.refresh", "refresco-1");
    fetchSimulado.mockReturnValueOnce(responder(200, PAR_2));

    expect(await restaurarSesion()).toEqual({ id: 7, rol: "epidemiologo" });
    expect(haySesion()).toBe(true);
  });

  it("sin token guardado no hace ninguna petición", async () => {
    expect(await restaurarSesion()).toBeNull();
    expect(fetchSimulado).not.toHaveBeenCalled();
  });

  it("si el token guardado ya no sirve, olvida la sesión", async () => {
    window.sessionStorage.setItem("siptb.refresh", "vencido");
    fetchSimulado.mockReturnValueOnce(responder(401, { detail: "Credenciales invalidas" }));
    expect(await restaurarSesion()).toBeNull();
    expect(window.sessionStorage.getItem("siptb.refresh")).toBeNull();
  });

  it("salir olvida la sesión de inmediato y revoca el refresh token", async () => {
    fetchSimulado.mockReturnValueOnce(responder(200, PAR));
    await entrar("a@demo.local", "clave");
    fetchSimulado.mockReturnValueOnce(responder(204));

    const pendiente = salir();
    expect(haySesion()).toBe(false);
    await pendiente;

    const [url, opciones] = fetchSimulado.mock.calls.at(-1);
    expect(url).toBe("/api/auth/logout");
    expect(JSON.parse(opciones.body)).toEqual({ refresh_token: "refresco-1" });
    expect(window.sessionStorage.getItem("siptb.refresh")).toBeNull();
  });

  it("salir no falla aunque el servidor no responda", async () => {
    fetchSimulado.mockReturnValueOnce(responder(200, PAR));
    await entrar("a@demo.local", "clave");
    fetchSimulado.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(salir()).resolves.toBeUndefined();
  });
});

describe("usuarioDelToken", () => {
  it("lee el rol y tolera tokens malformados", () => {
    expect(usuarioDelToken(jwt({ sub: "3", rol: "admin" }))).toEqual({ id: 3, rol: "admin" });
    expect(usuarioDelToken("basura")).toBeNull();
    expect(usuarioDelToken(null)).toBeNull();
  });
});
