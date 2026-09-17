# Entorno reproducible y estado inicial de los datos (Línea Base — Paso 1)

**Responsable:** Ignacio Retamozo

**Sección del backlog:** Build/QA/Deploy

**Estado:** entorno confirmado y probado en esta máquina; los dos hallazgos
de compatibilidad de §5 se decidieron con el responsable del proyecto y ya
están aplicados en `requirements.txt` (raíz y backend)

**Trazabilidad:** `docs/cierre_sprint1.md` §1 (tarea "Línea base — Paso 1"
asignada a Ignacio), NFR-010, TASK-001 (referencia futura)

**Documentos relacionados:** [`pipeline_datos.md`](./pipeline_datos.md)
(Línea Base — Paso 2, Tania), [`linea_base.md`](./linea_base.md) (Línea Base
— Paso 3, Ivonne), [`eda_inicial.md`](./eda_inicial.md),
[`inventario_datos.md`](./inventario_datos.md),
[`privacidad_datos.md`](./privacidad_datos.md), `CONTEXT.md`

**Evidencia (logs de esta sesión):** [`evidencia_entorno/`](./evidencia_entorno/)

---

## 1. Qué es este documento y por qué es el Paso 1

La línea base de este proyecto tiene tres pasos, hechos por tres personas
distintas y verificables por separado:

1. **Paso 1 (este documento):** ¿el entorno se levanta desde cero, en una
   máquina que no lo tenía configurado, y en qué estado están los datos
   *antes* de correr cualquier script? Es el punto de partida que hace
   verificables los pasos 2 y 3.
2. **Paso 2** (`pipeline_datos.md`, Tania): el pipeline de limpieza e
   imputación, asumiendo que el entorno y los datos crudos ya están
   disponibles.
3. **Paso 3** (`linea_base.md`, Ivonne): la referencia numérica y el registro
   de experimentos, asumiendo que el Paso 2 ya corrió.

Este documento se generó **ejecutando realmente** cada comando en una
máquina que no tenía el proyecto configurado (sin `.venv`, sin DVC
instalado), no describiendo de memoria lo que "debería" pasar. Cada
afirmación de esta página tiene su log correspondiente en
`docs/evidencia_entorno/`.

---

## 2. Decisión de entorno: venv, no Docker

Antes de crear nada se evaluaron tres opciones (venv, Docker, conda) y se
confirmó con el responsable del proyecto usar **venv** con dos entornos
separados. Motivos verificados en esta máquina:

- El backend ya documenta una convención de `venv` en su propio
  `README.md` (`dengue-malaria-prediccion/README.md`); usar otra cosa ahí
  habría creado dos formas distintas de hacer lo mismo.
- Docker está instalado (`docker --version` → `28.0.4`) pero **el daemon no
  estaba corriendo** y no existe ningún `Dockerfile` en el repositorio;
  introducirlo habría sido una pieza nueva sin necesidad técnica actual
  (todavía no hay PostgreSQL/PostGIS que orquestar — el backend solo sirve
  `/health`).
- No hay indicios de que el equipo use conda/mamba en ningún documento del
  proyecto.

Docker queda como opción razonable **más adelante**, cuando el backend
necesite PostgreSQL/PostGIS real (TASK-002 en adelante), no para esta
etapa.

---

## 3. Entorno 1 — datos y scripts (raíz del repositorio)

Cubre `scripts/*.py`, `dvc.yaml`/`dvc.lock` y las dependencias de
`requirements.txt` (raíz): pandas, numpy, matplotlib, requests, seaborn,
squarify, scipy, dvc, dvc-s3.

### 3.1 Requisito de versión de Python

Esta máquina solo tiene **Python 3.13.3** instalado (evidencia:
[`00_version_python.txt`](./evidencia_entorno/00_version_python.txt)). El
`requirements.txt` raíz **no fija versiones**, así que no hay un requisito
estricto documentado de versión de Python para este entorno — a diferencia
del backend (§4), donde sí importa (ver hallazgo en §5.2).

### 3.2 Pasos de creación (reproducidos)

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

