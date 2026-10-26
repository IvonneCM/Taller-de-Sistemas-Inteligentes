import { useEffect, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";

// Esqueleto de la Fase 5 (no implementa TASK-027 a 031): solo comprueba que la
// API responde y muestra un mapa base de Bolivia. Sin datos de riesgo todavia.
const API_URL = import.meta.env.VITE_API_URL ?? "/api";
const BOLIVIA = [-16.5, -64.5];

export default function App() {
  const [estado, setEstado] = useState("comprobando...");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then((d) => setEstado(d.status === "ok" ? "conectada" : "respuesta inesperada"))
      .catch(() => setEstado("sin conexión"));
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Predicción temprana de brotes de dengue y malaria</h1>
        <span>API: {estado}</span>
      </header>
      <MapContainer center={BOLIVIA} zoom={6} className="mapa">
        <TileLayer
          attribution="&copy; colaboradores de OpenStreetMap"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}
