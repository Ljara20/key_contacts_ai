# Key Contacts AI & Control Intelligence

**Arquitectura técnica, guía de desarrollo y evaluación de modelos**  
**Estado:** MVP local de Key Contacts + diseño de evolución multimodelo  
**Entorno de trabajo:** WSL (Ubuntu), Python 3.12, VS Code / Cursor  
**Última revisión documental:** 2026-11-17

> **Regla de interpretación:** «Implementado» significa que existe código en la base del MVP inspeccionada; «Diseñado» describe una decisión de arquitectura todavía sin implementación; «Condicionado» requiere datos, permisos o experimentos antes de desarrollarse. Ninguna métrica de calidad predictiva se considera validada sin un conjunto de prueba etiquetado.

## 1. Propósito y alcance

El proyecto contiene dos capacidades independientes con infraestructura compartida:

| Dominio | Pregunta de negocio | Resultado esperado | Restricción |
|---|---|---|---|
| **A. Key Contacts AI** | ¿Qué persona puede atender una solicitud? | Hasta **3 contactos elegibles**, ordenados, con fuente, vigencia y explicación; o abstención | Una similitud de texto **no** certifica responsabilidad. Las reglas de elegibilidad y el catálogo RACI deben estar validados. |
| **B. Control Intelligence** | ¿Falta evidencia de un control o hay una situación que requiere revisión? | Estado de revisión, alertas justificadas y referencias documentales | El sistema **no aprueba, firma ni declara incumplimiento automáticamente**. |

**Estrategia experimental acordada:** primero resolver las tareas con reglas y modelos locales de ML/DL; después construir un comparador con modelos generativos autorizados. La decisión final considerará tanto la **calidad** como el **uso de recursos, latencia y costo**. No se integrará un LLM por defecto en cada consulta.

## 2. Estado real frente a la arquitectura objetivo

| Componente | Estado | Evidencia en el repositorio / condición |
|---|---|---|
| Ingesta de archivos `.csv` y `.xlsx` | **Implementado** | `src/keycontacts/ingestion/readers.py` |
| Normalización conservadora y reporte de calidad | **Implementado (básico)** | `cleaning/pipeline.py`, `validation/schema.py`; no aplica todavía un bloqueo integral de registros defectuosos |
| Búsqueda TF-IDF en memoria | **Implementado** | `search/baseline.py`, comando `search` |
| **M01** TF-IDF persistente + similitud coseno | **Implementado** | `search/tfidf_model.py`, comandos `train-tfidf` y `predict-tfidf` |
| Métricas básicas de tiempo y memoria Python | **Implementado** | `ml/evaluation.py`; **no** mide CPU/GPU/RAM total |
| BM25, embeddings, fusión RRF | **Diseñado** | Sin módulos funcionales en esta versión |
| Clasificadores, LightGBM, stacking y ajuste fino DL | **Condicionado** | Requieren etiquetas de verdad-terreno y experimentación |
| RACI, estado vigente, permisos por usuario | **Pendiente crítico** | No usar resultados del MVP como asignaciones oficiales |
| Motor B: controles/evidencias | **Diseñado** | No implementado |
| LLM / RAG y benchmark completo | **Diseñado** | No implementado; sujeto a permisos y presupuesto |
| API FastAPI opcional | **Implementado como interfaz de desarrollo** | `api/app.py`; no presupone seguridad de producción |

### Qué significa «modelo» en este proyecto

- **TF-IDF y BM25** son métodos de representación/recuperación de información; TF-IDF ajusta su vocabulario al corpus, pero no aprende responsables a partir de ejemplos etiquetados.
- **Embeddings** son vectores producidos por un encoder de DL, normalmente preentrenado; **no equivalen** a modelos ensamblados.
- **Ensemble** combina salidas de varios recuperadores o predictores. **RRF** fusiona posiciones sin entrenar un metamodelo.
- **Stacking** sí requiere un metamodelo entrenado sobre predicciones fuera de muestra (out-of-fold) para evitar fuga de datos.
- **Pipeline secuencial** conecta etapas mediante contratos explícitos; no todas las etapas son modelos de ML.

## 3. Flujo de extremo a extremo

