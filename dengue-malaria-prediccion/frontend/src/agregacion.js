// Agregación por departamento (TASK-027, REQ-006).
//
// En el modelo de datos la "zona" es el municipio (design.md §3: `municipios`
// es la zona geográfica base), así que el selector ofrece Municipio y
// Departamento. La agregación es solo de visualización y NO crea predicciones:
//  - riesgo (dengue): se muestra el MAYOR riesgo y la MAYOR probabilidad entre
//    los municipios del departamento (criterio conservador, "peor caso");
//  - casos (malaria): suma de los casos observados de sus municipios.

export const ORDEN_RIESGO = { alto: 0, medio: 1, bajo: 2 };

function promedioCentroide(items) {
  const n = items.length;
  return {
    lat: items.reduce((s, i) => s + i.centroide.lat, 0) / n,
    lon: items.reduce((s, i) => s + i.centroide.lon, 0) / n,
  };
}

function agrupar(items) {
  const grupos = new Map();
  for (const item of items) {
    if (!grupos.has(item.departamento_id)) grupos.set(item.departamento_id, []);
    grupos.get(item.departamento_id).push(item);
  }
  return [...grupos].map(([id, municipios]) => ({
    id,
    nombre: municipios[0].departamento,
    centroide: promedioCentroide(municipios),
    geometrias: municipios.map((m) => m.geometria),
    n: municipios.length,
    municipios,
  }));
}

/** Zonas de dengue de /zonas/riesgo -> departamentos, de mayor a menor riesgo. */
export function agruparRiesgoPorDepartamento(zonas) {
  return agrupar(zonas)
    .map((d) => {
      const municipios = [...d.municipios].sort(
        (a, b) => ORDEN_RIESGO[a.nivel_riesgo] - ORDEN_RIESGO[b.nivel_riesgo]
          || Number(b.probabilidad_pct) - Number(a.probabilidad_pct),
      );
      return {
        ...d,
        municipios,
        nivel_riesgo: municipios[0].nivel_riesgo,
        probabilidad_pct: Math.max(...municipios.map((m) => Number(m.probabilidad_pct))),
      };
    })
    .sort((a, b) => ORDEN_RIESGO[a.nivel_riesgo] - ORDEN_RIESGO[b.nivel_riesgo]
      || b.probabilidad_pct - a.probabilidad_pct || a.nombre.localeCompare(b.nombre));
}

/** Casos observados de /casos/resumen (una enfermedad) -> departamentos, de más a menos casos. */
export function agruparCasosPorDepartamento(casos) {
  return agrupar(casos)
    .map((d) => ({
      ...d,
      municipios: [...d.municipios].sort((a, b) => b.total_casos - a.total_casos),
      total_casos: d.municipios.reduce((s, m) => s + m.total_casos, 0),
    }))
    .sort((a, b) => b.total_casos - a.total_casos || a.nombre.localeCompare(b.nombre));
}
