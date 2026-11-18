# Key Contacts AI & Control Intelligence

**Documento maestro del proyecto · Arquitectura, datos, modelos, evaluación e implementación**  
**Versión documental:** 2.0 · **Fecha:** 17 de noviembre de 2026  
**Entorno local confirmado:** WSL/Ubuntu, Python 3.12.3, VS Code o Cursor  
**Estado:** MVP local de Key Contacts con TF-IDF; arquitectura multimodelo y Control Intelligence pendientes de desarrollo.

> **Cómo leer este documento.** **IMPLEMENTADO** significa que hay código en el MVP M01 revisado. **DISEÑADO** significa arquitectura acordada pero aún no codificada. **CONDICIONADO** significa que requiere etiquetas, permisos, datos o experimentos. **PROPUESTO** significa un criterio sujeto a aprobación. No se atribuye ningún resultado de precisión, F1, Recall@3 ni ahorro de recursos a modelos que todavía no se hayan evaluado con datos válidos.

## 1. El proyecto en una página

### 1.1 ¿Qué problema resolvemos?

La compañía tiene datos de proyectos, equipos, contactos y controles repartidos entre archivos y otras fuentes. Cuando alguien necesita ayuda, puede desconocer a la persona responsable. En paralelo, la verificación de evidencias de controles puede demandar comprobaciones manuales y detectar faltantes tarde.

**Motor A · Key Contacts AI.** Recibe una solicitud en español o inglés y **propone hasta tres contactos elegibles**, cada uno con motivo, procedencia y vigencia, o responde que no existe una recomendación confiable. No asigna automáticamente casos. **Hoy, el MVP solo recupera correos asociados con textos similares; todavía no verifica responsabilidad.**

**Motor B · Control Intelligence.** Revisa datos de controles y evidencia autorizada mediante reglas, indica faltantes, incompletitud o retrasos y prepara información para revisión. **Nunca declara incumplimiento, aprueba ni firma por sí mismo.** Todavía no está implementado.

**Ejemplo de solicitud:** «Necesito ayuda con impuestos de un cliente en Colombia». Resultado **objetivo**: área/categoría estimada opcionalmente → contactos candidatos → comprobación de permisos, estado y RACI → Top 3 explicado o abstención. Una coincidencia léxica por sí sola no demuestra que un correo sea el responsable.

### 1.2 Principio de ingeniería y decisión experimental

Construir primero alternativas **locales de reglas, ML y DL preentrenado**, compararlas individualmente y combinadas, y **solo después** estudiar LLM/RAG autorizado. Seleccionar por **(1) seguridad y validez funcional, (2) calidad predictiva, (3) consumo/latencia/costo y (4) mantenibilidad**. Más modelos no significa automáticamente mejor solución.

### 1.3 Glosario mínimo

| Término | Significado en este proyecto |
|---|---|
| **Solicitud** | Texto del problema de un usuario y contexto autorizado. |
| **Catálogo / corpus** | Registros empresariales autorizados sobre los que buscamos. |
| **Ground truth (verdad de referencia)** | Contacto(s), categoría o estado correcto **confirmado por revisión humana** para evaluar sin adivinar. |
| **Baseline** | Método sencillo de comparación que una alternativa más compleja debe justificar superar. |
| **TF-IDF / BM25** | Recuperación de información por términos; no predicen responsables oficiales por sí solos. |
| **Embedding** | Vector numérico que representa un texto; se genera con un encoder, potencialmente basado en DL. **No es un ensemble**. |
| **Ensemble / RRF** | Varios métodos producen resultados y RRF combina sus posiciones. |
| **Stacking** | Un metamodelo supervisado aprende a combinar predicciones de modelos base. |
| **Pipeline** | Etapas conectadas: el output estructurado de una alimenta al siguiente módulo. |
| **RACI** | Matriz aprobada de responsabilidades; fuente de elegibilidad, no sustituto de predicción. |
| **Abstención** | El sistema no recomienda cuando carece de evidencia, permisos o confianza suficiente. |

## 2. Datos: para qué sirven Excel y CSV

### 2.1 Uso y límites de las fuentes

Los Excel/CSV que entregue el equipo son **entradas del pipeline**, no necesariamente datasets etiquetados para aprendizaje supervisado. Se conservará una copia original y se registrarán origen, versión, momento y problemas de calidad.

| Fuente | Datos relevantes | Uso posible | Condición crítica |
|---|---|---|---|
| `informacion finanzas.xlsx` (muestra recibida) | `Project Description`, `Customer Team`, `Market`, `Market Unit`, `System`, `FPC Email`, `Substitute Email`, `LM Email`, identificadores | Construir un catálogo de contexto y contactos asociados para búsqueda local | Los correos **no equivalen** a responsables correctos de cualquier solicitud. Validar semántica de columnas. |
| `e2e-customer-2026-10-21-04-38-28-760.xlsx` (muestra recibida) | Archivo de clientes; revisar hojas/campos antes de integrarlo | Fuente complementaria potencial | No se ha incorporado al entrenamiento de M01; no inferir relaciones sin mapeo validado. |
| Directorio/HR y matriz RACI | Personas activas, funciones, roles, vigencia, aprobaciones | Elegibilidad, vigencia y explicación oficial | **No integrados al MVP; requieren autorización.** |
| Historial validado de solicitudes | Texto de solicitud, fecha, categoría, contacto(s) realmente correctos y correcciones | Ground truth y entrenamiento supervisado | **No confirmado en las muestras actuales.** |
| Controles y evidencias | Definición, periodo, plazos, referencias, decisiones de revisores | Motor B | **Pendientes de aprobación/acceso.** |

