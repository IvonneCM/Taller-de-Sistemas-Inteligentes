/** IDs reales del backend; nunca se supone dengue=1. */
export function catalogoPanel(zonas, enfermedad) {
  const filas = (zonas ?? []).filter((z) => z.enfermedad === enfermedad);
  const ids = new Set(filas.map((z) => z.enfermedad_id).filter(Number.isInteger));
  const municipios = new Map(filas.map((z) => [z.municipio_id, z.municipio]));
  return {
    enfermedadId: ids.size === 1 ? [...ids][0] : null,
    municipios: [...municipios].map(([id, nombre]) => ({ id, nombre })),
  };
}
