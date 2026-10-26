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
const PRINCIPALES = 3;
const RADIO = 34;
const CIRCUNFERENCIA = 2 * Math.PI * RADIO;
const pesoNumerico = new Intl.NumberFormat("es-BO", { signDisplay: "always", minimumFractionDigits: 4, maximumFractionDigits: 4 });
const pesoValido = (v) => Number.isFinite(v.peso);

/** Probabilidad como anillo: el numero va en texto, el color solo refuerza el nivel. */
function Anillo({ porcentaje }) {
  const p = Math.max(0, Math.min(100, Number(porcentaje) || 0));
  return (
    <div className="anillo">
      <svg viewBox="0 0 80 80" aria-hidden="true">
        <circle className="pista" cx="40" cy="40" r={RADIO} />
        <circle className="valor-a" cx="40" cy="40" r={RADIO} strokeDasharray={`${(p / 100) * CIRCUNFERENCIA} ${CIRCUNFERENCIA}`} />
      </svg>
      <strong>{formatearPorcentaje(porcentaje)}</strong>
    </div>
  );
}

/** Una variable con su barra: ancho relativo a la mayor de la alerta, sin convertirla a porcentaje. */
function Factor({ v, maximo }) {
  return (
    <li className="variable factor">
      <div className="variable-cabecera">
        <span>{etiquetaVariable(v.variable)}</span>
        <span className="numero">{pesoValido(v) ? pesoNumerico.format(v.peso) : "Peso no informado"}</span>
      </div>
      {pesoValido(v) && (
        <>
          <div className="eje" aria-hidden="true">
            <span className={v.peso > 0 ? "sube" : "baja"} style={{ width: `${(Math.abs(v.peso) / maximo) * 50}%` }} />
          </div>
          <span className="nota">{v.peso > 0 ? "aumenta" : v.peso < 0 ? "reduce" : "no cambia"} el riesgo</span>
        </>
      )}
    </li>
  );
}

function TarjetaAlerta({ alerta }) {
  const [verTodas, setVerTodas] = useState(false);
  const variables = alerta.variables_explicativas;
  const maximo = Math.max(0.0001, ...variables.filter(pesoValido).map((v) => Math.abs(v.peso)));
  const visibles = verTodas ? variables : variables.slice(0, PRINCIPALES);
  return (
    <article className={`tarjeta alerta nivel-${alerta.nivel_riesgo}`}>
      <div className="alerta-cabeza">
        <Anillo porcentaje={alerta.probabilidad_pct} />
        <div>
          <h3>{nombreZona(alerta.municipio)}</h3>
          <p className="nota"><span className="mayuscula">{alerta.enfermedad}</span> · emitida el {fechaLarga(alerta.fecha_emision)}</p>
        </div>
        <Insignia nivel={alerta.nivel_riesgo} />
      </div>
      <div className="alerta-meta">
        <span>Umbral de alerta: <strong>{formatearPorcentaje(alerta.umbral_aplicado)}</strong></span>
        <span>{`Fecha estimada de riesgo: ${alerta.fecha_estimada_riesgo ? fechaLarga(alerta.fecha_estimada_riesgo) : "No informada"}.`}</span>
      </div>
      <p className="justificacion">{alerta.justificacion}</p>
      <div className="factores">
        <h4>{verTodas || variables.length <= PRINCIPALES ? "Variables explicativas" : `Los ${PRINCIPALES} factores principales`}</h4>
        <ul className="variables" aria-label={`Variables explicativas de la alerta ${alerta.id}`}>
          {visibles.map((v, i) => <Factor key={`${v.variable}-${i}`} v={v} maximo={maximo} />)}
        </ul>
        {variables.length > PRINCIPALES && (
          <button type="button" className="boton boton-suave boton-pequeno" aria-expanded={verTodas} onClick={() => setVerTodas((x) => !x)}>
            {verTodas ? "Ver solo los principales" : `Ver las ${variables.length} variables`}
          </button>
        )}
      </div>
    </article>
  );
}

function VacioAlertas({ pagina, enfermedad, alCambiarEnfermedad, irA }) {
  if (enfermedad === "malaria" && !pagina) {
    return (
      <Vacio titulo="La malaria todavía no tiene alertas" icono={<Campana />}>
        Las alertas salen de predicciones del modelo, y para malaria no hay modelo: solo existen casos acumulados, sin serie semanal.
        Los casos observados de malaria están en el mapa.
        <span className="hero-acciones" style={{ marginTop: "var(--e-md)" }}>
          <button type="button" className="boton" onClick={() => alCambiarEnfermedad?.("dengue")}>Ver alertas de dengue</button>
          <button type="button" className="boton boton-suave" onClick={() => irA?.("mapa")}>Ver casos de malaria en el mapa</button>
        </span>
      </Vacio>
    );
  }
  return (
    <Vacio titulo={pagina ? "No hay más alertas en esta página" : "No hay alertas emitidas"} icono={<Campana />}>
      No se encontraron alertas para estos filtros. No significa que no exista riesgo.
    </Vacio>
  );
}

function PaginaAlertas({ enfermedadId, enfermedad, municipioId, desde, hasta, soloVigentes, alCambiarEnfermedad, irA }) {
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
        <VacioAlertas pagina={pagina} enfermedad={enfermedad} alCambiarEnfermedad={alCambiarEnfermedad} irA={irA} />
      )}
      {filas.length > 0 && <div className="tarjetas">{filas.map((a) => <TarjetaAlerta key={a.id} alerta={a} />)}</div>}
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
export function Alertas({ zonas = [], enfermedad = "dengue", cargandoZonas = false, errorZonas, recargarZonas, irA, alCambiarEnfermedad }) {
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
      <div className="cabecera-panel">
        <p className="sobretitulo">Alertas · <span className="mayuscula">{enfermedad}</span></p>
        <h2>Alertas emitidas</h2>
      </div>
      <div className="tarjeta barra-herramientas">
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
      </div>
      <details className="mas aviso">
        <summary>Cómo leer las alertas</summary>
        <p>Vigente para planificación significa que corresponde a la última predicción del municipio y enfermedad, con fecha objetivo no vencida y explicación válida. No significa pendiente de atención ni no resuelta; el backend no registra resolución.</p>
        <p>Fechas de emisión inclusivas en UTC. Enfermedad: <span className="mayuscula">{enfermedad}</span>.</p>
        <p>En el modelo XGBoost actual, los pesos SHAP están en log-odds: un signo positivo eleva el margen respecto al valor base y uno negativo lo reduce. No son porcentajes ni demuestran causalidad. La API no incluye una escala por alerta; esta interpretación corresponde al modelo actual.</p>
      </details>
      <PaginaAlertas key={`${enfermedadId}-${municipioId}-${fechas.desde}-${fechas.hasta}-${soloVigentes}`} enfermedadId={enfermedadId} enfermedad={enfermedad} municipioId={municipioId} soloVigentes={soloVigentes} alCambiarEnfermedad={alCambiarEnfermedad} irA={irA} {...fechas} />
    </section>
  );
}
