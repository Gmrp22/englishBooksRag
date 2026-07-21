# Pure RAG — English Books App

## ¿Qué es RAG y por qué existe?

Cuando le preguntas algo a un LLM como llama3, el modelo responde desde su memoria de entrenamiento.
El problema: no sabe nada de TUS libros. Si le preguntas "¿Qué dice Atomic Habits sobre los hábitos
de la noche?", va a inventar algo plausible o a responder de manera genérica.

**RAG (Retrieval-Augmented Generation)** resuelve esto en dos pasos:

1. **Buscar** los fragmentos de tus libros que son relevantes para la pregunta
2. **Pasarle** esos fragmentos al LLM junto con la pregunta, para que responda usando TU contenido

Es básicamente esto:

```
Sin RAG:  pregunta → LLM → respuesta (de su memoria)

Con RAG:  pregunta → buscar en tus libros → fragmentos relevantes
                                                    ↓
                                       pregunta + fragmentos → LLM → respuesta
```

El LLM no cambia. Lo que cambia es que le das contexto real antes de que responda.

---

## ¿Qué vas a construir?

Una app personal que te permite:

- Hacerle preguntas a tus libros ("¿Qué dice este libro sobre la productividad?")
- Comparar cómo distintos libros tratan un mismo tema
- Estudiar inglés en contexto real ("Muéstrame ejemplos de passive voice en mis novelas")

**Stack:**
- `Python + FastAPI` — backend y pipeline RAG
- `ChromaDB` — base de datos de vectores (aquí viven tus libros procesados)
- `Ollama` — corre los modelos de embeddings y generación en tu máquina
- `Next.js + TypeScript` — interfaz web

---

## El flujo completo, explicado paso a paso

Antes de escribir código, necesitas tener clara la imagen completa:

```
┌─────────────────────────────────────────────────────────┐
│  FASE DE INGESTION (se hace una vez por libro)          │
│                                                         │
│  libro.pdf → dividir en pedazos → convertir a vectores  │
│                                        → guardar en DB  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  FASE DE QUERY (se hace cada vez que el usuario pregunta)│
│                                                         │
│  pregunta → convertir a vector → buscar pedazos         │
│             similares en DB → tomar los mejores 5       │
│             → armar prompt → enviar a LLM → respuesta   │
└─────────────────────────────────────────────────────────┘
```

Hay dos grandes momentos: cuando procesas el libro (ingestion) y cuando el usuario pregunta (query).

---

## Concepto 1 — Chunking (dividir el libro en pedazos)

### ¿Por qué no puedes usar el libro completo?

Dos razones:

1. **Los modelos de embedding tienen un límite de tokens.** `nomic-embed-text` acepta ~8,000 tokens.
   Un libro tiene 100,000+. No entra.

2. **Si metieras todo el libro en el prompt, el LLM se confunde.** Los LLMs degradan su atención
   cuando el contexto es muy largo. Pasan cosas como "lost in the middle": ignora lo que está
   en el centro del contexto.

La solución: dividir el libro en **chunks** (fragmentos) de tamaño manejable.

### ¿Cómo se dividen?

La estrategia más simple es **fixed-size with overlap** (tamaño fijo con traslape):

```
Texto original:
"Los hábitos se forman a través de un ciclo. El ciclo tiene tres partes:
señal, rutina y recompensa. La señal dispara el comportamiento..."

chunk_0 (500 chars): "Los hábitos se forman a través de un ciclo. El ciclo tiene tres partes:
señal, rutina y recompensa. La señal dis..."

chunk_1 (500 chars, empieza 50 chars antes del final del anterior):
"...La señal dispara el comportamiento. La rutina es la acción que realizas.
La recompensa es lo que..."
```

### ¿Por qué existe el overlap?

Sin overlap, chunk_1 empieza exactamente donde termina chunk_0. Si una idea importante cae
justo en ese borde, queda cortada a la mitad:

```
chunk_0: "...la señal dispara el compor-"
chunk_1: "tamiento automático..."
```

Si el usuario pregunta sobre "qué dispara el comportamiento automático", ninguno de los dos
chunks tiene la frase completa, y el embedding de cada mitad por separado no representa bien
la idea. Puede que ninguno se recupere como relevante.

Con overlap, chunk_1 no empieza donde terminó chunk_0, sino un poco *antes* (en el ejemplo
de arriba, 50 chars antes del final de chunk_0). Así la frase que caía en el borde queda
completa en al menos uno de los dos chunks:

```
chunk_0 (chars 0-500):   "...la señal dispara el comportamiento automático..."
chunk_1 (chars 450-950): "el comportamiento automático. La rutina es..."
```

En la práctica lo configuras con dos parámetros del splitter:

- `chunk_size = 500` — tamaño de cada pedazo
- `chunk_overlap = 50` — cuántos caracteres se repiten con el chunk anterior

Es un trade-off: más overlap reduce la probabilidad de cortar ideas a la mitad, pero genera
más chunks totales (más redundancia, más espacio en la DB, embeddings ligeramente más caros
de generar).

