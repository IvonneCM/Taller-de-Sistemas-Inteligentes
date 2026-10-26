import { useCallback } from "react";
import { pedir } from "../api.js";
import { etiquetaVariable, fechaLarga, formatearPorcentaje, nombreZona } from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Campana } from "./Iconos.jsx";
import { Insignia } from "./PanelDengue.jsx";

/** Alertas emitidas (TASK-030, REQ-009). Cada una trae su justificación (REQ-005). */
export function Alertas() {
  const cargar = useCallback(() => pedir("/alertas", { params: { limite: 50 } }), []);
  const carga = useCarga(cargar, []);

  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando alertas" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudieron cargar las alertas" />;

  if (!carga.datos.length) {
    return (
      <div className="pagina-estrecha aparece">
        <Vacio titulo="No hay alertas emitidas" icono={<Campana />}>
          Se emite una alerta cuando la probabilidad de brote de una zona supera el umbral
          configurado y el modelo puede explicar qué variables la justifican.
        </Vacio>
      </div>
    );
  }

  return (
    <section className="tarjetas aparece" aria-label="Alertas">
      {carga.datos.map((alerta) => (
        <article className="tarjeta alerta" key={alerta.id}>
          <div className="alerta-cabecera">
            <div>
              <h3>{nombreZona(alerta.municipio)}</h3>
              <p className="nota"><span className="mayuscula">{alerta.enfermedad}</span> · emitida el {fechaLarga(alerta.fecha_emision)}</p>
            </div>
            <Insignia nivel={alerta.nivel_riesgo} />
          </div>
          <p className="fila-texto">
            Probabilidad de <strong>{formatearPorcentaje(alerta.probabilidad_pct)}</strong>, sobre el
            umbral de {formatearPorcentaje(alerta.umbral_aplicado)}.
          </p>
          <p className="fila-texto">{alerta.justificacion}</p>
          <p className="nota">
            Variables: {alerta.variables_explicativas.slice(0, 3).map((v) => etiquetaVariable(v.variable)).join(" · ")}
          </p>
        </article>
      ))}
    </section>
  );
}
