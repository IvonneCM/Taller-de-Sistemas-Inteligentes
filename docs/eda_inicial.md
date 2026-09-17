# Análisis Exploratorio de Datos (EDA)
## Sistema de Predicción Temprana de Brotes de Dengue y Malaria

**Responsable:** Adriana Rocha Vedia  
**Sección del backlog:** Data  
**Estado:** EDA realizado con datos reales disponibles  
**Periodo epidemiológico:** SE1-SE13, 2026  
**Periodo climático analizado:** SE3-SE13, 2026  

---

# 1. Objetivo

El objetivo del Análisis Exploratorio de Datos (EDA) es evaluar la calidad,
cobertura y comportamiento de los datos disponibles para el desarrollo de un
sistema de predicción temprana de brotes de dengue y malaria.

El análisis busca principalmente:

- verificar la calidad de los datos obtenidos;
- identificar valores faltantes, registros atípicos y problemas de cobertura;
- analizar el comportamiento de temperatura, humedad y precipitación;
- identificar diferencias climáticas entre municipios;
- estudiar relaciones entre las variables climáticas;
- integrar la información climática y epidemiológica disponible;
- explorar posibles asociaciones entre clima, dengue y malaria;
- identificar limitaciones antes de iniciar el modelado predictivo.

El EDA se divide en tres componentes:

1. **EDA inicial:** perfilado general de los datos disponibles.
2. **EDA climático:** análisis detallado de los datos reales obtenidos de SENAMHI.
3. **EDA integrado:** análisis conjunto de clima, dengue y malaria.

---

# 2. Fuentes de datos

## 2.1 Datos epidemiológicos

Los datos epidemiológicos utilizados provienen del:

**Ministerio de Salud y Deportes de Bolivia — Boletín Epidemiológico N.º 13,
gestión 2026.**

Se dispone de información correspondiente a las semanas epidemiológicas
SE1-SE13 de 2026.

Los principales datasets utilizados son:

- `dengue_bolivia_municipal_SE01_13_2026.csv`
- `dengue_bolivia_semanal_SE01_13_2026.csv`
- `malaria_bolivia_municipal_SE01_13_2026.csv`

### Dengue

El dataset municipal de dengue contiene:

- departamento;
- municipio;
- año;
- casos acumulados SE1-SE13;
- incidencia por 10.000 habitantes;
- periodo;
- fuente;
- página de la fuente;
- notas metodológicas.

También se dispone de información semanal de dengue a nivel nacional.

### Malaria

El dataset municipal de malaria contiene:

- SEDES según la tabla oficial;
- municipio;
- año;
- periodo;
- casos de *P. vivax*;
- casos de *P. falciparum*;
- infecciones mixtas;
- total de casos de malaria;
- fuente;
- página de la fuente;
- notas metodológicas.

---

## 2.2 Datos climáticos

Los datos climáticos provienen de:

**SENAMHI Bolivia — WIS 2.0.**

La descarga fue automatizada mediante:

`scripts/descargar_senamhi.py`

El dataset climático RAW obtenido contiene:

**16.778 observaciones.**

Las variables utilizadas en el análisis son:

- temperatura del aire;
- humedad relativa;
- precipitación.

La cobertura temporal de los datos descargados es:

**14 de enero de 2026 al 4 de abril de 2026.**

Los municipios climáticos que coinciden con los datos epidemiológicos son:

- Guayaramerín;
- Ixiamas;
- Palos Blancos;
- San Buenaventura.

---

# 3. Pipeline de análisis

El flujo implementado actualmente es:

```text
Datos epidemiológicos reales
            +
Datos climáticos SENAMHI
            ↓
Control de calidad
            ↓
Procesamiento climático diario
            ↓
Agregación municipio-semana
            ↓
EDA climático
            ↓
Integración clima + epidemiología
            ↓
EDA integrado
```

Los principales scripts son:

- `scripts/descargar_senamhi.py`
- `scripts/procesar_clima.py`
- `scripts/eda_inicial.py`
- `scripts/eda_climatico.py`
- `scripts/integrar_datos.py`
- `scripts/eda_integrado.py`

---

# 4. Control de calidad de los datos climáticos

El procesamiento de los datos descargados de SENAMHI se realiza mediante:

`scripts/procesar_clima.py`

Antes de generar los datasets diario y semanal se ejecutó un control de
calidad sobre las observaciones.

