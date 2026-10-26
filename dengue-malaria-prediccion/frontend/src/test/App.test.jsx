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
const zona = (id, nombre, dep) => ({ municipio_id: id, municipio: nombre, departamento_id: dep === "BENI" ? 1 : 2, departamento: dep, centroide: { lat: -10 - id, lon: -65 }, geometria: geo });

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

const PRIORIDAD = (id, municipio, posicion, nivel, prob) => ({
  prediccion_id: 10 + posicion, municipio_id: id, municipio, departamento_id: 1, departamento: "BENI",
  enfermedad_id: 1, enfermedad: "dengue", horizonte_semanas: 3, probabilidad_pct: prob, nivel_riesgo: nivel,
  nivel_confianza: "alto", fecha_generacion: "2026-10-26T12:00:00Z", fecha_estimada_riesgo: "2026-11-16", posicion,
});
const RANKING = [PRIORIDAD(1, "GUAYARAMERIN", 1, "alto", 71.2), PRIORIDAD(2, "IXIAMAS", 2, "medio", 43.17)];
const RECURSOS = {
  ...RANKING[0], nivel_atencion: "PRIORITARIO",
  recomendaciones: ["Reforzar vigilancia epidemiológica.", "Priorizar campañas preventivas."],
  nota: "Los umbrales de riesgo y las recomendaciones son decisiones provisionales del MVP.",
};

const PANEL = {
  generado: "2026-10-26T12:00:00Z",
  alertas: { emitidas: 3, vigentes: 2 },
  dengue: {
    municipios_con_casos: 28, total_casos: 341,
    serie_semanal: [
      { fecha: "2026-03-08", semana: 10, casos: 44 }, { fecha: "2026-03-15", semana: 11, casos: 25 },
      { fecha: "2026-03-22", semana: 12, casos: 34 }, { fecha: "2026-03-29", semana: 13, casos: 5 },
    ],
    ultima_semana: { fecha: "2026-03-29", semana: 13, casos: 5 },
    semana_previa: { fecha: "2026-03-22", semana: 12, casos: 34 },
    top_municipios: [{ municipio_id: 4, municipio: "SAN BORJA", departamento: "Beni", casos: 140 }],
    riesgo: { alto: 3, medio: 8, bajo: 17, total: 28 },
    mayor_riesgo: { municipio_id: 19, municipio: "SANTA CRUZ DE LA SIERRA", departamento: "Santa Cruz", nivel_riesgo: "alto", probabilidad_pct: 83.67, fecha_estimada_riesgo: "2026-11-16" },
    mayores_riesgos: [
      { municipio_id: 19, municipio: "SANTA CRUZ DE LA SIERRA", departamento: "Santa Cruz", nivel_riesgo: "alto", probabilidad_pct: 83.67, fecha_estimada_riesgo: "2026-11-16" },
      { municipio_id: 7, municipio: "LA ASUNTA", departamento: "La Paz", nivel_riesgo: "alto", probabilidad_pct: 79.53, fecha_estimada_riesgo: "2026-11-16" },
    ],
    fecha_prediccion: "2026-10-26T12:00:00Z",
  },
  malaria: { municipios_con_casos: 21, total_casos: 1615, fecha_corte: "2026-03-29", top_municipios: [{ municipio_id: 5, municipio: "RIBERALTA", departamento: "Beni", casos: 682 }] },
  nota: "Los casos son observados; la ultima semana es provisional.",
};

/** Abre la app y pasa de Resumen (pantalla de entrada) a la pestaña Mapa. */
async function montarEnMapa() {
  render(<App />);
  await userEvent.click(await screen.findByRole("tab", { name: "Mapa" }));
}