```text
CSV / Excel autorizados
    |
    v
Ingesta -> Perfilado -> Validación de esquema -> Normalización -> Revisión de incidencias
    |
    v
Datos curados y versionados + catálogo oficial de contactos / RACI (pendiente)
    |
    +---------------------- DOMINIO A: KEY CONTACTS ----------------------+
    |                                                                   |
Solicitud + contexto autorizado                                        |
    |                                                                   |
    +--> Clasificación de área/categoría (OPCIONAL; exige etiquetas)    |
    |                                                                   |
    +--> Recuperación EN PARALELO: BM25 + embeddings (DISEÑADO) <--------+
                       |                  |
                       +--> fusión RRF <--+
                                |
                   Validación obligatoria de permisos,
                   región, vigencia y responsabilidad RACI
                                |
                   Ranking por reglas (inicial) / LightGBM
                   (posterior; si supera al baseline)
                                |
                        Top 3 o abstención
                                |
                       Confirmación humana
                                |
                      Feedback y auditoría

Datos curados + reglas de controles + evidencias
    |
    +-------------------- DOMINIO B: CONTROL INTELLIGENCE ---------------+
    |  Extracción verificable -> reglas versionadas -> alertas -> revisión|
    |  Anomalías estadísticas/ML, solo con histórico adecuado (opcional) |
    +--------------------------------------------------------------------+

COMPARACIÓN POSTERIOR: pipelines locales vs LLM/RAG autorizado,
medidos sobre casos equivalentes, con calidad + recursos + costos.
```

**Orden lógico, no obligación de ejecutar todo:** el clasificador no puede bloquear la búsqueda si su salida es incierta. Los filtros de permisos deben aplicarse **antes de acceder o exponer datos**, además de comprobar la elegibilidad antes del ranking final; el dibujo simplifica esos controles transversales.

## 4. Datos y contratos de entrada

### 4.1 Fuentes de referencia

| Fuente | Uso admisible | Precaución |
|---|---|---|
| Exportaciones de finanzas Excel/CSV | Contexto de proyecto, equipo, región y correos asociados | Un correo en `FPC Email`, `Substitute Email` o `LM Email` **no es** una etiqueta de responsable correcto para cualquier solicitud |
| Directorio/HR y catálogo RACI aprobados | Elegibilidad, vigencia y responsabilidades oficiales | **No disponibles ni integrados en este MVP** |
| Histórico de solicitudes y asignaciones revisadas | Entrenamiento supervisado y evaluación | **No confirmado** en los archivos de prueba |
| Catálogo de controles + evidencias autorizadas | Reglas y validación del Motor B | **Pendiente** |

**Columnas descriptivas usadas actualmente por M01:** `Project Description`, `Customer Team`, `Market`, `Market Unit`, `System` (solo las presentes). **Columnas candidatas de contacto:** `FPC Email`, `Substitute Email`, `LM Email`. Un archivo sin campos descriptivos adecuados no puede indexarse con M01. El lector conserva identificadores como texto; el pipeline no inventa correos, responsabilidades ni estados.

### 4.2 Pipeline de datos — contrato operativo actual

| Paso | Input | Acción actual | Output actual | Pendiente para producción |
|---|---|---|---|---|
| Ingesta | Ruta local `.csv` / `.xlsx`; hoja opcional | Lee tabla con pandas | DataFrame | Registro de orígenes/permisos y múltiples esquemas |
| Validación inicial | DataFrame | Informa presencia de columnas esperadas | Resumen de esquema | Esquemas por fuente y errores bloqueantes |
| Limpieza | DataFrame | Recorta espacios, normaliza vacíos y minúsculas de correos | Tabla normalizada | Reglas por columna, fechas, claves, semántica |
| Inspección de calidad | Tabla normalizada | Cuenta nulos, duplicados y correos inválidos | `quality_report.json` | Umbrales y puerta formal de calidad |
| Revisión | Filas con correos inválidos | Exporta filas señaladas | `finance_review.csv` | Flujo de corrección humana y cuarentena real |
| Publicación local | Tabla normalizada | Exporta CSV | `finance_normalized.csv` | Curación aprobada, versiones y fuente maestra |

**Importante:** actualmente `finance_normalized.csv` conserva también filas señaladas en el reporte; `finance_review.csv` es una **copia para revisión**, no un mecanismo de exclusión automática. Por ello el pipeline no debe describirse como un *quality gate* productivo ya implementado.

### 4.3 Contrato objetivo entre etapas (diseñado, no implementado)