Se identificaron:

**24 registros sospechosos.**

Todos correspondieron a:

`precipitacion_extrema_requiere_validacion`

Los registros sospechosos fueron separados para mantenerlos disponibles para
posterior revisión y evitar que valores extremos no validados distorsionen las
agregaciones.

Por tanto:

| Estado | Registros |
|---|---:|
| Registros RAW | 16.778 |
| Registros sospechosos | 24 |
| Registros utilizados | 16.754 |

El resultado del control de calidad se almacena en:

`data/processed/control_calidad_clima.csv`

Este procedimiento permite mantener la trazabilidad de las observaciones
descartadas durante el procesamiento.

---

# 5. Dataset climático diario

Después del control de calidad se generó:

`data/processed/clima_diario.csv`

El dataset contiene:

**274 registros municipio-día.**

La cobertura observada por municipio fue:

| Municipio | Días disponibles |
|---|---:|
| Guayaramerín | 80 |
| Ixiamas | 80 |
| Palos Blancos | 60 |
| San Buenaventura | 54 |

Guayaramerín e Ixiamas presentan la mayor cantidad de observaciones.

Palos Blancos y especialmente San Buenaventura poseen menor cobertura, por lo
que sus estadísticas climáticas deben interpretarse considerando esta
limitación.

---

# 6. Dataset climático semanal

Para facilitar la futura integración con datos epidemiológicos se generó:

`data/processed/clima_semanal.csv`

El análisis principal considera las semanas epidemiológicas:

**SE3-SE13 de 2026.**

El dataset contiene:

**44 registros municipio-semana.**

Cada uno de los cuatro municipios posee 11 semanas representadas.

Sin embargo, la cantidad de días observados dentro de cada semana no es
idéntica.

La cobertura suficiente encontrada fue:

| Municipio | Semanas disponibles | Semanas con cobertura suficiente | Porcentaje |
|---|---:|---:|---:|
| Guayaramerín | 11 | 11 | 100.00 % |
| Ixiamas | 11 | 11 | 100.00 % |
| Palos Blancos | 11 | 6 | 54.55 % |
| San Buenaventura | 11 | 3 | 27.27 % |

Esto muestra una diferencia importante en la calidad temporal de las
observaciones entre municipios.

---

# 7. EDA climático

El análisis climático se ejecuta mediante:

`scripts/eda_climatico.py`

Este análisis estudia independientemente las observaciones reales obtenidas
de SENAMHI e incluye:

- estadísticas descriptivas;
- análisis de cobertura;
- distribuciones;
- detección de valores atípicos;
- boxplots por municipio;
- evolución temporal;
- comparación entre municipios;
- correlaciones entre variables climáticas;
- mapas de calor;
- análisis conjunto de temperatura, humedad y precipitación.

---

# 8. Comportamiento de las variables climáticas

## 8.1 Temperatura

Las temperaturas medias observadas durante el periodo fueron:

| Municipio | Temperatura media |
|---|---:|
| Guayaramerín | 26.61 °C |
| Ixiamas | 24.90 °C |
| Palos Blancos | 25.83 °C |
| San Buenaventura | 26.60 °C |

Ixiamas presentó la menor temperatura media del conjunto analizado.

Guayaramerín y San Buenaventura presentaron temperaturas medias similares,
cercanas a 26.6 °C.

Palos Blancos presentó un rango térmico amplio, con observaciones entre
aproximadamente **19.45 °C y 39.15 °C**.

### Hallazgo

El comportamiento de la temperatura no es exactamente igual entre los
municipios. Esto indica que mantener la dimensión geográfica será importante
en etapas posteriores y que utilizar únicamente un promedio climático global
podría ocultar diferencias locales.

---

## 8.2 Humedad relativa

La humedad relativa fue elevada durante el periodo analizado.

Las medias fueron:

| Municipio | Humedad media |
|---|---:|
| Guayaramerín | 91.70 % |
| Ixiamas | 89.33 % |
| Palos Blancos | 92.37 % |
| San Buenaventura | 91.43 % |

Palos Blancos presentó la mayor humedad media e Ixiamas la menor.

Aunque las medias municipales son relativamente próximas, las series y
distribuciones muestran variación dentro de cada municipio.

### Hallazgo

La humedad presenta variabilidad temporal que puede perderse si únicamente se
utiliza el promedio del periodo. Para el futuro modelado será más útil
conservar su comportamiento semanal.