function simular({ rol = "epidemiologo", alertas = [], fallo = null, ranking = RANKING, riesgo = RIESGO } = {}) {
  restaurarSesion.mockResolvedValue({ id: 1, rol });
  pedir.mockImplementation(async (ruta) => {
    if (fallo && ruta === fallo.ruta) throw fallo.error;
    if (ruta === "/panel/resumen") return PANEL;
    if (ruta === "/casos/resumen") return CASOS;
    if (ruta === "/zonas/riesgo") return riesgo;
    if (ruta === "/alertas") return alertas;
    if (ruta === "/campanas/priorizacion") return ranking;
    if (/^\/municipios\/\d+\/recursos$/.test(ruta)) return RECURSOS;
    if (ruta === "/zonas/1/prediccion") return prediccion(["epidemiologo", "admin"].includes(rol) ? "completa" : "resumida");
    if (ruta === "/zonas/1/historial") return { predicciones: [], brotes_confirmados: [], ventana_correlacion_dias: 7 };
    throw new Error(`ruta no simulada: ${ruta}`);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
});

describe("resumen (pantalla de entrada)", () => {
  it("abre en el resumen con alertas vigentes, indicadores y gráfico semanal", async () => {
    simular();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "2 alertas vigentes de dengue" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("341")).toBeInTheDocument();      // casos de dengue
    expect(screen.getByText("1.615")).toBeInTheDocument();    // malaria acumulada
    expect(screen.getByText("3 de 28")).toBeInTheDocument();  // zonas en riesgo alto
    expect(screen.getAllByText(/Santa Cruz de la Sierra/)[0]).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Zonas con mayor probabilidad de brote" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Casos semanales de dengue.*SE 13: 5.*provisional/ })).toBeInTheDocument();
  });

  it("marca la última semana como provisional y no la presenta como una caída", async () => {
    simular();
    render(<App />);
    await screen.findByRole("heading", { name: "2 alertas vigentes de dengue" });
    expect(screen.getByText(/Provisional: suele corregirse al alza/)).toBeInTheDocument();
  });

  it("no muestra el selector de enfermedad: el resumen incluye las dos", async () => {
    simular();
    render(<App />);
    await screen.findByRole("heading", { name: "2 alertas vigentes de dengue" });
    expect(screen.queryByRole("radio", { name: "Dengue" })).not.toBeInTheDocument();
  });

  it("los botones llevan a las alertas y al mapa", async () => {
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Ver alertas" }));
    expect(screen.getByRole("tab", { name: "Alertas" })).toHaveAttribute("aria-selected", "true");
  });

  it("si el resumen falla lo dice y el resto de la app sigue disponible", async () => {
    const error = Object.assign(new Error("El servicio de datos no está disponible."), { estado: 503, requestId: "r1" });
    simular({ fallo: { ruta: "/panel/resumen", error } });
    render(<App />);
    expect(await screen.findByText("No se pudo cargar el resumen")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Mapa" }));
    expect(await screen.findByText("450")).toBeInTheDocument();
  });

  it("una respuesta incompleta no rompe la pantalla", async () => {
    simular();
    const base = pedir.getMockImplementation();
    pedir.mockImplementation(async (ruta, ...resto) => (ruta === "/panel/resumen" ? { generado: "x" } : base(ruta, ...resto)));
    render(<App />);
    expect(await screen.findByText("El resumen no está disponible")).toBeInTheDocument();
  });
});

describe("vista de malaria", () => {
  it("abre en malaria con los casos observados y sin inventar predicciones", async () => {
    simular();
    await montarEnMapa();

    expect(await screen.findByText("450")).toBeInTheDocument(); // 293 + 156 + 1
    expect(screen.getByRole("radio", { name: "Malaria" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("No hay predicción de malaria")).toBeInTheDocument();
    expect(screen.getByText("Guayaramerín")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^punto / })).toHaveLength(3);
    expect(pedir).not.toHaveBeenCalledWith("/zonas/1/prediccion", expect.anything());
  });

  it("al elegir una zona muestra su detalle y su porcentaje de la zona piloto", async () => {
    simular();
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    const detalle = (await screen.findByRole("heading", { name: "Guayaramerín" })).closest(".detalle");
    expect(within(detalle).getByText("293")).toBeInTheDocument();
    expect(within(detalle).getByText("65 %")).toBeInTheDocument(); // 293 de 450
  });

  it("sin casos de malaria dice que todavía no hay, sin cifras", async () => {
    simular();
    pedir.mockImplementation(async (ruta) => (ruta === "/casos/resumen" ? [] : ruta === "/zonas/riesgo" ? [] : []));
    await montarEnMapa();
    expect(await screen.findByText("Todavía no hay casos de malaria")).toBeInTheDocument();
  });
});

describe("vista de dengue", () => {
  it("al cambiar de enfermedad muestra el riesgo y lo recuerda", async () => {
    simular();
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));

    expect((await screen.findAllByText("44 %")).length).toBeGreaterThanOrEqual(1); // cifra principal y fila
    expect(screen.getByText(/Una estimación exploratoria/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^punto / })[0]).toHaveAttribute("data-color", "--riesgo-medio");
    expect(window.localStorage.getItem("siptb.enfermedad")).toBe("dengue");
  });

  it("recuerda dengue en la siguiente visita", async () => {
    window.localStorage.setItem("siptb.enfermedad", "dengue");
    simular();
    await montarEnMapa();
    expect(await screen.findByText(/predicción a 3 semanas/i)).toBeInTheDocument();
  });

  it("el epidemiólogo ve las variables que influyeron, en lenguaje claro", async () => {
    simular({ rol: "epidemiologo" });
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    expect(await screen.findByText("Qué influyó en esta predicción")).toBeInTheDocument();
    expect(screen.getByText("Precipitación, hace 2 semanas")).toBeInTheDocument();
    expect(screen.getByText("Temperatura media, promedio de 4 semanas")).toBeInTheDocument();
    expect(screen.getByText(/Casos de dengue observados/)).toHaveTextContent("9");
  });

  it("la autoridad ve el resumen y la invitación a pedir el detalle técnico", async () => {
    simular({ rol: "autoridad" });
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("button", { name: /^Guayaramerín/ }));

    expect(await screen.findByText(/disponible para epidemiólogos/)).toBeInTheDocument();
    expect(screen.queryByText("Qué influyó en esta predicción")).not.toBeInTheDocument();
    expect(screen.getByText("44 %", { selector: ".valor" })).toBeInTheDocument(); // REQ-003 también aquí
  });
});

