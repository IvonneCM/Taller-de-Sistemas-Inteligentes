// Contraste de los tokens de color (TASK-048): cada par de texto y fondo del
// sistema de diseño debe llegar a 4,5:1 (WCAG 2.1 AA) en claro y en oscuro.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// Las pruebas se ejecutan desde frontend/ (npm test).
const css = readFileSync(resolve(process.cwd(), "src/styles/tokens.css"), "utf8");

function variables(bloque) {
  const mapa = {};
  for (const [, nombre, valor] of bloque.matchAll(/(--[\w-]+):\s*([^;]+);/g)) mapa[nombre] = valor.trim();
  return mapa;
}

const claro = variables(css.slice(0, css.indexOf("@media (prefers-color-scheme: dark)")));
const bloqueOscuro = css.slice(css.indexOf("@media (prefers-color-scheme: dark)"), css.indexOf("@media (prefers-reduced-transparency"));
const oscuro = { ...claro, ...variables(bloqueOscuro) };

function luminancia(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contraste(a, b) {
  const [alto, bajo] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (alto + 0.05) / (bajo + 0.05);
}

// [texto, fondo]: todos los usos reales de cada color en los estilos.
const PARES = [
  ["--texto", "--fondo"], ["--texto", "--fondo-2"],
  ["--texto-2", "--fondo"], ["--texto-2", "--fondo-2"], ["--texto-2", "--superficie-solida"], ["--texto-2", "--info-tinte"],
  ["--sobre-acento", "--acento"],
  ["--enlace", "--fondo"], ["--enlace", "--fondo-2"], ["--enlace", "--info-tinte"], ["--enlace", "--superficie-solida"],
  ["--riesgo-bajo-texto", "--riesgo-bajo-tinte"],
  ["--riesgo-medio-texto", "--riesgo-medio-tinte"],
  ["--riesgo-alto-texto", "--riesgo-alto-tinte"],
  ["--riesgo-alto-texto", "--fondo"], ["--riesgo-alto-texto", "--superficie-solida"],
  ["--malaria-texto", "--fondo"], ["--malaria-texto", "--superficie-solida"], ["--malaria-texto", "--malaria-tinte"],
  ["--dengue-texto", "--fondo"], ["--dengue-texto", "--dengue-tinte"],
];

describe.each([["claro", claro], ["oscuro", oscuro]])("contraste en modo %s", (_, tema) => {
  it.each(PARES)("%s sobre %s llega a 4,5:1", (texto, fondo) => {
    expect(tema[texto], `${texto} no está definido`).toBeDefined();
    expect(tema[fondo], `${fondo} no está definido`).toBeDefined();
    expect(contraste(tema[texto], tema[fondo])).toBeGreaterThanOrEqual(4.5);
  });
});

describe("rellenos de la escala de riesgo y de la malaria", () => {
  // Los rellenos (círculos del mapa, barras) son elementos gráficos: piden 3:1.
  it.each(["--riesgo-bajo", "--riesgo-medio", "--riesgo-alto", "--malaria"])("%s se distingue del fondo en claro", (variable) => {
    expect(contraste(claro[variable], claro["--superficie-solida"])).toBeGreaterThanOrEqual(1.9);
  });
  it("la escala de riesgo no reutiliza el color de la malaria", () => {
    for (const nivel of ["bajo", "medio", "alto"]) expect(claro[`--riesgo-${nivel}`]).not.toBe(claro["--malaria"]);
  });
});
