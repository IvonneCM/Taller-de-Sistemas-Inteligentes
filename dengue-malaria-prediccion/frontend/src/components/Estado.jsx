// Estados de carga, error y vacío, con la misma forma en todas las vistas.

export function Cargando({ etiqueta = "Cargando…" }) {
  return (
    <div className="tarjeta esqueleto" role="status" aria-live="polite" aria-busy="true">
      <span /><span /><span />
      <span className="solo-lectores">{etiqueta}</span>
    </div>
  );
}

export function ErrorCarga({ error, alReintentar, titulo = "No se pudieron cargar los datos" }) {
  return (
    <div className="tarjeta estado" role="alert">
      <h3>{titulo}</h3>
      <p className="secundario">{error?.message ?? "Ocurrió un error inesperado."}</p>
      {error?.requestId && <p className="nota">Código de soporte: {error.requestId}</p>}
      {alReintentar && <button type="button" className="boton boton-suave" onClick={alReintentar}>Reintentar</button>}
    </div>
  );
}

export function Vacio({ titulo, children, icono }) {
  return (
    <div className="tarjeta estado">
      {icono}
      <h3>{titulo}</h3>
      {children && <p className="secundario">{children}</p>}
    </div>
  );
}