---

## 8.3 Precipitación

La precipitación presentó mayor variabilidad que la temperatura y la humedad.

La precipitación media por día observado fue:

| Municipio | Precipitación media por día observado |
|---|---:|
| Guayaramerín | 7.03 mm |
| Ixiamas | 11.81 mm |
| Palos Blancos | 6.16 mm |
| San Buenaventura | 0.18 mm |

Ixiamas presentó el mayor valor medio dentro de las observaciones procesadas.

Sin embargo, la precipitación debe interpretarse junto con la cobertura de
datos.

Guayaramerín e Ixiamas presentan aproximadamente 96.10 % de cobertura diaria,
mientras que Palos Blancos presenta 71.43 % y San Buenaventura 62.34 %.

Por esta razón, el valor bajo observado en San Buenaventura no debe
interpretarse directamente como evidencia de que fue el municipio más seco,
ya que existe una cantidad mayor de días sin observaciones disponibles.

Además, durante el control de calidad se detectaron 24 registros de
precipitación extrema que fueron marcados para validación.

### Hallazgo

La precipitación es una de las variables que requiere mayor cuidado durante el
procesamiento debido a:

- su alta variabilidad;
- presencia de valores extremos;
- diferencias de cobertura entre municipios;
- sensibilidad de las agregaciones a observaciones faltantes.

---

# 9. Relaciones entre las variables climáticas

Además del análisis individual, se estudiaron las relaciones entre
temperatura, humedad y precipitación.

---

## 9.1 Temperatura y humedad

Las correlaciones observadas fueron:

| Municipio | Correlación temperatura-humedad |
|---|---:|
| Guayaramerín | -0.818 |
| Ixiamas | -0.964 |
| Palos Blancos | -0.800 |
| San Buenaventura | -0.964 |

En los cuatro municipios se encontró una asociación inversa marcada.

Dentro del periodo observado, los aumentos de temperatura tienden a coincidir
con disminuciones de humedad relativa.

La relación fue especialmente fuerte en Ixiamas y San Buenaventura.

### Hallazgo

La relación inversa temperatura-humedad es uno de los patrones climáticos más
consistentes encontrados en el EDA.

Esto también indica que ambas variables contienen información relacionada, lo
que deberá considerarse posteriormente durante la selección de características
del modelo.

---

## 9.2 Temperatura y precipitación

Las correlaciones fueron:

| Municipio | Correlación temperatura-precipitación |
|---|---:|
| Guayaramerín | -0.391 |
| Ixiamas | -0.282 |
| Palos Blancos | -0.055 |
| San Buenaventura | 0.500 |

Guayaramerín e Ixiamas presentan asociaciones negativas débiles o moderadas.

En Palos Blancos prácticamente no se observa una relación lineal.

San Buenaventura presenta una asociación positiva en las observaciones
disponibles.

Sin embargo, San Buenaventura también posee menor cobertura climática, por lo
que este resultado debe interpretarse con precaución.

### Hallazgo

No existe un patrón uniforme entre temperatura y precipitación para los cuatro
municipios.

Esto muestra que las relaciones climáticas pueden variar geográficamente.

---

## 9.3 Humedad y precipitación

Las correlaciones observadas fueron:

| Municipio | Correlación humedad-precipitación |
|---|---:|
| Guayaramerín | 0.582 |
| Ixiamas | 0.345 |
| Palos Blancos | -0.018 |
| San Buenaventura | -0.500 |

Guayaramerín presenta la asociación positiva más clara.

Ixiamas también presenta una asociación positiva, aunque menor.

En Palos Blancos prácticamente no se observa una relación lineal.

San Buenaventura presenta una asociación negativa en los datos disponibles,
aunque nuevamente debe considerarse su menor cobertura.

### Hallazgo

Las relaciones entre humedad y precipitación tampoco son homogéneas entre
municipios.

Por ello, el análisis respalda conservar información geográfica y temporal
durante el futuro feature engineering.

---

# 10. Integración de datos climáticos y epidemiológicos

La integración se realiza mediante:

`scripts/integrar_datos.py`

Los municipios con información coincidente de **clima y dengue** son:

- Guayaramerín;
- Ixiamas;
- Palos Blancos;
- San Buenaventura.

Los municipios con información coincidente de **clima y malaria** son:

