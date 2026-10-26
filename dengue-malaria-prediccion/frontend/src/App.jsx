import { useCallback, useState } from "react";
import { pedir } from "./api.js";
import { ProveedorSesion, useSesion } from "./auth.jsx";
import { esTecnico } from "./format.js";
import { useCarga } from "./useCarga.js";
import { Acceso } from "./components/Acceso.jsx";
import { Alertas } from "./components/Alertas.jsx";
import { Barra } from "./components/Barra.jsx";
import { Cargando } from "./components/Estado.jsx";
import { Historial } from "./components/Historial.jsx";
import { Segmentado } from "./components/Segmentado.jsx";
import { VistaMapa } from "./components/VistaMapa.jsx";

const CLAVE_ENFERMEDAD = "siptb.enfermedad";

function enfermedadInicial() {
  try {
    const guardada = window.localStorage.getItem(CLAVE_ENFERMEDAD);
    return guardada === "dengue" ? "dengue" : "malaria"; // la malaria es la entrada por defecto
  } catch {
    return "malaria";
  }
}

function Aplicacion() {
  const { usuario, cerrar } = useSesion();
  const [enfermedad, setEnfermedad] = useState(enfermedadInicial);
  const [vista, setVista] = useState("mapa");

  const riesgo = useCarga(useCallback(() => pedir("/zonas/riesgo"), []), []);
  const casos = useCarga(useCallback(() => pedir("/casos/resumen"), []), []);
  const paneles = {
    zonas: [...(riesgo.datos ?? []), ...(casos.datos ?? [])],
    enfermedad,
    cargandoZonas: riesgo.fase === "cargando" || casos.fase === "cargando",
    errorZonas: riesgo.error ?? casos.error,
    recargarZonas: () => { riesgo.recargar(); casos.recargar(); },
  };

  const elegirEnfermedad = useCallback((valor) => {
    setEnfermedad(valor);
    try { window.localStorage.setItem(CLAVE_ENFERMEDAD, valor); } catch { /* sin almacenamiento */ }
  }, []);

  const vistas = [
    { valor: "mapa", etiqueta: "Mapa" },
    { valor: "alertas", etiqueta: "Alertas" },
    ...(esTecnico(usuario.rol) ? [{ valor: "historial", etiqueta: "Historial" }] : []),
  ];

  return (
    <div className="app">
      <Barra usuario={usuario} enfermedad={enfermedad} alCambiarEnfermedad={elegirEnfermedad} alSalir={cerrar} />
      <main className="contenido">
        <div className="vistas">
          <Segmentado rol="tab" etiqueta="Vista" opciones={vistas} valor={vista} alCambiar={setVista} />
        </div>
        {vista === "mapa" && <VistaMapa enfermedad={enfermedad} riesgo={riesgo} casos={casos} usuario={usuario} />}
        {vista === "alertas" && <Alertas key={enfermedad} {...paneles} />}
        {vista === "historial" && esTecnico(usuario.rol) && <Historial key={enfermedad} {...paneles} />}
      </main>
    </div>
  );
}

function Puerta() {
  const { estado } = useSesion();
  if (estado === "cargando") return <main className="acceso"><Cargando etiqueta="Restaurando la sesión" /></main>;
  if (estado === "anonimo") return <Acceso />;
  return <Aplicacion />;
}

export default function App() {
  return (
    <ProveedorSesion>
      <Puerta />
    </ProveedorSesion>
  );
}
