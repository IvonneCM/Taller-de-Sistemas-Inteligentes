import { useCallback, useId, useMemo, useState } from "react";
import { pedir } from "../api.js";
import { fechaLarga, formatearPorcentaje, nombreZona } from "../format.js";
import { useCarga } from "../useCarga.js";
import { Cargando, ErrorCarga, Vacio } from "./Estado.jsx";
import { Insignia } from "./PanelDengue.jsx";

function TablaHistorial({ zonaId }) {
  const cargar = useCallback(() => pedir(`/zonas/${zonaId}/historial`), [zonaId]);
  const carga = useCarga(cargar, [zonaId]);

  if (carga.fase === "cargando") return <Cargando etiqueta="Cargando el historial" />;
  if (carga.fase === "error") return <ErrorCarga error={carga.error} alReintentar={carga.recargar} titulo="No se pudo cargar el historial" />;

  const { predicciones, brotes_confirmados: brotes, ventana_correlacion_dias: ventana } = carga.datos;
  if (!predicciones.length) {
    return <Vacio titulo="Esta zona aún no tiene predicciones">Cuando el modelo genere predicciones, se compararán aquí con los brotes confirmados.</Vacio>;
  }

  return (
    <>
      <div className="tarjeta tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th scope="col">Generada</th><th scope="col">Enfermedad</th><th scope="col">Riesgo</th>
              <th scope="col">Estimada para</th><th scope="col">Brote confirmado</th>
            </tr>
          </thead>
          <tbody>
            {predicciones.map((p) => (
              <tr key={p.prediccion_id}>
                <td>{fechaLarga(p.fecha_generacion)}</td>
                <td className="mayuscula">{p.enfermedad}</td>
                <td><Insignia nivel={p.nivel_riesgo} /> <span className="nota numero sin-corte">{formatearPorcentaje(p.probabilidad_pct)}</span></td>
                <td>{fechaLarga(p.fecha_estimada_riesgo)}</td>
                <td>{p.brote_confirmado ? `Sí, el ${fechaLarga(p.fecha_brote_confirmado)}` : "Sin brote registrado"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="aviso">
        <h3>Cómo se compara</h3>
        <p>
          Una predicción se marca como acertada si hay un brote confirmado de la misma enfermedad
          a no más de {ventana} días de la fecha estimada. {brotes.length === 0 &&
            "Todavía no hay brotes confirmados cargados para esta zona, por eso ninguna aparece como acertada."}
        </p>
      </div>
    </>
  );
}

/** Historial de predicciones frente a brotes confirmados (TASK-029); solo técnicos. */
export function Historial({ zonas }) {
  const id = useId();
  const opciones = useMemo(() => {
    const vistas = new Map();
    (zonas ?? []).forEach((z) => vistas.set(z.municipio_id, z.municipio));
    return [...vistas].map(([valor, nombre]) => ({ valor, nombre: nombreZona(nombre) }));
  }, [zonas]);
  const [elegida, setElegida] = useState(null);
  const zonaId = elegida ?? opciones[0]?.valor ?? null;

  if (!opciones.length) {
    return <div className="pagina-estrecha"><Vacio titulo="No hay zonas con predicciones">El historial aparece cuando una zona tiene predicciones.</Vacio></div>;
  }

  return (
    <section className="pagina-estrecha aparece" aria-label="Historial">
      <div className="campo">
        <label htmlFor={`${id}-zona`}>Zona</label>
        <select id={`${id}-zona`} value={zonaId} onChange={(e) => setElegida(Number(e.target.value))}>
          {opciones.map((o) => <option key={o.valor} value={o.valor}>{o.nombre}</option>)}
        </select>
      </div>
      <TablaHistorial zonaId={zonaId} />
    </section>
  );
}