- Guayaramerín;
- Ixiamas;
- San Buenaventura.

Palos Blancos no presenta información municipal coincidente de malaria en el
dataset utilizado.

El resultado se almacena en:

`data/processed/dataset_integrado_municipal.csv`

---

# 11. Cobertura del dataset integrado

La cobertura climática utilizada para interpretar los resultados integrados es:

| Municipio | Cobertura diaria | Semanas con cobertura suficiente | Cobertura climática alta |
|---|---:|---:|---|
| Guayaramerín | 96.10 % | 100.00 % | Sí |
| Ixiamas | 96.10 % | 100.00 % | Sí |
| Palos Blancos | 71.43 % | 54.55 % | No |
| San Buenaventura | 62.34 % | 27.27 % | No |

### Hallazgo

Guayaramerín e Ixiamas poseen actualmente la información climática más
completa.

Las relaciones observadas para Palos Blancos y San Buenaventura deben
interpretarse con mayor precaución.

---

# 12. Comportamiento epidemiológico

## 12.1 Dengue

Los casos acumulados SE1-SE13 fueron:

| Municipio | Casos acumulados | Incidencia por 10.000 habitantes |
|---|---:|---:|
| San Buenaventura | 22 | 21.7 |
| Ixiamas | 15 | 12.0 |
| Guayaramerín | 9 | 2.2 |
| Palos Blancos | 5 | 1.9 |

San Buenaventura presenta el mayor número de casos y la mayor incidencia entre
los municipios integrados.

Ixiamas ocupa el segundo lugar tanto en casos como en incidencia.

### Hallazgo

El número absoluto de casos y la incidencia deben analizarse conjuntamente,
ya que el número de casos por sí solo no considera las diferencias de
población entre municipios.

---

## 12.2 Malaria

Los casos acumulados disponibles fueron:

| Municipio | P. vivax | P. falciparum | Mixta | Total |
|---|---:|---:|---:|---:|
| Guayaramerín | 199 | 87 | 7 | 293 |
| Ixiamas | 100 | 52 | 4 | 156 |
| San Buenaventura | 1 | 0 | 0 | 1 |
| Palos Blancos | Sin dato | Sin dato | Sin dato | Sin dato |

En Guayaramerín e Ixiamas predomina *P. vivax*.

Guayaramerín presenta el mayor número de casos de malaria entre los municipios
integrados.

### Hallazgo

El comportamiento espacial de malaria es diferente al observado para dengue.

Mientras San Buenaventura presenta los mayores valores de dengue dentro del
grupo analizado, Guayaramerín concentra la mayor cantidad de casos de malaria.

Esto refuerza la necesidad de analizar ambas enfermedades de forma separada
durante el futuro modelado.

---

# 13. EDA integrado: clima + dengue + malaria

El análisis conjunto se realizó mediante:

`scripts/eda_integrado.py`

El objetivo fue explorar si las diferencias climáticas observadas entre
municipios presentan algún patrón conjunto con los datos epidemiológicos
disponibles de dengue y malaria.

Se utilizaron tres variables climáticas:

- temperatura media;
- humedad media;
- precipitación media por día observado.

Y tres indicadores epidemiológicos:

- casos acumulados de dengue;
- incidencia de dengue por 10.000 habitantes;
- casos acumulados de malaria.

Para estudiar las relaciones se calcularon correlaciones de **Pearson** y
**Spearman**.

Pearson permite explorar asociaciones lineales entre las variables, mientras
que Spearman permite analizar si existe una relación monotónica basada en el
orden relativo de las observaciones.

---

## 13.1 Temperatura y dengue

Los resultados fueron:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Temperatura - casos de dengue | 4 | 0.116 | 0.000 |
| Temperatura - incidencia de dengue | 4 | 0.060 | 0.000 |

Los coeficientes obtenidos son cercanos a cero.

### Hallazgo

Dentro de los cuatro municipios disponibles, **no se observa una asociación
clara entre la temperatura media del periodo y los casos acumulados o la
incidencia acumulada de dengue**.

Esto no significa que la temperatura no sea relevante para el dengue.

El análisis actual compara promedios climáticos con casos acumulados, mientras
que una posible relación epidemiológica puede depender de cambios climáticos
semanales y de sus efectos con varias semanas de retraso.

Por tanto, este resultado refuerza la necesidad de realizar posteriormente un
análisis temporal con variables rezagadas.

---

