import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api.js", () => ({
  pedir: vi.fn(),
  entrar: vi.fn(),
  salir: vi.fn().mockResolvedValue(undefined),
  restaurarSesion: vi.fn(),
  alCambiarSesion: vi.fn(() => () => {}),
  usuarioDelToken: vi.fn(),
}));

// Leaflet necesita medidas reales del navegador: se sustituye por una lista de botones.
vi.mock("../components/MapaZonas.jsx", () => ({
  MapaZonas: ({ puntos, alSeleccionar, seleccionado }) => (
    <div data-testid="mapa" data-seleccionado={seleccionado ?? ""}>
      {puntos.map((p) => (
        <button key={p.id} type="button" data-color={p.variableColor} onClick={() => alSeleccionar(p.id)}>
          punto {p.nombre}: {p.etiqueta}
        </button>
      ))}
    </div>
  ),
}));

import { pedir, restaurarSesion, salir } from "../api.js";
import App from "../App.jsx";

const geo = { type: "MultiPolygon", coordinates: [[[[0, 0], [1, 0], [1, 1], [0, 0]]]] };
const zona = (id, nombre, dep) => ({ municipio_id: id, municipio: nombre, departamento_id: 1, departamento: dep, centroide: { lat: -10, lon: -65 }, geometria: geo });

const CASOS = [
  { ...zona(1, "GUAYARAMERIN", "BENI"), enfermedad_id: 2, enfermedad: "malaria", granularidad: "acumulado", total_casos: 293, desde: "2026-03-29", hasta: "2026-03-29", registros: 1, fuente: "Boletín N.º 13" },
  { ...zona(2, "IXIAMAS", "LA PAZ"), enfermedad_id: 2, enfermedad: "malaria", granularidad: "acumulado", total_casos: 156, desde: "2026-03-29", hasta: "2026-03-29", registros: 1, fuente: "Boletín N.º 13" },
  { ...zona(3, "SAN BUENAVENTURA", "LA PAZ"), enfermedad_id: 2, enfermedad: "malaria", granularidad: "acumulado", total_casos: 1, desde: "2026-03-29", hasta: "2026-03-29", registros: 1, fuente: "Boletín N.º 13" },
  { ...zona(1, "GUAYARAMERIN", "BENI"), enfermedad_id: 1, enfermedad: "dengue", granularidad: "semanal", total_casos: 9, desde: "2026-01-04", hasta: "2026-03-29", registros: 13, fuente: "Boletín N.º 13 (serie semanal)" },
];
const RIESGO = [
  { ...zona(1, "GUAYARAMERIN", "BENI"), enfermedad_id: 1, enfermedad: "dengue", nivel_riesgo: "medio", probabilidad_pct: 44.39, nivel_confianza: "alto", fecha_generacion: "2026-10-26T12:00:00Z", fecha_estimada_riesgo: "2026-11-16" },
  { ...zona(2, "IXIAMAS", "LA PAZ"), enfermedad_id: 1, enfermedad: "dengue", nivel_riesgo: "bajo", probabilidad_pct: 15.46, nivel_confianza: "alto", fecha_generacion: "2026-10-26T12:00:00Z", fecha_estimada_riesgo: "2026-11-16" },
];
const prediccion = (vista) => ({
  vista, municipio_id: 1, municipio: "GUAYARAMERIN", departamento_id: 1, departamento: "BENI",
  predicciones: [{
    enfermedad_id: 1, enfermedad: "dengue", nivel_riesgo: "medio", probabilidad_pct: 44.39, nivel_confianza: "alto",
    fecha_generacion: "2026-10-26T12:00:00Z", fecha_estimada_riesgo: "2026-11-16",
    ...(vista === "completa" ? {
      prediccion_id: 5, modelo_id: 1, modelo_nombre: "xgboost_baseline_dengue_t3", modelo_version: "v1",
      variables_explicativas: [
        { variable: "precipitacion_total_mm_lag2", peso: 0.4 },
        { variable: "temperatura_media_media_movil_4sem", peso: -0.29 },
      ],
    } : {}),
  }],
});