describe("vistas y permisos", () => {
  it("propaga el filtro global de enfermedad al panel de alertas", async () => {
    simular(); render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Alertas" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledWith("/alertas", expect.objectContaining({ params: expect.objectContaining({ enfermedad_id: 2 }) })));
    await userEvent.click(screen.getByRole("radio", { name: "Dengue" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledWith("/alertas", expect.objectContaining({ params: expect.objectContaining({ enfermedad_id: 1 }) })));
  });

  it("propaga el filtro global al historial sin modificar sus permisos", async () => {
    simular({ rol: "admin" }); render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Historial" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledWith("/zonas/1/historial", expect.objectContaining({ params: expect.objectContaining({ enfermedad_id: 2 }) })));
    await userEvent.click(screen.getByRole("radio", { name: "Dengue" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledWith("/zonas/1/historial", expect.objectContaining({ params: expect.objectContaining({ enfermedad_id: 1 }) })));
  });

  it.each(["autoridad", "sedes", "coordinador_municipal"])("%s no consulta historial técnico", async (rol) => {
    simular({ rol }); render(<App />);
    await screen.findByRole("tab", { name: "Alertas" });
    expect(screen.queryByRole("tab", { name: "Historial" })).not.toBeInTheDocument();
    expect(pedir.mock.calls.some(([ruta]) => ruta.includes("/historial"))).toBe(false);
  });

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
    window.localStorage.setItem("siptb.enfermedad", "dengue");
    simular();
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Alertas" }));
    expect(await screen.findByText("No hay alertas emitidas")).toBeInTheDocument();
  });

  it("en malaria las alertas explican que no hay modelo y ofrecen ir a dengue", async () => {
    simular(); // malaria es la enfermedad por defecto
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Alertas" }));
    expect(await screen.findByText("La malaria todavía no tiene alertas")).toBeInTheDocument();
    expect(screen.getByText(/no hay modelo: solo existen casos acumulados/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Ver alertas de dengue" }));
    expect(await screen.findByRole("radio", { name: "Dengue" })).toHaveAttribute("aria-checked", "true");
    expect(window.localStorage.getItem("siptb.enfermedad")).toBe("dengue");
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

describe("nivel de agregación (TASK-027)", () => {
  const dengue = (id, nombre, dep, nivel, prob) => ({
    ...zona(id, nombre, dep), enfermedad_id: 1, enfermedad: "dengue", nivel_riesgo: nivel, probabilidad_pct: prob,
    nivel_confianza: "alto", fecha_generacion: "2026-10-26T12:00:00Z", fecha_estimada_riesgo: "2026-11-16",
  });
  const RIESGO_DEPTOS = [
    dengue(3, "PALOS BLANCOS", "LA PAZ", "alto", 71.0),
    dengue(1, "GUAYARAMERIN", "BENI", "medio", 44.39),
    dengue(2, "IXIAMAS", "LA PAZ", "bajo", 15.46),
  ];

  it("por defecto muestra municipios y ofrece Departamento", async () => {
    simular();
    await montarEnMapa();
    expect(await screen.findByRole("radio", { name: "Municipio" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "Departamento" })).toHaveAttribute("aria-checked", "false");
  });

  it("malaria por departamento suma los casos de sus municipios", async () => {
    simular();
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Departamento" }));

    const filas = within(await screen.findByRole("region", { name: "Departamentos" })).getAllByRole("button");
    expect(filas).toHaveLength(2);
    expect(filas[0]).toHaveTextContent("Beni");
    expect(filas[0]).toHaveTextContent("293");
    expect(filas[1]).toHaveTextContent("La Paz");
    expect(filas[1]).toHaveTextContent("157"); // 156 + 1
    expect(screen.getByText("450")).toBeInTheDocument();
    expect(screen.getByText(/No hay una cifra oficial del departamento/)).toBeInTheDocument();
    const puntos = screen.getAllByRole("button", { name: /^punto / });
    expect(puntos).toHaveLength(2); // un punto por departamento, no por municipio
  });

  it("dengue por departamento muestra el mayor riesgo entre sus municipios", async () => {
    simular({ riesgo: RIESGO_DEPTOS });
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("radio", { name: "Departamento" }));

    const filas = within(await screen.findByRole("region", { name: "Departamentos" })).getAllByRole("button");
    expect(filas[0]).toHaveTextContent("La Paz");       // 71 % de Palos Blancos
    expect(filas[0]).toHaveTextContent("71 %");
    expect(filas[0]).toHaveTextContent("Riesgo alto");
    expect(filas[1]).toHaveTextContent("Beni");
    expect(screen.getByText(/criterio de peor caso/)).toBeInTheDocument();
    expect(screen.getByText(/No es una predicción propia del departamento/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^punto / })[0]).toHaveAttribute("data-color", "--riesgo-alto");
  });

  it("al elegir un departamento lista sus municipios con su propio riesgo", async () => {
    simular({ riesgo: RIESGO_DEPTOS });
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("radio", { name: "Departamento" }));
    await userEvent.click(within(await screen.findByRole("region", { name: "Departamentos" })).getAllByRole("button")[0]);

    const lista = await screen.findByRole("list", { name: "Municipios del departamento" });
    const items = within(lista).getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Palos Blancos");
    expect(items[0]).toHaveTextContent("Riesgo alto");
    expect(items[1]).toHaveTextContent("Ixiamas");
    expect(items[1]).toHaveTextContent("Riesgo bajo");
  });

  it("volver a Municipio restablece la lista y la selección", async () => {
    simular({ riesgo: RIESGO_DEPTOS });
    await montarEnMapa();
    await userEvent.click(await screen.findByRole("radio", { name: "Dengue" }));
    await userEvent.click(await screen.findByRole("radio", { name: "Departamento" }));
    await userEvent.click(await screen.findByRole("radio", { name: "Municipio" }));
    expect((await screen.findAllByRole("button", { name: /^punto / }))).toHaveLength(3);
    expect(screen.getByTestId("mapa")).toHaveAttribute("data-seleccionado", "");
  });
});

describe("campañas y recursos (TASK-031)", () => {
  it("la pestaña Campañas solo aparece para SEDES y coordinación municipal", async () => {
    for (const [rol, aparece] of [["sedes", true], ["coordinador_municipal", true], ["autoridad", false], ["epidemiologo", false], ["admin", false]]) {
      simular({ rol });
      const { unmount } = render(<App />);
      await screen.findByRole("tab", { name: "Alertas" });
      expect(screen.queryByRole("tab", { name: "Campañas" }) !== null, rol).toBe(aparece);
      unmount();
    }
  });

  it("SEDES ve el orden de prioridad, sin recomendaciones por municipio", async () => {
    simular({ rol: "sedes" });
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Campañas" }));

    const lista = await screen.findByRole("list");
    const filas = within(lista).getAllByRole("listitem");
    expect(filas).toHaveLength(2);
    expect(filas[0]).toHaveTextContent("Guayaramerín");
    expect(filas[0]).toHaveTextContent("71 %");
    expect(filas[0]).toHaveTextContent("Riesgo alto");
    expect(within(filas[0]).getByLabelText("Posición 1")).toBeInTheDocument();
    expect(within(lista).queryByRole("button")).not.toBeInTheDocument(); // no hay acción: SEDES no consulta recursos
    expect(screen.getByText(/recomendaciones de atención por municipio las consulta la coordinación/)).toBeInTheDocument();
    expect(pedir).not.toHaveBeenCalledWith(expect.stringMatching(/recursos/), expect.anything());
    expect(screen.getByText(/no son\s+protocolos oficiales de SEDES/)).toBeInTheDocument();
  });

  it("la coordinación municipal ve las recomendaciones de su municipio", async () => {
    simular({ rol: "coordinador_municipal", ranking: [RANKING[0]] });
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Campañas" }));

    expect(await screen.findByText("Reforzar vigilancia epidemiológica.")).toBeInTheDocument();
    expect(screen.getByText("Priorizar campañas preventivas.")).toBeInTheDocument();
    expect(screen.getByText(/Atención prioritaria/)).toBeInTheDocument();
    expect(screen.getByText(/decisiones provisionales del MVP/)).toBeInTheDocument();
  });

  it("sin predicciones vigentes explica qué falta, sin cifras inventadas", async () => {
    simular({ rol: "sedes", ranking: [] });
    render(<App />);
    await userEvent.click(await screen.findByRole("tab", { name: "Campañas" }));
    expect(await screen.findByText("No hay zonas para priorizar")).toBeInTheDocument();
  });
});

describe("errores y sesión", () => {
  it("si el servicio no está disponible lo dice, da el código de soporte y permite reintentar", async () => {
    const error = Object.assign(new Error("El servicio de datos no está disponible. Intenta de nuevo en unos segundos."), { estado: 503, requestId: "abc123" });
    simular({ fallo: { ruta: "/casos/resumen", error } });
    await montarEnMapa();

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