| Objeto lógico | Campos mínimos propuestos | Consumidor |
|---|---|---|
| `Request` | `request_id`, `query`, `language`, `region`, contexto permitido, instante de consulta | Clasificador y recuperadores |
| `Candidate` | `contact_id`, `source_record_id`, origen, fecha de vigencia, puntajes por recuperador | Fusión y reglas de elegibilidad |
| `EligibilityResult` | Candidato, `eligible`, códigos de motivo, versión RACI, permisos aplicados | Ranker y respuesta |
| `Recommendation` | `status`, hasta 3 candidatos elegibles, justificación y fuentes, versiones | API/UI y auditoría |
| `FeedbackEvent` | Solicitud, recomendación, selección/corrección verificada, fecha | Evaluación y futuros entrenamientos |

**Invariante:** el `score` de recuperación mide similitud/relevancia relativa, **no probabilidad calibrada de responsabilidad**.

## 5. Catálogo de modelos — input, propósito, procesamiento y output

### 5.1 Motor A: Key Contacts

| ID / método | Input principal | Qué hace | Output esperado | Relación con otros módulos | Estado |
|---|---|---|---|---|---|
| **M01 · TF-IDF + coseno** | Corpus descriptivo curado + consulta libre | Ajusta pesos léxicos, calcula similitud y deduplica emails | Hasta 3 **contactos asociados**, score y fuente de columna | Baseline **independiente** | **Implementado** |
| **M02 · BM25** | Consulta + mismos registros de referencia | Recupera coincidencias léxicas ponderadas | Ranking de IDs de registro/candidato con score BM25 | Rama paralela de M03 | **Diseñado** |
| **M03 · Embeddings multilingües** | Consulta + descripciones del catálogo | Codifica semántica con encoder local preentrenado | Ranking de IDs con similitud vectorial | Rama paralela de M02 | **Diseñado** |
| **M04 · RRF (ensemble)** | Rankings M02 y M03 sobre IDs compatibles | Combina posiciones, no promedia scores de escalas distintas | Ranking fusionado + procedencia | Salida alimenta validación/ranking | **Diseñado** |
| **M05 · Logistic Regression** | Solicitudes históricas y **etiquetas de área/categoría** | Clasificación supervisada con características textuales | Categoría + probabilidades del clasificador | Contexto **opcional** para recuperar; no filtrar de forma irreversible por una predicción incierta | **Condicionado** |
| **M06 · Linear SVM** | Mismas solicitudes etiquetadas de M05 | Clasificación alternativa para benchmark | Categoría + puntuación de decisión (no probabilidad por defecto) | **Alternativa**, no sucesor obligatorio de M05 | **Condicionado** |
| **M07 · LightGBM Ranker** | Consultas, candidatos elegibles y relevancia humana verificada | Aprende a ordenar candidatos | Ranking final de candidatos **ya elegibles** | Posterior a reglas; comparar con ranking transparente | **Condicionado** |
| **M08 · Transformer ajustado** | Solicitudes y etiquetas verificadas | Clasificación semántica ajustada al dominio | Categoría o score de relevancia, según tarea definida | **Alternativa experimental** a M05/M06, no etapa fija | **Condicionado** |
| **STK · Stacking** | Scores de modelos base, generados fuera de muestra, y etiquetas | Aprende a combinar predicciones | Score combinado | **Alternativa a estudiar**; no confundir con RRF | **Condicionado** |

**Selección actual:** mantener M01 como línea base; M02 y M03 se diseñarán primero como recuperadores **comparables sobre el mismo corpus**. M04 se ensayará solo después de medir sus componentes. M05–M08 y STK no se entrenarán sin etiquetas verificadas.

### 5.2 Motor B: Control Intelligence

| Componente | Input | Función | Output | Estado |
|---|---|---|---|---|
| **Reglas versionadas** | Control, periodo, requisito, fecha y referencia autorizada | Comprobar existencia, plazo y completitud verificable | Alerta objetiva o estado «requiere revisión» | Diseñado |
| **Extracción estructurada** | Excel/documentos permitidos | Extraer campos con lector/regex y ubicación de origen | Campos y referencias trazables | Diseñado |
| **NLP/NER opcional** | Documentos variables + ejemplos anotados | Extraer entidades difíciles para reglas | Campos con confianza y fuente | Condicionado |
| **Anomalías: umbrales / Isolation Forest / LOF** | Ejecuciones históricas comparables | Señalar patrones atípicos | Puntaje/alerta para revisión humana | Condicionado |
| **Enlace a Key Contacts** | Control y rol de revisión autorizado | Encontrar dueño/revisor vigente por RACI | Sugerencia trazable de contacto | Diseñado |