En Linux/macOS, activar con `source .venv/bin/activate`; en PowerShell,
`.venv\Scripts\Activate.ps1` (igual que documenta el README del backend).

### 3.3 Resultado

- Creación del entorno: sin errores
  ([`01_crear_venv_raiz.txt`](./evidencia_entorno/01_crear_venv_raiz.txt)).
- `pip install -r requirements.txt`: **exit code 0**, 90 paquetes instalados
  sin errores
  ([`03_pip_install_raiz.txt`](./evidencia_entorno/03_pip_install_raiz.txt)).
- `dvc --version` dentro del entorno: `3.67.1`
  ([`04_dvc_version.txt`](./evidencia_entorno/04_dvc_version.txt)).

**Conclusión:** el entorno de datos/scripts se levanta correctamente en una
máquina limpia con Python 3.13.

---

## 4. Entorno 2 — backend (`dengue-malaria-prediccion/`)

Cubre `app/`, `tests/` y las dependencias de
`dengue-malaria-prediccion/requirements.txt` (FastAPI, SQLAlchemy,
scikit-learn, XGBoost, SHAP, etc., todas con versión fijada).

### 4.1 Pasos de creación (los mismos que documenta el README del backend)

```bash
cd dengue-malaria-prediccion
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### 4.2 Resultado de `pip install -r requirements.txt` con las versiones originales: **falla**

Con Python 3.13 (única versión disponible en esta máquina), la instalación
completa del `requirements.txt` del backend **tal como estaba fijado
originalmente** no terminaba con éxito
([`13_pip_install_backend.txt`](./evidencia_entorno/13_pip_install_backend.txt),
exit code 1). El detalle está en §5.1-§5.2. Esto ya se resolvió (§5.3) y
`requirements.txt` quedó actualizado; esta subsección documenta el estado
en el que se encontró el problema, no el estado final.

### 4.3 Verificación funcional, con la solución ya aplicada (Opción B, §5.3)

Con `psycopg2-binary==2.9.13` y `shap==0.52.0` ya fijados en
`requirements.txt`, la instalación completa en el `.venv` del backend
termina en **exit code 0**, sin excluir ningún paquete
([`27_pip_install_backend_opcionB_final.txt`](./evidencia_entorno/27_pip_install_backend_opcionB_final.txt)).
Con eso se probó el flujo completo que describe el README, ya con el
`requirements.txt` definitivo:

| Verificación | Resultado | Evidencia |
|---|---|---|
| `uvicorn app.main:app --port 8001` | Arranca correctamente | [`28_uvicorn_arranque_final.txt`](./evidencia_entorno/28_uvicorn_arranque_final.txt) |
| `curl http://127.0.0.1:8001/health` | `{"status":"ok"}`, HTTP 200 | [`29_curl_health_final.txt`](./evidencia_entorno/29_curl_health_final.txt) |
| `python -m compileall -q app tests` | Sin errores (exit 0) | [`30_compileall_final.txt`](./evidencia_entorno/30_compileall_final.txt) |
| `pytest` | "no tests ran" (exit 5) — esperado, el README ya avisa que todavía no hay casos de prueba | [`31_pytest_final.txt`](./evidencia_entorno/31_pytest_final.txt) |
| Prueba funcional de SHAP (`TreeExplainer` sobre `XGBClassifier`) | `shap_values` calculado sin error | [`25_test_opcionB_shap_funcional.txt`](./evidencia_entorno/25_test_opcionB_shap_funcional.txt) |

**Conclusión:** el backend se instala y arranca de punta a punta en Python
3.13 con el `requirements.txt` definitivo, incluyendo la librería de
explicabilidad (SHAP) que antes fallaba.

---

## 5. Hallazgos de compatibilidad y decisión tomada

### 5.1 `psycopg2-binary==2.9.9` no instalaba en Python 3.13

```text
Downloading psycopg2-binary-2.9.9.tar.gz (384 kB)
...
Error: pg_config executable not found.
pg_config is required to build psycopg2 from source.
ERROR: Failed to build 'psycopg2-binary' when getting requirements to build wheel
```

