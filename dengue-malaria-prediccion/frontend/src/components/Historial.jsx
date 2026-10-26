import { useCallback, useId, useState } from "react";
import { pedir } from "../api.js";
import { catalogoPanel } from "../datosPaneles.js";
import { fechaLarga, formatearPorcentaje, nombreZona } from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { FiltrosFechas } from "./FiltrosFechas.jsx";
import { Insignia } from "./PanelDengue.jsx";

function Anticipacion({ dias }) {
  if (!Number.isFinite(dias)) return "No disponible";
  return dias >= 0 ? `${dias} días entre generación y confirmación`
    : `Confirmación ${Math.abs(dias)} días antes de la generación`;
}

function TablaHistorial({ zonaId, enfermedadId, desde, hasta }) {
  const cargar = useCallback(() => pedir(`/zonas/${zonaId}/historial`, {
    params: { enfermedad_id: enfermedadId, desde, hasta },
  }), [zonaId, enfermedadId, desde, hasta]);
  const carga = useCarga(cargar, [zonaId, enfermedadId, desde, hasta]);
  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando el historial" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudo cargar el historial" />;
  const { predicciones, brotes_confirmados: brotes, ventana_correlacion_dias: ventana } = carga.datos;
  return (
    <>
      {predicciones.length ? (
        <div className="tarjeta tabla-contenedor">
          <table className="tabla">
            <caption>Predicciones históricas</caption>
            <thead><tr>
              <th scope="col">Generada</th><th scope="col">Enfermedad</th><th scope="col">Riesgo y probabilidad</th>
              <th scope="col">Estimada para</th><th scope="col">Correlación con brote registrado</th><th scope="col">Anticipación descriptiva</th>
            </tr></thead>
            <tbody>{predicciones.map((p) => (
              <tr key={p.prediccion_id}>
                <td>{fechaLarga(p.fecha_generacion)}</td>
                <td className="mayuscula">{p.enfermedad}</td>
                <td><Insignia nivel={p.nivel_riesgo} /> <span className="nota numero sin-corte">{formatearPorcentaje(p.probabilidad_pct)}</span></td>
                <td>{fechaLarga(p.fecha_estimada_riesgo)}</td>
                <td>{p.brote_confirmado ? `Coincidencia registrada, el ${fechaLarga(p.fecha_brote_confirmado)}` : "Sin coincidencia registrada"}</td>
                <td><Anticipacion dias={p.anticipacion_dias} /></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <Vacio titulo="No hay predicciones en el rango consultado">Prueba otro rango de fechas o municipio.</Vacio>}
      {brotes.length ? (
        <div className="tarjeta tabla-contenedor">
          <table className="tabla">
            <caption>Brotes confirmados registrados</caption>
            <thead><tr><th scope="col">Confirmación</th><th scope="col">Enfermedad</th><th scope="col">Fuente</th></tr></thead>
            <tbody>{brotes.map((b) => <tr key={b.id}>
              <td>{fechaLarga(b.fecha_confirmacion)}</td><td className="mayuscula">{b.enfermedad}</td><td>{b.fuente}</td>
            </tr>)}</tbody>
          </table>
        </div>
      ) : <Vacio titulo="No hay brotes confirmados registrados en el rango">La ausencia de registros no demuestra que no hayan ocurrido brotes.</Vacio>}
      <div className="aviso">
        <h3>Cómo se compara</h3>
        <p>La API relaciona una predicción con un brote de la misma enfermedad y municipio a no más de {ventana} días de la fecha estimada.
          Es una coincidencia descriptiva, no una medida de precisión validada.</p>
        <p>La anticipación indica los días entre generación y confirmación, cuando existe correlación. No demuestra eficacia predictiva.</p>
        <p>El rango filtra la generación de predicciones y la confirmación de brotes en UTC. La correlación puede referenciar un brote fuera del rango mostrado.</p>
      </div>
    </>
  );
}

/** TASK-029: extiende la vista técnica existente; el servidor mantiene RBAC. */
export function Historial({ zonas, enfermedad = "dengue", cargandoZonas = false, errorZonas, recargarZonas }) {
  const id = useId();
  const { municipios, enfermedadId } = catalogoPanel(zonas, enfermedad);
  const [elegida, setElegida] = useState(null);
  const [fechas, setFechas] = useState({ desde: "", hasta: "" });
  const zonaId = municipios.some((m) => m.id === elegida) ? elegida : municipios[0]?.id;
  if (!municipios.length || enfermedadId === null) {
    if (cargandoZonas) return <Cargando etiqueta="Cargando municipios" />;
    if (errorZonas) return <ErrorCarga error={errorZonas} alReintentar={recargarZonas} />;
    return <Vacio titulo="No hay municipios disponibles para esta enfermedad">Se necesitan municipios e identificadores de enfermedad del backend para consultar el historial.</Vacio>;
  }
  return (
    <section className="pagina-estrecha aparece" aria-label="Historial">
      <div className="campo">
        <label htmlFor={`${id}-zona`}>Zona</label>
        <select id={`${id}-zona`} value={zonaId} onChange={(e) => setElegida(Number(e.target.value))}>
          {municipios.map((m) => <option key={m.id} value={m.id}>{nombreZona(m.nombre)}</option>)}
        </select>
      </div>
      <FiltrosFechas alAplicar={setFechas} />
      <p className="nota">Fechas inclusivas en UTC. Enfermedad seleccionada: <span className="mayuscula">{enfermedad}</span>.</p>
      <TablaHistorial key={`${zonaId}-${enfermedadId}-${fechas.desde}-${fechas.hasta}`} zonaId={zonaId} enfermedadId={enfermedadId} {...fechas} />
    </section>
  );
}
