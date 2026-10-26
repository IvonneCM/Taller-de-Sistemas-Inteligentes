// Datos exclusivos de tests; la aplicación solo muestra respuestas de su API.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Alertas } from "../components/Alertas.jsx";
import { pedir } from "../api.js";

vi.mock("../api.js", () => ({ pedir: vi.fn() }));
const zonas = [
  { municipio_id: 10, municipio: "GUAYARAMERIN", enfermedad: "dengue", enfermedad_id: 7 },
  { municipio_id: 20, municipio: "IXIAMAS", enfermedad: "dengue", enfermedad_id: 7 },
];
function alerta(id = 1, cambios = {}) {
  return {
    id, municipio: "GUAYARAMERIN", enfermedad: "dengue", nivel_riesgo: "alto",
    probabilidad_pct: 80, umbral_aplicado: 70, fecha_emision: "2026-01-20T12:00:00Z",
    fecha_estimada_riesgo: "2026-02-10",
    justificacion: `Justificación de prueba ${id}`,
    variables_explicativas: [{ variable: "temperatura_media_lag2", peso: 0.4 }, { variable: "humedad_media_lag3", peso: -0.2 }],
    ...cambios,
  };
}
const montar = (props = {}) => render(<Alertas zonas={zonas} enfermedad="dengue" {...props} />);
beforeEach(() => { vi.resetAllMocks(); pedir.mockResolvedValue([alerta()]); });