**Causa:** no existe un *wheel* precompilado de `psycopg2-binary==2.9.9`
para `cp313-win_amd64` (esa versión del paquete es anterior al lanzamiento
de Python 3.13), así que `pip` intenta compilarlo desde el código fuente, lo
que requiere `pg_config` (viene con una instalación de PostgreSQL) —
ausente en esta máquina y no documentado como prerrequisito en ninguna parte
del repo. Evidencia completa:
[`13_pip_install_backend.txt`](./evidencia_entorno/13_pip_install_backend.txt).

### 5.2 `shap==0.46.0` no instalaba en Python 3.13

```text
Attempting to build SHAP: with_binary=True, with_cuda=False (Attempt 2)
...
building 'shap._cext' extension
error: Unable to find a compatible Visual Studio installation.
ERROR: Failed building wheel for shap
```

**Causa:** tampoco existe *wheel* precompilado de `shap==0.46.0` para
`cp313-win_amd64`; `pip` intenta compilar su extensión en C, lo que en
Windows requiere Visual Studio Build Tools — ausentes en esta máquina.
Evidencia completa:
[`14_pip_install_backend_sin_psycopg2.txt`](./evidencia_entorno/14_pip_install_backend_sin_psycopg2.txt).

### 5.3 Decisión tomada: Opción B (actualizar versiones fijadas)

