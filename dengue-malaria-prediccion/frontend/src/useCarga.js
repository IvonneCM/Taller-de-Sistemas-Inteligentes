import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Carga asíncrona con estados explícitos (cargando | listo | error) y reintento.
 * `cargar` debe ser estable (useCallback) o `claves` debe cambiar cuando cambie.
 */
export function useCarga(cargar, claves = []) {
  const [estado, setEstado] = useState({ fase: "cargando", datos: null, error: null });
  const numero = useRef(0);

  const ejecutar = useCallback(() => {
    const actual = ++numero.current;
    setEstado((previo) => ({ ...previo, fase: "cargando", error: null }));
    cargar().then(
      (datos) => { if (actual === numero.current) setEstado({ fase: "listo", datos, error: null }); },
      (error) => { if (actual === numero.current) setEstado({ fase: "error", datos: null, error }); },
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, claves);

  useEffect(() => { ejecutar(); return () => { numero.current += 1; }; }, [ejecutar]);
  return { ...estado, recargar: ejecutar };
}