## 13.2 Humedad y dengue

Los resultados fueron:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Humedad - casos de dengue | 4 | -0.447 | -0.800 |
| Humedad - incidencia de dengue | 4 | -0.389 | -0.800 |

Pearson muestra una asociación negativa moderada en la pequeña muestra
disponible.

Spearman presenta una asociación negativa más marcada.

### Hallazgo

Los municipios con mayor humedad media tienden, dentro de estas cuatro
observaciones, a ocupar posiciones menores en casos e incidencia de dengue.

Sin embargo, **este resultado es únicamente exploratorio** debido al tamaño
de la muestra (`n = 4`).

No puede concluirse a partir de estos datos que una mayor humedad produzca una
reducción del dengue.

El patrón deberá volver a evaluarse cuando existan observaciones
municipio-semana suficientes.

---

## 13.3 Precipitación y dengue

Los resultados fueron:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Precipitación - casos de dengue | 4 | -0.432 | -0.200 |
| Precipitación - incidencia de dengue | 4 | -0.483 | -0.200 |

Pearson presenta asociaciones negativas moderadas, mientras que Spearman
muestra relaciones considerablemente más débiles.

### Hallazgo

No se identifica un patrón suficientemente consistente para establecer una
relación entre precipitación y dengue con los datos actuales.

La diferencia entre Pearson y Spearman también muestra que la relación
observada depende de la forma en que se comparan las cuatro observaciones.

Además, Palos Blancos y San Buenaventura presentan menor cobertura climática,
lo que añade incertidumbre a la comparación.

---

## 13.4 Temperatura y malaria

La relación obtenida fue:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Temperatura - malaria | 3 | -0.029 | 0.500 |

Pearson es prácticamente cero, mientras que Spearman presenta una asociación
positiva moderada.

### Hallazgo

Los dos métodos no muestran un patrón consistente.

Además, únicamente existen tres municipios con información coincidente de
malaria.

Por tanto, actualmente **no existe evidencia suficiente para interpretar una
relación entre temperatura media y malaria**.

---

## 13.5 Humedad y malaria

Los resultados fueron:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Humedad - malaria | 3 | 0.068 | 0.500 |

La correlación lineal de Pearson es cercana a cero, mientras que Spearman
presenta una asociación positiva moderada.

### Hallazgo

Al igual que con temperatura, los resultados no son suficientemente
consistentes para establecer un patrón.

El tamaño de muestra (`n = 3`) limita considerablemente cualquier
interpretación estadística.

---

## 13.6 Precipitación y malaria

La relación obtenida fue:

| Relación | n | Pearson | Spearman |
|---|---:|---:|---:|
| Precipitación - malaria | 3 | 0.614 | 0.500 |

Esta es la asociación positiva más visible entre las variables climáticas y
malaria dentro del análisis actual.

Pearson presenta una correlación positiva de 0.614 y Spearman una correlación
de 0.500.

### Hallazgo

Los tres municipios disponibles sugieren preliminarmente que mayores niveles
de precipitación podrían coincidir con mayores cantidades acumuladas de
malaria.

Sin embargo, con solamente tres observaciones este resultado **no debe
interpretarse como evidencia de una relación estadística o causal**.

Debe considerarse únicamente una hipótesis exploratoria que podrá evaluarse
cuando se disponga de una serie temporal y un mayor número de observaciones.

---

# 14. Resumen de relaciones clima-enfermedad

Los resultados exploratorios obtenidos fueron:

| Variable climática | Variable epidemiológica | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| Temperatura | Dengue | 4 | 0.116 | 0.000 |
| Temperatura | Incidencia dengue | 4 | 0.060 | 0.000 |
| Temperatura | Malaria | 3 | -0.029 | 0.500 |
| Humedad | Dengue | 4 | -0.447 | -0.800 |
| Humedad | Incidencia dengue | 4 | -0.389 | -0.800 |
| Humedad | Malaria | 3 | 0.068 | 0.500 |
| Precipitación | Dengue | 4 | -0.432 | -0.200 |
| Precipitación | Incidencia dengue | 4 | -0.483 | -0.200 |
| Precipitación | Malaria | 3 | 0.614 | 0.500 |

Los resultados permiten identificar algunos patrones preliminares, pero
también muestran que **no existe actualmente una relación clima-enfermedad
simple y uniforme**.

En particular:

