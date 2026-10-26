import { etiquetaRol } from "../format.js";
import { Gota, Mosquito } from "./Iconos.jsx";
import { Segmentado } from "./Segmentado.jsx";

const ENFERMEDADES = [
  { valor: "malaria", etiqueta: "Malaria", icono: <Mosquito tamano={18} /> },
  { valor: "dengue", etiqueta: "Dengue", icono: <Gota tamano={18} /> },
];

// El selector de enfermedad lo usan el mapa, las alertas y el historial; la vista de campañas es solo de dengue.
export function Barra({ usuario, enfermedad, alCambiarEnfermedad, alSalir, mostrarEnfermedad = true }) {
  return (
    <header className="barra">
      <div className="marca">
        <Mosquito tamano={26} />
        <span>Vigilancia de brotes</span>
      </div>
      <div className="barra-derecha">
        {mostrarEnfermedad && (
          <Segmentado etiqueta="Enfermedad" opciones={ENFERMEDADES} valor={enfermedad} alCambiar={alCambiarEnfermedad} />
        )}
        <div className="usuario">
          <strong>{etiquetaRol(usuario.rol)}</strong>
        </div>
        <button type="button" className="boton boton-suave" onClick={alSalir}>Salir</button>
      </div>
    </header>
  );
}
