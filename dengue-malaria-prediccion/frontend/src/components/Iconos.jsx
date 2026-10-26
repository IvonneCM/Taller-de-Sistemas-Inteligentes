// Iconos de línea (SVG en línea, sin dependencias). Son decorativos: el texto
// que los acompaña es la etiqueta accesible.

const propsBase = {
  viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6,
  strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", focusable: "false",
};

/** Mosquito Anopheles estilizado: la marca de la malaria. */
export function Mosquito({ tamano = 24 }) {
  return (
    <svg {...propsBase} width={tamano} height={tamano}>
      <circle cx="12" cy="7.5" r="1.5" />
      <path d="M12 6V3" />
      <ellipse cx="12" cy="14" rx="1.9" ry="4" />
      <path d="M10.2 11.8C6.6 9.6 4.6 10.2 3.2 7.4 6.4 6.6 9.6 8 10.4 10.4" />
      <path d="M13.8 11.8c3.6-2.2 5.6-1.6 7-4.4-3.2-.8-6.4.6-7.2 3" />
      <path d="M10.2 15.5 6.2 18.6M10.3 17l-2.6 3.6M13.8 15.5l4 3.1M13.7 17l2.6 3.6" />
    </svg>
  );
}

export function Gota({ tamano = 20 }) {
  return (
    <svg {...propsBase} width={tamano} height={tamano}>
      <path d="M12 3.5C9 8 6.5 10.6 6.5 14a5.5 5.5 0 0 0 11 0c0-3.4-2.5-6-5.5-10.5Z" />
    </svg>
  );
}

export function Campana({ tamano = 40 }) {
  return (
    <svg {...propsBase} width={tamano} height={tamano}>
      <path d="M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 1.5h-15L6 16.5Z" />
      <path d="M10 20.5a2 2 0 0 0 4 0" />
    </svg>
  );
}
