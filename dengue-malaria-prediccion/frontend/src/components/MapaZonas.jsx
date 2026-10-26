import { useEffect, useMemo, useState } from "react";
import { CircleMarker, GeoJSON, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";

const BOLIVIA = [-16.5, -64.5];

function leerColor(variable) {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim() || "#888888";
}

// Leaflet no lee variables CSS: se resuelven aquí y se recalculan si cambia el tema.
function useTema() {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const consulta = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!consulta) return undefined;
    const cambiar = () => setVersion((v) => v + 1);
    consulta.addEventListener("change", cambiar);
    return () => consulta.removeEventListener("change", cambiar);
  }, []);
  return version;
}

function Encuadre({ puntos }) {
  const mapa = useMap();
  const clave = puntos.map((p) => p.id).join(",");
  useEffect(() => {
    if (!puntos.length) return;
    const limites = L.latLngBounds(puntos.map((p) => [p.centroide.lat, p.centroide.lon]));
    for (const p of puntos) {
      for (const g of p.geometrias ?? [p.geometria]) {
        if (!g) continue;
        const cuadro = L.geoJSON({ type: "Feature", geometry: g }).getBounds();
        if (cuadro.isValid()) limites.extend(cuadro);
      }
    }
    mapa.fitBounds(limites.pad(0.08), { maxZoom: 9, animate: false });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapa, clave]);
  return null;
}

/**
 * Mapa de zonas. Cada punto: { id, nombre, centroide, geometria (o geometrias), variableColor,
 * radio, etiqueta }. Las zonas piloto son cuadrados de ~5 km (referenciales), así
 * que el dato principal se dibuja como círculo en el centroide.
 */
export function MapaZonas({ puntos, seleccionado, alSeleccionar, descripcion, leyenda = [] }) {
  const tema = useTema();
  const reducirMovimiento = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  const colores = useMemo(
    () => Object.fromEntries(puntos.map((p) => [p.id, leerColor(p.variableColor)])),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [puntos, tema],
  );
  const acento = leerColor("--acento");

  return (
    <div className="mapa-contenedor" role="region" aria-label={descripcion}>
      <MapContainer
        center={BOLIVIA} zoom={6} className="mapa" scrollWheelZoom
        zoomAnimation={!reducirMovimiento} fadeAnimation={!reducirMovimiento} markerZoomAnimation={!reducirMovimiento}
      >
        <TileLayer
          attribution="&copy; colaboradores de OpenStreetMap"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Encuadre puntos={puntos} />
        {puntos.map((p) => {
          const activo = p.id === seleccionado;
          const color = colores[p.id];
          const geometrias = p.geometrias ?? [p.geometria];
          return [
            ...geometrias.map((geometria, i) => (
              <GeoJSON
                key={`g-${p.id}-${i}-${color}-${activo}`}
                data={{ type: "Feature", geometry: geometria }}
                style={{
                  color: activo ? acento : color, weight: activo ? 4 : 2,
                  fillColor: color, fillOpacity: activo ? 0.72 : 0.5,
                }}
                eventHandlers={{ click: () => alSeleccionar(p.id) }}
              >
                <Tooltip sticky>{p.nombre} · {p.etiqueta}</Tooltip>
              </GeoJSON>
            )),
            <CircleMarker
              key={`c-${p.id}-${color}-${activo}`}
              center={[p.centroide.lat, p.centroide.lon]}
              radius={Math.max(5, p.radio * 0.6) + (activo ? 3 : 0)}
              pathOptions={{ color: activo ? acento : "#ffffff", weight: activo ? 3 : 1.5, fillColor: color, fillOpacity: 0.9 }}
              eventHandlers={{ click: () => alSeleccionar(p.id) }}
            >
              <Tooltip>{p.nombre} · {p.etiqueta}</Tooltip>
            </CircleMarker>,
          ];
        })}
      </MapContainer>
      {leyenda.length > 0 && (
        <div className="leyenda-mapa" aria-label="Leyenda del mapa">
          {leyenda.map((l) => (
            <span className="item" key={l.variable}><i style={{ background: leerColor(l.variable) }} />{l.etiqueta}</span>
          ))}
        </div>
      )}
    </div>
  );
}