### 2.2 Procesamiento de los archivos y punto de control

```text
Archivo CSV/XLSX autorizado
  -> 01 Lectura e identificación de fuente
  -> 02 Perfilado: columnas, tipos, nulos, duplicados, inconsistencias
  -> 03 Validación de esquema y formatos
  -> 04 Normalización conservadora (sin inventar valores)
  -> 05 Revisión de incidencias y asociación entre fuentes
  -> 06 Validación por dueño de datos / Quality Gate [DISEÑADO]
  -> 07 Datos curados y versionados [DISEÑADO]
     +-> índices de recuperación de Key Contacts
     +-> ejemplos etiquetados para ML/DL (solo si existen)
     +-> reglas/evidencias de Control Intelligence
```

**Estado real:** `cleaning/pipeline.py` limpia espacios, normaliza vacíos y correos, reporta nulos/duplicados y exporta `data/processed/finance_normalized.csv`, `finance_review.csv` y `quality_report.json`. **No hay puerta de calidad productiva**: los registros enviados a revisión permanecen también en el CSV normalizado. No descartar, imputar, fusionar ni marcar como vigente un contacto sin reglas aprobadas.

### 2.3 Dos productos de datos diferentes

| Producto | Requisitos de entrada | Destino |
|---|---|---|
| **Índice de búsqueda** | Texto descriptivo + identificador estable de registro + contactos asociados y fuente | M01, M02 y M03 |
| **Dataset etiquetado** | `request_id`, consulta, fecha, segmento, categoría validada, contacto(s) elegible(s) correcto(s), juicio de relevancia y revisor | Evaluación de recuperadores; entrenamiento/evaluación de clasificadores y rankers |

Un índice se puede construir **sin** etiquetas; las métricas de calidad predictiva **no** se pueden calcular con rigor sin ground truth. Si hay múltiples responsables aceptables, deben aparecer todos en la verdad de referencia.

### 2.4 Contratos objetivo entre componentes — DISEÑADOS

| Objeto | Campos mínimos propuestos | Restricción |
|---|---|---|
| `Request` | `request_id`, `query`, `language`, `region`, `requested_at`, `user_context` | Contenido y acceso autorizados. |
| `RetrievedCandidate` | `candidate_id`, `source_record_id`, `source`, `retriever_id`, `rank`, `score` | Score = relevancia, **no** probabilidad de ser responsable. |
| `EligibilityResult` | `candidate_id`, `eligible`, `reason_codes`, `raci_version`, `valid_at` | Permisos y vigencia verificados con fuentes maestras. |
| `Recommendation` | `status`, `contacts` (hasta 3), `reasons`, `sources`, `versions` | `status` permite abstención; no hay asignación automática. |
| `FeedbackEvent` | `request_id`, decisión, corrección, aprobador, fecha | Correcciones revisadas antes de entrenar. |

**Nota de contrato:** los identificadores de fila/correo actuales son provisionales. Antes de RRF, deduplicación entre fuentes o LightGBM, se necesita un **ID de candidato canónico**; si dos recuperadores devuelven entidades distintas con el mismo texto, no se deben fusionar ciegamente.

## 3. Arquitectura general y ensamblaje

### 3.1 Flujo objetivo del Motor A — DISEÑADO

```text
                         SOLICITUD + CONTEXTO
                                  |
                     Autorización antes de acceder
                                  |
                   Normalización de consulta (ES/EN)
                                  |
                    Clasificador [OPCIONAL, M05/06/08]
                                  |
              +-------------------+-------------------+
              |                                       |
         M02 BM25                                M03 Embeddings
              |                                       |
              +------------ rankings por ID ----------+
                                  |
                           M04 RRF [ENSEMBLE]
                                  |
                     Candidatos y procedencia
                                  |
                Reglas obligatorias: acceso, RACI,
                     estado, vigencia y región
                                  |
          Ranking transparente / M07 LightGBM [OPCIONAL]
                                  |
                   Validación final, Top 3 o abstención
                                  |
                       Decisión humana + auditoría
```

**Cómo se relacionan:** M02 y M03 funcionan en **paralelo**, no uno dentro del otro; M04 fusiona sus rankings. La categoría de un clasificador puede añadir contexto, pero **no excluir irrevocablemente** candidatos por una predicción incierta. Las reglas verificables no son modelos estadísticos y prevalecen sobre sus scores. M07 solo ordenará **candidatos elegibles**. STK es una alternativa experimental supervisada, **no** un paso obligatorio después de RRF.

