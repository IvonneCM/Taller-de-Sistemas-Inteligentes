# Declaración de Uso de Inteligencia Artificial y Revisión Humana

## Proyecto

**Sistema de Predicción Temprana de Dengue y Malaria en Bolivia**

------------------------------------------------------------------------

## 1. Objetivo

Documentar de forma transparente el uso de herramientas de Inteligencia
Artificial durante el desarrollo del proyecto, identificando las
herramientas utilizadas por los integrantes del equipo y estableciendo
el proceso de revisión humana aplicado a los resultados generados con su
apoyo.

La IA se utiliza como una herramienta de apoyo al desarrollo. Las
decisiones finales, la incorporación de código, la validación de datos,
la aceptación de documentación y la interpretación de resultados
permanecen bajo responsabilidad humana.

------------------------------------------------------------------------

## 2. Herramientas de IA utilizadas por el equipo

  -----------------------------------------------------------------------
  Integrante              Herramienta de IA       Modalidad de uso
  ----------------------- ----------------------- -----------------------
  Adriana Rocha           ChatGPT                 Asistencia de IA
                                                  integrada al flujo de
                                                  desarrollo y trabajo
                                                  con código

  Tania                   Claude Code             Asistencia de IA
                                                  integrada al flujo de
                                                  desarrollo y trabajo
                                                  con código

  Dilan                   Claude Code             Asistencia de IA
                                                  integrada al flujo de
                                                  desarrollo y trabajo
                                                  con código

  Ivonne                  OpenCode                Asistencia de IA para
                                                  tareas de desarrollo y
                                                  trabajo con código

  Ignacio                 Claude Code             Asistencia de IA
                                                  integrada al flujo de
                                                  desarrollo y trabajo
                                                  con código
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Registro de uso de IA

  ----------------------------------------------------------------------------------------------------
  ID          Integrante   Herramienta   Actividad / uso  Revisión humana    Evidencia
  ----------- ------------ ------------- ---------------- ------------------ -------------------------
  IA01        Adriana      ChatGPT       Apoyo para       Los comandos       Configuración DVC,
              Rocha                      comprender y     fueron ejecutados  archivos `.dvc`,
                                         configurar Git,  manualmente y sus  historial de Git y
                                         DVC y DagsHub y  resultados se      repositorio remoto.
                                         organizar el     verificaron antes  
                                         versionado de    de continuar.      
                                         datos.                              

  IA02        Adriana      ChatGPT       Apoyo para       Se comprobaron las `dvc.yaml`, `dvc.lock` y
              Rocha                      estructurar el   entradas y salidas ejecución exitosa del
                                         pipeline         reales de los      pipeline.
                                         reproducible del scripts, se        
                                         proyecto.        ejecutó `dvc dag`  
                                                          y posteriormente   
                                                          `dvc repro`.       
          

  IA03        Tania        Claude Code   Apoyo mediante   El código y los    Commits, scripts y
                                         IA durante       resultados         outputs correspondientes
                                         actividades de   incorporados al    a sus tareas.
                                         desarrollo y     proyecto deben ser 
                                         trabajo con      revisados mediante 
                                         código.          ejecución,         
                                                          inspección de      
                                                          resultados y       
                                                          control de         
                                                          versiones.         

  IA04        Dilan        Claude Code   Apoyo mediante   El código y los    Commits, scripts y
                                         IA durante       resultados         outputs correspondientes
                                         actividades de   incorporados al    a sus tareas.
                                         desarrollo y     proyecto deben ser 
                                         trabajo con      revisados mediante 
                                         código.          ejecución,         
                                                          inspección de      
                                                          resultados y       
                                                          control de         
                                                          versiones.         

  IA05        Ivonne       OpenCode      Apoyo mediante   Las propuestas     Commits, scripts,
                                         IA durante       incorporadas deben documentos u outputs
                                         actividades de   ser revisadas y    correspondientes a sus
                                         desarrollo y     contrastadas con   tareas.
                                         trabajo con      el funcionamiento  
                                         código.          real del proyecto. 

  IA06        Ignacio      Claude Code   Apoyo            La información o   Documentos, commits u
                                         conversacional   propuestas         otras evidencias
                                         durante          utilizadas deben   correspondientes a sus
                                         actividades      ser revisadas      tareas.
                                         relacionadas con antes de           
                                         el proyecto.     incorporarse al    
                                                          proyecto.          
  ----------------------------------------------------------------------------------------------------


------------------------------------------------------------------------

## 4. Proceso de revisión humana

El proyecto aplica revisión humana antes de aceptar resultados obtenidos
con apoyo de IA. El proceso general es:

**Necesidad o tarea → interacción con IA → propuesta generada → revisión
humana → prueba o contraste → corrección, si corresponde → aceptación**

La revisión puede incluir, según el tipo de resultado:

-   ejecución del código en el entorno del proyecto;
-   revisión de errores y salidas de consola;
-   inspección de datasets generados;
-   comparación con datos de entrada;
-   validación de rutas, dependencias y archivos;
-   revisión de métricas y resultados estadísticos;
-   revisión de documentación antes de incorporarla;
-   revisión mediante Git de los cambios realizados.

------------------------------------------------------------------------

## 5. Evidencia concreta de revisión humana

### 5.1 Reproducibilidad y DVC