- la temperatura media presenta poca asociación lineal con dengue;
- la humedad presenta asociaciones negativas con dengue en la muestra actual;
- la precipitación presenta asociaciones negativas moderadas con dengue según
  Pearson, pero débiles según Spearman;
- la precipitación presenta la asociación positiva más visible con malaria;
- varias relaciones cambian considerablemente entre Pearson y Spearman.

Estas diferencias muestran que las asociaciones observadas son sensibles al
reducido número de municipios disponibles.

---

## 14.1 Relación entre casos e incidencia de dengue

También se encontró una asociación muy elevada entre:

**casos acumulados de dengue e incidencia por 10.000 habitantes**

con:

- Pearson = **0.978**
- Spearman = **1.000**

Este resultado indica que, dentro de los cuatro municipios analizados, el
orden de los municipios según número de casos coincide con el orden según
incidencia.

Sin embargo, ambos indicadores representan aspectos relacionados del mismo
fenómeno epidemiológico y no deben interpretarse como variables completamente
independientes.

Para comparaciones entre municipios, la incidencia continúa siendo
especialmente importante porque considera el tamaño poblacional.

---

## 14.2 Diferencias entre Pearson y Spearman

El EDA mostró diferencias importantes entre ambos coeficientes.

Por ejemplo:

| Relación | Pearson | Spearman |
|---|---:|---:|
| Humedad - dengue | -0.447 | -0.800 |
| Precipitación - dengue | -0.432 | -0.200 |
| Temperatura - malaria | -0.029 | 0.500 |
| Humedad - malaria | 0.068 | 0.500 |

Estas diferencias indican que los resultados actuales son sensibles a los
valores concretos y al orden relativo de los pocos municipios disponibles.

Por ello, no sería apropiado seleccionar o descartar variables del futuro
modelo únicamente a partir de estas correlaciones.

---

# Advertencia sobre correlaciones elevadas

La matriz integrada produjo algunas correlaciones aparentemente muy altas,
por ejemplo:

- dengue - malaria: Pearson = -1.000;
- incidencia de dengue - malaria: Pearson = -0.999;
- dengue - malaria: Spearman = -1.000.

Estos valores **no deben interpretarse como evidencia de una relación
epidemiológica fuerte**.

La razón principal es que malaria solamente dispone de información para tres
municipios:

- Guayaramerín;
- Ixiamas;
- San Buenaventura.

Con `n = 3`, los coeficientes de correlación son extremadamente inestables y
pueden alcanzar valores cercanos a ±1 con facilidad.

Además, dengue y malaria representan enfermedades diferentes y el presente
EDA no controla otras variables epidemiológicas, demográficas, ambientales o
sociales.

Por esta razón, estas correlaciones se conservan como parte de la evidencia
exploratoria, pero **no se utilizarán para afirmar relaciones predictivas ni
causales**.

---

# Principal conclusión del EDA integrado

El principal resultado del EDA integrado no es encontrar una correlación
individual elevada, sino identificar las limitaciones y la estructura que
deberá tener el futuro dataset de modelado.

Actualmente se están comparando:

`promedio climático SE3-SE13`

contra:

`casos epidemiológicos acumulados SE1-SE13`

Esta estructura permite realizar una primera exploración espacial entre
municipios, pero no permite estudiar correctamente el objetivo central del
proyecto: **la predicción temprana de brotes**.

Para ello será necesario transformar el problema hacia:

`municipio + semana epidemiológica`

y posteriormente analizar relaciones como:

`clima(t) → casos(t+1)`

`clima(t) → casos(t+2)`

`clima(t) → casos(t+3)`

`clima(t) → casos(t+4)`

De esta forma será posible determinar si cambios en temperatura, humedad o
precipitación contienen información útil para anticipar cambios posteriores
en los casos de dengue o malaria.


# 15. Comparación conjunta entre municipios

El EDA integrado permite observar simultáneamente el perfil climático y
epidemiológico de cada municipio.

De manera descriptiva:

### Guayaramerín

- temperatura media relativamente alta;
- humedad elevada;
- buena cobertura climática;
- 9 casos acumulados de dengue;
- 293 casos de malaria;
- predominio de *P. vivax*.

### Ixiamas

- menor temperatura media entre los cuatro municipios;
- buena cobertura climática;
- mayor precipitación media por día observado;
- 15 casos acumulados de dengue;
- incidencia de dengue de 12.0 por 10.000 habitantes;
- 156 casos de malaria.