**Hoy:** `M01 TF-IDF` ejecuta una búsqueda independiente y devuelve **contactos asociados a registros**, sin esa cadena completa. No atribuir al MVP las protecciones RACI/RBAC del diseño futuro.

### 3.2 Flujo objetivo del Motor B — DISEÑADO

```text
Controles + periodo + evidencias autorizadas
  -> extracción verificable (lectura/regex; NLP opcional)
  -> reglas versionadas (existencia/plazo/completitud)
  -> alertas y referencias
  -> anomalías estadísticas/ML [opcionales; no implican incumplimiento]
  -> búsqueda de dueño/revisor por RACI [integración con Motor A]
  -> revisión y decisión humana (nunca firma automática)
```

### 3.3 Patrones que NO debemos confundir

| Patrón | Entrada | Combinación | Salida | Cuándo usarlo |
|---|---|---|---|---|
| **Recuperación individual** | Consulta + índice | Ninguna | Ranking de M01, M02 o M03 | Establecer baselines comparables. |
| **Ensamble paralelo RRF** | Rankings de M02 y M03 con mismos IDs | Fusión por posiciones | Ranking M04 | Solo si aporta mejora medible. |
| **Encadenamiento secuencial** | Output estructurado de una etapa | Clasificador opcional → recuperación → reglas → ranking | Recomendación final | Cuando existen contratos y fuentes verificadas. |
| **Stacking** | Predicciones *out-of-fold* + etiquetas | Metamodelo aprendido | Score/ranking combinado | Solo con datos suficientes y evaluación sin fuga. |
| **Alternativa GenAI** | Consulta + contexto autorizado | LLM/RAG, generación controlada | Respuesta verificable | Benchmark posterior contra la misma tarea. |

## 4. Catálogo de modelos: función, input y output

**Convención:** M01–M08 y STK son identificadores documentales del Motor A; las reglas del Motor B no deben confundirse con predictores aprendidos.

| Modelo | ¿Para qué sirve? | Input | Qué procesa / aprende | Output | Estado |
|---|---|---|---|---|---|
| **M01 TF-IDF + coseno** | Baseline de búsqueda léxica de contactos asociados. | Corpus descriptivo + consulta. | Aprende vocabulario/pesos TF-IDF; calcula similitud. | Hasta 3 correos asociados, score y campo de procedencia. | **IMPLEMENTADO** |
| **M02 BM25** | Comparar relevancia léxica con M01. | Misma consulta y catálogo. | Ponderación de términos y frecuencia de documento. | Ranking de candidatos con score BM25. | **DISEÑADO** |
| **M03 Embeddings multilingües** | Recuperar expresiones semánticamente parecidas en ES/EN. | Consulta + textos autorizados. | Encoder local preentrenado → vectores → similitud. | Ranking semántico y score vectorial. | **DISEÑADO** |
| **M04 RRF** | Evaluar ganancia de fusionar recuperadores. | Rankings M02 + M03 por ID canónico. | Fusiona posiciones; **no requiere entrenar**. | Ranking combinado + procedencias. | **DISEÑADO** |
| **M05 Logistic Regression** | Clasificar área/categoría de solicitud. | Texto + etiquetas verificadas. | Clasificador supervisado con vectorización textual. | Categoría y puntuaciones/probabilidades del modelo. | **CONDICIONADO** |
| **M06 Linear SVM** | Alternativa de clasificación a M05. | Mismo dataset etiquetado de M05. | Margen de decisión supervisado. | Categoría + margen (**no** probabilidad sin calibración). | **CONDICIONADO** |
| **M07 LightGBM Ranker** | Ordenar candidatos elegibles por relevancia. | Grupos solicitud-candidatos, atributos y grados de relevancia. | Aprende orden dentro de cada solicitud. | Ranking de contactos elegibles. | **CONDICIONADO** |
| **M08 Transformer ajustado** | Comparar DL supervisado en tarea definida. | Solicitudes + etiquetas de categoría **o** relevancia. | Fine-tuning de encoder bajo protocolo de evaluación. | Categoría o score de relevancia, según experimento. | **CONDICIONADO** |
| **STK Stacking** | Probar combinación aprendida. | Predicciones fuera de muestra y etiquetas. | Entrena metamodelo sin usar predicciones in-sample como etiquetas. | Score combinado. | **CONDICIONADO** |

**Relación importante:** M05/M06/M08 son **alternativas** de clasificación, no tres etapas encadenadas; M07 solo es útil con ejemplos de relevancia evaluados por humanos. Los scores de BM25 y coseno no se promedian directamente; RRF opera sobre posiciones. Cambiar un correo en un catálogo **no exige reentrenar** un clasificador: exige revisar y actualizar datos/índices.

### 4.1 Modelos y reglas del Motor B