function simular({ rol = "epidemiologo", alertas = [], fallo = null } = {}) {
  restaurarSesion.mockResolvedValue({ id: 1, rol });
  pedir.mockImplementation(async (ruta) => {
    if (fallo && ruta === fallo.ruta) throw fallo.error;
    if (ruta === "/casos/resumen") return CASOS;
    if (ruta === "/zonas/riesgo") return RIESGO;
    if (ruta === "/alertas") return alertas;
    if (ruta === "/zonas/1/prediccion") return prediccion(["epidemiologo", "admin"].includes(rol) ? "completa" : "resumida");
    if (ruta === "/zonas/1/historial") return { predicciones: [], brotes_confirmados: [], ventana_correlacion_dias: 7 };
    throw new Error(`ruta no simulada: ${ruta}`);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
});

describe("vista de malaria (la de entrada)", () => {
  it("abre en malaria con los casos observados y sin inventar predicciones", async () => {
    simular();
    render(<App />);

    expect(await screen.findByText("450")).toBeInTheDocument(); // 293 + 156 + 1
    expect(screen.getByRole("radio", { name: "Malaria" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("No hay predicción de malaria")).toBeInTheDocument();
    expect(screen.getByText("Guayaramerín")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^punto / })).toHaveLength(3);
    expect(pedir).not.toHaveBeenCalledWith("/zonas/1/prediccion", expect.anything());
  });

  it("al elegir una zona muestra su detalle y su porcentaje de la zona piloto", async () => {
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    const detalle = (await screen.findByRole("heading", { name: "Guayaramerín" })).closest(".detalle");
    expect(within(detalle).getByText("293")).toBeInTheDocument();
    expect(within(detalle).getByText("65 %")).toBeInTheDocument(); // 293 de 450
  });

  it("sin casos de malaria dice que todavía no hay, sin cifras", async () => {
    simular();
    pedir.mockImplementation(async (ruta) => (ruta === "/casos/resumen" ? [] : ruta === "/zonas/riesgo" ? [] : []));
    render(<App />);
    expect(await screen.findByText("Todavía no hay casos de malaria")).toBeInTheDocument();
  });
});

describe("vista de dengue", () => {
  it("al cambiar de enfermedad muestra el riesgo y lo recuerda", async () => {
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));

    expect((await screen.findAllByText("44 %")).length).toBeGreaterThanOrEqual(1); // cifra principal y fila
    expect(screen.getByText(/Una estimación exploratoria/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^punto / })[0]).toHaveAttribute("data-color", "--riesgo-medio");
    expect(window.localStorage.getItem("siptb.enfermedad")).toBe("dengue");
  });

  it("recuerda dengue en la siguiente visita", async () => {
    window.localStorage.setItem("siptb.enfermedad", "dengue");
    simular();
    render(<App />);
    expect(await screen.findByText(/predicción a 3 semanas/i)).toBeInTheDocument();
  });

  it("el epidemiólogo ve las variables que influyeron, en lenguaje claro", async () => {
    simular({ rol: "epidemiologo" });
    render(<App />);
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    expect(await screen.findByText("Qué influyó en esta predicción")).toBeInTheDocument();
    expect(screen.getByText("Precipitación, hace 2 semanas")).toBeInTheDocument();
    expect(screen.getByText("Temperatura media, promedio de 4 semanas")).toBeInTheDocument();
    expect(screen.getByText(/Casos de dengue observados/)).toHaveTextContent("9");
  });

  it("la autoridad ve el resumen y la invitación a pedir el detalle técnico", async () => {
    simular({ rol: "autoridad" });
    render(<App />);
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    expect(await screen.findByText(/disponible para epidemiólogos/)).toBeInTheDocument();
    expect(screen.queryByText("Qué influyó en esta predicción")).not.toBeInTheDocument();
    expect(screen.getByText("44 %", { selector: ".valor" })).toBeInTheDocument(); // REQ-003 también aquí
  });
});

describe("vistas y permisos", () => {
  it("el historial solo aparece para epidemiólogos y administración", async () => {
    simular({ rol: "autoridad" });
    const { unmount } = render(<App />);
    await screen.findByRole("tab", { name: "Alertas" });
    expect(screen.queryByRole("tab", { name: "Historial" })).not.toBeInTheDocument();
    unmount();

    simular({ rol: "admin" });
    render(<App />);
    expect(await screen.findByRole("tab", { name: "Historial" })).toBeInTheDocument();
  });

  it("las alertas vacías explican cuándo se emite una", async () => {
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Alertas" }));
    expect(await screen.findByText("No hay alertas emitidas")).toBeInTheDocument();
  });

  it("cada alerta muestra su justificación y variables (nunca una alerta vacía)", async () => {
    simular({
      alertas: [{
        id: 1, prediccion_id: 5, municipio_id: 1, municipio: "GUAYARAMERIN", departamento_id: 1, enfermedad_id: 1,
        enfermedad: "dengue", nivel_riesgo: "alto", probabilidad_pct: 82, umbral_aplicado: 70,
        fecha_emision: "2026-10-26T12:00:00Z", justificacion: "Lluvia reciente y casos en alza.",
        variables_explicativas: [{ variable: "precipitacion_total_mm_lag2", peso: 0.4 }],
      }],
    });
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Alertas" }));

    expect(await screen.findByText("Lluvia reciente y casos en alza.")).toBeInTheDocument();
    expect(screen.getByText(/Precipitación, hace 2 semanas/)).toBeInTheDocument();
    expect(screen.getByText("82 %")).toBeInTheDocument();
  });
});

describe("errores y sesión", () => {
  it("si el servicio no está disponible lo dice, da el código de soporte y permite reintentar", async () => {
    const error = Object.assign(new Error("El servicio de datos no está disponible. Intenta de nuevo en unos segundos."), { estado: 503, requestId: "abc123" });
    simular({ fallo: { ruta: "/casos/resumen", error } });
    render(<App />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("El servicio de datos no está disponible");
    expect(alerta).toHaveTextContent("Código de soporte: abc123");

    simular(); // el servicio se recupera
    await userEvent.click(within(alerta).getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("450")).toBeInTheDocument();
  });

  it("sin sesión guardada muestra el acceso", async () => {
    restaurarSesion.mockResolvedValue(null);
    render(<App />);
    expect(await screen.findByRole("heading", { name: /Vigilancia de malaria y dengue/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });

  it("al salir cierra la sesión y vuelve al acceso", async () => {
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Salir" }));

    expect(salir).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument());
  });
});