Un resultado de anomalía **no** equivale a incumplimiento; la ausencia de alertas **no** prueba conformidad.

## 6. Ensamblaje, encadenamiento y decisión final

| Patrón | Componentes | Qué recibe | Qué entrega | Criterio de uso |
|---|---|---|---|---|
| **Baseline individual** | M01 o M02 o M03 | Consulta/corpus | Ranking propio | Medir calidad y costo aisladamente |
| **Ensemble paralelo** | M02 + M03 → M04 (RRF) | Dos rankings con IDs comunes | Lista fusionada | Mantener solo si mejora el baseline |
| **Pipeline secuencial** | Clasificador opcional → búsqueda → elegibilidad → ranker | Consulta + contexto + catálogos autorizados | Top 3 válido o abstención | Operación de Key Contacts cuando existan datos y permisos |
| **Stacking supervisado** | Predictores base → metamodelo | Predicciones fuera de muestra + etiquetas | Score agregado | Solo tras comprobar mejora sin fuga de información |
| **Comparador generativo** | LLM/RAG autorizado frente a solución local | Mismos casos con contexto equivalente permitido | Respuestas evaluables y costos registrados | Experimento posterior, no dependencia del MVP |

**Reglas para encadenar:** (1) definir ID estable de registro/contacto; (2) contratos tipados y versionados; (3) no perder el origen de evidencia; (4) nunca convertir scores de similitud directamente en elegibilidad; (5) permitir saltar componentes opcionales; (6) permitir abstención; (7) registrar versiones y decisiones humanas.

## 7. Plan de evaluación reproducible

### 7.1 Métricas por componente

| Componente / experimento | Calidad principal | Recursos a registrar | Datos indispensables |
|---|---|---|---|
| M01 / M02 / M03 | **Recall@3, MRR**, por región e idioma | Latencia p50/p95, CPU, RAM, tamaño de índice, tiempo de construcción; GPU/VRAM en DL cuando corresponda | Consultas con contacto(s) correcto(s) validado(s) y vigencia histórica |
| M04: RRF | Recall@3, MRR, **NDCG@3** si hay grados de relevancia | Latencia/CPU/RAM **de extremo a extremo**, no solo fusión | Los mismos casos y candidatos de M02/M03 |
| M05 / M06 / M08: clasificación | Macro-F1, precision/recall por clase, matriz de confusión | Entrenamiento, inferencia, RAM, CPU/GPU | Solicitudes etiquetadas por área/categoría |
| M07 / STK: ranking aprendido | NDCG@3, Recall@3, reasignaciones en piloto | Costo de construir características, entrenar e inferir | Relevancia verificada por candidato; particiones sin fuga |
| Reglas / extracción Motor B | Cobertura de reglas, exactitud de campos, falsos positivos de alertas | Latencia, RAM y esfuerzo de revisión | Reglas aprobadas y casos positivos/negativos revisados |
| Detección de anomalías | Precision/recall **si** existen alertas adjudicadas; tasa de revisión útil | CPU/RAM, latencia y costo por alerta revisada | Ciclos comparables + validación humana |
| LLM/RAG (posterior) | Mismas métricas de tarea, errores factuales, cobertura de evidencia y abstención | Latencia, tokens, costo API/infraestructura; recursos del host si LLM local | Mismo benchmark y autorizaciones |

### 7.2 Protocolo obligatorio

1. Definir **unidad de evaluación**: solicitud → contacto correcto para A; control × periodo × ejecución para B.
2. Separar cronológicamente entrenamiento, validación y prueba cuando exista histórico; no usar resultados posteriores para predecir solicitudes anteriores.
3. Mantener iguales consultas, corpus permitido, ventana temporal y reglas de elegibilidad al comparar modelos.
4. Ejecutar **ablaciones**: comparar M02, M03 y M04; después añadir clasificación o ranking y medir el cambio real.
5. Medir condiciones de hardware comparables: versión de Python, número de hilos, CPU/GPU, RAM, tamaño de lote, carga en caliente/frío y repeticiones.
6. Reportar resultados por idioma, región, categoría y tipo de solicitud; incluir fallos y abstenciones.
7. No aprobar una variante solo por mayor calidad si empeora de forma inaceptable privacidad, costo, latencia o mantenimiento.
8. Registrar decisiones y artefactos de experimento; no alterar el conjunto de prueba para ajustar hiperparámetros.