| Técnica | Propósito | Input | Output | Requisito y estado |
|---|---|---|---|---|
| Reglas determinísticas | Señalar evidencia ausente, tardía o incompleta. | Control, periodo, evidencia, plazos. | Estado/alerta + regla y versión. | Definiciones aprobadas. **DISEÑADO** |
| Extracción estructurada/regex | Leer campos rastreables. | Excel/documentos permitidos. | Campos, ubicación y fuente. | Plantillas conocidas. **DISEÑADO** |
| NER/Transformer opcional | Extraer campos de formatos variables. | Documentos y ejemplos anotados. | Campo, confianza y referencia. | Anotaciones y validación. **CONDICIONADO** |
| Isolation Forest / LOF | Sugerir revisión de comportamientos atípicos. | Ciclos históricos comparables. | Score/anomalía para revisión. | Histórico y revisión humana. **CONDICIONADO** |

## 5. Cómo mediremos la **calidad predictiva**: protocolo común

### 5.1 Primero: definir la respuesta correcta

**Motor A, recuperación:** para cada `request_id`, registrar consulta, fecha histórica, región/idioma, **conjunto de contactos correctos y elegibles en esa fecha** y, cuando aplique, grados de relevancia (p. ej., 3 responsable principal; 2 alternativa válida; 0 incorrecto). Validación por expertos y registro de desacuerdos. No derivar el ground truth automáticamente de `FPC Email` o del ranking que produjo el mismo modelo.

**Motor A, clasificación:** cada solicitud tiene área/categoría humana revisada. Las categorías poco frecuentes también deben estar representadas y evaluadas.

**Motor B:** cada control × periodo × ejecución tiene estado y evidencia revisados, reglas aplicables y etiqueta humana (faltante, tardía, completa, caso dudoso). Una alerta estadística es una **hipótesis**, no una aprobación ni un fallo confirmado.

**Sin ground truth:** podemos medir cobertura, estabilidad, latencia y RAM, **pero no afirmar Accuracy/F1/Recall@3 validados**.

### 5.2 Particiones y prevención de sesgos

1. Definir un **benchmark congelado** con casos, etiquetas, versiones de fuentes y reglas, antes de comparar.
2. Si hay histórico, dividir temporalmente **train → validation → test**; la fecha de referencia del caso determina qué contactos y RACI eran válidos. Si no existe histórico, documentar otra partición evitando que el mismo caso/proyecto duplicado se filtre entre conjuntos.
3. Ajustar hiperparámetros, umbrales y selección de arquitectura solo con train/validation. **Test se reserva para evaluación final**; si se itera sobre test, registrar nuevo test independiente.
4. Los clasificadores supervisados requieren que vectorizadores, selección de características y calibración se ajusten **solo con train**.
5. Para stacking, las predicciones que entrenan el metamodelo deben ser **out-of-fold** dentro de train; no usar el modelo base entrenado sobre el mismo ejemplo.
6. Comparar usando los mismos casos, permisos, corpus temporalmente válido, hardware y protocolo; reportar incertidumbre por remuestreo o intervalos si la muestra lo permite.
7. Desglosar errores por idioma (ES/EN), región, categoría, clase minoritaria y casos sin respuesta. Registrar abstenciones y falsos positivos.

### 5.3 Definiciones de métricas (sin mezclarlas)

| Métrica | Cálculo / interpretación | Utilidad y advertencia |
|---|---|---|
| **Accuracy** | Predicciones de clase correctas / total de ejemplos. | Clasificación; puede ocultar fallos en clases minoritarias. |
| **Precision (por clase)** | `TP / (TP + FP)` para cada clase. | Evitar asignar categorías/alertas incorrectas; indicar cómo se resuelve denominador cero. |
| **Recall (por clase)** | `TP / (TP + FN)` para cada clase. | Evitar omitir clases/alertas relevantes. |
| **F1 por clase** | `2 × Precision × Recall / (Precision + Recall)` cuando esté definido. | Equilibrio entre precision y recall. |
| **Macro-F1** | Promedio no ponderado del F1 de cada clase. | Métrica principal de clasificación cuando hay desbalance; acompañar con resultados por clase. |
| **Matriz de confusión** | Conteo de clases reales vs predichas. | Permite analizar errores críticos (p. ej., Taxes clasificado como otro tema). |
| **Hit@3 (tasa de acierto)** | Fracción de solicitudes con **al menos un** contacto correcto en el Top 3. | Con varios contactos válidos **no equivale** a Recall@3 general. |
| **Recall@3 (general)** | Promedio por solicitud de `|Top3 ∩ relevantes| / |relevantes|` para casos con relevantes conocidos. | Cobertura de todos los contactos relevantes; definir exclusión o política de consultas sin relevantes. |
| **Precision@3** | Promedio de `# relevantes en Top 3 / 3` (convención de tres posiciones). | Penaliza candidatos irrelevantes; explicitar cómo se tratan rankings incompletos. |
| **MRR@3** | Promedio de `1/rango` del **primer** contacto correcto entre posiciones 1–3; 0 si no aparece. | Premia que el primer resultado correcto esté arriba. |
| **NDCG@3** | `DCG@3 / IDCG@3` usando niveles de relevancia verificados. | Evalúa calidad del orden con varios grados; requiere esquema de relevancia definido. |
| **Tasa de abstención** | Solicitudes sin recomendación / total. | Debe evaluarse junto con aciertos/errores; abstenerse de todo no es éxito. |
| **Tasa de recomendación no elegible** | Recomendaciones que incumplen RACI/permisos/vigencia / recomendaciones verificadas. | **Restricción crítica**: un ranking alto no compensa la violación. |
| **Precision/recall de alertas** | Comparar alertas positivas/negativas con revisión humana. | Motor B; reportar falsos positivos por periodo y esfuerzo de revisión. |

