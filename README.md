# DocuMind: Enterprise Document Management & RAG Platform

> Production-grade Retrieval-Augmented Generation (RAG) platform powered by **PostgreSQL + pgvector** and **Google Gemini AI**.

---

## 1. Project Overview

**DocuMind** is a full-stack, multi-tenant enterprise document intelligence platform. It enables organizations to ingest multi-format corporate documents (PDF, DOCX, TXT), perform automated text cleaning and page-accurate chunking, generate high-dimensional vector embeddings, index them natively in PostgreSQL using `pgvector` with HNSW acceleration, and execute grounded semantic queries with source citations.

---

## 2. Problem Statement

Enterprise teams face critical challenges when leveraging Large Language Models (LLMs) on private documentation:
1. **Hallucinations**: Generative LLMs invent unsupported facts when queried on internal company knowledge.
2. **Missing Citations**: Answers lack traceable proof (document names, exact page numbers, chunk identifiers).
3. **Multi-Tenant Isolation**: Risk of cross-user or cross-department document leakage.
4. **Scattered Infrastructure**: Managing separate vector databases alongside relational databases adds operational overhead and synchronization delays.

---

## 3. Objectives

- **100% Grounded Q&A**: Zero external hallucinations; if documents lack sufficient context, DocuMind explicitly refuses to guess by returning:  
  `"I could not find sufficient information in the uploaded documents to answer this question."`
- **Strict Evidence Attribution**: Every response provides source metadata with document name, page number, cosine similarity score, and excerpt.
- **Single-Engine Persistence**: Relational data, access control, and vector embeddings reside securely in PostgreSQL via `pgvector`.
- **Tenant Scoped Isolation**: Ownership checks enforced at the database and query layer.

---

## 4. Key Features

- **Multi-Format Extraction**: PyMuPDF (`fitz`) for PDF with page-accurate indexing, `python-docx` for Word documents, and resilient TXT decoders.
- **Semantic Chunking with Overlap**: Configurable window sizes with boundary awareness preventing sentence chopping.
- **Batch Embeddings**: Integration with Google Gemini `text-embedding-004` (768 dimensions).
- **HNSW Vector Indexing**: Cosine similarity searches accelerated via PostgreSQL HNSW indexing (`vector_cosine_ops`).
- **Configurable RAG Tuning**: Interactive controls for Top-K retrieval and similarity cutoff thresholds.
- **Dedicated Semantic Vector Search**: Direct inspection of raw vector similarity rankings independently of LLM synthesis.
- **Conversation Threading**: Persistent multi-session chat histories.
- **Comprehensive Health Checks**: Endpoint checking API status, PostgreSQL connectivity, and pgvector extension version.
- **Alembic Database Migrations**: Version-controlled migrations with native vector support.

---

## 5. System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │       Frontend: React 18 + Vite + Tailwind CSS         │
                    │   (Dashboard, Document Manager, AI Chat, Search)      │
                    └───────────────────────────┬────────────────────────────┘
                                                │ REST API / Axios + JWT
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               FastAPI API Gateway                      │
                    │      (Auth, Document Ingestion, RAG Chat, Search)      │
                    └───────┬───────────────────────────────┬────────────────┘
                            │                               │
            ┌───────────────▼───────────────┐               │
            │     Ingestion Pipeline        │               │
            │  - PyMuPDF / docx Extraction  │               │
            │  - Clean & Overlapping Chunks │               │
            │  - Gemini Batch Embeddings    │               │
            └───────────────┬───────────────┘               │
                            │                               │
                            ▼                               ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                      PostgreSQL 16 + pgvector                          │
    │  - Relational: users, documents, conversations, messages, citations    │
    │  - Vector: document_chunks (embedding vector(768) + HNSW Index)        │
    └────────────────────────────────────────────────────────────────────────┘
