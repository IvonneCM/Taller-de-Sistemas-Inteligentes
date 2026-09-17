# Resumen de calidad del pipeline de datos

Generado: 2026-09-16T22:24:20.716140

Duracion de ejecucion: 0.13 segundos

## Epidemiologia

```json
{
  "dengue_municipal": {
    "recibidos": 28,
    "validos": 28,
    "rechazados": 0
  },
  "malaria_municipal": {
    "recibidos": 21,
    "validos": 21,
    "rechazados": 0
  },
  "dengue_semanal_nacional": {
    "recibidos": 13,
    "provisionales": 13,
    "rechazados": 0
  },
  "municipios_sin_reporte_dengue": [
    "BELLA FLOR",
    "EUREKA(SANTOS MERCADO)",
    "INGAVI(HUMAITA)",
    "NACEBE(SANTA ROSA DEL ABUNA)",
    "NUEVO MANOA(NUEVA ESPERANZA)",
    "PORVENIR",
    "PUERTO GONZALO MORENO",
    "PUERTO RICO",
    "REYES",
    "SAN LORENZO(PND)",
    "SAN PEDRO(PND)",
    "SANTA ROSA (BNI)",
    "SENA",
    "VILLA NUEVA (LOMA ALTA)"
  ],
  "municipios_sin_reporte_malaria": [
    "ALTO BENI",
    "APOLO",
    "BERMEJO",
    "BUENA VISTA",
    "CAMIRI",
    "CARANAVI",
    "CARAPARI",
    "CERCADO TJ",
    "CORIPATA",
    "LA ASUNTA",
    "LA GUARDIA",
    "MACHARETI",
    "MAPIRI",
    "MONTERO",
    "PALOS BLANCOS",
    "PUERTO QUIJARRO",
    "SAN BORJA",
    "SANTA CRUZ DE LA SIERRA",
    "TEOPONTE",
    "VILLA MONTES",
    "YACUIBA"
  ]
}
```

## Clima

```json
{
  "dias_esperados_calendario_global": 81,
  "mediana_historica_por_semana_aplicable": false,
  "municipios_por_nivel_confianza": {
    "confianza_baja": [
      "PALOS BLANCOS"
    ],
    "confianza_normal": [
      "GUAYARAMERIN",
      "IXIAMAS",
      "PALOS BLANCOS",
      "SAN BUENAVENTURA"
    ]
  },
  "semanas_datos_insuficientes": []
}
```

## Reglas no aplicables con los datos actuales

- Mediana historica por semana del anio (5.2, paso 2): requiere mas de un anio de observaciones; el dataset actual solo cubre 2026.
