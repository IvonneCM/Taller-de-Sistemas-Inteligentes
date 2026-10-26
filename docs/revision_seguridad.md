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
| HTTPS en el despliegue (NFR-005) | **AVISO** (verificado el 2026-10-26 en Render) | `python -m app.core.revision_seguridad --url https://taller-de-sistemas-inteligentes.onrender.com`: HTTPS con certificado válido, pero **sin `Strict-Transport-Security`**. Además `/docs`, `/redoc` y `/openapi.json` responden 404 en el despliegue (no se publican en producción). Conviene repetir el control cuando cambie el dominio. |
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

## 3. Hallazgos que requieren decisión

| # | Hallazgo | Gravedad | Qué hacer | Quién |
|---|---|---|---|---|
| H-1 | **`python-multipart 0.0.9`** tiene 10 avisos de seguridad (DoS al leer formularios, entre otros). Se usa en `POST /auth/login`, que es público. | Media | Subir a `0.0.31` en `requirements-api.txt`. **Probado:** con esa versión pasan las 144 pruebas de API y extremo a extremo (se revirtió después; no se cambió ningún archivo de requisitos). | Ignacio (requirements) |
| H-2 | **`python-jose 3.3.0`** tiene 4 avisos distintos; dos se corrigen en 3.4.0 y **dos no tienen versión corregida ni siquiera en 3.5.0**. | Baja hoy; media a futuro | Subir a 3.4.0 como mínimo y evaluar migrar a PyJWT. **Exposición real baja:** se usa solo HS256 con clave simétrica y lista fija de algoritmos, sin JWE ni claves asimétricas, y ninguno de los avisos aplica a ese uso. | Ivonne (auth) |
| H-3 | **No hay límite de intentos de login**: se puede probar contraseñas sin freno. El login iguala el tiempo de respuesta para no revelar usuarios, pero no bloquea. | Media | Limitar intentos por correo y por IP (p. ej. en el servidor o en nginx). | Ivonne / Ignacio |
| H-4 | **nginx no envía cabeceras de seguridad** (`X-Content-Type-Options`, `Content-Security-Policy`, `X-Frame-Options`, `Referrer-Policy`) y no redirige a HTTPS. | Baja | Agregarlas en `frontend/nginx.conf`; HSTS cuando haya HTTPS. | Ignacio |
| H-5 | **El refresh token vive en `sessionStorage`** y quedaría expuesto si hubiera un XSS (riesgo M-11). | Baja | Aceptado para el MVP; la alternativa es una cookie `HttpOnly`, que exige cambiar el login. | Equipo |
| H-6 | **Las alertas y predicciones no son inmutables en la base**, solo en el código (NFR-009 lo acepta). | Baja | Si se quiere reforzar, un trigger que rechace `UPDATE` y `DELETE`. | Equipo |
| H-7 | Las imágenes base de Docker no se escanearon. | Baja | Escanear con un analizador de imágenes antes del despliegue. | Ignacio |
| H-8 | El `CMD` del Dockerfile usa `--forwarded-allow-ips='*'`: uvicorn confía en `X-Forwarded-For` de cualquier origen. Es correcto mientras la API solo sea alcanzable a través del proxy de Render. | Baja | Restringir a las IP del proxy si el hosting lo permite. | Ignacio |
| H-9 | **Sin `Strict-Transport-Security`** en el despliegue (lo detectó el control de HTTPS). | Baja | Agregarla desde la API o el proxy cuando el dominio sea estable. | Ignacio |

La API **ya está expuesta en internet** (Render). Por eso conviene resolver pronto H-1 a H-3: las dependencias con avisos y, sobre todo, el límite de intentos de login.

**Hallazgo corregido durante esta revisión:** el límite de tiempo por consulta (TASK-040) se pasaba como parámetro de arranque de la conexión y el pooler de Neon lo rechaza ("unsupported startup parameter"), por lo que la API desplegada devolvía 503 en `/health/ready` y no podía consultar la base. Ahora se aplica con `SET LOCAL` por transacción; verificado contra Neon con consultas de solo lectura (`/health/ready` → 200) y vigilado por una prueba.

## 4. Límites de esta revisión

- La búsqueda de secretos es heurística: no reemplaza a una herramienta dedicada ni revisa el historial de git.
- No se hicieron pruebas de penetración ni de carga.
- El Dockerfile corre como usuario sin privilegios (`appuser`), pero no se revisó el resto de la configuración del contenedor.
- Todo se verificó **en local y en Docker**; nada se probó contra un despliegue real.

## 5. Firma del equipo

Debe firmarse después de resolver (o aceptar por escrito) los hallazgos de la sección 3.

| Integrante | Revisó | Fecha | Firma |
|---|---|---|---|
| Ignacio Retamozo Torrez | | | |
| Tania Pérez | | | |
| Ivonne Colque | | | |
| Adriana Rocha Vedia | | | |
| Dilan Mamani Pamuri | | | |
