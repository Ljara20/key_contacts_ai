# Key Contacts AI — proyecto local MVP 0.1.0

## Qué funciona actualmente
- Ingesta de `.xlsx` y `.csv` (tipos textuales para no perder ceros en IDs).
- Normalización conservadora, reporte de calidad en JSON, filas con correos inválidos a revisión.
- Índice local TF-IDF con búsqueda de candidatos, sin API pagada ni tokens.
- Medición básica de latencia y memoria Python; métricas Recall@K y MRR listas para etiquetas reales.
- API FastAPI opcional, pruebas pytest y estructura modular editable en Cursor / VS Code.

**Limitación crítica:** no existen aún etiquetas verificadas ni catálogo RACI/estado de personas. La búsqueda entrega **candidatos**, no responsables oficialmente confirmados. No habilitar para usuarios finales ni publicar datos personales sin controles corporativos. La solución de Control Intelligence, DL/LLM y benchmark comparativo están planeados, **no implementados** en esta primera base.

## Instalación Windows 11, Python 3.12
Abre esta carpeta desde VS Code / Cursor y ejecuta en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
```

## Primera prueba (datos sintéticos)

```powershell
python scripts/generate_demo.py
python -m keycontacts.cli ingest data/raw/demo_finance.csv
python -m keycontacts.cli search "impuestos colombia"
```

## Con tus archivos Excel o CSV
Copia tus archivos en `data/raw/` (no se incluyen en el ZIP ni deben subirse a git):

```powershell
python -m keycontacts.cli ingest "data/raw/informacion finanzas.xlsx"
python -m keycontacts.cli search "soporte de impuestos en Colombia"
```

Para indicar hoja distinta: `--sheet "NombreHoja"` o `--sheet 1`.

**Salidas:** `data/processed/finance_normalized.csv`, `finance_review.csv`, `quality_report.json`.

## API opcional

```powershell
python -m pip install -r requirements-api.txt
python -m uvicorn keycontacts.api.app:app --reload
```

Prueba `http://127.0.0.1:8000/docs` (en entorno de desarrollo privado solamente).

## Estructura y reemplazo incremental
- `src/keycontacts/ingestion/readers.py`: fuentes CSV/Excel.
- `src/keycontacts/validation/schema.py`: contratos y validaciones.
- `src/keycontacts/cleaning/pipeline.py`: ETL y control de calidad.
- `src/keycontacts/search/baseline.py`: baseline TF-IDF local.
- `src/keycontacts/ml/evaluation.py`: evaluación y medición de recursos.
- `src/keycontacts/api/app.py`: interfaz HTTP.
- `src/keycontacts/cli.py`: interfaz consola.
- `tests/`: pruebas de regresión.

Sustituye cada archivo `.py` manteniendo las firmas públicas y corre `pytest` después de cada cambio. Separa la lógica de negocio de API/UI y lectura de datos. Los `requirements-dl.txt` son **opcionales**, aún no ejecutan un modelo DL. Para futuras comparaciones, registrar calidad, latencia p50/p95, RAM/VRAM de proceso y costos con mismo dataset/condiciones.

## Avisos de seguridad y datos
- Archivos originales se preservan; la salida normalizada puede contener emails personales y debe mantenerse protegida.
- No se imputan correos, rol RACI, vigencia, ni responsables supuestos.
- El MVP **no implementa autorización ni controles de acceso a nivel de consulta**; úsalo solamente en desarrollo local autorizado.
- Los campos del Excel pueden cambiar según exportación. Los encabezados observados son provisionales y deben validarse con muestras reales.
