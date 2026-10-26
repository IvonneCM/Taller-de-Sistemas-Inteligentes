import { useId, useState } from "react";
import { useSesion } from "../auth.jsx";
import { Mosquito } from "./Iconos.jsx";

const FORMATO_CORREO = /^\S+@\S+\.\S+$/;

export const validarCorreo = (valor) => {
  if (!valor.trim()) return "Escribe tu correo.";
  return FORMATO_CORREO.test(valor.trim()) ? null : "Revisa el correo: falta algo, como el @ o el dominio.";
};
export const validarClave = (valor) => (valor ? null : "Escribe tu contraseña.");

/** Pantalla de acceso (TASK-037). Validación en línea, un solo botón principal. */
export function Acceso() {
  const { iniciar, aviso } = useSesion();
  const id = useId();
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [fallo, setFallo] = useState(null);

  const idCorreo = `${id}-correo`;
  const idClave = `${id}-clave`;

  async function enviar(evento) {
    evento.preventDefault();
    const nuevos = { correo: validarCorreo(correo), clave: validarClave(clave) };
    setErrores(nuevos);
    if (nuevos.correo || nuevos.clave) return;
    setEnviando(true);
    setFallo(null);
    try {
      await iniciar(correo.trim(), clave);
    } catch (error) {
      setFallo(error);
      setEnviando(false);
    }
  }

  return (
    <main className="acceso">
      <div className="acceso-contenido aparece">
        <header className="acceso-cabecera">
          <span className="icono"><Mosquito tamano={44} /></span>
          <h1>Vigilancia de malaria y dengue</h1>
          <p>Predicción temprana de brotes para los equipos de salud de Bolivia.</p>
        </header>

        <form className="tarjeta tarjeta-relleno" onSubmit={enviar} noValidate aria-label="Acceso">
          {aviso && !fallo && <div className="banner-info" role="status">{aviso}</div>}
          {fallo && <div className="banner-error" role="alert">{fallo.message}</div>}

          <div className="campo">
            <label htmlFor={idCorreo}>Correo</label>
            <input
              id={idCorreo} type="email" name="username" autoComplete="username" inputMode="email"
              value={correo} onChange={(e) => setCorreo(e.target.value)}
              onBlur={() => setErrores((p) => ({ ...p, correo: correo ? validarCorreo(correo) : null }))}
              aria-invalid={Boolean(errores.correo)} aria-describedby={errores.correo ? `${idCorreo}-error` : undefined}
              disabled={enviando}
            />
            {errores.correo && <span id={`${idCorreo}-error`} className="campo-error">{errores.correo}</span>}
          </div>

          <div className="campo">
            <label htmlFor={idClave}>Contraseña</label>
            <input
              id={idClave} type="password" name="password" autoComplete="current-password"
              value={clave} onChange={(e) => setClave(e.target.value)}
              aria-invalid={Boolean(errores.clave)} aria-describedby={errores.clave ? `${idClave}-error` : undefined}
              disabled={enviando}
            />
            {errores.clave && <span id={`${idClave}-error`} className="campo-error">{errores.clave}</span>}
          </div>

          <button type="submit" className="boton boton-ancho" disabled={enviando}>
            {enviando ? "Entrando…" : "Entrar"}
          </button>
        </form>

        <p className="nota">
          Acceso solo para personal de salud autorizado. El sistema trabaja con conteos agregados
          por municipio: no almacena datos de pacientes.
        </p>
      </div>
    </main>
  );
}