**Precisión sobre el código actual:** la función existente `ml/evaluation.py::recall_at_k` comprueba si **algún** contacto verdadero aparece en las predicciones y promedia por solicitud: implementa conceptualmente **Hit@k**, aunque se llame `recall_at_k`. Su función `reciprocal_rank` calcula el promedio del recíproco de la primera posición relevante (MRR si se limita a k). **No declararemos Recall@3 general implementado** hasta corregir nombre/definición y añadir pruebas. Esto evita confundir métricas en publicaciones.

### 5.4 Matriz de evaluación **por modelo**: calidad + criterios de promoción

Los criterios siguientes son **propuestas metodológicas**, **no umbrales porcentuales ya acordados**. Para cada componente se fijarán mínimos numéricos con negocio sobre un conjunto de validación antes de consultar test final.

| Componente | Ground truth necesario | Métrica primaria | Métricas diagnósticas | Criterio para adoptarlo o conservarlo |
|---|---|---|---|---|
| **M01 TF-IDF** | Contactos válidos por consulta/fecha. | Hit@3 y Recall@3 general (definir ambos). | MRR@3, Precision@3, cortes ES/EN/región. | Línea base reproducible; no declarar calidad sin etiquetas. |
| **M02 BM25** | Exactamente los mismos casos que M01. | Recall@3 general o Hit@3 según objetivo acordado. | MRR@3, Precision@3 y errores por segmento. | Comparar con M01; adoptar si mejora calidad o iguala con ahorro significativo, sin comprometer restricciones. |
| **M03 Embeddings** | Mismos casos + relevancia validada. | Recall@3 general o Hit@3. | MRR@3, cobertura de paráfrasis, ES/EN. | Demostrar valor semántico adicional o justificar costo; revisar licencia y latencia local. |
| **M04 RRF** | Mismos casos y IDs canónicos, grados de relevancia si hay. | Recall@3; **NDCG@3** con etiquetas graduadas. | MRR@3, Hit@3 y ablaciones. | Comparar con **el mejor M02 o M03**, no solo con el peor; la ganancia debe justificar ambos recuperadores. |
| **M05 Logistic Regression** | Solicitudes con categorías confirmadas. | **Macro-F1**. | Accuracy, precision/recall por clase, confusión. | Superar regla o clase mayoritaria, sin perder recall crítico; evaluar estabilidad por área. |
| **M06 Linear SVM** | **Mismo split** que M05. | **Macro-F1**. | Confusión, recall por clase, diferencias pareadas. | Superar o igualar M05 con ventajas demostrables de costo/latencia; no interpretar margen como probabilidad. |
| **M07 LightGBM Ranker** | Relevancia por contacto dentro de cada solicitud; solo elegibles. | **NDCG@3**. | MRR@3, Recall@3, tasa de primera opción correcta. | Superar ranking transparente; no degradar elegibilidad ni costo extremo a extremo. |
| **M08 Transformer** | Categorías **o** relevancia etiquetadas según tarea. | **Macro-F1 si clasifica; NDCG@3 si rankea.** | Recall por clase o MRR, errores críticos. | Comparar solo con modelos que resuelven **la misma tarea**; justificar consumo adicional. |
| **STK Stacking** | Etiquetas + predicciones OOF de modelos base. | La métrica de su tarea (Macro-F1/NDCG@3). | Calibración si corresponde, ablación, estabilidad. | Superar mejor modelo base sobre test independiente sin fuga/overfitting. |
| **B Reglas / extracción** | Casos y campos verificados con fuentes. | Cobertura de reglas y exactitud por campo. | Falsos positivos, falsos negativos, trazabilidad. | Alertas reproducibles con regla+evidencia; revisión humana obligatoria. |
| **B Anomalías** | Alertas confirmadas/descartadas por revisores. | Precision de alertas útiles (si hay etiquetas). | Recall, falsos positivos por ciclo, carga de revisión. | Mejorar selección de revisiones frente a umbrales simples; nunca declarar incumplimiento automático. |
| **GenAI / RAG** | **Mismas solicitudes y verdad de referencia** de la tarea comparable. | Métrica de tarea + fidelidad factual/evidencia. | Alucinaciones, abstención, variabilidad por repeticiones. | Cumplir seguridad y superar ventaja costo/calidad justificable frente al pipeline local. |