### 7.3 Estado de instrumentación

| Métrica | Situación actual |
|---|---|
| Tiempo de una ejecución (`latency_ms`) | Disponible en `timed_call` |
| Pico de asignaciones rastreadas por Python (`python_peak_memory_mb`) | Disponible; **no representa RAM residente total** |
| Tamaño del archivo `.joblib` | Disponible al guardar M01 |
| Recall@k y MRR | Funciones disponibles en `ml/evaluation.py`; **faltan etiquetas reales** |
| CPU, RAM total, GPU/VRAM, energía, throughput, p95 con múltiples ejecuciones | **Por implementar** |
| Costos por 1.000 solicitudes y tokens de GenAI | **Por implementar** |

**Resultado de la comparación:** buscar soluciones no dominadas en calidad/recursos (frontera de Pareto), documentando restricciones de negocio; no presentar un modelo como ganador antes de medirlo.

## 8. Estructura del repositorio y responsabilidades

```text
key_contacts_ai/
├── data/
│   ├── raw/                       # entradas originales locales; no versionar datos sensibles
│   ├── processed/                 # salidas actuales de normalización
│   └── rejected/                  # reservado; no es cuarentena automatizada actualmente
├── models/                        # artefactos locales .joblib y metadatos
├── reports/                       # reservado para resultados de experimentos
├── scripts/generate_demo.py       # datos ficticios
├── src/keycontacts/
│   ├── ingestion/readers.py       # lectura CSV / XLSX
│   ├── validation/schema.py       # validación mínima actual
│   ├── cleaning/pipeline.py       # normalización y reporte
│   ├── search/baseline.py         # TF-IDF en memoria
│   ├── search/tfidf_model.py      # M01 persistente
│   ├── ml/evaluation.py           # métricas de recuperación y recursos Python
│   ├── api/app.py                 # API de desarrollo (opcional)
│   └── cli.py                     # comandos existentes
├── tests/
│   ├── test_core.py
│   └── test_tfidf_model.py
├── requirements.txt
├── requirements-api.txt
├── requirements-dl.txt           # dependencias opcionales; NO implementan DL por sí mismas
├── pyproject.toml
└── README.md
```

**Módulos futuros (no crear carpetas vacías obligatorias):** `search/bm25_model.py`, `search/embeddings_model.py`, `search/rrf_fusion.py`, `classification/`, `ranking/`, `contracts/`, `orchestration/`, `control_intelligence/`, `evaluation/resource_monitor.py`. Sus nombres y APIs se formalizarán antes de integrar cada módulo; conservar las rutas existentes hasta entonces.

### Reglas de código limpio y colaboración en Cursor

- **Una responsabilidad por módulo:** lector ≠ validador ≠ modelo ≠ orquestador ≠ API.
- **Interfaces estables:** definir entrada/salida y excepciones antes de sustituir un `.py`; evitar dependencias circulares.
- **No mezclar lógica de negocio con CLI/UI:** la interfaz solo coordina y presenta resultados.
- **Pruebas por cambio:** unitarias del módulo, integración de contratos y regresión del pipeline.
- **Datos/versiones trazables:** fuente, fecha, hash, índice/modelo, reglas y decisiones; no registrar contenido sensible en logs.
- **Despliegue:** aislar configuración y secretos, restringir accesos y documentar rollback antes de piloto.
- **Revisión humana:** resultados o etiquetas aportados por usuarios no pasan directamente a entrenamiento de producción.

## 9. Ejecución local en WSL

Situado en la **raíz** `key_contacts_ai`:

```bash
python3 --version                 # esperado en tu WSL: 3.12.x
source .venv/bin/activate         # si ya creaste el entorno
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
```

Si el entorno aún no existe: `python3.12 -m venv .venv` y `source .venv/bin/activate` (requiere soporte `python3.12-venv` en Ubuntu).

### Flujo de prueba con datos sintéticos

