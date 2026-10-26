# Revisión de seguridad y cumplimiento (TASK-035)

Checklist con evidencia técnica **reproducible**. La TASK-035 pide que el equipo lo firme antes de la presentación: este documento deja listo todo lo verificable hoy y señala con honestidad lo que **no** se pudo verificar. No es una auditoría de seguridad profesional.

**Fecha de la revisión:** 2026-10-26 · **Versión revisada:** rama `dilan` · **Cómo repetirla:**

```bash
python -m app.core.revision_seguridad                              # sale con código 1 si hay alguna falla
python -m app.core.revision_seguridad --url https://<despliegue>   # además comprueba HTTPS
pip-audit -r requirements-api.txt --no-deps --disable-pip          # dependencias de Python
cd frontend && npm audit                                           # dependencias de la interfaz
```

## 1. Lo que pide la tarea

| Pedido | Estado | Evidencia |
|---|---|---|
| Ausencia de datos personales de pacientes (REQ-020) | **OK** | Control automático: 69 columnas de la base revisadas, solo `usuarios.email` (personal que opera el sistema). Los conectores rechazan columnas con datos personales (`app/etl/conectores/epidemiologia.py`) y toda la información es un conteo agregado por municipio. |
| HTTPS en el despliegue (NFR-005) | **OK** (verificado el 2026-10-26 en Render, ya con la corrección: HTTPS con certificado válido y `Strict-Transport-Security`) | `python -m app.core.revision_seguridad --url https://taller-de-sistemas-inteligentes.onrender.com`: HTTPS con certificado válido, pero **sin `Strict-Transport-Security`**. Además `/docs`, `/redoc` y `/openapi.json` responden 404 en el despliegue (no se publican en producción). Conviene repetir el control cuando cambie el dominio. |
| Ninguna alerta sin justificación en la base (REQ-005) | **OK** | Control automático sobre el sistema en Docker: 2 alertas, las dos con justificación y variables explicativas. Triple barrera: restricción `CHECK` en la base, `evaluacion_alertas` y filtro de `GET /alertas`. |
| Checklist firmado por el equipo | **Pendiente** | Ver la sección 5. |

## 2. Otros controles verificados

| Control | Estado | Evidencia |
|---|---|---|
| Contraseñas con hash bcrypt (NFR-005) | OK | 5 de 5 usuarios con hash bcrypt válido; el modelo rechaza una contraseña en texto plano; `tests/test_revision_seguridad.py` prueba que se detecta una en texto plano. |
| Sin secretos en el repositorio (NFR-005) | OK | 471 archivos versionados revisados con una búsqueda heurística (claves privadas, claves de AWS, URL de base con clave real, `SECRET_KEY` real, archivos `.env`). El `.env` real está ignorado por git. |
| `SECRET_KEY` sin valor por defecto y robusta | OK | `app/core/config.py` no tiene valor por defecto; con `ENVIRONMENT=production` rechaza una clave débil. |
| Predicciones inmutables (NFR-009) | OK, con matiz | Ningún código actualiza ni borra predicciones. La inmutabilidad es **de aplicación**: la base no la impone (no hay un trigger). |
| Control de acceso por rol (REQ-007, REQ-019) | OK | `tests/api/` (test_auth, test_rbac, test_acceso_endpoints) y la prueba extremo a extremo por rol: la vista resumida no recibe los campos técnicos; el servidor, no la interfaz, decide. |
| Registros sin datos sensibles | OK | `tests/test_observabilidad.py`: los logs no contienen contraseñas, correos ni cadenas de consulta. |
| Errores sin trazas ni lo enviado por la persona | OK | Los 500 son genéricos y los 422 no devuelven `input` (TASK-040). |
| Documentación de la API en producción | OK (nuevo) | Con `ENVIRONMENT=production` no se publican `/docs`, `/redoc` ni `/openapi.json`; probado en `tests/test_revision_seguridad.py`. |
| CORS | OK | No está habilitado: la interfaz llama a `/api` en el mismo origen (nginx). |
| Dependencias de la interfaz | OK | `npm audit`: 0 vulnerabilidades (producción y herramientas de prueba). |

## 3. Hallazgos y su resolución

Todos los hallazgos con solución técnica se corrigieron el 2026-10-26 (rama `dilan`). Los que quedan se **aceptan por escrito**, con su motivo. Las correcciones llegan a la API desplegada cuando Render redespliega desde `main`.