```

---

## 6. RAG Retrieval & Generation Workflow

```
                        User Question
                              │
                              ▼
                   EmbeddingService (Gemini)
                              │  (768-dim Query Vector)
                              ▼
                 VectorSearchService (pgvector)
                   - Filter: user_id = current_user
                   - Distance: 1 - (embedding <=> query_vector)
                   - Thresholding: similarity >= SIMILARITY_THRESHOLD
                   - Ordering: Top-K descending
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            [No Chunks Found]    [Chunks Retrieved]
                    │                   │
                    ▼                   ▼
         Return Standard Fallback  ContextBuilder + PromptBuilder
         "I could not find..."          │
                                        ▼
                                 LLMService (Gemini)
                                        │
                                        ▼
                              CitationFormatter
                                        │
                                        ▼
                          Grounded Answer + Source Cards
```

---

## 7. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS | High-performance enterprise dashboard & chat UI |
| **Icons & Style** | Lucide React, Glassmorphism | Clean, professional SaaS design system |
| **Backend API** | Python 3.11, FastAPI, Pydantic v2 | High-concurrency async web framework |
| **ORM & Migrations**| SQLAlchemy 2.0, Alembic | Type-safe database queries & migrations |
| **Database & Vector**| PostgreSQL 16 + pgvector | Relational storage + native 768-dim HNSW vector search |
| **PDF Extraction** | PyMuPDF (`fitz`) | Page-accurate, high-speed PDF text parsing |
| **DOCX Extraction**| `python-docx` | Word document paragraph & table extraction |
| **AI Models** | Google Gemini `text-embedding-004` & `gemini-1.5-flash` | Embeddings and strictly grounded generative answers |
| **Testing** | pytest, pytest-asyncio, httpx | Automated unit, integration, and RAG evaluation tests |
| **Deployment** | Docker, Docker Compose, Nginx | Multi-container production orchestration |

---

## 8. Database Schema

### Entity Relationship Diagram
```
users (id, name, email, password_hash, is_active, created_at, updated_at)
  ├── documents (id, user_id, filename, original_filename, file_type, file_size, storage_path, status, total_pages, total_chunks)
  │     └── document_chunks (id, document_id, chunk_index, content, page_number, chunk_metadata, embedding vector(768))
  └── conversations (id, user_id, title, created_at, updated_at)
        └── messages (id, conversation_id, role, content, created_at)
              └── message_citations (id, message_id, chunk_id, document_name, page_number, similarity_score, excerpt)
```

---

## 9. API Endpoints

### System Health
- `GET /health`: System, PostgreSQL, and pgvector extension status.

### Authentication
- `POST /api/auth/register`: Register enterprise account with unique email.
- `POST /api/auth/login`: Authenticate and receive signed JWT token.
- `GET /api/auth/me`: Get active user profile.

### Documents
- `POST /api/documents/upload`: Upload PDF, DOCX, or TXT file.
- `GET /api/documents`: List user's documents.
- `GET /api/documents/{id}`: View document details and vector chunks.
- `DELETE /api/documents/{id}`: Delete document and cascade delete vector chunks.
- `POST /api/documents/{id}/process`: Retry/trigger document ingestion pipeline.
- `GET /api/documents/{id}/status`: Check status (`pending`, `processing`, `completed`, `failed`).

### RAG Chat & Semantic Search
- `POST /api/chat`: Grounded RAG query returning answer, source citations, and conversation ID.
- `POST /api/search`: Direct semantic search on vector chunks without LLM generation.

### Conversations
- `GET /api/conversations`: List user conversation threads.
- `POST /api/conversations`: Create new conversation thread.
- `GET /api/conversations/{id}`: Retrieve message history and citation cards.
- `DELETE /api/conversations/{id}`: Delete conversation thread.

### Dashboard
- `GET /api/dashboard/stats`: Aggregate metrics (total documents, chunks, pages, storage).

---

## 10. Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/documind_db` |
| `JWT_SECRET` | Secret key for signing JWT tokens | `<strong_random_secret>` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| JWT token expiration in minutes | `1440` (24 hours) |
| `GEMINI_API_KEY` | Google Gemini API Key | `""` *(runs in mock mode if unset)* |
| `EMBEDDING_MODEL` | Gemini embedding model | `text-embedding-004` |
| `LLM_MODEL` | Gemini generative model | `gemini-1.5-flash` |
| `EMBEDDING_DIMENSION`| Vector dimensions | `768` |
| `TOP_K` | Default number of retrieved chunks | `4` |
| `SIMILARITY_THRESHOLD`| Cosine similarity cutoff | `0.40` |
| `UPLOAD_DIRECTORY` | Disk storage directory for documents | `./uploads` |
| `MAX_FILE_SIZE_MB` | Maximum allowed file upload size | `50` |

