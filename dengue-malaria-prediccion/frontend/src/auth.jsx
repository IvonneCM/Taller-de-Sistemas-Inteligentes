import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { alCambiarSesion, entrar, restaurarSesion, salir, usuarioDelToken } from "./api.js";

const Contexto = createContext(null);

export function ProveedorSesion({ children }) {
  const [estado, setEstado] = useState("cargando"); // cargando | anonimo | autenticado
  const [usuario, setUsuario] = useState(null);
  const [aviso, setAviso] = useState(null);

  useEffect(() => {
    let activo = true;
    restaurarSesion().then((u) => {
      if (!activo) return;
      setUsuario(u);
      setEstado(u ? "autenticado" : "anonimo");
    });
    const baja = alCambiarSesion((evento) => {
      if (evento === "sesion-vencida") {
        setAviso("Tu sesión venció. Vuelve a entrar.");
        setUsuario(null);
        setEstado("anonimo");
      }
    });
    return () => { activo = false; baja(); };
  }, []);

  const iniciar = useCallback(async (email, password) => {
    const u = await entrar(email, password);
    setAviso(null);
    setUsuario(u ?? usuarioDelToken());
    setEstado("autenticado");
  }, []);

  const cerrar = useCallback(async () => {
    setUsuario(null);
    setEstado("anonimo");
    setAviso(null);
    await salir();
  }, []);

  const valor = useMemo(
    () => ({ estado, usuario, aviso, iniciar, cerrar }),
    [estado, usuario, aviso, iniciar, cerrar],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useSesion debe usarse dentro de <ProveedorSesion>.");
  return valor;
}