```bash
python scripts/generate_demo.py
python -m keycontacts.cli ingest data/raw/demo_finance.csv
python -m keycontacts.cli train-tfidf
python -m keycontacts.cli predict-tfidf "impuestos colombia" --top 3
python -m pytest -q
```

### Flujo con archivo autorizado

```bash
# Copiar el archivo autorizado de forma local a data/raw/; no subirlo a Git
python -m keycontacts.cli ingest "data/raw/informacion finanzas.xlsx"
python -m keycontacts.cli train-tfidf
python -m keycontacts.cli predict-tfidf "finanzas colombia" --top 3
```

**Archivos producidos:** `data/processed/finance_normalized.csv`, `finance_review.csv`, `quality_report.json`; y `models/tfidf_contacts.joblib`, `tfidf_contacts.json` al entrenar. **Solo cargar modelos `.joblib` creados por fuentes confiables**, porque la deserialización puede ejecutar código.

**Comando legado:** `python -m keycontacts.cli search "impuestos colombia"` construye TF-IDF en memoria; `predict-tfidf` usa el índice previamente guardado. No confundir sus costos medidos: `search` no incluye en `timed_call` el costo de construir `ContactSearcher`, mientras que `train-tfidf` y `predict-tfidf` se miden por separado.

**API de desarrollo opcional:** instalar `requirements-api.txt` y ejecutar `python -m uvicorn keycontacts.api.app:app --reload`; no abrirla a usuarios o redes corporativas sin controles de acceso aprobados.

## 10. Plan incremental y criterios de avance

| Etapa | Entregable | Condición mínima antes de avanzar |
|---|---|---|
| **0 · Datos y permisos** | Inventario de fuentes, diccionario y responsables de datos | Autorización de uso y significado validado de columnas |
| **1 · Base actual** | Ingesta + M01 + pruebas | Funciona localmente; las limitaciones están documentadas |
| **2 · Recuperadores locales** | M02 BM25 y M03 embeddings como módulos independientes | Contratos de IDs compatibles y benchmark sin fuga |
| **3 · Ensamble** | M04 RRF + pruebas de ablación | Mejora cuantificada o decisión explícita de descartarlo |
| **4 · Supervisados** | M05/M06; M07/M08/STK solo si proceden | Etiquetas humanas suficientes, baselines y evaluación temporal |
| **5 · Control Intelligence** | Reglas/evidencias y revisión humana | Definiciones de control y permisos aprobados |
| **6 · Benchmark GenAI** | Alternativa generativa controlada y comparación multiobjetivo | Mismo conjunto de casos, evaluación de calidad, recursos y costos |
| **7 · Piloto** | Orquestación, elegibilidad, monitoreo y auditoría | RACI, RBAC, seguridad y criterios de aceptación validados |

### Definición de terminado para cada modelo nuevo

Cada implementación debe aportar **(a)** contrato de input/output y manejo de errores; **(b)** código aislado; **(c)** pruebas unitarias y de integración; **(d)** ejemplo reproducible; **(e)** métricas por modelo y de extremo a extremo; **(f)** limitaciones y requisitos de datos; **(g)** decisión de adopción basada en comparación.

## 11. Riesgos y decisiones abiertas

| Tema | Regla de trabajo |
|---|---|
| Calidad de correos/asignaciones | No suponer RACI ni propietario de una solicitud a partir de una columna de contacto |
| Datos sensibles | Acceso mínimo, aprobación corporativa, no publicar archivos/embeddings sin evaluación de seguridad |
| Clasificación equivocada | Mantener recuperación amplia o abstenerse; una clase incierta no debe ocultar responsables correctos |
| Cambios de personal | Actualizar el catálogo/índice; **no** reentrenar el clasificador por cada cambio de correo |
| Métricas sin etiquetas | Reportar **«no evaluado»**, nunca fabricar precisión/recall |
| Generación | LLM solo para tareas justificadas; salida con referencias y verificación, sin inventar evidencia |
| Herramientas | Cursor y VS Code son editores; el proyecto se ejecuta con Python en WSL |

---

**Fuente de alcance:** documento *Proyecto 04 — Key Contacts AI & Control Intelligence, Arquitectura sostenible V1.0* (propuesta de diseño, no aprobación corporativa). **Fuente del estado de implementación:** archivos reales del MVP local con M01 inspeccionados para esta actualización. Las tablas de modelos M02–M08, STK y GenAI son **planes técnicos**, no resultados experimentales.