### ¿Qué metadatos guardar con cada chunk?

Cada chunk no es solo texto. Necesita contexto sobre de dónde vino:

```python
{
  "text": "Los hábitos se forman a través de un ciclo...",
  "book_title": "Atomic Habits",
  "author": "James Clear",
  "page": 42,
  "chunk_index": 7   # el séptimo pedazo de este libro
}
```

Esto sirve para que la respuesta final pueda citar: *"Según Atomic Habits (p. 42)..."*

---

## Concepto 2 — Embeddings (convertir texto en números)

### ¿Qué es un embedding?

Un embedding es una lista de números (un vector) que representa el **significado** de un texto.

```
"Los hábitos se forman por repetición"  →  [0.021, -0.54, 0.88, 0.12, ...]
                                            (768 números)

"Los hábitos nacen de acciones repetidas" →  [0.019, -0.51, 0.85, 0.14, ...]
                                              (muy similar al anterior)

"El cielo es azul"  →  [-0.3, 0.72, -0.1, 0.55, ...]
                        (muy diferente)
```

La propiedad clave: **textos con significados parecidos tienen vectores parecidos**.

Esto lo hace un modelo de embedding (en tu caso, `nomic-embed-text` corriendo en Ollama).

### ¿Por qué necesitas embeddings para RAG?

Porque cuando el usuario pregunta algo, necesitas encontrar qué fragmentos del libro son relevantes.

La búsqueda por palabras clave (como `grep`) falla si el usuario usa sinónimos:

```
El libro dice: "la perseverancia es clave para el éxito"
Usuario pregunta: "importancia de no rendirse"

grep: no encuentra nada (palabras distintas)
embeddings: encuentra el fragmento (mismo significado)
```

### La regla de oro de los embeddings

> El modelo que usas para **incrustar** los chunks al guardarlos debe ser el **mismo** que usas
> para incrustar la pregunta del usuario.

Si guardaste con `nomic-embed-text` y buscas con otro modelo, los vectores viven en espacios
distintos y la búsqueda no funciona.

---

## Concepto 3 — Vector Store / ChromaDB (dónde se guardan los vectores)

### ¿Qué es una base de datos vectorial?

Una base de datos normal busca por igualdad exacta: `WHERE title = 'Atomic Habits'`.

Una base de datos vectorial busca por **similitud**: "dame los 5 vectores más parecidos a este".

ChromaDB es una base de datos vectorial que corre localmente, sin servidores, guarda en disco.
Perfecta para aprender.

### ¿Cómo funciona la búsqueda?

La similitud entre dos vectores se mide con **cosine similarity** (similitud coseno).
No necesitas entender la matemática, pero sí la intuición:

```
Similitud coseno = 1.0  →  textos idénticos en significado
Similitud coseno = 0.9  →  muy similares
Similitud coseno = 0.5  →  algo relacionados
Similitud coseno = 0.0  →  sin relación
```

ChromaDB devuelve los resultados ordenados de más a menos similar. Tú le pides los top-5.

---

## Concepto 4 — Prompt Engineering para RAG

### ¿Qué problema resuelve?

Sin instrucciones claras, el LLM puede:
- Ignorar los fragmentos y responder de su memoria de entrenamiento
- Inventar citas que no existen en el libro
- No indicar de dónde sacó la información

### La estructura del prompt RAG

Un buen prompt para RAG tiene tres partes:

```
[SYSTEM]
Eres un asistente de lectura. Responde SOLO usando los fragmentos proporcionados.
Si la respuesta no está en los fragmentos, dilo explícitamente.
Cita siempre el libro y la página.

[CONTEXT - los fragmentos recuperados]
[Atomic Habits, p.42]
Los hábitos se forman a través de un ciclo de señal, rutina y recompensa...

[Atomic Habits, p.43]
La señal puede ser cualquier cosa que dispare el comportamiento automático...

[USER]
¿Cómo se forma un hábito según Atomic Habits?
```

La clave es que el sistema le dice al LLM que su única fuente de verdad son los fragmentos.

---

## Estructura del proyecto

```
englishBooksRag/
├── backend/
│   ├── ingest.py       # Fase 1 y 2: chunk → embed → guardar en ChromaDB
│   ├── retrieve.py     # Fase 3: pregunta → embed → buscar en ChromaDB
│   ├── generate.py     # Fase 4: fragmentos + pregunta → armar prompt → LLM
│   └── api.py          # Fase 5: exponer todo como API con FastAPI
├── frontend/           # Fase 6: UI en Next.js
├── books/              # Pon aquí tus PDFs y EPUBs
├── chroma_db/          # ChromaDB guarda aquí automáticamente
├── pyproject.toml
└── .env
```

---

## Plan de implementación — fase a fase

### Fase 1 — Ingest: leer y dividir un libro

**Lo que vas a aprender:** cómo leer PDFs/EPUBs y dividirlos en chunks con metadatos.

**Criterio de éxito:** Puedes correr `python ingest.py books/mi-libro.pdf` y ver en la terminal
que se crearon N chunks con su texto y metadatos.

