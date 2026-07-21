# Dudas y Respuestas — Log de aprendizaje

Registro de preguntas que surgen mientras se implementa el proyecto, con sus respuestas.
Organizado por fase. Ver también [`mapa-de-conceptos.md`](./mapa-de-conceptos.md) para cómo
cada tema se conecta con campos más grandes.

## Índice

- **Fase 1 — Ingest**
  - [¿Qué técnicas se usan normalmente para leer documentos (PDF/EPUB) en proyectos RAG?](#qué-técnicas-se-usan-normalmente-para-leer-documentos-pdfepub-en-proyectos-rag)
  - [¿Cómo se googlea el tema de extracción de documentos?](#cómo-se-googlea-el-tema-de-extracción-de-documentos)

---

## Fase 1 — Ingest (leer y dividir el libro)

### ¿Qué técnicas se usan normalmente para leer documentos (PDF/EPUB) en proyectos RAG?

Depende del formato:

**Para PDF:**

| Librería | Cuándo usarla |
|---|---|
| `PyMuPDF` (fitz) | La opción por defecto para la mayoría de casos: rápida, extrae texto y preserva número de página. **Es la que usa este proyecto.** |
| `pdfplumber` | Cuando el PDF tiene tablas importantes que quieres extraer bien |
| `pypdf` / `PyPDF2` | Más simple, pero se le complica con layouts raros (columnas, texto rotado) |
| `unstructured` | Librería "inteligente": detecta layout, columnas, tablas, encabezados automáticamente. Más pesada, útil cuando los PDFs son complicados (papers académicos, revistas) |
| OCR (`pytesseract`, o `unstructured` con modo OCR) | Solo si el PDF es en realidad imágenes escaneadas (no tiene capa de texto real) |

**Para EPUB:**

- `ebooklib` — lee la estructura del epub (capítulos como HTML)
- `beautifulsoup4` — limpia el HTML que devuelve ebooklib para quedarte con texto plano

Esta combinación (`ebooklib` + `beautifulsoup4`) es la que usa este proyecto (ver Setup inicial
en `pure-rag.md`).

**Alternativa de más alto nivel:** `LangChain` y `LlamaIndex` traen "document loaders" que
abstraen todo esto (un solo `PyPDFLoader` o `EpubReader` que internamente usa estas mismas
librerías). El doc del proyecto lo menciona en "Temas avanzados" — la recomendación es construirlo
a mano primero (como se está haciendo aquí) para entender qué pasa por debajo, y migrar a esas
abstracciones después si aporta valor.

**Cosas a las que hay que prestar atención sin importar la librería:**

- **Metadata de página**: necesitas guardar en qué página cayó cada chunk (para las citas, ver
  Concepto 1 de `pure-rag.md`). No todas las librerías te dan esto gratis.
- **Ruido repetido**: headers/footers que se repiten en cada página, números de página sueltos —
  ensucian los chunks si no se filtran.
- **Layouts multi-columna**: la extracción de texto puede mezclar el orden de las columnas si la
  librería no maneja bien el layout. PyMuPDF lo maneja razonablemente bien pero no siempre perfecto.
- **Tablas e imágenes**: normalmente se ignoran o requieren tratamiento especial en un RAG de solo
  texto.

Para este proyecto, con libros de texto corrido (novelas, libros de no-ficción), `PyMuPDF` +
`ebooklib`/`beautifulsoup4` es suficiente — no hace falta `unstructured` ni OCR salvo que alguno
de los libros sea un PDF escaneado.

### ¿Cómo se googlea el tema de extracción de documentos?

El nombre general del campo es **"document parsing"** o **"document extraction"** — con eso ya
encuentras comparativas de librerías (PyMuPDF vs pdfplumber vs unstructured, etc.).

Términos más específicos según lo que necesites:

| Lo que buscas | Término |
|---|---|
| Extraer texto plano de PDF/EPUB (caso simple, el de este proyecto) | **"PDF text extraction python"** |
| Documentos con tablas, columnas, layouts complejos | **"document layout analysis"** |
| PDFs escaneados (imágenes, no texto real) | **"OCR"** (Optical Character Recognition) — `pytesseract` es la librería típica |
| El campo académico/NLP que engloba todo esto (extraer info estructurada de texto/documentos) | **"Information Extraction"** — dentro de NLP |
| Productos/servicios comerciales que hacen esto automático (para comparar qué tan "manual" es tu approach) | **"Document AI"** (Google), **"Textract"** (AWS), **"Azure Document Intelligence"** |

Para lo que necesitas ahora mismo (Fase 1, libros de texto corrido), con **"PDF text extraction
python"** y **"epub parsing python"** ya encuentras todo lo necesario — no hace falta ir hasta
"document layout analysis" u OCR salvo que tus libros sean PDFs escaneados.