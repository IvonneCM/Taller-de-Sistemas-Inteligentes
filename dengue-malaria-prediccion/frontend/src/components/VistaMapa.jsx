import { useEffect, useMemo, useState } from "react";
import { MapaZonas } from "./MapaZonas.jsx";
import { PanelDengue, puntosDengue } from "./PanelDengue.jsx";
import { PanelDepartamento, puntosDepartamentoDengue, puntosDepartamentoMalaria } from "./PanelDepartamento.jsx";
import { PanelMalaria, puntosMalaria } from "./PanelMalaria.jsx";
import { Segmentado } from "./Segmentado.jsx";

// En el modelo de datos la "zona" es el municipio (design.md §3), por eso solo hay dos niveles.
const NIVELES = [
  { valor: "municipio", etiqueta: "Municipio" },
  { valor: "departamento", etiqueta: "Departamento" },
];

/** Mapa y panel de la enfermedad y el nivel elegidos (TASK-027, 028). */
export function VistaMapa({ enfermedad, riesgo, casos, usuario }) {
  const [seleccionado, setSeleccionado] = useState(null);
  const [nivel, setNivel] = useState("municipio");
  useEffect(() => setSeleccionado(null), [enfermedad, nivel]);

  const esMalaria = enfermedad === "malaria";
  const porDepartamento = nivel === "departamento";
  const puntos = useMemo(() => {
    if (esMalaria) return porDepartamento ? puntosDepartamentoMalaria(casos.datos) : puntosMalaria(casos.datos);
    return porDepartamento ? puntosDepartamentoDengue(riesgo.datos) : puntosDengue(riesgo.datos);
  }, [esMalaria, porDepartamento, casos.datos, riesgo.datos]);

  const leyenda = esMalaria
    ? [{ variable: "--malaria", etiqueta: "Casos acumulados de malaria (el tamaño crece con los casos)" }]
    : [
        { variable: "--riesgo-alto", etiqueta: "Riesgo alto" },
        { variable: "--riesgo-medio", etiqueta: "Riesgo medio" },
        { variable: "--riesgo-bajo", etiqueta: "Riesgo bajo" },
      ];
  const unidad = porDepartamento ? "departamento" : "municipio";
  const descripcion = `Mapa de ${esMalaria ? "casos de malaria" : "riesgo de dengue"} por ${unidad}. La lista junto al mapa tiene la misma información.`;

  return (
    <>
      <div className="vistas">
        <Segmentado etiqueta="Nivel de agregación" opciones={NIVELES} valor={nivel} alCambiar={setNivel} />
      </div>
      <div className="mapa-y-panel">
        <MapaZonas puntos={puntos} seleccionado={seleccionado} alSeleccionar={setSeleccionado} descripcion={descripcion} leyenda={leyenda} />
        {porDepartamento
          ? <PanelDepartamento tipo={esMalaria ? "malaria" : "dengue"} carga={esMalaria ? casos : riesgo} seleccionado={seleccionado} alSeleccionar={setSeleccionado} />
          : esMalaria
            ? <PanelMalaria carga={casos} seleccionado={seleccionado} alSeleccionar={setSeleccionado} />
            : <PanelDengue carga={riesgo} casos={casos.datos} usuario={usuario} seleccionado={seleccionado} alSeleccionar={setSeleccionado} />}
      </div>
    </>
  );
}
