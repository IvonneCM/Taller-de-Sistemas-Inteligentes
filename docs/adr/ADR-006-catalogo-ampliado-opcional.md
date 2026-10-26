# ADR-006: Ampliar el catálogo de municipios más allá de la zona piloto (opcional)

- **Estado:** Propuesto (opt-in; no se ejecuta por defecto)
- **Fecha:** 2026-10-26
- **Decisores:** Tania Pérez (capa de datos). Pendiente de comunicar al equipo.
- **Relacionado:** decisión 1 del reparto "Listo para Empezar" (zona piloto = 4 municipios), `docs/adr/ADR-005-malaria-acumulado-en-bd.md`, `docs/contrato_esquema_bd.md`, `dengue-malaria-prediccion/app/etl/ampliar_catalogo.py`

## Contexto

`seed_catalogo` carga solo 4 municipios (Guayaramerín, Ixiamas, Palos Blancos, San
Buenaventura). Los datos reales cubren 28 municipios con dengue y 22 con malaria, y los
brotes están en municipios que el catálogo no tiene (San Borja: 140 casos; Caranavi: 60).
Con 4 municipios el máximo semanal es 5 casos: casi no hay brotes que predecir ni validar
(TASK-034), y la base recibe solo 52 de las 364 filas semanales de dengue.

`municipios.geometria` es MULTIPOLYGON NOT NULL. No hay límites oficiales del INE.

## Decisión

Agregar un comando **opcional**, `python -m app.etl.ampliar_catalogo`, que añade los 38
municipios restantes de `data/reference/`. No cambia `seed_catalogo`, no cambia los tests
ni el comportamiento por defecto: quien no lo ejecuta sigue con 4 municipios. Se corre
antes de `seed_demo`, que entonces carga los casos y predicciones de todos.

Geometría: límite administrativo de OpenStreetMap (ODbL) cuando existe (37 de 38;
`scripts/geocodificar_limites.py`); cuadrado referencial de ~5 km si solo hay un punto
(Santa Rosa de Yacuma). Los 4 municipios piloto conservan su cuadrado referencial.

## Consecuencias

- **Positivas:** 28 municipios con dengue en la base (364 filas semanales en vez de 52);
  malaria pasa de 3 a 21 filas; las 28 predicciones cubren a San Borja y Caranavi.
- **Negativas / a vigilar:**
  - **El catálogo ampliado deja al descubierto la debilidad del modelo baseline.** Con 13
    semanas de datos, el modelo da 83,7 % a Santa Cruz de la Sierra (9 casos en total) y
    63,8 % a San Borja (140 casos, el epicentro), y emite alertas con `nivel_confianza`
    "alto". No son predicciones creíbles por municipio. No debe presentarse como
    resultado real; debe declararse en TASK-036 y en el Risk Register.
  - Mezcla de geometrías: 4 municipios con cuadrado referencial y 37 con límite real.
  - Los límites de OSM no son los oficiales del INE; reemplazar cuando haya fuente oficial.
  - Contradice la decisión 1 del reparto (zona piloto = 4): requiere que el equipo lo acepte.
  - `municipios.nombre` no es UNIQUE y los conectores buscan por nombre (hoy no hay repetidos).
- **Cómo revertir:** borrar la base local y volver a ejecutar `seed_catalogo`; el comando es
  opt-in y no deja nada fuera de la base.
