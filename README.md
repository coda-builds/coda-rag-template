# rag-pipeline-template

> **A production-ready Retrieval-Augmented Generation (RAG) pipeline for client projects.**
> Upload your documents. Query them in natural language. Deploy in minutes.

---

## What this is

This is a client-deliverable template for a **company knowledge base search tool**: a business uploads its internal documentation (handbooks, policies, FAQs, product guides) and their team can query it in plain English and receive accurate, cited answers grounded in the actual documents.

**Example queries this system answers:**

- *"What is the expense limit for a hotel in London?"*
- *"How do I submit a purchase order for over £5,000?"*
- *"What are the MFA requirements for accessing the VPN?"*
- *"What leave entitlement do I have and how do I request it?"*

The system retrieves the most relevant document sections and uses an LLM to synthesise a precise answer — with source attribution — instead of returning a list of links.

---

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **API** | [FastAPI](https://fastapi.tiangolo.com/) | Async Python, automatic OpenAPI docs, production-proven |
| **Embeddings** | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | 384-dim, fast CPU inference, excellent semantic quality |
| **Vector store** | [pgvector](https://github.com/pgvector/pgvector) on [Supabase](https://supabase.com) | Managed Postgres, no extra infra, HNSW indexing built-in |
| **Generation** | [OpenRouter API](https://openrouter.ai/) | Unified LLM gateway; access to 200+ models via one API key; meta-llama/llama-3.1-70b-instruct default |
| **Deployment** | [Railway](https://railway.app/) | One-click deploy from GitHub, automatic HTTPS, env management |

---

## Architecture

```
Client Request
      │
      ▼
┌─────────────┐
│  FastAPI    │  /api/query, /api/documents, /health
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Embedding Service  │  all-MiniLM-L6-v2 (local, cached at startup)
│  (sentence-xformers)│  Query → 384-dim normalised vector
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  pgvector (HNSW)    │  Cosine similarity search
│  on Supabase        │  Returns top-k most relevant chunks
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  OpenRouter API     │  Context + query → grounded answer
│  llama-3.1-70b-inst │  Temperature 0.2 for factual precision
└─────────────────────┘
```

---

## Repository structure

```
rag-pipeline-template/
├── app/
│   ├── main.py                  # FastAPI app, startup, health check
│   ├── config.py                # Pydantic settings (reads .env)
│   ├── api/
│   │   ├── deps.py              # Shared dependencies (API key auth)
│   │   └── routes/
│   │       ├── documents.py     # Ingest, list, delete endpoints
│   │       └── query.py         # RAG query endpoint
│   ├── core/
│   │   ├── embeddings.py        # all-MiniLM-L6-v2 wrapper
│   │   ├── retriever.py         # pgvector HNSW similarity search
│   │   └── generator.py         # OpenRouter API call with retry
│   ├── db/
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   └── migrations/
│   │       └── 001_init.sql     # Schema: documents table + HNSW index
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response schemas
│   └── services/
│       ├── ingestion.py         # Embed + insert document chunks
│       └── rag.py               # Orchestrates retrieval + generation
├── sample_docs/                 # Generic business documents (demo)
│   ├── company_handbook.md
│   ├── it_security_policy.md
│   ├── product_faq.md
│   ├── finance_procedures.md
│   └── onboarding_guide.md
├── scripts/
│   ├── ingest_sample_docs.py    # Bulk-ingest sample_docs/ into the API
│   └── test_query.py            # Run demo queries and print results
├── tests/
│   └── test_api.py              # Integration tests (pytest)
├── .github/workflows/ci.yml     # GitHub Actions: lint + test
├── .env.example                 # Copy to .env and fill in values
├── railway.toml                 # Railway deployment config
└── requirements.txt
```

---

## Quick start (local)

### Prerequisites

- Python 3.11 or 3.12
- A [Supabase](https://supabase.com) project (free tier is sufficient)
- An [OpenRouter API key](https://openrouter.ai/keys)

### 1. Clone and install

```bash
git clone https://github.com/your-username/rag-pipeline-template.git
cd rag-pipeline-template
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres
OPENROUTER_API_KEY=sk-or-...
```

### 3. Apply the database schema

Open the [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql) and run the contents of:

```
app/db/migrations/001_init.sql
```

This creates the `documents` table with the pgvector column and HNSW index.

### 4. Start the API

```bash
python -m uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**. Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### 5. Ingest sample documents

```bash
python scripts/ingest_sample_docs.py
```

This chunks and embeds the five sample business documents in `sample_docs/` and inserts them into pgvector.

### 6. Run demo queries

```bash
python scripts/test_query.py
```

You should see answers with cited sources for questions like *"What is the annual leave policy?"* and *"What are the MFA requirements?"*.

---

## API reference

### `POST /api/documents`

Ingest a single document chunk.

```json
{
  "title": "IT Security Policy – Password Requirements",
  "content": "All company accounts must use passwords of at least 14 characters...",
  "source": "it_security_policy.md",
  "metadata": { "department": "IT", "version": "2.4" }
}
```

**Response `201`:**
```json
{ "inserted": 1, "ids": ["a1b2c3d4-..."] }
```

---

### `POST /api/documents/batch`

Ingest up to 500 chunks in one request.

```json
{
  "documents": [
    { "title": "...", "content": "...", "source": "...", "metadata": {} },
    { "title": "...", "content": "...", "source": "...", "metadata": {} }
  ]
}
```

---

### `GET /api/documents`

List ingested documents (paginated).

Query params: `limit` (default 50, max 200), `offset` (default 0).

---

### `DELETE /api/documents/{id}`

Remove a document by UUID. Returns `204 No Content`.

---

### `POST /api/query`

Run the full RAG pipeline: embed → retrieve → generate.

```json
{
  "query": "What is the annual leave entitlement?",
  "top_k": 5,
  "filter": { "source": "company_handbook.md" }
}
```

**Response `200`:**
```json
{
  "query": "What is the annual leave entitlement?",
  "answer": "All employees receive 25 days of annual leave per year, in addition to public holidays...",
  "sources": [
    {
      "id": "a1b2c3d4-...",
      "title": "Employee Handbook – Annual Leave",
      "content": "All employees receive 25 days...",
      "source": "company_handbook.md",
      "score": 0.912
    }
  ],
  "model": "meta-llama/llama-3.1-70b-instruct",
  "retrieval_top_k": 5
}
```

The `filter` field is optional. When provided, only documents whose metadata contains the specified key-value pairs are searched.

---

### `GET /health`

Liveness and readiness probe. Checks database connectivity.

```json
{
  "status": "ok",
  "database": true,
  "embedding_model": "all-MiniLM-L6-v2",
  "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
  "version": "1.0.0"
}
```

---

## Deployment on Railway

### One-time setup

1. Push this repo to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. In the Railway project, open **Variables** and add:
   - `DATABASE_URL` – your Supabase connection string
   - `OPENROUTER_API_KEY` – your OpenRouter key
   - `APP_ENV` – set to `production`
   - `API_KEY` – a secret string to protect your endpoints (optional but recommended)
5. Railway reads `railway.toml` automatically. The service starts with:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. Railway provides a public HTTPS URL automatically (e.g. `https://rag-pipeline-template.up.railway.app`).

### Subsequent deployments

Push to `main` → Railway auto-deploys. On Railway's Hobby and Pro plans, deployments are zero-downtime (the new container is healthy before the old one is removed). On the free Starter plan, expect a brief restart.

### Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `OPENROUTER_API_KEY` | ✅ | — | OpenRouter API key |
| `APP_ENV` | | `development` | Set to `production` in Railway |
| `LOG_LEVEL` | | `INFO` | Python log level |
| `OPENROUTER_MODEL` | | `meta-llama/llama-3.1-70b-instruct` | Any model available on OpenRouter |
| `EMBEDDING_MODEL` | | `all-MiniLM-L6-v2` | HuggingFace model name |
| `RETRIEVAL_TOP_K` | | `5` | Default number of chunks to retrieve |
| `ALLOWED_ORIGINS` | | `*` | CORS origins (comma-separated or `*`) |
| `API_KEY` | | *(empty)* | If set, all `/api/*` routes require `Authorization: Bearer <key>` |

---

## Customisation guide

### Changing the embedding model

`all-MiniLM-L6-v2` is a strong default. To switch models:

1. Update `EMBEDDING_MODEL` in `.env`.
2. Update `embedding_dimensions` in `app/config.py` to match the new model's output size.
3. Update the `vector(384)` type in `app/db/migrations/001_init.sql` to the new dimension count.
4. Re-run the migration (drop and recreate the table, or `ALTER COLUMN`).
5. Re-ingest all documents.

Popular alternatives on the same library:

| Model | Dimensions | Notes |
|-------|-----------|-------|
| `all-MiniLM-L6-v2` | 384 | Default; fast, small, great quality |
| `all-mpnet-base-v2` | 768 | Higher quality, ~3× slower |
| `multi-qa-MiniLM-L6-cos-v1` | 384 | Optimised for QA retrieval |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+ languages |

### Changing the LLM

Set `OPENROUTER_MODEL` to any model available on your OpenRouter account:

```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet        # Best quality
OPENROUTER_MODEL=openai/gpt-4o-mini                 # Fast and cost-effective
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct   # Lightweight, low cost
```

Browse the full model list at [openrouter.ai/models](https://openrouter.ai/models).

### Chunking strategy

The ingestion script splits documents at Markdown headings. For production use, consider:

- **Fixed-size chunking** with overlap for long prose (e.g. 512 tokens, 50-token overlap)
- **Semantic chunking** using the [`semantic-chunkers`](https://pypi.org/project/semantic-chunkers/) library
- **Document-aware chunking** for PDFs, preserving page and section context

Implement your strategy in `scripts/ingest_sample_docs.py` before calling `POST /api/documents/batch`.

### Adding metadata filters

The `POST /api/query` endpoint accepts a `filter` field that restricts retrieval to documents matching specific metadata values:

```json
{
  "query": "What is the password policy?",
  "filter": { "department": "IT" }
}
```

Tag your documents at ingestion time with whatever metadata dimensions matter to your use case (department, document type, date, product line, etc.).

### Securing the API

Set `API_KEY` in your environment to require bearer token authentication on all `/api/*` routes:

```bash
curl -H "Authorization: Bearer your-secret-key" \
     -X POST https://your-app.up.railway.app/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the leave policy?"}'
```

The `/health` endpoint is always public (required for Railway's health check).

---

## HNSW index tuning

The default index parameters in `001_init.sql` are:

```sql
CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

| Parameter | Default | Effect |
|-----------|---------|--------|
| `m` | 16 | Edges per node. Higher = better recall, more memory. Range: 4–64. |
| `ef_construction` | 64 | Build-time search width. Higher = better index quality, slower build. |
| `ef_search` (query-time) | 40 | Set via `SET hnsw.ef_search = 80;` before queries for higher recall. |

For a knowledge base with < 100,000 documents, the defaults are excellent. For > 500,000 documents, consider `m=32, ef_construction=128`.

---

## Running tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

Tests require a live database and OpenRouter API key. Set them in your environment or `.env` before running.

---

## Client-ready deliverable

This template is designed to be the foundation for a **complete, client-deployed RAG product** delivered in **4–5 working days**:

| Day | Work |
|-----|------|
| **Day 1** | Repo setup, Supabase project creation, schema migration, OpenRouter integration verified, health check passing |
| **Day 2** | Ingestion pipeline complete, client's document set chunked and embedded, retrieval quality verified |
| **Day 3** | Railway deployment live, HTTPS endpoint working, API key authentication configured, client-facing docs written |
| **Day 4** | QA: test all query types, tune `top_k` and `ef_search` for the client's document set, edge cases handled |
| **Day 5** | Handover: walkthrough call, deployment runbook, client shown how to ingest new documents |

**What the client gets:**

- A running HTTPS API endpoint they can call from any front-end or internal tool
- A Supabase database they own with all their embedded documents
- The full source code in their own GitHub repository
- A clear README for their developers to maintain and extend it
- The ability to add documents via a simple POST request at any time

This is a self-contained, maintainable system — not a black box. The client owns every component.

---

## Licence

MIT. Use freely in client projects, commercial or otherwise.