### Palos Blancos

- humedad media elevada;
- cobertura climática intermedia;
- 5 casos acumulados de dengue;
- incidencia de 1.9 por 10.000 habitantes;
- sin información municipal coincidente de malaria en el dataset utilizado.

### San Buenaventura

- temperatura media relativamente alta;
- menor cobertura climática del grupo;
- 22 casos acumulados de dengue;
- mayor incidencia de dengue del grupo: 21.7 por 10.000 habitantes;
- 1 caso de malaria disponible.

### Hallazgo

Los municipios no presentan un único perfil clima-enfermedad.

Las diferencias observadas justifican continuar el análisis utilizando la
unidad **municipio-semana**, en lugar de agregar toda la información nacional
o utilizar únicamente promedios generales.

---

# 16. Limitación temporal

Existe una limitación importante en la integración actual.

Los datos epidemiológicos municipales representan:

**SE1-SE13 de 2026.**

Los datos climáticos procesados para la integración representan principalmente:

**SE3-SE13 de 2026.**

Por tanto:

**la alineación temporal no es completa.**

Además, los datos epidemiológicos municipales actualmente disponibles son
acumulados.

Esto significa que todavía no es posible evaluar correctamente relaciones
temporales como:

```text
Clima semana t
        ↓
Casos semana t+1
Casos semana t+2
Casos semana t+3
Casos semana t+4
```

Esta relación temporal es especialmente importante porque el objetivo del
proyecto es anticipar posibles cambios epidemiológicos con varias semanas de
antelación.

---

# 17. Implicaciones para el futuro modelado

Los resultados del EDA permiten identificar varias decisiones importantes para
las siguientes etapas.

## 17.1 Mantener la dimensión temporal

Los promedios del periodo son útiles para exploración, pero no serán
suficientes para el modelo predictivo.

La unidad objetivo debería evolucionar hacia:

`municipio + semana epidemiológica`

---

## 17.2 Crear variables rezagadas

Cuando exista información epidemiológica semanal municipal suficiente podrán
generarse variables como:

- temperatura lag 1;
- temperatura lag 2;
- temperatura lag 3;
- temperatura lag 4;
- humedad lag 1-4;
- precipitación lag 1-4.

Esto permitirá evaluar si determinadas condiciones climáticas preceden cambios
en dengue o malaria.

---

## 17.3 Considerar la cobertura de datos

La cobertura climática debería conservarse como información de calidad.

Por ejemplo:

- número de días observados;
- porcentaje de cobertura semanal;
- indicador de cobertura suficiente.

Esto permitirá evitar que una semana con pocos datos sea tratada igual que una
semana completamente observada.

---

## 17.4 Mantener la variable municipio

Las diferencias encontradas entre municipios indican que la ubicación puede
contener información relevante.

Las relaciones entre temperatura, humedad y precipitación no fueron idénticas
en todos los municipios.

---

## 17.5 Tratar dengue y malaria de forma diferenciada

Los perfiles epidemiológicos encontrados son distintos.

Por ejemplo, San Buenaventura presenta los mayores valores de dengue dentro del
grupo analizado, mientras Guayaramerín concentra la mayor cantidad de malaria.

Por tanto, no debe asumirse que ambas enfermedades responderán exactamente a
las mismas variables o con los mismos rezagos temporales.

---

# 18. Principales hallazgos del EDA

A partir de los datos reales disponibles se identificaron los siguientes
hallazgos:

1. **Ya existe información climática real utilizable de SENAMHI**, con 16.778
   observaciones RAW correspondientes a temperatura, humedad y precipitación.

2. **La cobertura climática no es homogénea.** Guayaramerín e Ixiamas presentan
   mejor cobertura que Palos Blancos y San Buenaventura.

3. **La temperatura y la humedad presentan una asociación inversa consistente**
   en los cuatro municipios analizados.

4. **La precipitación presenta mayor variabilidad** y requiere especial cuidado
   debido a registros extremos y diferencias de cobertura.

5. **Las relaciones entre temperatura, humedad y precipitación cambian entre
   municipios**, por lo que no existe un único comportamiento climático para
   toda el área analizada.

6. **Los perfiles epidemiológicos de dengue y malaria son diferentes.**
   San Buenaventura presenta los mayores valores de dengue dentro del conjunto
   integrado, mientras Guayaramerín concentra la mayor cantidad de malaria.

