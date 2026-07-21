# Mapa de Conceptos — ¿Qué campo engloba cada cosa que vas a aprender?

Este proyecto (`pure-rag.md`) te enseña a construir RAG, pero RAG en sí no es un campo académico —
es un **patrón de ingeniería** que combina piezas de varios campos distintos. Este doc mapea cada
concepto que vas a tocar al campo más grande al que pertenece, para que sepas dónde buscar si
quieres profundizar más allá del proyecto.

---

## Jerarquía completa

```
Matemáticas
└── Álgebra Lineal
    └── cosine similarity, producto punto, vectores, normas

Ciencias de la Computación
├── Algoritmos y Estructuras de Datos
│   └── ANN (Approximate Nearest Neighbor), HNSW, chunking/text splitting
│
└── Machine Learning
    └── Deep Learning
        └── NLP (Natural Language Processing)
            └── word embeddings, sentence embeddings, cross-encoders (reranking)

Information Retrieval (campo aplicado, usa las 3 ramas de arriba)
├── Sparse Retrieval    → TF-IDF, BM25, keyword search
└── Dense Retrieval     → vector search, vector databases

Ingeniería de Software
├── Backend / APIs      → FastAPI, REST, Server-Sent Events (SSE)
└── Frontend            → React, Next.js, TypeScript

LLM Engineering (campo nuevo, aplicado, mezcla NLP + ingeniería de software)
├── Prompt Engineering  → diseño de prompts, system prompts
└── RAG                 → el patrón completo: IR + NLP + LLM Engineering
    ├── Hybrid Search
    ├── Reranking
    ├── HyDE
    └── Semantic Chunking
```

---

## Tabla — concepto específico → campo que lo engloba

| Concepto (de tu proyecto) | Campo que lo engloba | Dónde aparece en `pure-rag.md` |
|---|---|---|
| Chunking, fixed-size splitting, overlap | Algoritmos y Estructuras de Datos (procesamiento de texto) | Concepto 1, Fase 1 |
| Embeddings (word/sentence), cómo un modelo aprende significado | NLP → Deep Learning → Machine Learning | Concepto 2, Fase 2 |
| Cosine similarity, producto punto, vectores | Álgebra Lineal | Concepto 3 |
| ANN, HNSW (cómo ChromaDB busca rápido) | Algoritmos y Estructuras de Datos | Concepto 3, Fase 3 |
| Vector database (ChromaDB) | Information Retrieval (Dense Retrieval) | Concepto 3, Fase 2-3 |
| TF-IDF, BM25, keyword search | Information Retrieval (Sparse Retrieval) | mencionado en Hybrid Search |
| Prompt design, system prompt, evitar alucinaciones | Prompt Engineering (LLM Engineering) | Concepto 4, Fase 4 |
| Streaming de respuesta, Server-Sent Events (SSE) | Ingeniería de Software — Backend | Fase 5 |
| REST API, endpoints HTTP (FastAPI) | Ingeniería de Software — Backend | Fase 5 |
| Consumo de SSE en React, UI de chat | Ingeniería de Software — Frontend | Fase 6 |
| Hybrid search (BM25 + vectores combinados) | Information Retrieval (combina Sparse + Dense) | Temas avanzados |
| Reranking (cross-encoders) | NLP / Deep Learning | Temas avanzados |
| HyDE (Hypothetical Document Embedding) | LLM Engineering (usa NLP + prompting) | Temas avanzados |
| Semantic chunking | NLP + Algoritmos (combina embeddings con lógica de splitting) | Temas avanzados |
| RAG como arquitectura completa | LLM Engineering (patrón, no campo académico) | Todo el doc |

---

## Por dónde empezar si quieres ir más profundo que el proyecto

Orden recomendado, de la base matemática hacia arriba:

1. **Álgebra Lineal** — cosine similarity, producto punto, vectores.
   Recurso: "3Blue1Brown — Essence of Linear Algebra" (visual, no necesitas ser matemático).

2. **Word embeddings (origen histórico)** — para entender la intuición de "significado = posición
   en un espacio" antes de ver modelos modernos.
   Busca: "word2vec explained".

3. **Sentence/text embeddings** — el paso que usa directamente tu proyecto (nomic-embed-text).
   Busca: "sentence embeddings explained".

4. **Algoritmos y Estructuras de Datos — ANN / HNSW** — cómo ChromaDB encuentra los top-5 sin
   comparar contra todo.
   Busca: "HNSW algorithm explained".

5. **Documentación oficial de ChromaDB** — conecta la teoría con el código real.
   docs.trychroma.com

6. **NLP más formal** — si quieres entender embeddings, reranking y HyDE con más profundidad.
   Curso: Stanford CS224N (Natural Language Processing with Deep Learning).

7. **RAG architecture** — ahora sí, al final, para ver cómo se junta todo lo anterior en un
   solo patrón, y entender las variantes (hybrid search, agentic RAG, etc.).

---

## Nota sobre "¿esto es IA o no?"

No todo lo que toca este proyecto es IA:

- **Sí es IA (redes neuronales entrenadas):** el modelo de embeddings (nomic-embed-text), el LLM
  de generación (llama3.2), reranking con cross-encoders.
- **No es IA (matemática/algoritmos clásicos):** cosine similarity, ANN/HNSW, chunking por tamaño
  fijo, TF-IDF/BM25, todo el backend con FastAPI, todo el frontend con React.

RAG junta ambos mundos: usa IA para generar y entender significado, y usa ingeniería de software
clásica (bases de datos, APIs, algoritmos de búsqueda) para que ese significado se pueda guardar
y consultar rápido.
