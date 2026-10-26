import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api.js", () => ({
  entrar: vi.fn(),
  restaurarSesion: vi.fn().mockResolvedValue(null),
  alCambiarSesion: vi.fn(() => () => {}),
  salir: vi.fn(),
  usuarioDelToken: vi.fn(() => ({ id: 1, rol: "autoridad" })),
}));

import { entrar } from "../api.js";
import { ProveedorSesion } from "../auth.jsx";
import { Acceso, validarClave, validarCorreo } from "../components/Acceso.jsx";

function pantalla() {
  return render(<ProveedorSesion><Acceso /></ProveedorSesion>);
}

beforeEach(() => vi.clearAllMocks());

describe("validación", () => {
  it("correo: vacío, mal formado y correcto", () => {
    expect(validarCorreo("  ")).toMatch(/Escribe tu correo/);
    expect(validarCorreo("sin-arroba")).toMatch(/falta algo/);
    expect(validarCorreo("a@b")).toMatch(/falta algo/);
    expect(validarCorreo(" a@demo.local ")).toBeNull();
  });
  it("contraseña vacía", () => {
    expect(validarClave("")).toMatch(/Escribe tu contraseña/);
    expect(validarClave("x")).toBeNull();
  });
});

describe("pantalla de acceso", () => {
  it("expone etiquetas, autocompletado y un único botón principal", () => {
    pantalla();
    expect(screen.getByLabelText("Correo")).toHaveAttribute("autocomplete", "username");
    expect(screen.getByLabelText("Contraseña")).toHaveAttribute("autocomplete", "current-password");
    expect(screen.getByLabelText("Contraseña")).toHaveAttribute("type", "password");
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("al enviar vacío muestra los errores en línea y no llama a la API", async () => {
    pantalla();
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Escribe tu correo.")).toBeInTheDocument();
    expect(screen.getByText("Escribe tu contraseña.")).toBeInTheDocument();
    expect(screen.getByLabelText("Correo")).toHaveAttribute("aria-invalid", "true");
    expect(entrar).not.toHaveBeenCalled();
  });

  it("valida el correo al salir del campo", async () => {
    pantalla();
    await userEvent.type(screen.getByLabelText("Correo"), "no-es-un-correo");
    await userEvent.tab();
    expect(await screen.findByText(/falta algo/)).toBeInTheDocument();
  });

  it("con credenciales incorrectas muestra el error y permite reintentar", async () => {
    entrar.mockRejectedValueOnce(new Error("Correo o contraseña incorrectos."));
    pantalla();
    await userEvent.type(screen.getByLabelText("Correo"), "a@demo.local");
    await userEvent.type(screen.getByLabelText("Contraseña"), "mala");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Correo o contraseña incorrectos.");
    expect(screen.getByRole("button", { name: "Entrar" })).toBeEnabled();
  });

  it("mientras entra deshabilita el formulario para no enviar dos veces", async () => {
    let resolver;
    entrar.mockReturnValueOnce(new Promise((r) => { resolver = r; }));
    pantalla();
    await userEvent.type(screen.getByLabelText("Correo"), "a@demo.local");
    await userEvent.type(screen.getByLabelText("Contraseña"), "clave");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("button", { name: "Entrando…" })).toBeDisabled();
    expect(screen.getByLabelText("Correo")).toBeDisabled();
    resolver({ id: 1, rol: "autoridad" });
    await waitFor(() => expect(entrar).toHaveBeenCalledTimes(1));
  });

  it("envía el correo sin espacios sobrantes", async () => {
    entrar.mockResolvedValueOnce({ id: 1, rol: "autoridad" });
    pantalla();
    await userEvent.type(screen.getByLabelText("Correo"), "  a@demo.local  ");
    await userEvent.type(screen.getByLabelText("Contraseña"), "clave");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    await waitFor(() => expect(entrar).toHaveBeenCalledWith("a@demo.local", "clave"));
  });
});