### 5.5 Qué significa un modelo aceptado

**No existe un porcentaje universal de Accuracy/F1/Recall válido para todos.** La aceptación se decide **antes del test final** con umbrales fijados por responsables funcionales y de seguridad. Debe cumplir simultáneamente: (a) no recomendar contactos sin permisos/RACI vigente; (b) alcanzar el mínimo de calidad definido para la tarea y segmentos críticos; (c) demostrar comparación reproducible con baseline; (d) tener costo/latencia/memoria dentro de presupuesto; (e) conservar trazabilidad, pruebas y opción de abstención. Si falta ground truth, el estado correcto es **«no evaluado predictivamente»**, aunque el modelo ejecute sin errores.

## 6. Cómo mediremos **performance de ejecución y recursos**

**No confundir:** *calidad predictiva* = acierto de resultados frente a la verdad; *performance operativa* = tiempo, consumo y costo de producirlos. Ambas se miden por separado y luego se toman decisiones conjuntas.

| Indicador | Definición / forma de medir | Alcance |
|---|---|---|
| **Latencia media, p50, p95** | Varias consultas repetidas; percentil 95 de tiempos de respuesta. | Por modelo y pipeline completo, señalando arranque en frío/caliente. |
| **Throughput** | Solicitudes por segundo a concurrencia declarada. | Servicio/pipeline, no solo llamada aislada. |
| **CPU** | Tiempo CPU y/o utilización, muestreo durante ejecución. | Indexación, entrenamiento, inferencia. |
| **RAM residente máxima (RSS)** | Pico de memoria real del proceso y subprocesos. | Diferente del heap instrumentado de Python. |
| **GPU/VRAM** | Utilización y pico de memoria de GPU local cuando aplique. | Encoders DL/LLM local. |
| **Disco** | Tamaño de modelos, índices, cachés y artefactos. | Mantenimiento y despliegue. |
| **Tiempo de preparación** | Lectura, limpieza, construcción de índices y entrenamiento separados. | No esconder preprocesamiento bajo «inferencia gratis». |
| **Energía (opcional)** | Wh estimados/medidos por operación y metodología. | Solo si el equipo puede medir con rigor. |
| **Costo por 1.000 consultas** | Infraestructura amortizada + operación; API según tarifas realmente registradas. | Comparación local vs GenAI. |
| **Tokens** | Tokens de entrada/salida, cuando se use LLM. | No aplicar a TF-IDF/BM25. |

**Estado actual:** `ml/evaluation.py::timed_call` mide tiempo de una llamada y pico de asignaciones rastreables de memoria Python; **no mide RSS total, CPU, GPU, energía ni p95**. El artefacto M01 registra tamaño del archivo guardado. Para un benchmark válido añadiremos instrumentación separada, repetición de pruebas, hardware/versiones fijados, caché y carga declarados; no mezclar tiempo de creación de índice con tiempo de inferencia sin explicarlo.

## 7. Plan de experimentos y evaluación del sistema ensamblado

| Experimento | Configuración | Qué pregunta responde | Condición de comparación |
|---|---|---|---|
| **E01** | M01 TF-IDF | ¿Cuál es la calidad/costo de la línea base? | Dataset etiquetado congelado. |
| **E02** | M02 BM25 | ¿Mejora la recuperación léxica? | Mismos casos y catálogo. |
| **E03** | M03 embeddings | ¿Aporta comprensión semántica? | Misma verdad y restricciones. |
| **E04** | M02 + M03 + M04 RRF | ¿Mejora el ensemble al mejor componente? | IDs canónicos y ablación. |
| **E05** | Clasificador + recuperador | ¿Clasificar primero suma o causa pérdida de recall? | Comparar con/sin clasificador; fallback. |
| **E06** | Recuperación + reglas + M07 | ¿Mejora el orden sin romper elegibilidad? | Mismo conjunto elegible y etiquetas graduadas. |
| **E07** | Pipeline local completo | ¿Cuál es calidad y consumo **end-to-end**? | Incluir filtros, normalización e índices. |
| **E08** | LLM/RAG autorizado | ¿Mejora la tarea frente al local? | Mismo benchmark y contexto permitido. |
| **E09** | Sistema híbrido seleccionado | ¿Aporta la política de enrutamiento? | Calidad, tasa de invocación LLM, latencia y costo total. |

**Prueba de ablación:** retirar un módulo (por ejemplo M03, M04 o clasificador) y observar la diferencia en calidad y recursos. **Propagación de errores:** verificar cuánto cae Recall@3 cuando el clasificador asigna un área incorrecta; cuánto sube la abstención con filtros; cuántos candidatos correctos se pierden por deduplicación/IDs. **No** comparar un modelo individual contra el pipeline final como si resolvieran idéntica tarea sin explicitar reglas adicionales.

### Reporte de benchmark: plantilla sin valores inventados

