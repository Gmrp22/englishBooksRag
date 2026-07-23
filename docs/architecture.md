# Arquitectura

Diseño de sistema objetivo para este proyecto — no el plan paso a paso (eso vive en
[`plan.md`](./plan.md)), sino **qué componentes existen y cómo se comunican**, corriendo
100% local con Docker (sin costo de nube) pero siguiendo el mismo patrón que se usaría en
producción.

## Diagrama

```
┌─────────┐     ┌──────────────┐     ┌───────────────┐
│   UI    │────▶│  API/Backend │────▶│ Object Storage │  (MinIO local, habla protocolo S3)
└─────────┘     └──────────────┘     └───────────────┘
                       │                     guarda el PDF/EPUB crudo
                       ▼
                ┌──────────────┐
                │  Postgres DB  │   crea registro: status="uploaded"
                └──────────────┘
                       │
                       ▼
                ┌──────────────┐
                │  Job Queue    │   (Redis + Celery, o RQ)
                └──────────────┘   la API responde YA al usuario (no espera)
                       │
                       ▼
                ┌──────────────┐
                │    Worker     │   proceso aparte, en background:
                │  (async job)  │   descarga de storage → extract → clean →
                └──────────────┘   chunk → embed → guarda vectores
                       │
              ┌────────┴────────┐
              ▼                 ▼
      ┌───────────────┐  ┌──────────────┐
      │ Postgres        │  │ pgvector      │
      │ (metadata,      │  │ (embeddings,  │
      │  status="ready")│  │  vía Postgres)│
      └───────────────┘  └──────────────┘
```

## Componentes

| Pieza | Rol | Por qué (y no la versión "junior") |
|---|---|---|
| **API/Backend** | Recibe el upload, encola el trabajo, responde de inmediato | No procesa el archivo en la misma request — evita timeouts con archivos grandes |
| **Object Storage** (MinIO local, S3 en prod) | Guarda el PDF/EPUB crudo | MinIO habla el mismo protocolo S3 (`boto3`) — se aprende el patrón real sin pagar AWS |
| **Job Queue** (Redis + Celery/RQ) | Desacopla "recibir archivo" de "procesarlo" | Sin esto, el servidor web se bloquea procesando síncronamente |
| **Worker** | Ejecuta el pipeline: extract → clean → chunk → embed → store | Corre aparte del servidor web, se puede escalar independiente |
| **Postgres** | Metadata de libros, status de procesamiento (`uploaded`/`processing`/`ready`/`failed`) | La UI puede mostrar progreso real al usuario |
| **pgvector** (extensión de Postgres) | Guarda embeddings + permite búsqueda por similitud | Un solo Postgres hace de DB relacional y vector DB — menos piezas que administrar que un vector DB dedicado (Pinecone/Qdrant) |

## Pipeline de ingesta (dentro del Worker)

1. Descargar archivo crudo del Object Storage
2. **Extract**: `pymupdf4llm.to_markdown()` → texto/markdown crudo
3. **Clean**: quitar ruido (portada, índice alfabético, headers/footers repetidos)
4. **Chunk**: cortar el texto limpio en pedazos
5. **Embed**: generar vector por chunk
6. **Store**: guardar chunk + vector + metadata (página, capítulo) en pgvector
7. Actualizar status en Postgres a `ready`

## Cómo correr esto local

Docker Compose con 3 contenedores: Postgres (con extensión `pgvector`), Redis, MinIO.
Mismo código de aplicación (`boto3`, cliente de Postgres) funcionaría contra servicios reales
en la nube sin cambios — solo cambian las credenciales/endpoints.
