import { describe, expect, it } from "vitest";
import {
  esTecnico, etiquetaRol, etiquetaVariable, fechaLarga, formatearEntero, formatearPorcentaje, nombreZona,
} from "../format.js";

describe("nombreZona", () => {
  it("restituye las tildes de los municipios conocidos", () => {
    expect(nombreZona("GUAYARAMERIN")).toBe("Guayaramerín");
    expect(nombreZona("PALOS BLANCOS")).toBe("Palos Blancos");
  });
  it("pone en título los desconocidos y tolera vacío", () => {
    expect(nombreZona("SANTA ANA DEL YACUMA")).toBe("Santa Ana Del Yacuma");
    expect(nombreZona("")).toBe("");
    expect(nombreZona(null)).toBe("");
  });
});

describe("etiquetaVariable", () => {
  it("traduce rezagos y promedios móviles", () => {
    expect(etiquetaVariable("precipitacion_total_mm_lag2")).toBe("Precipitación, hace 2 semanas");
    expect(etiquetaVariable("humedad_media_media_movil_4sem")).toBe("Humedad, promedio de 4 semanas");
    expect(etiquetaVariable("casos_dengue_lag3")).toBe("Casos de dengue, hace 3 semanas");
  });
  it("deja intacto lo que no reconoce", () => {
    expect(etiquetaVariable("variable_rara")).toBe("variable_rara");
  });
});

describe("fechas y números", () => {
  it("una fecha sin hora no se corre de día", () => {
    expect(fechaLarga("2026-11-16")).toContain("16");
    expect(fechaLarga("2026-11-16")).toMatch(/noviembre/);
    expect(fechaLarga("2026-01-01")).toContain("1");
    expect(fechaLarga("2026-01-01")).toMatch(/enero/);
  });
  it("una fecha con hora se muestra en hora de Bolivia", () => {
    // 01:00 UTC del 27 es todavía el 26 en La Paz (UTC-4).
    expect(fechaLarga("2026-10-27T01:00:00Z")).toContain("26");
  });
  it("vacío no rompe", () => expect(fechaLarga(null)).toBe(""));
  it("formatea enteros y porcentajes", () => {
    expect(formatearPorcentaje(44.39)).toBe("44 %");
    expect(formatearPorcentaje("15.46")).toBe("15 %");
    expect(formatearEntero(293)).toBe("293");
  });
});

describe("roles", () => {
  it("etiqueta y reconoce los técnicos", () => {
    expect(etiquetaRol("epidemiologo")).toBe("Epidemiólogo/a");
    expect(etiquetaRol("otro")).toBe("otro");
    expect(esTecnico("admin")).toBe(true);
    expect(esTecnico("autoridad")).toBe(false);
  });
});
