// Formato y etiquetas en español para mostrar datos de la API.

// La base guarda los municipios en MAYÚSCULAS y sin tildes.
const NOMBRES = {
  GUAYARAMERIN: "Guayaramerín",
  IXIAMAS: "Ixiamas",
  "PALOS BLANCOS": "Palos Blancos",
  "SAN BUENAVENTURA": "San Buenaventura",
};

export function nombreZona(nombre) {
  if (!nombre) return "";
  if (NOMBRES[nombre]) return NOMBRES[nombre];
  return nombre.toLowerCase().replace(/(^|\s)\S/g, (c) => c.toUpperCase());
}

export const ROLES = {
  autoridad: "Autoridad de salud",
  sedes: "SEDES",
  epidemiologo: "Epidemiólogo/a",
  coordinador_municipal: "Coordinación municipal",
  admin: "Administración",
};

export const etiquetaRol = (rol) => ROLES[rol] ?? rol;

// Solo para decidir qué sugerir en pantalla; el servidor decide qué devuelve.
export const esTecnico = (rol) => rol === "epidemiologo" || rol === "admin";

const entero = new Intl.NumberFormat("es-BO");
export const formatearEntero = (n) => entero.format(n);
export const formatearPorcentaje = (n) => `${Math.round(Number(n))} %`;

// "2026-11-16" es una fecha sin hora: se muestra tal cual (UTC), sin correr un día.
export function fechaLarga(iso) {
  if (!iso) return "";
  const soloFecha = /^\d{4}-\d{2}-\d{2}$/.test(iso);
  const fecha = new Date(soloFecha ? `${iso}T00:00:00Z` : iso);
  return fecha.toLocaleDateString("es-BO", {
    day: "numeric", month: "long", year: "numeric",
    timeZone: soloFecha ? "UTC" : "America/La_Paz",
  });
}

export const NIVELES = { bajo: "Riesgo bajo", medio: "Riesgo medio", alto: "Riesgo alto" };
export const ORDEN_RIESGO = { alto: 0, medio: 1, bajo: 2 };

const FACTORES = {
  casos_dengue: "Casos de dengue",
  temperatura_media: "Temperatura media",
  humedad_media: "Humedad",
  precipitacion_total_mm: "Precipitación",
};

/** "precipitacion_total_mm_lag2" -> "Precipitación, hace 2 semanas". */
export function etiquetaVariable(nombre) {
  const coincidencia = /^(.*?)_(?:lag(\d)|media_movil_(\d)sem)$/.exec(nombre);
  if (!coincidencia) return nombre;
  const [, base, lag, ventana] = coincidencia;
  const factor = FACTORES[base] ?? base;
  return lag ? `${factor}, hace ${lag} semanas` : `${factor}, promedio de ${ventana} semanas`;
}
