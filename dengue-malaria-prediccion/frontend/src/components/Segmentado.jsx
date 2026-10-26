import { useRef } from "react";

/**
 * Control segmentado accesible. `rol="radio"` para elegir un valor (grupo de
 * opciones) y `rol="tab"` para cambiar de vista. Flechas izquierda/derecha
 * mueven la selección; solo la opción activa entra en el orden de tabulación.
 */
export function Segmentado({ opciones, valor, alCambiar, etiqueta, rol = "radio" }) {
  const botones = useRef([]);
  const esTab = rol === "tab";

  function alTeclear(evento, indice) {
    const paso = evento.key === "ArrowRight" || evento.key === "ArrowDown" ? 1
      : evento.key === "ArrowLeft" || evento.key === "ArrowUp" ? -1 : 0;
    if (!paso) return;
    evento.preventDefault();
    const siguiente = (indice + paso + opciones.length) % opciones.length;
    alCambiar(opciones[siguiente].valor);
    botones.current[siguiente]?.focus();
  }

  return (
    <div className="segmentado" role={esTab ? "tablist" : "radiogroup"} aria-label={etiqueta}>
      {opciones.map((opcion, indice) => {
        const activa = opcion.valor === valor;
        const atributos = esTab ? { "aria-selected": activa } : { "aria-checked": activa };
        return (
          <button
            key={opcion.valor}
            ref={(nodo) => { botones.current[indice] = nodo; }}
            type="button"
            role={rol}
            tabIndex={activa ? 0 : -1}
            onClick={() => alCambiar(opcion.valor)}
            onKeyDown={(evento) => alTeclear(evento, indice)}
            {...atributos}
          >
            {opcion.icono}
            {opcion.etiqueta}
          </button>
        );
      })}
    </div>
  );
}