---

## 11. How to Run (Step-by-Step)

### Option A: Running from Local Git Clone (Fastest)

#### 1. Clone the Repository
```bash
git clone https://github.com/kreshwanth/documind-rag.git
cd documind-rag
```

#### 2. Start the Backend Server (Terminal 1)
```powershell
# Navigate to backend folder
cd backend

# Create & activate Python virtual environment
python -m venv venv

# If on Windows PowerShell, enable script execution (one-time setup):
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Backend API server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend is now running at: `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`)*

---

#### 3. Start the Frontend Application (Terminal 2)
Open a **new terminal window**:
```powershell
# Navigate to frontend folder (wrap path in quotes if using full path with spaces)
cd documind-rag/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
*Frontend is now running at: `http://localhost:5173`*

---

#### 4. Open & Use the Application
1. Open your browser and navigate to **`http://localhost:5173`**.
2. Click **Create Enterprise Account** to register a new account or **Sign In**.
3. Upload PDF documents in the **Documents** tab.
4. Go to **Chat** and ask questions to get grounded AI answers with page citations!

---

### Option B: Running with Docker Compose (All-in-One)

1. Clone the repository and configure environment variables:
   ```bash
   cp .env.example .env
   ```
2. Start the complete containerized stack (PostgreSQL + pgvector, Backend, Frontend):
   ```bash
   docker compose up --build -d
   ```
3. Access the services:
   - **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 12. Automated Test Suite

Run the automated test benchmarks and evaluation suite:
```bash
cd backend
pytest
```
Or run the RAG accuracy benchmark suite directly:
```bash
python test_all_benchmarks.py
```

---

## 13. Example RAG Interaction

### Request (`POST /api/chat`)
```json
{
  "question": "What is the policy regarding remote work reimbursement?",
  "top_k": 4,
  "similarity_threshold": 0.40
}
```

### Grounded Response (`200 OK`)
```json
{
  "answer": "According to Section 4 of the Employee Handbook, employees are eligible for a monthly remote work stipend of $150 to cover broadband and home office utilities.",
  "sources": [
    {
      "document_name": "Employee_Handbook_2026.pdf",
      "page_number": 12,
      "similarity_score": 0.8924,
      "excerpt": "Remote Work Stipend: Full-time remote employees receive a monthly allowance of $150..."
    }
  ],
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_fallback": false
}
```

### Unsupported Question Response (`200 OK`)
```json
{
  "answer": "I could not find sufficient information in the uploaded documents to answer this question.",
  "sources": [],
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_fallback": true
}
```

---

## 14. Security & Compliance

- **Multi-Tenant Scoping**: All chunk searches and document lookups enforce `WHERE user_id = current_user.id`.
- **Path Traversal Protection**: Uploaded files are assigned UUID-prefixed safe storage names outside the web root.
- **Password Security**: Passwords hashed with `bcrypt` using salted one-way hashing.
- **Zero Hallucination Tolerance**: Strict negative prompting combined with cosine thresholding prevents fabricating unsupported answers.
