import { useId, useState } from "react";

/** Fechas UTC: solo se aplica un rango válido; no dispara consultas al escribir. */
export function FiltrosFechas({ alAplicar }) {
  const id = useId();
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [error, setError] = useState(false);
  function aplicar(evento) {
    evento.preventDefault();
    const invalido = Boolean(desde && hasta && desde > hasta);
    setError(invalido);
    if (!invalido) alAplicar({ desde, hasta });
  }
  function limpiar() {
    setDesde(""); setHasta(""); setError(false);
    alAplicar({ desde: "", hasta: "" });
  }
  return (
    <form className="filtros-periodo" onSubmit={aplicar} noValidate aria-label="Filtro de fechas">
      <div className="campo">
        <label htmlFor={`${id}-desde`}>Desde</label>
        <input id={`${id}-desde`} type="date" value={desde} onChange={(e) => setDesde(e.target.value)} aria-invalid={error} aria-describedby={error ? `${id}-error` : undefined} />
      </div>
      <div className="campo">
        <label htmlFor={`${id}-hasta`}>Hasta</label>
        <input id={`${id}-hasta`} type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} aria-invalid={error} aria-describedby={error ? `${id}-error` : undefined} />
      </div>
      <button type="submit" className="boton boton-suave">Aplicar fechas</button>
      <button type="button" className="boton boton-suave" onClick={limpiar}>Limpiar fechas</button>
      {error && <p id={`${id}-error`} role="alert">La fecha inicial no puede ser posterior a la final.</p>}
    </form>
  );
}
