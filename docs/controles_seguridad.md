# Controles de seguridad y privacidad

**Autor:** Dilan Mamani

**Estado:** Propuesta para revisión del equipo

**Trazabilidad:** REQ-019, REQ-020, NFR-005, NFR-009, TASK-003, TASK-007,
TASK-017, TASK-018 y TASK-035

## 1. Objetivo y alcance

Este documento establece los controles mínimos para proteger el backend, las
credenciales y los datos epidemiológicos del sistema. Aplica a desarrollo,
pruebas y despliegue. No sustituye una auditoría de producción.

En la fase actual solo existen el esqueleto de FastAPI y `GET /health`. Los
controles de autenticación, autorización y persistencia descritos aquí son
requisitos de implementación futura, salvo los identificados explícitamente
como presentes en el repositorio.

## 2. Estado verificable

| Control | Estado actual | Evidencia |
|---|---|---|
| Exclusión de `.env`, llaves y datos crudos | Presente | `.gitignore` excluye `.env`, `*.pem`, `*.key` y `data/raw/`. |
| Plantilla de configuración sin secretos reales | Presente | `.env.example` usa credenciales locales de ejemplo y marcadores. |
| Endpoint de salud sin datos sensibles | Presente | `app/main.py` devuelve únicamente `{"status": "ok"}`. |
| Prohibición de datos personales de pacientes | Definido en requisitos y diseño | REQ-020 y modelo agregado por municipio y fecha. |
| JWT y expiración de tokens | Diseñado, no implementado | TASK-017 pendiente. |
| RBAC aplicado en backend | Diseñado, no implementado | TASK-018 pendiente. |
| Hash de contraseñas | Diseñado, no implementado | TASK-007 y TASK-017 pendientes. |
| HTTPS/TLS | Diseñado, no verificable sin despliegue | TASK-004 y TASK-035 pendientes. |
| Auditoría inmutable | Diseñado, no implementado | NFR-009 y migraciones pendientes. |

Una decisión documentada no debe presentarse como control operativo hasta que
existan código, prueba y evidencia de despliegue.

## 3. Matriz de controles

| Código | Control | Requisito | Implementación esperada | Evidencia de aceptación |
|---|---|---|---|---|
| SEG-01 | Autenticación JWT | REQ-019 | OAuth2 password flow, access token de corta duración y refresh token revocable. | Pruebas de login válido, inválido, expirado y revocado. |
| SEG-02 | Autorización por roles | REQ-019 | Verificación RBAC en dependencias o servicios de FastAPI, nunca solo en el frontend. | Matriz de endpoints por rol y pruebas 401/403. |
| SEG-03 | Hash de contraseñas | NFR-005 | `bcrypt` o `argon2`, con salt administrado por la librería; nunca texto plano. | Revisión de esquema y prueba de verificación de hash. |
| SEG-04 | HTTPS/TLS | NFR-005 | Redirección o rechazo de HTTP en el entorno desplegado y TLS válido. | Captura o comando que verifique HTTPS y certificado. |
| SEG-05 | Minimización de datos | REQ-020 | Persistir casos agregados por municipio, enfermedad y periodo. | Revisión de tablas, muestras y respuestas de API sin identificadores personales. |
| SEG-06 | Gestión de secretos | NFR-005 | Variables de entorno o gestor de secretos; rotación ante exposición. | Escaneo del repositorio y configuración del entorno sin revelar valores. |
| SEG-07 | Validación de entradas | REQ-019, REQ-020 | Esquemas Pydantic, límites de tamaño y rechazo de campos no permitidos. | Pruebas con tipos inválidos, contenido adicional y cargas excesivas. |
| SEG-08 | Acceso mínimo a base de datos | NFR-005 | Usuario de aplicación sin permisos administrativos y consultas parametrizadas. | Revisión de permisos y pruebas de operaciones autorizadas. |
| SEG-09 | Auditoría | NFR-009 | Predicciones, alertas y eventos de seguridad con fecha, actor y resultado. | Prueba de inmutabilidad y consulta del historial. |
| SEG-10 | Protección del login | REQ-019, NFR-005 | Límite de intentos, respuesta genérica y registro de fallos sin contraseñas. | Prueba de rate limit y revisión de logs. |

## 4. Autenticación y sesiones

La implementación de TASK-017 deberá cumplir estas reglas:

1. El access token tendrá expiración corta configurable; el valor inicial de
   diseño es 30 minutos.
2. El refresh token tendrá expiración separada y podrá revocarse.
3. El backend validará firma, expiración, emisor y algoritmo permitido. No
   aceptará el algoritmo indicado libremente por el token.
4. La clave de firma se obtendrá del entorno y tendrá suficiente entropía. El
   marcador de `.env.example` nunca se usará en un entorno desplegado.
5. Las respuestas de login no revelarán si falló el usuario o la contraseña.
6. No se registrarán contraseñas, tokens completos ni secretos en logs.
7. `GET /health` podrá permanecer público porque no consulta ni expone datos
   del dominio. Los endpoints de datos requerirán autenticación.