| # | Hallazgo | Gravedad | Estado | Qué se hizo / por qué se acepta |
|---|---|---|---|---|
| H-1 | `python-multipart 0.0.9`: 10 avisos (DoS al leer formularios) en el login público. | Media | **Resuelto** | Subido a `0.0.31` y `starlette 1.10.0` (el aviso de DoS en formularios también estaba en Starlette). `requirements-api.txt`. |
| H-2 | `python-jose 3.3.0`: 4 avisos, 2 sin versión corregida. | Baja hoy; media a futuro | **Resuelto** | Se migró a **PyJWT 2.15.1** (`app/core/security.py`): desaparece la dependencia con avisos sin corrección. Mismo comportamiento: solo HS256, firma, expiración, emisor y tipo de token; las pruebas de tokens manipulados y de algoritmo distinto siguen en verde. |
| H-3 | Sin límite de intentos de login. | Media | **Resuelto** | `app/core/limite_intentos.py`: 5 intentos fallidos por correo y 20 por IP en 15 minutos; después, `429` con `Retry-After`, sin comparar la contraseña. Un login correcto borra el contador del correo. Configurable (`LOGIN_MAX_INTENTOS_EMAIL`, `LOGIN_MAX_INTENTOS_IP`, `LOGIN_VENTANA_SEGUNDOS`; `0` lo desactiva). 12 pruebas en `tests/api/test_limite_login.py`. **Límites conocidos:** el contador vive en la memoria de una instancia (con varias instancias o tras un reinicio cada una cuenta aparte), y bloquear por correo permite que alguien impida entrar a un usuario durante 15 minutos; se acepta porque lo contrario (probar claves sin freno) es peor. |
| H-4 | nginx sin cabeceras de seguridad. | Baja | **Resuelto** | `frontend/nginx.conf`: `Content-Security-Policy` (solo este origen y las teselas de OpenStreetMap), `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `server_tokens off`. Verificado en el navegador: el mapa y el login funcionan sin violaciones de la política. La API añade las suyas (`app/core/cabeceras_seguridad.py`, 5 pruebas). La redirección a HTTPS la hace Render, no nginx. |
| H-5 | El refresh token vive en `sessionStorage` (riesgo M-11). | Baja | **Aceptado** | Mitigado por la CSP nueva (`script-src 'self'`, que dificulta un XSS), el access token solo en memoria y los refresh revocables en el servidor. La alternativa (cookie `HttpOnly`) exige rediseñar el login y queda para después del MVP. |
| H-6 | Predicciones y alertas no son inmutables en la base, solo en el código. | Baja | **Aceptado** | NFR-009 pide inmutabilidad de aplicación. Un trigger que bloquee `UPDATE` y `DELETE` impediría también la limpieza de las pruebas y de la carga de demostración; el control automático verifica que ningún código las modifique. |
| H-7 | Imágenes de Docker sin escanear. | Baja | **Resuelto** | Se escanearon con Trivy (graves y críticas con corrección disponible). `api` y `ml`: 0. `web` (nginx 1.27): 60 (58 graves, 2 críticas) en paquetes del sistema; se pasó a `nginx:1.30-alpine` con `apk upgrade` y quedó en 0. Las 3 imágenes: **0 graves o críticas**. Repetir con `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL --ignore-unfixed <imagen>`. |
| H-8 | `--forwarded-allow-ips='*'` en el `CMD`. | Baja | **Aceptado** | Render no publica un rango fijo de IP de su proxy. Consecuencia: quien alcance la API directamente podría falsear `X-Forwarded-For` y evadir el límite **por IP**; el límite **por correo** no depende de eso y sigue frenando la adivinación de una cuenta. |
| H-9 | Sin `Strict-Transport-Security`. | Baja | **Resuelto y verificado en Render** | La API la envía con `ENVIRONMENT=production` (también `Content-Security-Policy` cerrada). Verificado el 2026-10-26 tras el redespliegue: `python -m app.core.revision_seguridad --url https://taller-de-sistemas-inteligentes.onrender.com` → **7 controles OK, 0 avisos**; el sexto intento fallido de login responde 429; `/docs` responde 404. |

**Hallazgo corregido durante esta revisión:** el límite de tiempo por consulta (TASK-040) se pasaba como parámetro de arranque de la conexión y el pooler de Neon lo rechaza ("unsupported startup parameter"), por lo que la API desplegada devolvía 503 en `/health/ready` y no podía consultar la base. Ahora se aplica con `SET LOCAL` por transacción; verificado contra Neon y en el despliegue (`scripts/smoke_test.py`: 8 de 8).

**Dependencias tras las correcciones:** `pip-audit -r requirements-api.txt`: sin vulnerabilidades conocidas; `npm audit`: 0. Para llegar ahí hubo que subir `fastapi` de 0.115.0 a 0.162.0 (con Starlette 1.10.0): la suite completa pasó (456 pruebas de backend); el único ajuste fue una prueba que recorría `app.routes` y ahora debe tolerar el enrutador agrupado de FastAPI.

## 4. Límites de esta revisión

- La búsqueda de secretos es heurística: no reemplaza a una herramienta dedicada ni revisa el historial de git.
- No se hicieron pruebas de penetración ni de carga.
- El Dockerfile corre como usuario sin privilegios (`appuser`), pero no se revisó el resto de la configuración del contenedor.
- Las correcciones se verificaron en local, en Docker y **en el despliegue de Render** (control `--url`, prueba de humo, límite de login y documentación oculta, el 2026-10-26).

## 5. Firma del equipo

Debe firmarse después de resolver (o aceptar por escrito) los hallazgos de la sección 3.

| Integrante | Revisó | Fecha | Firma |
|---|---|---|---|
| Ignacio Retamozo Torrez | | | |
| Tania Pérez | | | |
| Ivonne Colque | | | |
| Adriana Rocha Vedia | | | |
| Dilan Mamani Pamuri | | | |
