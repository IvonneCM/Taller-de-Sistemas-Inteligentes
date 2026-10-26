// Fixtures exclusivas de pruebas; no son registros epidemiológicos reales.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Historial } from "../components/Historial.jsx";
import { pedir } from "../api.js";

vi.mock("../api.js", () => ({ pedir: vi.fn() }));
const zonas = [
  { municipio_id: 10, municipio: "GUAYARAMERIN", enfermedad: "dengue", enfermedad_id: 7 },
  { municipio_id: 20, municipio: "IXIAMAS", enfermedad: "dengue", enfermedad_id: 7 },
  { municipio_id: 10, municipio: "GUAYARAMERIN", enfermedad: "malaria", enfermedad_id: 9 },
];
const prediccion = {
  prediccion_id: 1, enfermedad: "dengue", probabilidad_pct: 80, nivel_riesgo: "alto",
  fecha_generacion: "2026-01-01T12:00:00Z", fecha_estimada_riesgo: "2026-01-22",
  brote_confirmado: true, fecha_brote_confirmado: "2026-01-23", anticipacion_dias: 22,
};
const historial = {
  predicciones: [prediccion], ventana_correlacion_dias: 7,
  brotes_confirmados: [{ id: 12, enfermedad: "dengue", fecha_confirmacion: "2026-01-23", fuente: "Fuente exclusiva de test" }],
};
const montar = (props = {}) => render(<Historial zonas={zonas} enfermedad="dengue" {...props} />);
const fechas = (desde, hasta) => {
  fireEvent.change(screen.getByLabelText("Desde"), { target: { value: desde } });
  fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: hasta } });
};
beforeEach(() => { vi.resetAllMocks(); pedir.mockResolvedValue(historial); });

describe("TASK-029", () => {
  it("muestra predicciones, probabilidad, riesgo, brotes y anticipación", async () => {
    montar();
    expect(await screen.findByRole("table", { name: "Predicciones históricas" })).toBeInTheDocument();
    expect(screen.getByText("80 %")).toBeInTheDocument();
    expect(screen.getByText("Riesgo alto")).toBeInTheDocument();
    expect(screen.getByText(/Coincidencia registrada, el/)).toBeInTheDocument();
    expect(screen.getByText("22 días entre generación y confirmación")).toBeInTheDocument();
    expect(within(screen.getByRole("table", { name: "Brotes confirmados registrados" })).getByText("Fuente exclusiva de test")).toBeInTheDocument();
    expect(screen.getByText(/coincidencia descriptiva, no una medida de precisión/)).toBeInTheDocument();
    expect(screen.queryByText(/acertada/)).not.toBeInTheDocument();
  });

  it("conserva selector y envía IDs reales de municipio y enfermedad", async () => {
    montar();
    await screen.findByText("80 %");
    await userEvent.selectOptions(screen.getByLabelText("Zona"), "20");
    await waitFor(() => expect(pedir).toHaveBeenLastCalledWith("/zonas/20/historial", {
      params: { enfermedad_id: 7, desde: "", hasta: "" },
    }));
  });

  it("aplica rango inclusivo desde/hasta mediante los parámetros soportados", async () => {
    montar();
    await screen.findByText("80 %");
    fechas("2026-01-01", "2026-02-01");
    expect(pedir).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    await waitFor(() => expect(pedir).toHaveBeenLastCalledWith("/zonas/10/historial", {
      params: { enfermedad_id: 7, desde: "2026-01-01", hasta: "2026-02-01" },
    }));
  });

  it("no consulta un rango invertido y permite corregirlo", async () => {
    montar(); await screen.findByText("80 %");
    fechas("2026-02-01", "2026-01-01");
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    expect(screen.getByRole("alert")).toHaveTextContent("La fecha inicial no puede ser posterior");
    expect(pedir).toHaveBeenCalledTimes(1);
    fechas("2026-01-01", "2026-01-01");
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledTimes(2));
  });

  it("limpia fechas sin perder municipio ni enfermedad", async () => {
    montar(); await screen.findByText("80 %");
    fechas("2026-01-01", "");
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledTimes(2));
    await userEvent.click(screen.getByRole("button", { name: "Limpiar fechas" }));
    await waitFor(() => expect(pedir).toHaveBeenLastCalledWith("/zonas/10/historial", { params: { enfermedad_id: 7, desde: "", hasta: "" } }));
  });

  it("distingue ausencia de predicciones y ausencia de registros de brotes", async () => {
    pedir.mockResolvedValue({ ...historial, predicciones: [], brotes_confirmados: [] });
    montar();
    expect(await screen.findByText("No hay predicciones en el rango consultado")).toBeInTheDocument();
    expect(screen.getByText(/La ausencia de registros no demuestra/)).toBeInTheDocument();
  });

  it("muestra brotes aunque no existan predicciones en el rango", async () => {
    pedir.mockResolvedValue({ ...historial, predicciones: [] });
    montar();
    expect(await screen.findByRole("table", { name: "Brotes confirmados registrados" })).toBeInTheDocument();
    expect(screen.getByText("No hay predicciones en el rango consultado")).toBeInTheDocument();
  });

  it("no transforma anticipación nula o negativa en eficacia predictiva", async () => {
    pedir.mockResolvedValue({ ...historial, predicciones: [
      { ...prediccion, prediccion_id: 1, anticipacion_dias: null },
      { ...prediccion, prediccion_id: 2, anticipacion_dias: -2 },
    ] });
    montar();
    expect(await screen.findByText("No disponible")).toBeInTheDocument();
    expect(screen.getByText("Confirmación 2 días antes de la generación")).toBeInTheDocument();
  });

  it("muestra errores y reintenta la misma consulta", async () => {
    pedir.mockRejectedValueOnce(new Error("Sin acceso al historial"));
    montar();
    expect(await screen.findByRole("alert")).toHaveTextContent("Sin acceso al historial");
    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("80 %")).toBeInTheDocument();
  });

  it("conserva el estado de carga", () => {
    pedir.mockReturnValue(new Promise(() => {}));
    montar();
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  });

  it("no adivina IDs cuando no hay catálogo de la enfermedad", () => {
    montar({ enfermedad: "zika" });
    expect(screen.getByText("No hay municipios disponibles para esta enfermedad")).toBeInTheDocument();
    expect(pedir).not.toHaveBeenCalled();
  });

  it("la selección de malaria conserva su ID sin solicitar dengue", async () => {
    montar({ enfermedad: "malaria" });
    await waitFor(() => expect(pedir).toHaveBeenCalledWith("/zonas/10/historial", { params: { enfermedad_id: 9, desde: "", hasta: "" } }));
  });
});
