import { useId } from "react";
import { formatearEntero } from "../format.js";

const ANCHO = 640;
const ALTO = 250;
const MARGEN = { izq: 40, der: 8, arriba: 24, abajo: 30 };

/**
 * Casos por semana epidemiologica. Las ultimas `provisionales` semanas se rayan:
 * los boletines las corrigen al alza despues (en el Boletin N.º 13 la semana mas
 * reciente muestra solo una parte de los casos que terminan reportandose), asi que
 * una caida en ese extremo NO debe leerse como mejora.
 */
export function GraficoSemanal({ serie, provisionales = 1, titulo }) {
  const id = useId();
  if (!serie?.length) return null;
  const maximo = Math.max(1, ...serie.map((s) => s.casos));
  const techo = Math.ceil(maximo / 10) * 10 || 10;
  const util = ANCHO - MARGEN.izq - MARGEN.der;
  const alto = ALTO - MARGEN.arriba - MARGEN.abajo;
  const paso = util / serie.length;
  const ancho = Math.min(36, paso * 0.68);
  const marcas = [0, 0.5, 1].map((f) => Math.round(techo * f));
  const resumen = `${titulo}: ${serie.map((s) => `SE ${s.semana}: ${s.casos}`).join(", ")}. La última semana es provisional.`;

  return (
    <figure style={{ margin: 0 }}>
      <svg className="grafico" viewBox={`0 0 ${ANCHO} ${ALTO}`} role="img" aria-label={resumen}>
        <defs>
          <pattern id={`${id}-rayas`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="transparent" />
            <rect width="3" height="6" fill="var(--dengue)" opacity="0.45" />
          </pattern>
        </defs>
        {marcas.map((m) => {
          const y = MARGEN.arriba + alto - (m / techo) * alto;
          return (
            <g key={m}>
              <line className="rejilla-g" x1={MARGEN.izq} x2={ANCHO - MARGEN.der} y1={y} y2={y} />
              <text x={MARGEN.izq - 8} y={y + 4} textAnchor="end">{m}</text>
            </g>
          );
        })}
        {serie.map((s, i) => {
          const prov = i >= serie.length - provisionales;
          const h = (s.casos / techo) * alto;
          const x = MARGEN.izq + paso * i + (paso - ancho) / 2;
          const y = MARGEN.arriba + alto - h;
          return (
            <g key={s.fecha}>
              <rect
                className={`barra-g${prov ? " provisional" : ""}`} x={x} y={y} width={ancho} height={Math.max(h, 1)} rx="4"
                style={prov ? { fill: `url(#${id}-rayas)` } : undefined}
              >
                <title>{`SE ${s.semana} (${s.fecha}): ${formatearEntero(s.casos)} casos${prov ? " · provisional" : ""}`}</title>
              </rect>
              <text className="valor-g" x={x + ancho / 2} y={y - 6} textAnchor="middle">{s.casos}</text>
              <text x={x + ancho / 2} y={ALTO - 10} textAnchor="middle">{s.semana}</text>
            </g>
          );
        })}
      </svg>
      <figcaption className="leyenda-grafico">
        <span>Eje horizontal: semana epidemiológica</span>
        <span><i className="muestra" />Semana consolidada</span>
        <span><i className="muestra prov" />Provisional: suele corregirse al alza</span>
      </figcaption>
      <table className="solo-lectores">
        <caption>{titulo}</caption>
        <thead><tr><th>Semana epidemiológica</th><th>Casos</th></tr></thead>
        <tbody>{serie.map((s) => <tr key={s.fecha}><td>{s.semana}</td><td>{s.casos}</td></tr>)}</tbody>
      </table>
    </figure>
  );
}
