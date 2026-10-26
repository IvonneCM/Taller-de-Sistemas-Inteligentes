import { useEffect, useMemo, useState } from "react";
import { MapaZonas } from "./MapaZonas.jsx";
import { PanelDengue, puntosDengue } from "./PanelDengue.jsx";
import { PanelMalaria, puntosMalaria } from "./PanelMalaria.jsx";

/** Mapa y panel de la enfermedad elegida (TASK-027, 028). */
export function VistaMapa({ enfermedad, riesgo, casos, usuario }) {
  const [seleccionado, setSeleccionado] = useState(null);
  useEffect(() => setSeleccionado(null), [enfermedad]);

  const esMalaria = enfermedad === "malaria";
  const puntos = useMemo(
    () => (esMalaria ? puntosMalaria(casos.datos) : puntosDengue(riesgo.datos)),
    [esMalaria, casos.datos, riesgo.datos],
  );

  return (
    <div className="mapa-y-panel">
      <MapaZonas
        puntos={puntos}
        seleccionado={seleccionado}
        alSeleccionar={setSeleccionado}
        descripcion={
          esMalaria
            ? "Mapa de casos de malaria por municipio. La lista junto al mapa tiene la misma información."
            : "Mapa de riesgo de dengue por municipio. La lista junto al mapa tiene la misma información."
        }
      />
      {esMalaria
        ? <PanelMalaria carga={casos} seleccionado={seleccionado} alSeleccionar={setSeleccionado} />
        : <PanelDengue carga={riesgo} casos={casos.datos} usuario={usuario} seleccionado={seleccionado} alSeleccionar={setSeleccionado} />}
    </div>
  );
}