## 5. Autorización por roles

El control de roles se aplicará en el servidor mediante una dependencia como
`require_role(...)`. Ocultar botones en el frontend no constituye una medida
de autorización.

| Capacidad | Roles previstos |
|---|---|
| Consultar riesgo y alertas resumidas | Todos los roles autenticados. |
| Consultar historial y métricas detalladas | Epidemiólogo y administrador. |
| Configurar umbrales | Administrador. |
| Ingerir datos | Administrador o identidad técnica del proceso ETL. |
| Consultar recursos de un municipio | Coordinador asignado y administrador. |

Cada endpoint deberá devolver `401` sin una identidad válida y `403` cuando
la identidad sea válida pero no tenga el rol requerido. El filtro se aplicará
antes de consultar o serializar información restringida.

## 6. Contraseñas

- Almacenar únicamente `password_hash`; el modelo no tendrá una columna de
  contraseña en texto plano.
- Usar la API de `passlib` con `bcrypt` o una alternativa acordada como
  `argon2`.
- No enviar contraseñas por correo, logs ni parámetros de URL.
- Permitir cambio y restablecimiento con tokens de un solo uso cuando esa
  función entre en alcance.
- Revisar el costo del hash en el entorno de despliegue antes de fijarlo.

Estas medidas implementan el componente de contraseñas de NFR-005.

## 7. Privacidad y datos epidemiológicos

Para cumplir REQ-020:

1. Solo se aceptarán conteos agregados por municipio, enfermedad y periodo.
2. Se rechazarán nombre, CI, teléfono, correo, dirección exacta, historia
   clínica, coordenadas del paciente y cualquier identificador equivalente.
3. Los conectores usarán una lista permitida de columnas. Una columna no
   reconocida bloqueará el lote hasta su revisión.
4. Los archivos rechazados por contener datos personales no se copiarán al
   repositorio ni a logs de diagnóstico.
5. Las respuestas de API se construirán con esquemas explícitos para evitar
   exponer columnas internas accidentalmente.
6. Las exportaciones, respaldos y datos de prueba mantendrán la misma regla de
   minimización.

Los datos agregados reducen el riesgo, pero no eliminan la necesidad de
controlar acceso, especialmente en municipios o periodos con conteos bajos.

## 8. Secretos y configuración

- `.env` continuará excluido de Git.
- `.env.example` documentará nombres y valores ficticios, nunca credenciales
  activas.
- Railway o el entorno elegido almacenará los secretos fuera del código.
- Toda credencial expuesta se revocará y rotará; eliminarla de un commit no
  basta para considerarla segura.
- El equipo ejecutará una búsqueda de secretos antes de cada integración y
  antes de la defensa.
- Los permisos de las claves externas se limitarán a la fuente y operación
  necesarias.

## 9. Transporte, API y base de datos

- Todo entorno accesible por red usará HTTPS/TLS. El equipo verificará que no
  exista un endpoint alternativo por HTTP que exponga datos.
- CORS tendrá una lista explícita de orígenes del dashboard; no se combinará
  origen global con credenciales.
- Pydantic validará tipos, rangos y campos admitidos.
- SQLAlchemy o consultas parametrizadas impedirán concatenar entrada del
  usuario en SQL.
- El usuario de base de datos de la aplicación no podrá crear roles, bases de
  datos ni extensiones.
- Los mensajes externos serán genéricos; el detalle técnico quedará en logs
  protegidos y sin secretos.

## 10. Registro y respuesta

Se registrarán intentos de autenticación fallidos, denegaciones de rol,
cambios de configuración, ejecuciones ETL y generación de alertas. Cada evento
incluirá fecha, actor o identidad técnica, acción y resultado, pero nunca
contraseñas, tokens completos o datos personales.

Ante una posible exposición se deberá:

1. revocar y rotar la credencial afectada;
2. conservar la evidencia necesaria sin difundir el secreto;
3. revisar accesos y alcance;
4. corregir la causa;
5. registrar la decisión y las acciones realizadas.

## 11. Criterios de aceptación

TASK-035 no deberá cerrarse hasta verificar:

- ningún secreto real aparece en el historial o los archivos rastreados;
- todas las rutas de datos rechazan usuarios no autenticados;
- cada rol solo accede a sus capacidades;
- las contraseñas están almacenadas con hash;
- el despliegue responde mediante HTTPS válido;
- tablas, logs y respuestas no contienen datos personales de pacientes;
- las alertas y predicciones conservan un historial inmutable;
- las pruebas de seguridad relevantes pasan en integración continua.

## 12. Revisión pendiente

El equipo deberá revisar esta matriz al implementar cada tarea y registrar la
evidencia concreta. La aprobación final requiere al menos una persona distinta
del autor y debe quedar anotada en el acta o en la herramienta de gestión.
