import { formatearEntero, formatearPorcentaje, fechaLarga, nombreZona } from "../format.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { GraficoSemanal } from "./GraficoSemanal.jsx";
import { Insignia } from "./PanelDengue.jsx";

function Ranking({ filas, clase = "" }) {
  if (!filas.length) return <p className="secundario">Todavía no hay casos cargados.</p>;
  const maximo = Math.max(1, ...filas.map((f) => f.casos));
  return (
    <ol className={`ranking-barras ${clase}`}>
      {filas.map((f) => (
        <li key={f.municipio_id}>
          <div className="fila-r">
            <span>{nombreZona(f.municipio)} <span className="nota">· {nombreZona(f.departamento)}</span></span>
            <strong>{formatearEntero(f.casos)}</strong>
          </div>
          <div className="barra-valor" aria-hidden="true"><span style={{ width: `${(f.casos / maximo) * 100}%` }} /></div>
        </li>
      ))}
    </ol>
  );
}

function Indicador({ titulo, valor, pie, clase = "" }) {
  return (
    <div className={`tarjeta kpi ${clase}`}>
      <span className="titulo-kpi">{titulo}</span>
      <span className="valor">{valor}</span>
      <span className="nota">{pie}</span>
    </div>
  );
}

/** Vista de entrada: indicadores de ambas enfermedades en una sola pantalla. */
export function Resumen({ panel, irA }) {
  if (panel.fase === "cargando") return <Cargando etiqueta="Cargando el resumen" />;
  if (panel.fase === "error") return <ErrorCarga error={panel.error} alReintentar={panel.recargar} titulo="No se pudo cargar el resumen" />;
  const d = panel.datos;
  // Una respuesta incompleta no debe romper la pantalla: se avisa y se puede reintentar.
  if (!d?.alertas || !d?.dengue || !d?.malaria) {
    return <Vacio titulo="El resumen no está disponible">La API respondió sin los indicadores esperados. Los datos siguen disponibles en el mapa y en las alertas.</Vacio>;
  }
  const { dengue, malaria, alertas } = d;
  const hayAlertas = alertas.vigentes > 0;
  const riesgo = dengue.riesgo;
  const sinDatos = !dengue.total_casos && !malaria.total_casos && !riesgo.total;

  return (
    <section className="resumen aparece" aria-label="Resumen de la situación">
      <div className="hero">
        <div>
          <p className="sobretitulo">Situación epidemiológica · Bolivia</p>
          <h2>{hayAlertas
            ? `${alertas.vigentes} ${alertas.vigentes === 1 ? "alerta vigente" : "alertas vigentes"} de dengue`
            : "Sin alertas vigentes"}</h2>
          <p>
            {dengue.mayor_riesgo
              ? <>Mayor probabilidad de brote a 3 semanas: <strong>{nombreZona(dengue.mayor_riesgo.municipio)}</strong> ({formatearPorcentaje(dengue.mayor_riesgo.probabilidad_pct)}), con fecha estimada de riesgo el {fechaLarga(dengue.mayor_riesgo.fecha_estimada_riesgo)}.</>
              : "Todavía no hay predicciones cargadas."}
          </p>
        </div>
        <div className="hero-acciones">
          <button type="button" className="boton boton-claro" onClick={() => irA("alertas")}>Ver alertas</button>
          <button type="button" className="boton boton-fantasma" onClick={() => irA("mapa")}>Abrir el mapa</button>
        </div>
      </div>

      {sinDatos && (
        <div className="aviso"><h3>Todavía no hay datos cargados</h3>
          <p>Cuando se carguen casos y predicciones, aquí aparecerán los indicadores.</p></div>
      )}

      <div className="kpis">
        <Indicador clase="kpi-alerta" titulo="Alertas vigentes" valor={formatearEntero(alertas.vigentes)} pie={`${formatearEntero(alertas.emitidas)} emitidas en total`} />
        <Indicador clase="kpi-medio" titulo="Zonas en riesgo alto" valor={`${riesgo.alto} de ${riesgo.total}`} pie={`${riesgo.medio} en riesgo medio · dengue`} />
        <Indicador clase="kpi-dengue" titulo="Casos de dengue" valor={formatearEntero(dengue.total_casos)} pie={`en ${dengue.municipios_con_casos} municipios · ${dengue.serie_semanal.length} semanas`} />
        <Indicador clase="kpi-malaria" titulo="Casos de malaria" valor={formatearEntero(malaria.total_casos)} pie={`acumulado en ${malaria.municipios_con_casos} municipios${malaria.fecha_corte ? ` al ${fechaLarga(malaria.fecha_corte)}` : ""}`} />
      </div>

      <div className="rejilla-2">
        <div className="tarjeta">
          <div className="tarjeta-titulo">
            <h3>Casos semanales de dengue</h3>
            <p className="nota">Suma de los {dengue.municipios_con_casos} municipios con casos reportados.</p>
          </div>
          <div className="tarjeta-cuerpo">
            {dengue.serie_semanal.length
              ? <GraficoSemanal serie={dengue.serie_semanal} titulo="Casos semanales de dengue" />
              : <p className="secundario">Todavía no hay serie semanal.</p>}
          </div>
        </div>
        <div className="tarjeta">
          <div className="tarjeta-titulo">
            <h3>Riesgo de dengue por zona</h3>
            <p className="nota">Predicción a 3 semanas del modelo vigente.</p>
          </div>
          <div className="tarjeta-cuerpo">
            {riesgo.total ? (
              <>
                <div className="pila" role="img" aria-label={`${riesgo.alto} zonas en riesgo alto, ${riesgo.medio} en medio y ${riesgo.bajo} en bajo`}>
                  <span className="alto" style={{ flexGrow: riesgo.alto }} />
                  <span className="medio" style={{ flexGrow: riesgo.medio }} />
                  <span className="bajo" style={{ flexGrow: riesgo.bajo }} />
                </div>
                <div className="conteos">
                  <div className="c-alto"><strong>{riesgo.alto}</strong><span className="nota">alto</span></div>
                  <div className="c-medio"><strong>{riesgo.medio}</strong><span className="nota">medio</span></div>
                  <div className="c-bajo"><strong>{riesgo.bajo}</strong><span className="nota">bajo</span></div>
                </div>
                {(dengue.mayores_riesgos ?? []).length > 0 && (
                  <ol className="ranking-barras riesgo" aria-label="Zonas con mayor probabilidad de brote">
                    {dengue.mayores_riesgos.map((z) => (
                      <li key={z.municipio_id}>
                        <div className="fila-r">
                          <span>{nombreZona(z.municipio)} <span className="nota">· {nombreZona(z.departamento)}</span></span>
                          <strong>{formatearPorcentaje(z.probabilidad_pct)}</strong>
                        </div>
                        <div className={`barra-valor riesgo-${z.nivel_riesgo}`} aria-hidden="true"><span style={{ width: `${Math.min(100, z.probabilidad_pct)}%` }} /></div>
                        <Insignia nivel={z.nivel_riesgo} />
                      </li>
                    ))}
                  </ol>
                )}
              </>
            ) : <p className="secundario">Todavía no hay predicciones.</p>}
          </div>
        </div>
      </div>

      <div className="rejilla-2 igual">
        <div className="tarjeta">
          <div className="tarjeta-titulo"><h3>Dengue: municipios con más casos</h3></div>
          <div className="tarjeta-cuerpo"><Ranking filas={dengue.top_municipios} /></div>
        </div>
        <div className="tarjeta">
          <div className="tarjeta-titulo"><h3>Malaria: municipios con más casos</h3><p className="nota">Acumulado; no existe serie semanal.</p></div>
          <div className="tarjeta-cuerpo"><Ranking filas={malaria.top_municipios} clase="malaria" /></div>
        </div>
      </div>

      <div className="aviso aviso-datos"><p>{d.nota}</p></div>
    </section>
  );
}
