import { formatearEntero, fechaLarga, nombreZona } from "../format.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Mosquito } from "./Iconos.jsx";

/** Casos de malaria por zona, tal como los entrega la fuente (acumulado SE 1-13). */
export function filtrarMalaria(casos) {
  return (casos ?? []).filter((c) => c.enfermedad === "malaria");
}

export function puntosMalaria(casos) {
  const filas = filtrarMalaria(casos);
  const maximo = Math.max(1, ...filas.map((c) => c.total_casos));
  return filas.map((c) => ({
    id: c.municipio_id,
    nombre: nombreZona(c.municipio),
    centroide: c.centroide,
    geometria: c.geometria,
    variableColor: "--malaria",
    // Área proporcional a los casos: el radio crece con la raíz cuadrada.
    radio: 8 + 20 * Math.sqrt(c.total_casos / maximo),
    etiqueta: `${formatearEntero(c.total_casos)} casos`,
  }));
}

export function PanelMalaria({ carga, seleccionado, alSeleccionar }) {
  if (carga.fase === "cargando" && !carga.datos) return <Cargando etiqueta="Cargando casos de malaria" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} />;

  const filas = filtrarMalaria(carga.datos);
  if (!filas.length) {
    return (
      <Vacio titulo="Todavía no hay casos de malaria" icono={<Mosquito tamano={36} />}>
        Cuando se carguen los boletines epidemiológicos, aparecerán aquí por municipio.
      </Vacio>
    );
  }

  const total = filas.reduce((suma, c) => suma + c.total_casos, 0);
  const maximo = Math.max(...filas.map((c) => c.total_casos));
  const elegida = filas.find((c) => c.municipio_id === seleccionado);

  return (
    <section className="panel aparece" aria-label="Casos de malaria">
      <div className="tarjeta tarjeta-relleno cabecera-panel">
        <p className="sobretitulo">Malaria · acumulado al {fechaLarga(filas[0].hasta)}</p>
        <p className="cifra cifra-malaria">{formatearEntero(total)}</p>
        <p className="secundario">
          casos confirmados en {filas.length} municipios de la zona piloto, según el Boletín
          Epidemiológico N.º 13.
        </p>
      </div>

      {elegida && (
        <div className="tarjeta detalle aparece" aria-live="polite">
          <h3>{nombreZona(elegida.municipio)}</h3>
          <div className="datos">
            <div className="dato"><span className="nota">Casos acumulados</span><span className="valor">{formatearEntero(elegida.total_casos)}</span></div>
            <div className="dato"><span className="nota">De la zona piloto</span><span className="valor">{Math.round((elegida.total_casos / total) * 100)} %</span></div>
          </div>
          <p className="nota">{elegida.fuente}</p>
        </div>
      )}

      <div className="tarjeta tarjeta-lista">
        <ul className="lista-zonas">
          {filas.map((c) => (
            <li key={c.municipio_id}>
              <button
                type="button" className="zona" aria-pressed={c.municipio_id === seleccionado}
                onClick={() => alSeleccionar(c.municipio_id === seleccionado ? null : c.municipio_id)}
              >
                <span>
                  <span className="zona-nombre">{nombreZona(c.municipio)}</span>
                  <span className="nota"> · {nombreZona(c.departamento)}</span>
                </span>
                <span className="zona-valor">{formatearEntero(c.total_casos)}</span>
                <span className="zona-barra barra-valor" aria-hidden="true">
                  <span style={{ width: `${(c.total_casos / maximo) * 100}%` }} />
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="aviso">
        <h3>No hay predicción de malaria</h3>
        <p>
          La fuente publica un único total por municipio para las 13 semanas, sin el detalle
          semana a semana. Con tan poca historia no se puede entrenar un modelo que anticipe
          brotes, así que aquí se muestran casos observados, no predicciones.
        </p>
        <details className="mas">
          <summary>Cómo leer estos datos</summary>
          <p>
            Son conteos confirmados agregados por municipio (nunca datos de pacientes). El tamaño de
            cada círculo es proporcional a los casos. Las zonas dibujadas son cuadrados de unos 5 km
            centrados en la estación meteorológica: son referenciales, no el límite oficial del municipio.
          </p>
        </details>
      </div>
    </section>
  );
}
