# Municipios con epidemiología real pero sin cobertura climática

**Define:** Tania Perez — Frente "Pipeline de datos"
**Fecha:** 2026-10-25
**Para qué sirve:** lista de prioridad para solicitar/descargar estaciones
SENAMHI adicionales y así ampliar el dataset integrado más allá de los 4
municipios piloto (`n=4` → hasta `n=39` si se consigue clima real para
todos). Ver limitación de muestra pequeña en
`docs/resultados_linea_base.md` (Experimento C) y en
`docs/contrato_esquema_datos_procesados.md` §7.

## Por qué existe esta lista

El pipeline actual (`scripts/procesar_clima.py` → `limpieza_datos.py` →
`integrar_datos.py`) no está limitado por el código: está limitado por los
**datos crudos disponibles**. Verificado el 2026-10-25: tanto el archivo
versionado con DVC (`senamhi_raw_SE01_13_2026.csv`, bloqueado por
credenciales) como el único respaldo accesible sin credenciales
(`data/raw/clima/senamhi/senamhi_descarga_parcial.csv`, 16,778 registros)
cubren **las mismas 4 estaciones**: GUAYARAMERIN, IXIAMAS, PALOS BLANCOS,
SAN BUENAVENTURA.

En cambio, la epidemiología real (Boletín Epidemiológico N.º 13, 2026) ya
cubre muchos más municipios:

- **Dengue:** 28 municipios con registro válido.
- **Malaria:** 21 municipios con registro válido.
- **Unión (sin los 4 piloto):** 39 filas candidatas (un municipio puede
  aparecer una vez por dengue y otra por malaria si las fuentes no
  coinciden en el nombre de departamento — ver nota sobre RURRENABAQUE
  abajo).

Si se consigue clima real (no estimado, no interpolado) para estos
municipios, el dataset integrado de `docs/contrato_esquema_datos_procesados.md`
§7 crecería de 4 filas a hasta 39 — suficiente para que Adriana entrene
con regularización razonable en vez de sobreajustar con 0 grados de
libertad.

## Lista completa, ordenada por carga de enfermedad (prioridad de descarga)

| Municipio | Departamento/SEDES | Casos dengue (SE1-13) | Casos malaria (SE1-13) | Carga total |
|---|---|---|---|---|
| RIBERALTA | BENI | 4 | 682 | 686 |
| SAN BORJA | BENI | 140 | 0 | 140 |
| SENA | PANDO | 0 | 126 | 126 |
| EUREKA (SANTOS MERCADO) | PANDO | 0 | 58 | 58 |
| CARANAVI | LA PAZ | 60 | 0 | 60 |
| NUEVO MANOA (NUEVA ESPERANZA) | PANDO | 0 | 55 | 55 |
| PUERTO GONZALO MORENO | PANDO | 0 | 34 | 34 |
| NACEBE (SANTA ROSA DEL ABUNÁ) | PANDO | 0 | 32 | 32 |
| INGAVI (HUMAITA) | PANDO | 0 | 29 | 29 |
| SAN LORENZO (PND) | PANDO | 0 | 24 | 24 |
| COBIJA | PANDO | 1 | 21 | 22 |
| PUERTO RICO | PANDO | 0 | 22 | 22 |
| LA ASUNTA | LA PAZ | 19 | 0 | 19 |
| SANTA ROSA (BNI) | BENI | 0 | 19 | 19 |
| REYES | BENI | 0 | 18 | 18 |
| SAN PEDRO (PND) | PANDO | 0 | 15 | 15 |
| RURRENABAQUE | BENI | 15 | 0 (ver nota) | 15 |
| TRINIDAD | BENI | 12 | 2 | 14 |
| VILLA NUEVA (LOMA ALTA) | PANDO | 0 | 12 | 12 |
| BELLA FLOR | PANDO | 0 | 11 | 11 |
| SANTA CRUZ DE LA SIERRA | SANTA CRUZ | 9 | 0 | 9 |
| YACUIBA | TARIJA | 5 | 0 | 5 |
| PORVENIR | PANDO | 0 | 4 | 4 |
| MAPIRI | LA PAZ | 3 | 0 | 3 |
| LA GUARDIA | SANTA CRUZ | 3 | 0 | 3 |
| BERMEJO | TARIJA | 3 | 0 | 3 |
| CERCADO TJ | TARIJA | 3 | 0 | 3 |
| MONTERO | SANTA CRUZ | 2 | 0 | 2 |
| PUERTO QUIJARRO | SANTA CRUZ | 2 | 0 | 2 |
| MACHARETI | CHUQUISACA | 1 | 0 | 1 |
| ALTO BENI | LA PAZ | 1 | 0 | 1 |
| APOLO | LA PAZ | 1 | 0 | 1 |
| CORIPATA | LA PAZ | 1 | 0 | 1 |
| TEOPONTE | LA PAZ | 1 | 0 | 1 |
| BUENA VISTA | SANTA CRUZ | 1 | 0 | 1 |
| CAMIRI | SANTA CRUZ | 1 | 0 | 1 |
| CARAPARI | TARIJA | 1 | 0 | 1 |
| VILLA MONTES | TARIJA | 1 | 0 | 1 |
| RURRENABAQUE (malaria) | LA PAZ | — | 1 | 1 |

**Nota sobre RURRENABAQUE:** aparece dos veces porque la fuente de dengue
lo reporta bajo departamento BENI y la de malaria bajo LA PAZ (columna
`sedes_segun_tabla` del archivo de malaria). No se unificó unilateralmente
— es una divergencia real entre fuentes que debe confirmarse con SEDES
antes de tratarlo como un solo municipio o dos.

## Qué hacer con esta lista

1. **Priorizar por carga total** (columna derecha): RIBERALTA, SAN BORJA y
   SENA concentran la mayor carga de enfermedad sin cobertura climática —
   son los candidatos de mayor valor para pedir estación SENAMHI primero.
2. **Verificar disponibilidad real en SENAMHI (WIS 2.0)** antes de asumir
   que hay estación cercana — esta lista solo dice qué municipios *valen
   la pena* pedir, no que el dato exista.
3. Una vez con el clima real de cualquiera de estos municipios en
   `data/raw/clima/senamhi/`, correr `python scripts/pipeline_completo.py`
   — el pipeline ya está escrito para generalizar a más municipios, no
   hace falta tocar código, solo expandir `data/raw/`.

## Advertencia

Esta lista usa **datos epidemiológicos reales** (`dengue_municipal_validado.csv`,
`malaria_municipal_validado.csv`, ya filtrados por `estado_calidad == 'valido'`).
No contiene ninguna cifra climática ni estimada — es puramente un índice de
priorización para la adquisición de datos pendiente.