Durante la configuración del pipeline se verificaron directamente las
entradas y salidas utilizadas por los scripts. Posteriormente se
ejecutó:

``` bash
dvc dag
```

para comprobar las dependencias del pipeline.

Finalmente se ejecutó:

``` bash
dvc repro
```

y se comprobó la ejecución satisfactoria del flujo y la generación de
`dvc.lock`.

Esto evidencia que las sugerencias apoyadas por IA fueron comprobadas en
el entorno real antes de su incorporación.

### 5.2 Procesamiento y análisis de datos

La revisión humana de resultados relacionados con datos considera:

-   ejecución de los scripts;
-   control de datos faltantes;
-   revisión de cobertura temporal y geográfica;
-   identificación de valores sospechosos;
-   validación de archivos procesados;
-   revisión de la integración de datos climáticos y epidemiológicos;
-   contraste entre interpretaciones y resultados reales.

### 5.3 Código

Cuando una herramienta de IA apoya la creación o modificación de código,
el resultado no se considera validado únicamente porque el código haya
sido generado.

La revisión requiere, según corresponda:

1.  inspeccionar el código;
2.  ejecutarlo;
3.  comprobar que no produzca errores;
4.  verificar sus entradas y salidas;
5.  comprobar que no altere archivos ajenos a la tarea;
6.  revisar los cambios mediante Git antes de incorporarlos.

### 5.4 Documentación

La documentación generada o mejorada con IA se revisa considerando su
correspondencia con:

-   el estado real del proyecto;
-   las tareas efectivamente realizadas;
-   el contenido del repositorio;
-   las decisiones metodológicas del equipo;
-   las evidencias disponibles.

------------------------------------------------------------------------

## 6. Human-in-the-Loop (HITL)

El proyecto adopta un enfoque **Human-in-the-Loop**, manteniendo
intervención humana en los puntos de decisión.

La IA puede proponer código, explicaciones, estructuras o documentación,
pero la aceptación final corresponde al integrante responsable de la
tarea.

No se considera suficiente una respuesta generada por IA como evidencia
de que una actividad funciona. Siempre que sea aplicable, debe existir
una comprobación mediante código, datos, resultados, documentación o
revisión del repositorio.

------------------------------------------------------------------------

## 7. Criterios de aceptación de resultados apoyados por IA

Un resultado puede incorporarse cuando:

1.  corresponde al objetivo y alcance del proyecto;
2.  puede contrastarse con el código, datos o documentación disponible;
3.  no contradice los resultados obtenidos mediante ejecución;
4.  el código funciona en el entorno real del proyecto;
5.  las entradas y salidas utilizadas son correctas;
6.  no introduce modificaciones no revisadas;
7.  las interpretaciones estadísticas reconocen sus limitaciones;
8.  existe una persona responsable de su revisión.

Si no cumple estos criterios, debe corregirse, descartarse o someterse a
revisión adicional.

------------------------------------------------------------------------

## 8. Riesgos asociados al uso de IA

Las herramientas utilizadas ---ChatGPT, Claude Code, OpenCode y Claude
Web--- pueden generar propuestas incorrectas, incompletas o no adaptadas
al entorno real del proyecto.

Entre los principales riesgos se encuentran:

-   código que no funciona o contiene errores;
-   rutas o dependencias inexistentes;
-   interpretaciones incorrectas de datos;
-   documentación que no coincide con lo implementado;
-   afirmaciones no respaldadas por evidencia;
-   modificaciones innecesarias en archivos;
-   dependencia excesiva de contenido generado automáticamente.

Estos riesgos se mitigan mediante revisión humana, ejecución, contraste
con los datos, control de versiones y documentación de las decisiones.

El riesgo asociado al uso de IA también se contempla en
`docs/risk_register.md`.

------------------------------------------------------------------------

## 9. Responsabilidad

El uso de herramientas de IA no transfiere la responsabilidad sobre los
resultados.

Cada integrante mantiene responsabilidad sobre los elementos que revisa
e incorpora al proyecto. El equipo es responsable de las decisiones
técnicas y metodológicas presentadas como parte del trabajo.

Las herramientas de IA se consideran mecanismos de apoyo y no autores ni
responsables de las decisiones finales.

------------------------------------------------------------------------

## 10. Evidencias del proyecto

La revisión humana y el trabajo realizado pueden respaldarse mediante:

-   historial de commits;
-   ramas de trabajo del equipo;
-   scripts del repositorio;
-   archivos de datos procesados;
-   outputs de los análisis;
-   archivos `.dvc`;
-   `dvc.yaml`;
-   `dvc.lock`;
-   ejecución de `dvc repro`;
-   `docs/risk_register.md`;
-   documentación técnica;
-   capturas o registros de ejecución conservados por el equipo.

------------------------------------------------------------------------

## 11. Declaración final

El equipo declara el uso de **ChatGPT, Claude Code y OpenCode** como herramientas de apoyo durante el desarrollo del proyecto.

Los resultados generados o sugeridos mediante estas herramientas no
deben considerarse automáticamente válidos. Su incorporación requiere
revisión humana y, cuando corresponde, ejecución, contraste con datos,
revisión del código o comprobación documental.

Las decisiones finales y la responsabilidad sobre el código, los datos,
los análisis, la documentación y los resultados presentados corresponden
al equipo del proyecto.