7. **La integración clima-epidemiología ya es posible**, pero actualmente está
   limitada a cuatro municipios para dengue y tres con información coincidente
   de malaria.

8. **Las correlaciones integradas son exploratorias**, debido al reducido número
   de municipios.

9. **La principal limitación actual es temporal:** los casos municipales están
   disponibles como acumulados SE1-SE13, mientras que para predicción temprana
   se necesitan series municipio-semana.

10. El EDA actual proporciona una **línea base real, reproducible y trazable**
    para continuar con la construcción del dataset de modelado.

---

# 19. Conclusiones

El Análisis Exploratorio de Datos permitió pasar de una etapa inicial de
evaluación de disponibilidad a un análisis basado en datos reales climáticos y
epidemiológicos de Bolivia.

Los datos obtenidos de SENAMHI permitieron caracterizar el comportamiento de
temperatura, humedad y precipitación en Guayaramerín, Ixiamas, Palos Blancos y
San Buenaventura.

Se identificó una relación inversa consistente entre temperatura y humedad,
mientras que las relaciones que involucran precipitación presentan mayor
variabilidad entre municipios.

La integración con los datos epidemiológicos permitió comparar estos perfiles
climáticos con los casos acumulados de dengue y malaria. Sin embargo, el
reducido número de municipios y la falta de series epidemiológicas municipales
semanales impiden utilizar las asociaciones actuales como evidencia predictiva.

Por tanto, el EDA actual constituye una **línea base real para el proyecto**,
pero todavía no representa el dataset definitivo para entrenar el modelo de
predicción temprana.

El siguiente paso será ampliar la dimensión temporal de los datos
epidemiológicos y construir observaciones a nivel **municipio-semana**. Esto
permitirá generar variables rezagadas de 1 a 4 semanas y evaluar si las
condiciones climáticas preceden cambios posteriores en dengue y malaria.

---

# 20. Evidencias generadas

## 20.1 EDA climático

Los resultados del análisis climático se encuentran en:

`scripts/eda_climatico_output/`

Incluyen:

- distribuciones de variables;
- boxplots por municipio;
- series temporales;
- matrices de correlación;
- mapas de calor;
- comparaciones entre municipios;
- relaciones temperatura-humedad;
- relaciones temperatura-precipitación;
- relaciones humedad-precipitación.

---

## 20.2 EDA integrado

Los resultados se encuentran en:

`scripts/eda_integrado_output/`

Entre las principales evidencias se encuentran:

- `resumen_integrado.csv`
- `correlacion_integrada_pearson.csv`
- `correlacion_integrada_spearman.csv`
- `correlaciones_clima_enfermedad.csv`
- `heatmap_correlacion_integrada_pearson.png`
- `heatmap_correlacion_integrada_spearman.png`
- `heatmap_clima_enfermedades.png`
- `heatmap_perfil_integrado.png`
- `heatmap_municipios_variables.png`
- `dengue_por_municipio.png`
- `malaria_por_municipio.png`
- `temperatura_media_municipio.png`
- `humedad_media_municipio.png`
- `precipitacion_media_dia.png`
- `temperatura_vs_dengue.png`
- `humedad_vs_dengue.png`
- `precipitacion_vs_dengue.png`
- `temperatura_vs_incidencia_dengue.png`
- `humedad_vs_incidencia_dengue.png`
- `precipitacion_vs_incidencia_dengue.png`
- `temperatura_vs_malaria.png`
- `humedad_vs_malaria.png`
- `precipitacion_vs_malaria.png`
- `perfil_climatico_dengue.png`
- `perfil_climatico_malaria.png`
- `composicion_malaria.png`
- `comparacion_municipios_integrada.csv`
- `resumen_eda_integrado.txt`

---

# 21. Reproducibilidad

Para reproducir el flujo de análisis:

```bash
python scripts/descargar_senamhi.py
python scripts/procesar_clima.py
python scripts/eda_climatico.py
python scripts/integrar_datos.py
python scripts/eda_integrado.py
```

Los scripts mantienen separados:

- datos RAW;
- control de calidad;
- datos procesados;
- integración;
- análisis exploratorio;
- evidencias gráficas.

Esto permite repetir el EDA cuando se incorporen nuevos periodos, municipios o
fuentes epidemiológicas sin modificar la estructura general del pipeline.