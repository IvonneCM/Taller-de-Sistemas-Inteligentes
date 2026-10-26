"""La imagen `api` del Dockerfile solo instala requirements-api.txt (sin
pandas, scikit-learn, xgboost ni shap). Importar la aplicacion NO debe
arrastrarlos: si lo hiciera, la API desplegada no arrancaria (error que detecto
Docker y que los tests, corridos con todas las dependencias, no veian)."""

import subprocess
import sys

PESADOS = ["pandas", "numpy", "sklearn", "xgboost", "shap", "scipy"]


def test_importar_la_aplicacion_no_carga_librerias_de_ml():
    codigo = (
        "import sys; import app.main; "
        f"pesados = [m for m in {PESADOS!r} if m in sys.modules]; "
        "print(','.join(pesados)); sys.exit(1 if pesados else 0)"
    )
    resultado = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
    assert resultado.returncode == 0, (
        "app.main importa librerias que la imagen `api` no instala: "
        f"{resultado.stdout.strip() or resultado.stderr[-400:]}"
    )
