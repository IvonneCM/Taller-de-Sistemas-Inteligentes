import { describe, expect, it } from "vitest";
import { agruparCasosPorDepartamento, agruparRiesgoPorDepartamento } from "../agregacion.js";

const geo = (n) => ({ type: "MultiPolygon", coordinates: [[[[n, 0], [n + 1, 0], [n + 1, 1], [n, 0]]]] });
const zona = (id, depId, dep, nivel, prob, lat, lon) => ({
  municipio_id: id, municipio: `M${id}`, departamento_id: depId, departamento: dep,
  nivel_riesgo: nivel, probabilidad_pct: prob, centroide: { lat, lon }, geometria: geo(id),
});

describe("agruparRiesgoPorDepartamento", () => {
  const zonas = [
    zona(1, 10, "BENI", "medio", 44.39, -10, -65),
    zona(2, 20, "LA PAZ", "bajo", 15.46, -13, -68),
    zona(3, 20, "LA PAZ", "alto", "71.20", -15, -67),
  ];

  it("toma el mayor riesgo y la mayor probabilidad entre los municipios", () => {
    const [primero, segundo] = agruparRiesgoPorDepartamento(zonas);
    expect(primero).toMatchObject({ id: 20, nombre: "LA PAZ", nivel_riesgo: "alto", probabilidad_pct: 71.2, n: 2 });
    expect(segundo).toMatchObject({ id: 10, nivel_riesgo: "medio", probabilidad_pct: 44.39, n: 1 });
  });

  it("ordena los municipios de cada departamento de mayor a menor riesgo", () => {
    const [laPaz] = agruparRiesgoPorDepartamento(zonas);
    expect(laPaz.municipios.map((m) => m.municipio_id)).toEqual([3, 2]);
  });

  it("el centroide es el promedio de los de sus municipios y conserva todas las geometrías", () => {
    const [laPaz] = agruparRiesgoPorDepartamento(zonas);
    expect(laPaz.centroide).toEqual({ lat: -14, lon: -67.5 });
    expect(laPaz.geometrias).toHaveLength(2);
  });

  it("no inventa nada: sin zonas devuelve una lista vacía", () => {
    expect(agruparRiesgoPorDepartamento([])).toEqual([]);
  });

  it("con probabilidades iguales desempata por nombre, de forma estable", () => {
    const iguales = [zona(1, 1, "SANTA CRUZ", "bajo", 10, 0, 0), zona(2, 2, "BENI", "bajo", 10, 0, 0)];
    expect(agruparRiesgoPorDepartamento(iguales).map((d) => d.nombre)).toEqual(["BENI", "SANTA CRUZ"]);
  });
});

describe("agruparCasosPorDepartamento", () => {
  const casos = [
    { ...zona(1, 10, "BENI", null, null, -10, -65), total_casos: 293 },
    { ...zona(2, 20, "LA PAZ", null, null, -13, -68), total_casos: 156 },
    { ...zona(3, 20, "LA PAZ", null, null, -15, -67), total_casos: 1 },
  ];

  it("suma los casos observados de los municipios", () => {
    const deptos = agruparCasosPorDepartamento(casos);
    expect(deptos.map((d) => [d.nombre, d.total_casos])).toEqual([["BENI", 293], ["LA PAZ", 157]]);
    expect(deptos.reduce((s, d) => s + d.total_casos, 0)).toBe(450); // coincide con el total general
  });

  it("ordena los municipios de más a menos casos", () => {
    const laPaz = agruparCasosPorDepartamento(casos).find((d) => d.id === 20);
    expect(laPaz.municipios.map((m) => m.total_casos)).toEqual([156, 1]);
  });
});
