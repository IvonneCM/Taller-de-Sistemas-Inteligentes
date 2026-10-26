import { useCallback, useId, useState } from "react";
import { pedir } from "../api.js";
import { catalogoPanel } from "../datosPaneles.js";
import { etiquetaVariable, fechaLarga, formatearPorcentaje, nombreZona } from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { FiltrosFechas } from "./FiltrosFechas.jsx";
import { Campana } from "./Iconos.jsx";
import { Insignia } from "./PanelDengue.jsx";

const TAMANO_PAGINA = 50;
const pesoNumerico = new Intl.NumberFormat("es-BO", { signDisplay: "always", minimumFractionDigits: 4, maximumFractionDigits: 4 });

function PaginaAlertas({ enfermedadId, municipioId, desde, hasta, soloVigentes }) {
  const [pagina, setPagina] = useState(0);
  const cargar = useCallback(() => pedir("/alertas", { params: {
    enfermedad_id: enfermedadId, municipio_id: municipioId || undefined,
    desde, hasta, limite: TAMANO_PAGINA, desplazamiento: pagina * TAMANO_PAGINA,
    solo_vigentes: soloVigentes,
  } }), [enfermedadId, municipioId, desde, hasta, pagina, soloVigentes]);
  const carga = useCarga(cargar, [enfermedadId, municipioId, desde, hasta, pagina, soloVigentes]);
  const filas = carga.fase === "listo" ? [...carga.datos].sort((a, b) =>
    new Date(b.fecha_emision) - new Date(a.fecha_emision) || b.id - a.id) : [];
  return (
    <>
      {carga.fase === "cargando" && <Cargando etiqueta="Cargando alertas" />}
      {carga.fase === "error" && <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudieron cargar las alertas" />}
      {carga.fase === "listo" && !filas.length && (
        <Vacio titulo={pagina ? "No hay más alertas en esta página" : "No hay alertas emitidas"} icono={<Campana />}>
          No se encontraron alertas para estos filtros. No significa que no exista riesgo.
        </Vacio>
      )}
      {filas.length > 0 && <div className="tarjetas">
        {filas.map((alerta) => (
          <article className="tarjeta alerta" key={alerta.id}>
            <div className="alerta-cabecera">
              <div>
                <h3>{nombreZona(alerta.municipio)}</h3>
                <p className="nota"><span className="mayuscula">{alerta.enfermedad}</span> · emitida el {fechaLarga(alerta.fecha_emision)}</p>
              </div>
              <Insignia nivel={alerta.nivel_riesgo} />
            </div>
            <p className="fila-texto">Probabilidad de <strong>{formatearPorcentaje(alerta.probabilidad_pct)}</strong>, con umbral de {formatearPorcentaje(alerta.umbral_aplicado)}.</p>
            <p className="fila-texto">{alerta.justificacion}</p>
            <p className="nota">Fecha estimada de riesgo: {alerta.fecha_estimada_riesgo ? fechaLarga(alerta.fecha_estimada_riesgo) : "No informada"}.</p>
            <ul className="variables" aria-label={`Variables explicativas de la alerta ${alerta.id}`}>
              {alerta.variables_explicativas.map((v, i) => <li className="variable-cabecera" key={`${v.variable}-${i}`}>
                <span>{etiquetaVariable(v.variable)}</span>
                <span className="numero">{Number.isFinite(v.peso) ? pesoNumerico.format(v.peso) : "Peso no informado"}</span>
              </li>)}
            </ul>
          </article>
        ))}
      </div>}
      <nav className="paginacion" aria-label="Paginación de alertas">
        <button className="boton boton-suave" type="button" disabled={pagina === 0 || carga.fase === "cargando"} onClick={() => setPagina((p) => p - 1)}>Anterior</button>
        <p className="nota" aria-live="polite">Página {pagina + 1}{carga.fase === "listo" ? ` · ${filas.length} alertas mostradas` : ""}</p>
        <button className="boton boton-suave" type="button" disabled={carga.fase !== "listo" || filas.length < TAMANO_PAGINA} onClick={() => setPagina((p) => p + 1)}>Siguiente</button>
      </nav>
      <p className="nota">El servidor no informa el total de alertas. Una página completa permite consultar la siguiente; puede estar vacía. Las alertas pueden cambiar entre consultas.</p>
    </>
  );
}

/** TASK-030: alertas emitidas, sin inventar estados de actividad o resolución. */
export function Alertas({ zonas = [], enfermedad = "dengue", cargandoZonas = false, errorZonas, recargarZonas }) {
  const id = useId();
  const { enfermedadId, municipios } = catalogoPanel(zonas, enfermedad);
  const [municipioId, setMunicipioId] = useState("");
  const [fechas, setFechas] = useState({ desde: "", hasta: "" });
  const [soloVigentes, setSoloVigentes] = useState(false);
  if (enfermedadId === null) {
    if (cargandoZonas) return <Cargando etiqueta="Cargando municipios" />;
    if (errorZonas) return <ErrorCarga error={errorZonas} alReintentar={recargarZonas} />;
    return <Vacio titulo="No hay municipios disponibles para esta enfermedad">No se consultan alertas de otra enfermedad como sustitución.</Vacio>;
  }
  return (
    <section className="panel-alertas aparece" aria-label="Alertas">
      <h2>Alertas emitidas</h2>
      <p className="nota">Vigente para planificación significa que corresponde a la última predicción del municipio y enfermedad, con fecha objetivo no vencida y explicación válida. No significa pendiente de atención ni no resuelta; el backend no registra resolución.</p>
      <div className="campo">
        <label htmlFor={`${id}-vigencia`}>Mostrar alertas</label>
        <select id={`${id}-vigencia`} value={String(soloVigentes)} onChange={(e) => setSoloVigentes(e.target.value === "true")}>
          <option value="true">Vigentes para planificación</option>
          <option value="false">Todas las emitidas</option>
        </select>
      </div>
      <div className="campo">
        <label htmlFor={`${id}-municipio`}>Municipio</label>
        <select id={`${id}-municipio`} value={municipioId} onChange={(e) => setMunicipioId(e.target.value)}>
          <option value="">Todos los municipios</option>
          {municipios.map((m) => <option key={m.id} value={m.id}>{nombreZona(m.nombre)}</option>)}
        </select>
      </div>
      <FiltrosFechas alAplicar={setFechas} />
      <p className="nota">Fechas de emisión inclusivas en UTC. Enfermedad: <span className="mayuscula">{enfermedad}</span>.</p>
      <p className="nota">En el modelo XGBoost actual, los pesos SHAP están en log-odds: un signo positivo eleva el margen respecto al valor base y uno negativo lo reduce. No son porcentajes ni demuestran causalidad. La API no incluye una escala por alerta; esta interpretación corresponde al modelo actual.</p>
      <PaginaAlertas key={`${enfermedadId}-${municipioId}-${fechas.desde}-${fechas.hasta}-${soloVigentes}`} enfermedadId={enfermedadId} municipioId={municipioId} soloVigentes={soloVigentes} {...fechas} />
    </section>
  );
}
