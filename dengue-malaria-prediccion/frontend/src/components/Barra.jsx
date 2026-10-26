import { etiquetaRol } from "../format.js";
import { Gota, Mosquito } from "./Iconos.jsx";
import { Segmentado } from "./Segmentado.jsx";

const ENFERMEDADES = [
  { valor: "malaria", etiqueta: "Malaria", icono: <Mosquito tamano={18} /> },
  { valor: "dengue", etiqueta: "Dengue", icono: <Gota tamano={18} /> },
];

export function Barra({ usuario, enfermedad, alCambiarEnfermedad, alSalir }) {
  return (
    <header className="barra">
      <div className="marca">
        <Mosquito tamano={26} />
        <span>Vigilancia de brotes</span>
      </div>
      <div className="barra-derecha">
        <Segmentado etiqueta="Enfermedad" opciones={ENFERMEDADES} valor={enfermedad} alCambiar={alCambiarEnfermedad} />
        <div className="usuario">
          <strong>{etiquetaRol(usuario.rol)}</strong>
        </div>
        <button type="button" className="boton boton-suave" onClick={alSalir}>Salir</button>
      </div>
    </header>
  );
}