Cambiar versiones fijadas en `requirements.txt` es una decisión de diseño
del equipo (afecta TASK-001, ya escrita en `tasks.md` con esas versiones
específicas), así que no se decidió unilateralmente al encontrar el
problema — coherente con la regla 5 de `CLAUDE.md` ("si una tarea implica
una decisión no cubierta por `design.md`, detente y pregunta"). Se
plantearon dos alternativas y el responsable del proyecto confirmó la
Opción B:

| Opción | Qué implicaba | Decisión |
|---|---|---|
| A. Fijar el proyecto a Python 3.12 (como ya sugiere `design.md` y el README del backend) | Requiere instalar Python 3.12 en cada máquina; no se pudo verificar en esta máquina porque solo hay 3.13 instalado; no evita que el mismo problema reaparezca en la máquina de otro integrante con una versión de Python aún más nueva. | No elegida |
| **B. Actualizar las versiones fijadas de `psycopg2-binary` y `shap` a una que sí tenga wheel para 3.13** | Mantiene Python 3.13 (la versión realmente disponible en el equipo hoy); cambia versiones ya elegidas en `design.md`/`tasks.md`. | **Elegida y aplicada** |

**Verificación previa a aplicar el cambio** (no solo "debería funcionar" —
se probó antes de tocar `requirements.txt`):

1. `pip install --dry-run psycopg2-binary` (sin fijar versión) resuelve a
   `psycopg2_binary-2.9.13-cp313-cp313-win_amd64.whl` — sí tiene wheel para
   Python 3.13
   ([`21_test_psycopg2_ultima_version.txt`](./evidencia_entorno/21_test_psycopg2_ultima_version.txt)).
2. `pip install --dry-run shap` resuelve a `shap-0.52.0-cp312-abi3-win_amd64.whl`
   (wheel de ABI estable, válido también para 3.13), pero requiere
   `numpy>=2`
   ([`22_test_shap_ultima_version.txt`](./evidencia_entorno/22_test_shap_ultima_version.txt)).
3. Se instaló el `requirements.txt` completo del backend en un entorno
   limpio, con `psycopg2-binary==2.9.13`, `shap==0.52.0` y `numpy` sin
   fijar (para que se resolviera junto con shap): **exit code 0**, sin
   conflictos con `sqlalchemy==2.0.35`, `scikit-learn==1.5.2`,
   `xgboost==2.1.1` ni `pandas==2.2.3`
   ([`23_test_opcionB_full_install.txt`](./evidencia_entorno/23_test_opcionB_full_install.txt)).
4. Se importaron todas las librerías clave juntas sin error
   ([`24_test_opcionB_imports.txt`](./evidencia_entorno/24_test_opcionB_imports.txt)).
5. **Prueba funcional real** (no solo import): se entrenó un
   `XGBClassifier` de juguete y se calculó
   `shap.TreeExplainer(modelo).shap_values(X)` — corrió sin error
   ([`25_test_opcionB_shap_funcional.txt`](./evidencia_entorno/25_test_opcionB_shap_funcional.txt)).
   Esto es justo la operación que necesita TASK-013/REQ-004.

**Hallazgo adicional:** `shap==0.52.0` ya no compila una extensión en C
(por eso ya no requiere Visual Studio) — pasó a apoyarse en `numba`/
`llvmlite` (compilación JIT), que sí traen *wheel* para 3.13. Estas quedan
como dependencias transitivas nuevas de `shap`, no se agregaron como pines
directos en `requirements.txt` (igual que el resto de dependencias
transitivas del archivo, que tampoco están fijadas una por una).

**Cambio aplicado en `dengue-malaria-prediccion/requirements.txt`:**

| Paquete | Antes | Ahora |
|---|---|---|
| `psycopg2-binary` | `2.9.9` | `2.9.13` |
| `shap` | `0.46.0` | `0.52.0` |
| `numpy` | `1.26.4` | `2.5.3` |

Reinstalado en el `.venv` real del backend (no solo en el entorno de
prueba) con **exit code 0**
([`27_pip_install_backend_opcionB_final.txt`](./evidencia_entorno/27_pip_install_backend_opcionB_final.txt))
y reverificado de punta a punta en §4.3.

### 5.4 Riesgo menor (ya resuelto): `requirements.txt` raíz sin versiones fijadas

Al ejecutar `scripts/linea_base_modelo.py` dentro del entorno nuevo (§3)
para confirmar que el pipeline corre de punta a punta, los 5 archivos de
salida ya versionados en `scripts/linea_base_output/` se regeneraron con
diferencias en la **12ª-15ª cifra decimal** (ej. `7.666666666666667` vs
`7.666666666666668`), no en el resultado reportado. La causa era que
`requirements.txt` (raíz) no fijaba versión de `numpy`/`pandas`/`scipy`, así
que esta instalación trajo versiones más nuevas
(`numpy 2.5.3`, `pandas 3.0.5`, `scipy 1.18.1`) que las que generaron los
archivos ya commiteados. Los archivos regenerados **se restauraron a su
versión commiteada** después de la verificación (no se dejó ese cambio
lateral en el repositorio).

**Decisión tomada:** el responsable del proyecto confirmó fijar las 9
dependencias del `requirements.txt` raíz a las versiones ya instaladas y
verificadas en el `.venv` de esta sesión:

```text
pandas==3.0.5
numpy==2.5.3
matplotlib==3.11.2
requests==2.34.2
seaborn==0.13.2
squarify==0.4.5
scipy==1.18.1
dvc==3.67.1
dvc-s3==3.3.0
```

Reinstalado desde el archivo ya fijado en el mismo `.venv`: **exit code 0**
([`26_pip_install_raiz_pinned.txt`](./evidencia_entorno/26_pip_install_raiz_pinned.txt)).
No afecta ninguna cifra reportada en `linea_base.md`; elimina el riesgo de
reproducibilidad exacta para cualquiera que clone el repo desde ahora.

---

## 6. Estado inicial de los datos (antes de cualquier transformación)

Esta sección describe los datos **tal como están disponibles al clonar el
repositorio y antes de ejecutar un solo script**, distinto de
`pipeline_datos.md` (que describe el resultado *después* de transformarlos).

### 6.1 Datos crudos (`data/raw/`) — no accesibles en esta máquina

`data/raw/` está versionado con DVC contra un remoto S3 en DagsHub. En esta
máquina, **antes de cualquier transformación, los datos crudos no están
presentes**: solo existen los punteros `.dvc` que declaran su huella
(checksum) y tamaño esperados, no el contenido.

| Fuente | Puntero DVC | md5 esperado | Tamaño esperado | Archivos | ¿Presente localmente? |
|---|---|---|---:|---:|---|
| Epidemiología (Ministerio de Salud) | `data/raw/epidemiologia.dvc` | `385a7f2097d3da522b13b68124b66738.dir` | 14.313 bytes | 3 | **No** |
| Clima RAW (SENAMHI) | `data/raw/clima/senamhi/senamhi_raw_SE01_13_2026.csv.dvc` | `c0458753e42c23b95ffb85d162383947` | 2.878.876 bytes | 1 | **No** |

Evidencia de los punteros:
[`07_punteros_dvc_raw.txt`](./evidencia_entorno/07_punteros_dvc_raw.txt).

Se intentó `dvc pull -r origin-s3` (mismo comando que documenta
`pipeline_datos.md`) y **falló por falta de credenciales**, reproduciendo
exactamente el bloqueo ya anotado en `CONTEXT.md`:

```text
ERROR: failed to connect to s3 (dvc/files/md5) - Unable to locate credentials
ERROR: failed to pull data from the cloud - 2 files failed to download
```

Evidencia:
[`06_dvc_pull_intento.txt`](./evidencia_entorno/06_dvc_pull_intento.txt),
[`05_dvc_status.txt`](./evidencia_entorno/05_dvc_status.txt). Consecuencia
directa y verificada: `scripts/procesar_clima.py` (primer paso del pipeline)
falla con `FileNotFoundError` al intentar leer el CSV crudo que no está
presente —
[`09_intento_procesar_clima.txt`](./evidencia_entorno/09_intento_procesar_clima.txt).

**Nota sobre un archivo local que podría confundirse con el crudo real:**
existe `data/raw/clima/senamhi/senamhi_descarga_parcial.csv` (nombre de
archivo temporal del script de descarga, excluido de Git por
`.gitignore`). Tiene el **mismo tamaño en bytes y el mismo número de filas**
que el archivo esperado según el puntero DVC, pero su **md5 no coincide**
(`ceda9b9af59ce8c86424149adcdde01b` calculado vs.
`c0458753e42c23b95ffb85d162383947` esperado — ver
[`08_md5_descarga_parcial.txt`](./evidencia_entorno/08_md5_descarga_parcial.txt)).
Por tanto **no debe tratarse como un sustituto válido** del dato crudo
versionado ni usarse para reproducir el pipeline; solo `dvc pull` con
credenciales reales garantiza el dato crudo canónico.

### 6.2 Datos ya procesados (`data/processed/`) — preexistentes, no generados en esta tarea

A diferencia de `data/raw/`, `data/processed/` **sí está en Git plano** (no
en DVC) y ya contenía, antes de esta tarea, las salidas de los pipelines de
Adriana y Tania (Paso 2). Este documento no los regenera — el pipeline que
los produce ya está descrito en `pipeline_datos.md`. Se listan aquí solo
para dejar constancia del estado con el que arranca cualquier trabajo
posterior:

| Archivo | Filas (incl. cabecera) | Tamaño |
|---|---:|---:|
| `clima_diario.csv` | 275 | 35.562 bytes |
| `clima_diario_imputado.csv` | 325 | 68.627 bytes |
| `clima_semanal.csv` | 45 | 4.619 bytes |
| `clima_semanal_calidad.csv` | 45 | 4.554 bytes |
| `control_calidad_clima.csv` | 16.779 | 2.990.503 bytes |
| `dataset_integrado_municipal.csv` | 5 | 2.399 bytes |
| `dengue_municipal_validado.csv` | 29 | 8.831 bytes |
| `dengue_semanal_validado.csv` | 14 | 3.285 bytes |
| `malaria_municipal_validado.csv` | 22 | 6.425 bytes |

Evidencia:
[`20_inventario_processed.txt`](./evidencia_entorno/20_inventario_processed.txt).

Como esos archivos sí están disponibles, se pudo verificar de punta a punta
que un script del pipeline **que no depende de `data/raw/`** corre sin
errores en el entorno nuevo (§3): `scripts/linea_base_modelo.py`, que lee
`dengue_semanal_validado.csv` y `dataset_integrado_municipal.csv` y
reproduce exactamente los números publicados en `linea_base.md` (MAE 8.83,
RMSE 11.82, MAPE 70.68% del experimento A) — ver
[`10_ejecucion_linea_base_modelo.txt`](./evidencia_entorno/10_ejecucion_linea_base_modelo.txt).

### 6.3 Resumen honesto del estado inicial

En esta máquina, "estado inicial de los datos" significa: **cero bytes de
`data/raw/` reales, y `data/processed/` completo pero heredado de una
ejecución previa del equipo, no reproducido aquí por el bloqueo de DVC**.
Cualquier persona que clone el repositorio hoy sin credenciales de DagsHub
llegará exactamente a este mismo estado — no es un problema de esta
máquina en particular.

---

## 7. Variables de entorno (`.env`)

- No existe ningún archivo `.env` en el repositorio (correcto: está
  excluido por `.gitignore` en `dengue-malaria-prediccion/.gitignore` y
  no se encontró ninguno suelto en el árbol de trabajo).
- `dengue-malaria-prediccion/.env.example` documenta las variables
  previstas (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
  `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `ENVIRONMENT`,
  `CLIMA_API_URL`, `CLIMA_API_KEY`, `EPIDEMIOLOGIA_FUENTE_URL`) y coincide
  con lo que usa `app/main.py` hoy: el endpoint `/health` no lee ninguna de
  ellas, por lo que el backend arranca sin copiar `.env.example` a `.env`
  (confirmado en la prueba de §4.3).
- Las credenciales del remoto DVC (`origin-s3`) **no se configuran por
  `.env`**, sino con `dvc remote modify --local origin-s3
  access_key_id/secret_access_key` (ver `pipeline_datos.md` y
  `cierre_sprint1.md` §3.1); esta máquina no tiene esas credenciales
  configuradas, de ahí el bloqueo de §6.1.

---

## 8. Checklist de Línea Base — Paso 1

- [x] Entorno reproducible del track de datos (`requirements.txt` raíz)
      confirmado y funcionando, con versiones fijadas (§3, §5.4).
- [x] Entorno reproducible del backend confirmado y funcionando de punta a
      punta, incluida la instalación completa de `psycopg2-binary` y
      `shap` sobre Python 3.13 (§4-§5).
- [x] Estado inicial de los datos crudos descrito con evidencia (punteros
      DVC, intento real de `dvc pull`, error de credenciales) (§6.1).
- [x] Estado de los datos ya procesados descrito, sin reproducirlos de
      nuevo en esta tarea (§6.2).
- [x] Evidencia (logs de comandos reales) guardada en
      `docs/evidencia_entorno/` para cada afirmación de este documento.
- [x] Decisión de equipo tomada: Opción B de §5.3 (actualizar
      `psycopg2-binary` y `shap`), verificada con instalación limpia,
      imports conjuntos y una prueba funcional real de SHAP+XGBoost antes
      de aplicarla.
- [x] Decisión de equipo tomada: fijar versiones en `requirements.txt`
      raíz (§5.4), aplicada y reinstalada con éxito.
- [ ] Pendiente, fuera del alcance de este documento: obtener credenciales
      DVC en esta máquina para poder correr `descargar_senamhi.py` →
      `procesar_clima.py` → `integrar_datos.py` de punta a punta (§6.1).

---

## 9. Reproducibilidad de este documento

```bash
# Entorno 1 (raíz)
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m dvc status
./.venv/Scripts/python.exe -m dvc pull -r origin-s3   # falla sin credenciales, esperado
./.venv/Scripts/python.exe scripts/linea_base_modelo.py

# Entorno 2 (backend)
cd dengue-malaria-prediccion
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # exit 0 en Python 3.13, ver §5.3
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
curl http://127.0.0.1:8000/health
./.venv/Scripts/python.exe -m compileall -q app tests
./.venv/Scripts/python.exe -m pytest
```

No requiere red salvo para `pip install` y el intento (fallido, esperado)
de `dvc pull`.

---