| Run | Modelo/pipeline | Split/versiones | Métrica de calidad primaria | Segmentos críticos | p95 ms | RAM MB | Costo/1.000 | Decisión |
|---|---|---|---|---|---|---|---|---|
| `pendiente` | `M01` | `pendiente` | `No evaluado` | `No evaluado` | `No medido` | `No medido` | `No estimado` | Baseline técnico, no validado predictivamente |

**Criterio de selección:** primero rechazar configuraciones inseguras, inválidas o inferiores al mínimo de calidad; después comparar la **frontera de Pareto** entre calidad, latencia, memoria y costo. Una pequeña mejora de puntuación no justifica automáticamente duplicar infraestructura. Registrar hipótesis, cambios, errores y motivo de cada decisión.

## 8. Estado del MVP e implementación por archivos

| Función | Estado verificable | Archivo |
|---|---|---|
| Lectura CSV/Excel | **IMPLEMENTADO** | `src/keycontacts/ingestion/readers.py` |
| Normalización/CSV para revisión | **IMPLEMENTADO BÁSICO** | `cleaning/pipeline.py`, `validation/schema.py` |
| TF-IDF en memoria | **IMPLEMENTADO** | `search/baseline.py` |
| M01 TF-IDF persistente | **IMPLEMENTADO** | `search/tfidf_model.py` |
| CLI local de ingesta/entrenamiento/consulta | **IMPLEMENTADO** | `cli.py` |
| Tiempo/pico de memoria Python por llamada | **IMPLEMENTADO** | `ml/evaluation.py` |
| Función llamada `recall_at_k` (semántica Hit@k) y MRR | **CÓDIGO DISPONIBLE, SIN BENCHMARK ETIQUETADO** | `ml/evaluation.py` |
| Métricas Accuracy/Macro-F1/Precision@3/NDCG@3 | **PENDIENTE** | Futuro paquete `evaluation/` |
| BM25/embeddings/RRF/clasificación/rankers | **DISEÑADO O CONDICIONADO** | Módulos futuros |
| RACI/RBAC, motor B, LLM | **PENDIENTE** | Componentes futuros |

### 8.1 Estructura del repositorio real (M01)

```text
key_contacts_ai/
├── data/
│   ├── raw/                 # Archivos de entrada locales
│   ├── processed/           # Salidas de normalización
│   └── rejected/            # Reservado; no cuarentena real
├── models/                  # Artefactos guardados por entrenamiento
├── reports/                 # Reservado para métricas/resultados
├── scripts/generate_demo.py
├── src/keycontacts/
│   ├── ingestion/readers.py
│   ├── validation/schema.py
│   ├── cleaning/pipeline.py
│   ├── search/baseline.py
│   ├── search/tfidf_model.py
│   ├── ml/evaluation.py
│   ├── api/app.py
│   └── cli.py
├── tests/test_core.py
├── tests/test_tfidf_model.py
├── requirements.txt
├── requirements-api.txt
├── requirements-dl.txt
├── pyproject.toml
└── README.md
```

**Módulos DISEÑADOS para evolución (todavía no existen):** `search/bm25_model.py`, `search/embeddings_model.py`, `search/rrf_fusion.py`, `classification/`, `ranking/`, `contracts/`, `orchestration/`, `control_intelligence/`, `evaluation/`. Se crearán solo al implementar; cada nuevo `.py` tendrá contrato y pruebas, preservando compatibilidad con el código inicial.

### 8.2 Ejecutar localmente en WSL

Desde la raíz `key_contacts_ai`:

```bash
python3 --version                   # WSL confirmado: 3.12.3
source .venv/bin/activate           # entorno ya creado por el equipo
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q

# Demo sintética (no es evaluación de precisión)
python scripts/generate_demo.py
python -m keycontacts.cli ingest data/raw/demo_finance.csv
python -m keycontacts.cli train-tfidf
python -m keycontacts.cli predict-tfidf "impuestos colombia" --top 3
```

Un archivo autorizado puede procesarse con `python -m keycontacts.cli ingest "data/raw/informacion finanzas.xlsx"`, tras colocarlo localmente en `data/raw/`. La salida por defecto se llama `finance_normalized.csv`; antes de entrenar, verificar fuente, columnas y calidad. La API opcional es para desarrollo, no producción sin controles de acceso.

**Seguridad de artefactos:** archivos `.joblib` deben cargarse solamente desde fuentes confiables (deserialización basada en pickle). No cargar datos/embeddings sensibles en servicios externos ni registrar información personal en logs sin autorización.

## 9. Guía de trabajo, calidad de código y gobernanza

### 9.1 Antes de integrar cualquier nuevo modelo

1. Especificar **tarea, ID de modelo, input, output y excepción**; no usar nombres genéricos como «IA inteligente».
2. Identificar **ground truth**, distribución de clases, escala y cantidad de ejemplos; si faltan, documentar el bloqueo.
3. Elegir **métrica primaria y diagnósticas** para esa tarea; definir objetivos/umbrales **antes** del test final.
4. Implementar código modular con pruebas unitarias, de integración y regresión; no alterar los contratos existentes sin versión.
5. Medir calidad sobre casos independientes, luego recursos en condiciones reproducibles.
6. Comparar con el baseline correspondiente (misma tarea/dataset); hacer ablaciones si se integra en pipeline.
7. Documentar resultados reales o «no evaluado», riesgos, consumo, versiones y decisión de adopción.

