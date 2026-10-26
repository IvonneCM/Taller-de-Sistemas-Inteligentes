import { useId, useState } from "react";
import { enviarArchivo } from "../api.js";
import { fechaLarga, formatearEntero, nombreZona } from "../format.js";
import { Cargando, ErrorCarga } from "./Estado.jsx";

const RUTA = "/admin/boletines";

function accion(m) {
  if (m.accion === "nuevo") return "Se agrega";
  if (m.accion === "actualiza") return `Reemplaza el boletín N.º ${m.boletin_anterior}`;
  return `Sin cambios: ya tiene el N.º ${m.boletin_anterior}`;
}

function Resultado({ r }) {
  return (
    <div className="tarjeta resultado-boletin" aria-live="polite">
      <div className="tarjeta-titulo">
        <h3>Boletín de la semana {r.semana} · {r.anio}</h3>
        <p className="nota">Tabla «Dinámica semanal de casos de dengue por municipio», página {r.pagina}.</p>
      </div>
      <div className="tarjeta-cuerpo">
        <p className="verificacion-ok">{r.verificacion}</p>
        <ul className="cifras-boletin">
          <li><strong>{formatearEntero(r.total_casos)}</strong><span className="nota">casos de dengue (SE 1 a {r.semana})</span></li>
          <li><strong>{r.municipios_en_boletin}</strong><span className="nota">municipios en el boletín</span></li>
          <li><strong>{r.municipios.length}</strong><span className="nota">del catálogo del sistema</span></li>
        </ul>
        {r.municipios.length > 0 ? (
          <div className="tabla-contenedor">
            <table className="tabla">
              <caption>Municipios del catálogo</caption>
              <thead><tr><th scope="col">Municipio</th><th scope="col">Casos</th><th scope="col">Qué pasa</th><th scope="col">Semanas nuevas</th><th scope="col">Semanas corregidas</th></tr></thead>
              <tbody>
                {r.municipios.map((m) => (
                  <tr key={m.municipio_id}>
                    <th scope="row">{nombreZona(m.municipio)}</th>
                    <td>{formatearEntero(m.casos)}</td>
                    <td>{accion(m)}</td>
                    <td>{m.semanas_nuevas}</td>
                    <td>{m.semanas_revisadas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="secundario">Ningún municipio del boletín está en el catálogo del sistema.</p>}
        {r.revisiones.length > 0 && (
          <details className="mas">
            <summary>{r.revisiones.length} {r.revisiones.length === 1 ? "corrección" : "correcciones"} a semanas ya cargadas</summary>
            <ul className="lista-simple">
              {r.revisiones.map((v) => (
                <li key={`${v.municipio}-${v.semana}`}>{nombreZona(v.municipio)}, semana {v.semana}: {v.antes} → {v.despues} casos</li>
              ))}
            </ul>
          </details>
        )}
        {r.fuera_de_catalogo.length > 0 && (
          <details className="mas">
            <summary>{r.fuera_de_catalogo.length} municipios del boletín no están en el catálogo y se omiten</summary>
            <p>{r.fuera_de_catalogo.map(nombreZona).join(", ")}.</p>
          </details>
        )}
      </div>
    </div>
  );
}

/** Ingesta asistida: una persona sube el PDF, el sistema lo verifica y lo guarda tras confirmar (REQ-014). */
export function CargaBoletin({ ultimaSemana, alGuardar }) {
  const id = useId();
  const [archivo, setArchivo] = useState(null);
  const [estado, setEstado] = useState({ fase: "inicio" });

  async function enviar(ruta, fase, siguiente) {
    setEstado((e) => ({ ...e, fase }));
    try {
      const resultado = await enviarArchivo(ruta, archivo);
      setEstado({ fase: siguiente, resultado });
      if (siguiente === "guardado") alGuardar?.();
    } catch (error) {
      setEstado({ fase: "error", error });
    }
  }

  const { fase, resultado, error } = estado;
  const ocupado = fase === "revisando" || fase === "guardando";
  const hayCambios = resultado && resultado.filas_nuevas + resultado.filas_actualizadas > 0;

  return (
    <section className="panel-boletin aparece" aria-label="Cargar boletín">
      <div className="cabecera-panel">
        <p className="sobretitulo">Datos · Ingesta</p>
        <h2>Cargar un boletín epidemiológico</h2>
      </div>

      <div className="aviso aviso-datos">
        <p>
          {ultimaSemana
            ? <>El último dato semanal de dengue es de la <strong>semana {ultimaSemana.semana}</strong> ({fechaLarga(ultimaSemana.fecha)}). </>
            : "Todavía no hay casos semanales de dengue cargados. "}
          El sitio del Ministerio de Salud no permite descargar los boletines automáticamente: cuando salga uno nuevo, súbelo aquí.
        </p>
      </div>

      <div className="tarjeta barra-herramientas">
        <div className="campo">
          <label htmlFor={`${id}-pdf`}>Boletín en PDF</label>
          <input
            id={`${id}-pdf`} type="file" accept="application/pdf,.pdf" disabled={ocupado}
            onChange={(e) => { setArchivo(e.target.files?.[0] ?? null); setEstado({ fase: "inicio" }); }}
          />
        </div>
        <button type="button" className="boton" disabled={!archivo || ocupado} onClick={() => enviar(`${RUTA}/vista-previa`, "revisando", "previa")}>
          Revisar boletín
        </button>
      </div>
      <p className="nota">Primero se revisa sin guardar nada: el sistema busca la tabla de dengue por municipio y comprueba que cuadre con los totales impresos. Si algo no cuadra, el boletín se rechaza entero.</p>

      {fase === "revisando" && <Cargando etiqueta="Leyendo el boletín" />}
      {fase === "guardando" && <Cargando etiqueta="Guardando los casos" />}
      {fase === "error" && <ErrorCarga error={error} titulo="No se pudo usar este boletín" />}

      {resultado && !ocupado && (
        <>
          <Resultado r={resultado} />
          {fase === "previa" && (
            <div className="hero-acciones">
              {hayCambios
                ? <button type="button" className="boton" onClick={() => enviar(RUTA, "guardando", "guardado")}>Guardar en la base</button>
                : <p className="secundario">No hay nada nuevo que guardar.</p>}
              <button type="button" className="boton boton-suave" onClick={() => setEstado({ fase: "inicio" })}>Cancelar</button>
            </div>
          )}
          {fase === "guardado" && (
            <div className="aviso aviso-exito" role="status">
              <h3>Boletín guardado</h3>
              <p>{resultado.filas_nuevas} semanas nuevas y {resultado.filas_actualizadas} actualizadas. {resultado.nota}</p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
