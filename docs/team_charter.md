# Team Charter

## Integrantes y disponibilidad

Todos los integrantes cursan pasantías en **GATOBYTE** en horario laboral, por lo que el equipo solo puede reunirse, revisar PR o coordinar entregas fuera de ese horario (noches y fines de semana).

| Integrante | Responsabilidad | Disponibilidad | Restricción |
|---|---|---|---|
| Colque Murillo Ivonne Micaela | Valor / producto | Lun-Vie 20:00, Sáb 10:00 | pasantía en GATOBYTE hasta 19:00 |
| Rocha Vedia Adriana Nathalie | Proceso / bloqueos | Lun-Vie 20:30, Dom 15:00 | pasantía en GATOBYTE hasta 19:00 |
| Pérez Dick Tania Morelia | Datos | Mar-Jue 20:00, Sáb 14:00 | pasantía en GATOBYTE hasta 19:00 |
| Retamozo Torrez Ignacio | Modelo / IA | Lun-Vie 21:00, Dom 16:00 | pasantía en GATOBYTE hasta 19:00 |
| Mamani Pamuri Dilan Obed | Ingeniería | Mié-Vie 20:00, Sáb 11:00 | pasantía en GATOBYTE hasta 19:00 |

No se agendan reuniones ni revisiones antes de las 19:30 en días de semana, dado que todos los integrantes están ocupados en GATOBYTE durante el día.

## Canales y tiempos de respuesta

- ClickUp: tareas, responsables y evidencia.
- WhatsApp: coordinación rápida, no decisiones finales.
- GitHub Issues: defectos técnicos y bloqueos reproducibles.
- Tiempo de respuesta normal: 24 horas (considerando que el equipo trabaja fuera de su horario de pasantía).
- Bloqueo crítico: se etiqueta en ClickUp y se notifica al canal del equipo en WhatsApp.

## Revisión de PR

- Ningún cambio a `main` sin PR.
- Cada PR debe incluir: objetivo, archivos modificados, prueba ejecutada y evidencia.
- Al menos 1 integrante revisa antes de fusionar.
- No se aprueban PR con secretos, datos sensibles o tests fallidos.
- Las decisiones de IA asistida se declaran en el PR.
- Dado el horario reducido del equipo, las revisiones se realizan en la ventana nocturna o de fin de semana; si un PR es urgente se notifica por WhatsApp.

## Manejo de bloqueos

Un bloqueo debe reportarse en ClickUp con este formato:

- **Bloqueo:** qué impide avanzar.
- **Inicio:** fecha y hora en que empezó.
- **Impacto:** qué entrega o tarea está en riesgo.
- **Intentos:** qué se intentó para resolverlo.
- **Siguiente acción:** qué se va a hacer y quién lo hace.

Ejemplo:
```
Bloqueo: no podemos coordinar reunión en horario laboral.
Inicio: 13/08, 19:00.
Impacto: retraso en la revisión del Team Charter.
Intentos: coordinación por WhatsApp durante el descanso de GATOBYTE.
Siguiente acción: mover la reunión a las 20:30 y registrar el acuerdo en ClickUp.
```

## Reglas de integridad y uso de IA

- Se permite IA (Claude, ChatGPT u otros asistentes) para análisis, diseño, código, pruebas y documentación.
- No se ingresan datos personales, secretos ni credenciales a ningún asistente de IA.
- Todo código o documento generado con IA debe revisarse, probarse y entenderse antes de integrarlo.
- El PR debe declarar qué se generó con IA y qué verificaciones se ejecutaron.
- La responsabilidad final sobre el contenido entregado es del equipo, no de la herramienta.

## Definition of Done inicial

Una tarea se considera terminada cuando:

- Tiene criterio de aceptación cumplido.
- Incluye evidencia enlazada en ClickUp.
- El cambio está en GitHub con commit/PR.
- No introduce secretos ni datos sensibles.
- Si modifica código, ejecuta pruebas o justifica por qué no aplican.
- Si usa IA, declara uso y verificación.