### 9.2 Criterio de terminado (Definition of Done)

Un módulo se considera **entregado técnicamente** si tiene código revisable, ejemplo reproducible, manejo de errores, contrato, pruebas, versionado y guía de ejecución. Un modelo se considera **validado predictivamente** solo si hay etiquetas fiables, evaluación fuera de muestra y criterios de aceptación aprobados. **Entregado ≠ validado ≠ autorizado para producción.**

### 9.3 Responsables y restricciones

| Actor | Decisión o revisión requerida |
|---|---|
| Líderes de negocio / Data Owners | Significado de datos, verdad de referencia, objetivos y errores críticos. |
| Data/ML Lead | Particiones, métricas, experimentación, sesgos, modelos y selección. |
| Control Interno | Reglas, evidencia, alcance de alertas y revisión humana del Motor B. |
| Software/Plataforma | API, integración, calidad, rendimiento, despliegues y rollback. |
| Seguridad/TI | Permisos, privacidad, aprobación de modelos, fuentes y LLM. |

**Restricciones no negociables:** mínimo privilegio; no inventar responsables, estados ni evidencias; no aprobación automática de controles; no entrenamiento con datos no autorizados; cambios de modelo verificables y reversibles; no utilizar outputs no verificados como etiquetas automáticamente.

## 10. Hoja de ruta y decisiones abiertas

| Orden | Trabajo | Evidencia que debe quedar |
|---|---|---|
| **P0** | Aprobar fuentes y semántica; definir IDs/RACI y ground truth de consultas | Diccionario, permisos, muestra auditada, dataset etiquetado si existe. |
| **P1** | Corregir definición Hit@k/Recall@k y construir evaluación reproducible de M01 | Pruebas de métricas, benchmark inicial, reporte sin datos inventados. |
| **P2** | Implementar M02 BM25 y M03 embeddings por separado | Mismos contratos, casos y métricas de calidad/recursos. |
| **P3** | Ensayar M04 RRF y ablaciones | Comparación contra mejor recuperador individual. |
| **P4** | Evaluar M05/M06; condicionar M07/M08/STK a etiquetas suficientes | Macro-F1/errores por clase o NDCG@3, decisiones reproducibles. |
| **P5** | Implementar reglas y flujo de revisión del Motor B | Casos etiquetados, cobertura, evidencia y trazabilidad. |
| **P6** | Comparar LLM/RAG autorizado con el pipeline local | Calidad por tarea + tokens/costo/latencia/recursos. |
| **P7** | Integrar seguridad, RACI, observabilidad y piloto | Evidencia de aceptación funcional, privacidad e impacto. |

**Decisiones todavía sin resolver:** (i) catálogo oficial de responsables y fuente maestra; (ii) disponibilidad y calidad de solicitudes históricas; (iii) política de acceso y retención; (iv) esquema estable de IDs; (v) umbrales de calidad y errores críticos; (vi) presupuesto/infraestructura para DL y LLM; (vii) qué controles del Motor B entran al piloto.

## 11. Transferencia a otro equipo o a un nuevo chat

**Contexto verificable de partida.** Es un proyecto local Python 3.12.3 en WSL, desarrollado en VS Code/Cursor. Existen dos dominios, **A Key Contacts** (MVP de recuperación de contactos asociados) y **B Control Intelligence** (todavía diseñado). Se reciben Excel/CSV, se normalizan con pipeline básico y se consulta un índice TF-IDF persistente **M01**. El MVP **no valida RACI ni permisos corporativos** ni tiene ground truth para afirmar calidad predictiva. Los modelos M02 BM25, M03 embeddings, M04 RRF y posteriores están planeados, **no implementados**. La estrategia es evaluar primero ML/DL local, después GenAI controlada, bajo calidad **y** recursos. **Próximo paso técnico prioritario:** fijar benchmark etiquetado y formalizar métricas (distinguiendo Hit@k de Recall@k) antes de comparar nuevos recuperadores.

**Para retomar sin inventar progreso:** revisar `README.md`, `pyproject.toml`, `src/keycontacts/cli.py`, `src/keycontacts/search/tfidf_model.py`, `src/keycontacts/ml/evaluation.py`, `tests/` y `data/processed/quality_report.json`. Confirmar cambios hechos localmente antes de reemplazar archivos: este documento refleja la versión del MVP disponible al redactarlo, no modificaciones posteriores en el equipo.

---

**Fuentes del documento:** *Proyecto 04 — Arquitectura sostenible V1.0* (alcance propuesto), README anterior y archivos del MVP M01 examinados. **No constituye aprobación de arquitectura corporativa ni informe de resultados experimentales.**
