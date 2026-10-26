import { useCallback } from "react";
import { pedir } from "../api.js";
import {
  esTecnico, etiquetaVariable, fechaLarga, formatearEntero, formatearPorcentaje, NIVELES, nombreZona,
} from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Gota } from "./Iconos.jsx";

export function filtrarDengue(zonas) {
  return (zonas ?? []).filter((z) => z.enfermedad === "dengue");
}

export function puntosDengue(zonas) {
  return filtrarDengue(zonas).map((z) => ({
    id: z.municipio_id,
    nombre: nombreZona(z.municipio),
    centroide: z.centroide,
    geometria: z.geometria,
    variableColor: `--riesgo-${z.nivel_riesgo}`,
    radio: 10 + (Number(z.probabilidad_pct) / 100) * 18,
    etiqueta: `${NIVELES[z.nivel_riesgo].toLowerCase()} · ${formatearPorcentaje(z.probabilidad_pct)}`,
  }));
}

export function Insignia({ nivel }) {
  return <span className={`insignia riesgo-${nivel}`}>{NIVELES[nivel]}</span>;
}

function Variables({ variables }) {
  const maximo = Math.max(0.0001, ...variables.map((v) => Math.abs(v.peso)));
  return (
    <ul className="variables" aria-label="Variables que más influyeron">
      {variables.slice(0, 5).map((v) => (
        <li className="variable" key={v.variable}>
          <div className="variable-cabecera">
            <span>{etiquetaVariable(v.variable)}</span>
            <span className="nota numero">{v.peso > 0 ? "aumenta" : "reduce"} el riesgo</span>
          </div>
          <div className="eje" aria-hidden="true">
            <span className={v.peso > 0 ? "sube" : "baja"} style={{ width: `${(Math.abs(v.peso) / maximo) * 50}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function DetalleZona({ zona, usuario, casos }) {
  const cargar = useCallback(
    () => pedir(`/zonas/${zona.municipio_id}/prediccion`, { params: { enfermedad_id: zona.enfermedad_id } }),
    [zona.municipio_id, zona.enfermedad_id],
  );
  const carga = useCarga(cargar, [zona.municipio_id, zona.enfermedad_id]);
  const observados = (casos ?? []).find((c) => c.municipio_id === zona.municipio_id && c.enfermedad === "dengue");

  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando el detalle de la zona" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudo cargar el detalle" />;

  const prediccion = carga.datos.predicciones[0];
  const completa = carga.datos.vista === "completa";

  return (
    <div className="tarjeta detalle aparece" aria-live="polite">
      <div>
        <h3>{nombreZona(zona.municipio)}</h3>
        <p className="nota">{nombreZona(zona.departamento)} · generada el {fechaLarga(prediccion.fecha_generacion)}</p>
      </div>
      <div className="datos">
        <div className="dato"><span className="nota">Probabilidad</span><span className="valor">{formatearPorcentaje(prediccion.probabilidad_pct)}</span></div>
        <div className="dato"><span className="nota">Riesgo</span><Insignia nivel={prediccion.nivel_riesgo} /></div>
        <div className="dato"><span className="nota">Confianza de los datos</span><span className="valor mayuscula">{prediccion.nivel_confianza}</span></div>
      </div>
      <p className="fila-texto">Riesgo estimado para el <strong>{fechaLarga(prediccion.fecha_estimada_riesgo)}</strong>.</p>

      {observados && (
        <p className="fila-texto secundario">
          Casos de dengue observados (semanas 1 a 13): <strong className="numero">{formatearEntero(observados.total_casos)}</strong>.
        </p>
      )}

      {completa ? (
        <div>
          <h3>Qué influyó en esta predicción</h3>
          <Variables variables={prediccion.variables_explicativas} />
          <p className="nota">
            Variables que más pesaron en el modelo ({carga.datos.predicciones[0].modelo_nombre}, {carga.datos.predicciones[0].modelo_version}).
            Rojo: empuja el riesgo hacia arriba; verde: lo reduce.
          </p>
        </div>
      ) : (
        <p className="nota">
          {esTecnico(usuario.rol)
            ? "Detalle técnico no disponible."
            : "El detalle de qué variables influyeron está disponible para epidemiólogos y administración."}
        </p>
      )}
    </div>
  );
}

export function PanelDengue({ carga, casos, usuario, seleccionado, alSeleccionar }) {
  if (carga.fase === "cargando" && !carga.datos) return <Cargando etiqueta="Cargando el riesgo de dengue" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} />;

  const zonas = filtrarDengue(carga.datos);
  if (!zonas.length) {
    return (
      <Vacio titulo="Todavía no hay predicciones de dengue" icono={<Gota tamano={36} />}>
        Aparecerán cuando el modelo genere su primera tanda de predicciones.
      </Vacio>
    );
  }

  const mayor = zonas[0];
  const elegida = zonas.find((z) => z.municipio_id === seleccionado);

  return (
    <section className="panel aparece" aria-label="Riesgo de dengue">
      <div className="tarjeta tarjeta-relleno cabecera-panel">
        <p className="sobretitulo">Dengue · predicción a 3 semanas</p>
        <p className="cifra">{formatearPorcentaje(mayor.probabilidad_pct)}</p>
        <p className="secundario">
          es la mayor probabilidad de brote entre las {zonas.length} zonas: {nombreZona(mayor.municipio)}.
        </p>
        <div className="leyenda" aria-label="Leyenda de riesgo">
          {["alto", "medio", "bajo"].map((n) => <Insignia key={n} nivel={n} />)}
        </div>
      </div>

      {elegida && <DetalleZona zona={elegida} usuario={usuario} casos={casos} />}

      <div className="tarjeta tarjeta-lista">
        <ul className="lista-zonas">
          {zonas.map((z) => (
            <li key={z.municipio_id}>
              <button
                type="button" className="zona" aria-pressed={z.municipio_id === seleccionado}
                onClick={() => alSeleccionar(z.municipio_id === seleccionado ? null : z.municipio_id)}
              >
                <span>
                  <span className="zona-nombre">{nombreZona(z.municipio)}</span>
                  <span className="nota"> · {nombreZona(z.departamento)}</span>
                </span>
                <span className="zona-valor">{formatearPorcentaje(z.probabilidad_pct)}</span>
                <span className="zona-barra"><Insignia nivel={z.nivel_riesgo} /></span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="aviso">
        <h3>Una estimación exploratoria</h3>
        <p>
          Estas probabilidades salen de un modelo de referencia entrenado con 13 semanas de 2026
          en cuatro municipios. Sirven para orientar dónde mirar primero; no son un diagnóstico
          ni una garantía, y todavía no validan las metas de precisión del proyecto.
        </p>
      </div>
    </section>
  );
}
