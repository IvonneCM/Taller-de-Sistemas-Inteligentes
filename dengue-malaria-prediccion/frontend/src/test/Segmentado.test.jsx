import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { Segmentado } from "../components/Segmentado.jsx";

const OPCIONES = [{ valor: "a", etiqueta: "Alfa" }, { valor: "b", etiqueta: "Beta" }, { valor: "c", etiqueta: "Gamma" }];

function Prueba({ rol }) {
  const [valor, setValor] = useState("a");
  return <Segmentado etiqueta="Prueba" opciones={OPCIONES} valor={valor} alCambiar={setValor} rol={rol} />;
}

describe("Segmentado", () => {
  it("como grupo de opciones usa radios y marca el valor", () => {
    render(<Prueba rol="radio" />);
    expect(screen.getByRole("radiogroup", { name: "Prueba" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Alfa" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "Beta" })).toHaveAttribute("aria-checked", "false");
  });

  it("como vistas usa pestañas y aria-selected", () => {
    render(<Prueba rol="tab" />);
    expect(screen.getByRole("tablist", { name: "Prueba" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Alfa" })).toHaveAttribute("aria-selected", "true");
  });

  it("solo la opción activa entra en el orden de tabulación", () => {
    render(<Prueba rol="radio" />);
    expect(screen.getByRole("radio", { name: "Alfa" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "Beta" })).toHaveAttribute("tabindex", "-1");
  });

  it("las flechas mueven la selección y el foco, dando la vuelta en los extremos", async () => {
    render(<Prueba rol="radio" />);
    screen.getByRole("radio", { name: "Alfa" }).focus();

    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("radio", { name: "Beta" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "Beta" })).toHaveFocus();

    await userEvent.keyboard("{ArrowLeft}{ArrowLeft}");
    expect(screen.getByRole("radio", { name: "Gamma" })).toHaveAttribute("aria-checked", "true");
  });

  it("un clic cambia la selección", async () => {
    render(<Prueba rol="radio" />);
    await userEvent.click(screen.getByRole("radio", { name: "Gamma" }));
    expect(screen.getByRole("radio", { name: "Gamma" })).toHaveAttribute("aria-checked", "true");
  });
});
