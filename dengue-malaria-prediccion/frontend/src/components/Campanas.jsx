import { useCallback, useState } from "react";
import { pedir } from "../api.js";
import { fechaLarga, formatearPorcentaje, nombreZona, veRecursos } from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Insignia } from "./PanelDengue.jsx";

const ATENCION = { PRIORITARIO: "Atención prioritaria", PREVENTIVO: "Atención preventiva", RUTINARIO: "Atención rutinaria" };

function Recursos({ municipioId }) {
  const cargar = useCallback(() => pedir(`/municipios/${municipioId}/recursos`), [municipioId]);
  const carga = useCarga(cargar, [municipioId]);

  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando las recomendaciones" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudieron cargar las recomendaciones" />;

  const r = carga.datos;
  return (
    <div className="tarjeta detalle aparece" aria-live="polite">
      <div>
        <h3>{nombreZona(r.municipio)}</h3>
        <p className="nota">{ATENCION[r.nivel_atencion] ?? r.nivel_atencion} · riesgo estimado para el {fechaLarga(r.fecha_estimada_riesgo)}</p>
      </div>
      <ul className="recomendaciones" aria-label="Recomendaciones">
        {r.recomendaciones.map((texto) => <li key={texto}>{texto}</li>)}
      </ul>
      <p className="nota">{r.nota}</p>
    </div>
  );
}

/** Priorización de campañas (TASK-031, REQ-011) y recomendaciones por municipio (REQ-012). */
export function Campanas({ usuario }) {
  const cargar = useCallback(() => pedir("/campanas/priorizacion"), []);
  const carga = useCarga(cargar, []);
  const [elegido, setElegido] = useState(null);
  const conRecursos = veRecursos(usuario.rol);

  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando la priorización" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudo cargar la priorización" />;

  const filas = carga.datos;
  if (!filas.length) {
    return (
      <div className="pagina-estrecha aparece">
        <Vacio titulo="No hay zonas para priorizar">
          La priorización usa la predicción de dengue a 3 semanas vigente de cada municipio. Aparecerá
          cuando el modelo genere predicciones cuya fecha de riesgo aún no haya pasado.
        </Vacio>
      </div>
    );
  }

  // La coordinación solo ve su municipio: se muestran sus recomendaciones de inmediato.
  const activo = elegido ?? (conRecursos && filas.length === 1 ? filas[0].municipio_id : null);

  return (
    <section className="pagina-estrecha aparece" aria-label="Priorización de campañas">
      <div className="cabecera-panel">
        <p className="sobretitulo">Dengue · predicción a 3 semanas</p>
        <h2>Dónde priorizar las campañas</h2>
        <p className="secundario">
          Orden por nivel de riesgo, fecha estimada y probabilidad. La probabilidad es la de registrar al
          menos un caso, no la gravedad de un brote.
        </p>
      </div>

      <div className="tarjeta tarjeta-lista">
        <ol className="lista-zonas ranking">
          {filas.map((f) => {
            const contenido = (
              <>
                <span className="posicion" aria-label={`Posición ${f.posicion}`}>{f.posicion}</span>
                <span>
                  <span className="zona-nombre">{nombreZona(f.municipio)}</span>
                  <span className="nota"> · {nombreZona(f.departamento)}</span>
                  <span className="nota bloque">Riesgo estimado para el {fechaLarga(f.fecha_estimada_riesgo)}</span>
                </span>
                <span className="ranking-cola">
                  <span className="zona-valor">{formatearPorcentaje(f.probabilidad_pct)}</span>
                  <Insignia nivel={f.nivel_riesgo} />
                </span>
              </>
            );
            return (
              <li key={f.municipio_id}>
                {conRecursos ? (
                  <button
                    type="button" className="zona fila-ranking" aria-pressed={f.municipio_id === activo}
                    onClick={() => setElegido(f.municipio_id === elegido ? null : f.municipio_id)}
                  >{contenido}</button>
                ) : <div className="zona fila-ranking sin-accion">{contenido}</div>}
              </li>
            );
          })}
        </ol>
      </div>

      {conRecursos && activo && <Recursos municipioId={activo} />}
      {!conRecursos && (
        <p className="nota">Las recomendaciones de atención por municipio las consulta la coordinación municipal.</p>
      )}

      {/* Con las recomendaciones a la vista, la API ya trae esta misma advertencia. */}
      {!(conRecursos && activo) && (
      <div className="aviso">
        <h3>Reglas provisionales</h3>
        <p>
          Los cortes de riesgo y las recomendaciones son decisiones provisionales del MVP: no son
          protocolos oficiales de SEDES ni sustituyen la evaluación epidemiológica.
        </p>
      </div>
      )}
    </section>
  );
}
