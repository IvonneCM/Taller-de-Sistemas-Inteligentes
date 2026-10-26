import {
  agruparCasosPorDepartamento, agruparRiesgoPorDepartamento,
} from "../agregacion.js";
import {
  fechaLarga, formatearEntero, formatearPorcentaje, nombreZona,
} from "../format.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Mosquito, Gota } from "./Iconos.jsx";
import { filtrarDengue, Insignia } from "./PanelDengue.jsx";
import { filtrarMalaria } from "./PanelMalaria.jsx";

/** Puntos del mapa a nivel de departamento (TASK-027). */
export function puntosDepartamentoDengue(zonas) {
  return agruparRiesgoPorDepartamento(filtrarDengue(zonas)).map((d) => ({
    id: d.id,
    nombre: nombreZona(d.nombre),
    centroide: d.centroide,
    geometrias: d.geometrias,
    variableColor: `--riesgo-${d.nivel_riesgo}`,
    radio: 12 + (d.probabilidad_pct / 100) * 18,
    etiqueta: `${d.nivel_riesgo} · ${formatearPorcentaje(d.probabilidad_pct)} (máximo de ${d.n} municipio${d.n === 1 ? "" : "s"})`,
  }));
}

export function puntosDepartamentoMalaria(casos) {
  const deptos = agruparCasosPorDepartamento(filtrarMalaria(casos));
  const maximo = Math.max(1, ...deptos.map((d) => d.total_casos));
  return deptos.map((d) => ({
    id: d.id,
    nombre: nombreZona(d.nombre),
    centroide: d.centroide,
    geometrias: d.geometrias,
    variableColor: "--malaria",
    radio: 10 + 22 * Math.sqrt(d.total_casos / maximo),
    etiqueta: `${formatearEntero(d.total_casos)} casos`,
  }));
}

function Municipios({ filas, columna }) {
  return (
    <ul className="lista-zonas" aria-label="Municipios del departamento">
      {filas.map((m) => (
        <li key={m.municipio_id} className="fila-municipio">
          <span>{nombreZona(m.municipio)}</span>
          {columna(m)}
        </li>
      ))}
    </ul>
  );
}

/** Panel por departamento, para dengue (mayor riesgo) o malaria (casos sumados). */
export function PanelDepartamento({ tipo, carga, seleccionado, alSeleccionar }) {
  const esMalaria = tipo === "malaria";
  if (carga.fase === "cargando" && !carga.datos) return <Cargando etiqueta="Cargando los departamentos" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} />;

  const deptos = esMalaria
    ? agruparCasosPorDepartamento(filtrarMalaria(carga.datos))
    : agruparRiesgoPorDepartamento(filtrarDengue(carga.datos));
  if (!deptos.length) {
    return (
      <Vacio titulo={esMalaria ? "Todavía no hay casos de malaria" : "Todavía no hay predicciones de dengue"}
        icono={esMalaria ? <Mosquito tamano={36} /> : <Gota tamano={36} />}>
        Cuando haya datos, aparecerán agrupados por departamento.
      </Vacio>
    );
  }

  const maximo = Math.max(...deptos.map((d) => d.total_casos ?? 0), 1);
  const elegido = deptos.find((d) => d.id === seleccionado);
  const total = esMalaria ? deptos.reduce((s, d) => s + d.total_casos, 0) : null;

  return (
    <section className="panel aparece" aria-label="Departamentos">
      <div className="tarjeta tarjeta-relleno cabecera-panel">
        <p className="sobretitulo">{esMalaria ? "Malaria · por departamento" : "Dengue · por departamento"}</p>
        {esMalaria ? (
          <>
            <p className="cifra cifra-malaria">{formatearEntero(total)}</p>
            <p className="secundario">casos confirmados en {deptos.length} departamento{deptos.length === 1 ? "" : "s"}, sumando sus municipios.</p>
          </>
        ) : (
          <>
            <p className="cifra">{formatearPorcentaje(deptos[0].probabilidad_pct)}</p>
            <p className="secundario">es el mayor riesgo entre los departamentos: {nombreZona(deptos[0].nombre)}.</p>
            <div className="leyenda" aria-label="Leyenda de riesgo">
              {["alto", "medio", "bajo"].map((n) => <Insignia key={n} nivel={n} />)}
            </div>
          </>
        )}
      </div>

      {elegido && (
        <div className="tarjeta detalle aparece" aria-live="polite">
          <h3>{nombreZona(elegido.nombre)}</h3>
          <p className="nota">
            {elegido.n} municipio{elegido.n === 1 ? "" : "s"} con datos
            {!esMalaria && ` · riesgo estimado para el ${fechaLarga(elegido.municipios[0].fecha_estimada_riesgo)}`}
          </p>
          <Municipios
            filas={elegido.municipios}
            columna={(m) => (esMalaria
              ? <span className="zona-valor">{formatearEntero(m.total_casos)}</span>
              : <span className="ranking-cola"><span className="zona-valor">{formatearPorcentaje(m.probabilidad_pct)}</span><Insignia nivel={m.nivel_riesgo} /></span>)}
          />
        </div>
      )}

      <div className="tarjeta tarjeta-lista">
        <ul className="lista-zonas">
          {deptos.map((d) => (
            <li key={d.id}>
              <button
                type="button" className="zona" aria-pressed={d.id === seleccionado}
                onClick={() => alSeleccionar(d.id === seleccionado ? null : d.id)}
              >
                <span>
                  <span className="zona-nombre">{nombreZona(d.nombre)}</span>
                  <span className="nota"> · {d.n} municipio{d.n === 1 ? "" : "s"}</span>
                </span>
                <span className="zona-valor">{esMalaria ? formatearEntero(d.total_casos) : formatearPorcentaje(d.probabilidad_pct)}</span>
                {esMalaria ? (
                  <span className="zona-barra barra-valor" aria-hidden="true"><span style={{ width: `${(d.total_casos / maximo) * 100}%` }} /></span>
                ) : (
                  <span className="zona-barra"><Insignia nivel={d.nivel_riesgo} /></span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="aviso">
        <h3>Cómo se agrupa</h3>
        <p>
          {esMalaria
            ? "Cada departamento suma los casos observados de sus municipios. No hay una cifra oficial del departamento en esta fuente."
            : "Cada departamento muestra el mayor riesgo y la mayor probabilidad entre sus municipios (criterio de peor caso). No es una predicción propia del departamento: el modelo predice por municipio."}
        </p>
      </div>
    </section>
  );
}
