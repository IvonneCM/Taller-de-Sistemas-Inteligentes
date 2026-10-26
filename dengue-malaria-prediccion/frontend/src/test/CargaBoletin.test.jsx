// Datos exclusivos de tests; la aplicación solo muestra respuestas de su API.
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CargaBoletin } from "../components/CargaBoletin.jsx";
import { enviarArchivo } from "../api.js";

vi.mock("../api.js", () => ({ enviarArchivo: vi.fn() }));

const PDF = new File(["%PDF-1.4"], "SE13.pdf", { type: "application/pdf" });
function resultado(cambios = {}) {
  return {
    guardado: false, semana: 13, anio: 2026, pagina: 8,
    fuente: "Min. Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13 (serie semanal)",
    total_casos: 341, totales_semana: [], municipios_en_boletin: 28,
    municipios: [
      { municipio_id: 1, municipio: "GUAYARAMERIN", casos: 9, accion: "actualiza", boletin_anterior: 9, semanas_nuevas: 4, semanas_revisadas: 1 },
      { municipio_id: 2, municipio: "IXIAMAS", casos: 15, accion: "nuevo", boletin_anterior: null, semanas_nuevas: 13, semanas_revisadas: 0 },
    ],
    fuera_de_catalogo: ["SAN BORJA", "RIBERALTA"],
    filas_nuevas: 17, filas_actualizadas: 9,
    revisiones: [{ municipio: "GUAYARAMERIN", semana: 4, antes: 1, despues: 2 }],
    verificacion: "Las filas y columnas coinciden con los totales impresos en el boletín.",
    nota: "Las predicciones no cambian todavía.",
    ...cambios,
  };
}

async function elegirYRevisar() {
  await userEvent.upload(screen.getByLabelText("Boletín en PDF"), PDF);
  await userEvent.click(screen.getByRole("button", { name: "Revisar boletín" }));
}

beforeEach(() => vi.resetAllMocks());

describe("carga de boletines", () => {
  it("muestra hasta qué semana hay datos y no deja revisar sin archivo", () => {
    render(<CargaBoletin ultimaSemana={{ semana: 13, fecha: "2026-03-29" }} />);
    expect(screen.getByText(/semana 13/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Revisar boletín" })).toBeDisabled();
  });

  it("revisa sin guardar y guarda solo al confirmar", async () => {
    const alGuardar = vi.fn();
    enviarArchivo.mockResolvedValueOnce(resultado()).mockResolvedValueOnce(resultado({ guardado: true }));
    render(<CargaBoletin alGuardar={alGuardar} />);
    await elegirYRevisar();

    expect(enviarArchivo).toHaveBeenCalledWith("/admin/boletines/vista-previa", PDF);
    expect(await screen.findByText("Boletín de la semana 13 · 2026")).toBeInTheDocument();
    expect(screen.getByText(/coinciden con los totales impresos/)).toBeInTheDocument();
    expect(screen.getByText("Reemplaza el boletín N.º 9")).toBeInTheDocument();
    expect(screen.getByText("Se agrega")).toBeInTheDocument();
    expect(screen.getByText("1 corrección a semanas ya cargadas")).toBeInTheDocument();
    expect(screen.getByText("2 municipios del boletín no están en el catálogo y se omiten")).toBeInTheDocument();
    expect(alGuardar).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Guardar en la base" }));
    expect(enviarArchivo).toHaveBeenLastCalledWith("/admin/boletines", PDF);
    expect(await screen.findByText("Boletín guardado")).toBeInTheDocument();
    expect(screen.getByText(/17 semanas nuevas y 9 actualizadas/)).toBeInTheDocument();
    expect(alGuardar).toHaveBeenCalledTimes(1);
  });

  it("sin cambios no ofrece guardar", async () => {
    enviarArchivo.mockResolvedValueOnce(resultado({ filas_nuevas: 0, filas_actualizadas: 0 }));
    render(<CargaBoletin />);
    await elegirYRevisar();
    expect(await screen.findByText("No hay nada nuevo que guardar.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guardar en la base" })).not.toBeInTheDocument();
  });

  it("un boletín rechazado muestra el motivo del servidor", async () => {
    const error = Object.assign(new Error("El boletín de la semana 21 no trae la tabla."), { requestId: "abc123" });
    enviarArchivo.mockRejectedValueOnce(error);
    render(<CargaBoletin />);
    await elegirYRevisar();
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo usar este boletín");
    expect(screen.getByText("El boletín de la semana 21 no trae la tabla.")).toBeInTheDocument();
    expect(screen.getByText(/abc123/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Revisar boletín" })).toBeEnabled());
  });
});