describe("TASK-030", () => {
  it("muestra tarjetas, justificación, umbral, variables y pesos con signo", async () => {
    montar();
    expect(await screen.findByRole("article")).toHaveTextContent("Guayaramerín");
    expect(screen.getByText("Justificación de prueba 1")).toBeInTheDocument();
    expect(screen.getByText("80 %")).toBeInTheDocument();
    expect(screen.getByText(/70 %/)).toBeInTheDocument();
    expect(screen.getByText("Temperatura media, hace 2 semanas")).toBeInTheDocument();
    expect(screen.getByText(/\+0[.,]4000/)).toBeInTheDocument();
    expect(screen.getByText(/-0[.,]2000/)).toBeInTheDocument();
    expect(screen.getByText(/SHAP están en log-odds/)).toBeInTheDocument();
    expect(screen.getByText(/No son porcentajes ni demuestran causalidad/)).toBeInTheDocument();
  });

  it("ordena por emisión descendente y después por ID descendente", async () => {
    pedir.mockResolvedValue([alerta(1), alerta(2, { fecha_emision: "2026-01-25T12:00:00Z" }), alerta(3)]);
    montar();
    await screen.findAllByRole("article");
    expect(screen.getAllByRole("article").map((e) => within(e).getByText(/Justificación/).textContent))
      .toEqual(["Justificación de prueba 2", "Justificación de prueba 3", "Justificación de prueba 1"]);
  });

  it("envía enfermedad y municipio sin IDs hardcodeados", async () => {
    montar(); await screen.findByRole("article");
    await userEvent.selectOptions(screen.getByLabelText("Municipio"), "20");
    await waitFor(() => expect(pedir).toHaveBeenLastCalledWith("/alertas", { params: {
      enfermedad_id: 7, municipio_id: "20", desde: "", hasta: "", limite: 50, desplazamiento: 0, solo_vigentes: false,
    } }));
  });

  it("aplica fechas de emisión y bloquea rangos invertidos", async () => {
    montar(); await screen.findByRole("article");
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "2026-02-01" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "2026-01-01" } });
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    expect(pedir).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent("La fecha inicial no puede ser posterior");
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "2026-03-01" } });
    await userEvent.click(screen.getByRole("button", { name: "Aplicar fechas" }));
    await waitFor(() => expect(pedir.mock.lastCall[1].params).toMatchObject({ desde: "2026-02-01", hasta: "2026-03-01" }));
  });

  it("consulta páginas posteriores a las primeras 50 y permite retroceder", async () => {
    pedir.mockImplementation(async (_, { params }) => params.desplazamiento ? [alerta(51)] : Array.from({ length: 50 }, (_, i) => alerta(i+1)));
    montar(); await screen.findAllByRole("article");
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(await screen.findByText("Justificación de prueba 51")).toBeInTheDocument();
    expect(pedir.mock.lastCall[1].params.desplazamiento).toBe(50);
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Anterior" }));
    await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(50));
    expect(pedir.mock.lastCall[1].params.desplazamiento).toBe(0);
  });

  it("reinicia la página al cambiar municipio", async () => {
    pedir.mockResolvedValue(Array.from({ length: 50 }, (_, i) => alerta(i+1)));
    montar(); await screen.findAllByRole("article");
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    await waitFor(() => expect(pedir.mock.lastCall[1].params.desplazamiento).toBe(50));
    await userEvent.selectOptions(screen.getByLabelText("Municipio"), "20");
    await waitFor(() => expect(pedir.mock.lastCall[1].params).toMatchObject({ municipio_id: "20", desplazamiento: 0 }));
  });

  it("permite volver si la página posterior a una completa está vacía", async () => {
    pedir.mockResolvedValueOnce(Array.from({ length: 50 }, (_, i) => alerta(i+1))).mockResolvedValueOnce([]);
    montar(); await screen.findAllByRole("article");
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(await screen.findByText("No hay más alertas en esta página")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeEnabled();
    expect(screen.getByText(/El servidor no informa el total/)).toBeInTheDocument();
  });

  it("presenta vacío sin afirmar que no hay riesgo", async () => {
    pedir.mockResolvedValue([]); montar();
    expect(await screen.findByText("No hay alertas emitidas")).toBeInTheDocument();
    expect(screen.getByText(/No significa que no exista riesgo/)).toBeInTheDocument();
  });

  it("muestra error y reintenta", async () => {
    pedir.mockRejectedValueOnce(new Error("Error de consulta")); montar();
    expect(await screen.findByRole("alert")).toHaveTextContent("Error de consulta");
    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("article")).toBeInTheDocument();
  });

  it("conserva carga y no inventa estado activo o resuelto", async () => {
    pedir.mockReturnValueOnce(new Promise(() => {}));
    const { unmount } = montar();
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    unmount(); pedir.mockResolvedValue([alerta()]); montar();
    await screen.findByRole("article");
    expect(screen.getByText(/No significa pendiente de atención ni no resuelta/)).toBeInTheDocument();
    expect(screen.queryByText(/^Activa$|^Resuelta$|^Vencida$/i)).not.toBeInTheDocument();
  });

  it("muestra todas las variables, incluido peso cero, sin convertir a porcentaje", async () => {
    pedir.mockResolvedValue([alerta(1, { variables_explicativas: [{ variable: "a", peso: 0 }, { variable: "b", peso: -1 }, { variable: "c", peso: 1 }, { variable: "d", peso: 0.1 }] })]);
    montar(); await screen.findByRole("article");
    expect(within(screen.getByRole("list", { name: "Variables explicativas de la alerta 1" })).getAllByRole("listitem")).toHaveLength(4);
    expect(screen.getByText(/\+0[.,]0000/)).toBeInTheDocument();
  });

  it("no consulta sin un ID de enfermedad verificable", () => {
    montar({ enfermedad: "malaria" });
    expect(pedir).not.toHaveBeenCalled();
    expect(screen.getByText(/No se consultan alertas de otra enfermedad/)).toBeInTheDocument();
  });

  it("conserva todas las emitidas por defecto y usa el filtro real al seleccionar vigentes", async () => {
    montar(); await screen.findByRole("article");
    expect(screen.getByLabelText("Mostrar alertas")).toHaveValue("false");
    expect(pedir.mock.lastCall[1].params.solo_vigentes).toBe(false);
    await userEvent.selectOptions(screen.getByLabelText("Mostrar alertas"), "true");
    await waitFor(() => expect(pedir.mock.lastCall[1].params.solo_vigentes).toBe(true));
    expect(pedir.mock.lastCall[1].params.desplazamiento).toBe(0);
  });

  it("muestra la fecha objetivo proporcionada y no inventa fecha si falta", async () => {
    pedir.mockResolvedValue([alerta(1), alerta(2, { fecha_estimada_riesgo: undefined })]);
    montar(); await screen.findAllByRole("article");
    expect(screen.getByText(/Fecha estimada de riesgo: .*febrero/)).toBeInTheDocument();
    expect(screen.getByText("Fecha estimada de riesgo: No informada.")).toBeInTheDocument();
  });

  it("reinicia paginación al cambiar vigencia y conserva el filtro al avanzar", async () => {
    pedir.mockResolvedValue(Array.from({ length: 50 }, (_, i) => alerta(i+1)));
    montar(); await screen.findAllByRole("article");
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    await waitFor(() => expect(pedir.mock.lastCall[1].params.desplazamiento).toBe(50));
    await userEvent.selectOptions(screen.getByLabelText("Mostrar alertas"), "true");
    await waitFor(() => expect(pedir.mock.lastCall[1].params).toMatchObject({ solo_vigentes: true, desplazamiento: 0 }));
    await screen.findAllByRole("article");
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    await waitFor(() => expect(pedir.mock.lastCall[1].params).toMatchObject({ solo_vigentes: true, desplazamiento: 50 }));
  });
});