**Archivos:** `backend/ingest.py`

---

### Fase 2 — Embed y guardar en ChromaDB

**Lo que vas a aprender:** cómo llamar a Ollama para obtener embeddings y cómo guardar en ChromaDB.

**Criterio de éxito:** Puedes abrir ChromaDB y ver que los chunks están guardados con sus vectores.
Corres `collection.count()` y muestra el número de chunks del libro.

**Archivos:** `backend/ingest.py` (continúa)

---

### Fase 3 — Retrieval: buscar en ChromaDB

**Lo que vas a aprender:** cómo hacer una consulta de similitud, filtrar por libro, e interpretar
las distancias para saber qué tan relevante es un resultado.

**Criterio de éxito:** Desde la terminal preguntas algo y ves los 5 fragmentos más relevantes
con sus distancias. Puedes identificar cuándo un resultado es bueno y cuándo no.

**Archivos:** `backend/retrieve.py`

---

### Fase 4 — Generation: armar prompt y llamar al LLM

**Lo que vas a aprender:** cómo construir el prompt con los fragmentos, cómo hacer streaming
de la respuesta, y cómo formatear las citas.

**Criterio de éxito:** Desde la terminal haces una pregunta y ves la respuesta streameada
con referencias reales a páginas del libro.

**Archivos:** `backend/generate.py`

---

### Fase 5 — API con FastAPI

**Lo que vas a aprender:** cómo exponer el pipeline como endpoints HTTP, cómo hacer
streaming desde FastAPI con Server-Sent Events (SSE).

**Criterio de éxito:** Puedes hacer `curl` a tu API y recibir una respuesta streameada.

**Endpoints:**
```
POST /ingest          → procesa un libro
GET  /books           → lista libros ingestados
POST /query           → pregunta (con filtro opcional por libro)
POST /compare         → misma pregunta en múltiples libros
POST /study           → modo estudio de inglés
```

**Archivos:** `backend/api.py`

---

### Fase 6 — UI con Next.js

**Lo que vas a aprender:** cómo consumir SSE desde React, cómo construir el selector de libros
y cómo mostrar las citas inline.

**Criterio de éxito:** Tienes una UI funcional donde puedes elegir un libro, hacer una pregunta
y ver la respuesta aparecer en tiempo real con las citas.

**Páginas:**
- `/` — biblioteca de libros (subir, listar)
- `/chat` — Q&A con streaming y selector de libro
- `/compare` — comparación entre libros
- `/study` — modo inglés

**Archivos:** `frontend/`

---

## Setup inicial

```bash
# 1. Instalar dependencias de Python
cd backend
python -m venv .venv
source .venv/bin/activate    # en Windows: .venv\Scripts\activate
pip install fastapi uvicorn pymupdf ebooklib beautifulsoup4 chromadb ollama

# 2. Bajar los modelos de Ollama
ollama pull nomic-embed-text   # modelo de embeddings (~274MB)
ollama pull llama3.2           # modelo de generación (~2GB)

# 3. Setup de Next.js
cd ../frontend
npx create-next-app@latest . --typescript --tailwind --app
```

---

## Preguntas que deberías poder responder al terminar cada fase

| Fase | Pregunta |
|------|----------|
| 1 | ¿Por qué necesitamos dividir el libro en chunks? ¿Qué pasa si el chunk es muy grande? ¿Muy pequeño? |
| 2 | ¿Qué es un embedding? ¿Por qué textos similares tienen vectores similares? |
| 3 | ¿Qué es cosine similarity? ¿Cuándo un resultado de retrieval es "malo"? |
| 4 | ¿Por qué el system prompt le dice al LLM que solo use el contexto? |
| 5 | ¿Cómo funciona Server-Sent Events para streaming? |
| 6 | ¿Cuál es el flujo completo de una pregunta de usuario hasta la respuesta? |

---

## Temas avanzados (después de terminar las 6 fases)

Estos son conceptos que existen porque el RAG básico tiene limitaciones reales:

- **Hybrid search** — combinar búsqueda por palabras clave (BM25) + vectores. Útil cuando el
  usuario busca términos específicos (nombres propios, términos técnicos) que los embeddings
  a veces no capturan bien.

- **Reranking** — después de recuperar top-20 chunks, usar un segundo modelo (cross-encoder)
  para reordenarlos por relevancia real. Mejora mucho la calidad pero agrega latencia.

- **HyDE (Hypothetical Document Embedding)** — en vez de embedir la pregunta directamente,
  primero le pides al LLM que genere una respuesta hipotética, y embides esa. Funciona mejor
  porque el espacio de embedding de respuestas es más similar al de los documentos.

- **Semantic chunking** — en vez de dividir por tamaño fijo, dividir donde hay un cambio real
  de tema (detectado con embeddings). Chunks más coherentes semánticamente.

- **Migración a LangChain** — cuando hayas construido todo a mano, las abstracciones de
  LangChain (loaders, splitters, retrievers, chains) te van a hacer mucho más sentido.
