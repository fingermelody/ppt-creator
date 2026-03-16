# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

PPT-RSD is an intelligent PPT generation and assembly system built with a React frontend and Python FastAPI backend. The system allows users to:
- Upload and manage PPT documents in a library
- Design PPT outlines with AI assistance (smart generation or wizard mode)
- Assemble new PPTs by selecting pages from the document library
- Refine PPT pages with AI-powered editing

## Tech Stack

**Frontend:**
- React 18 + TypeScript + Vite
- TDesign UI components
- Zustand for state management
- React Query for data fetching
- Playwright for E2E testing, Vitest for unit tests

**Backend:**
- Python 3.9+ + FastAPI
- SQLAlchemy ORM (SQLite for dev, PostgreSQL for production)
- ChromaDB for vector storage (slide similarity search)
- Redis for caching
- Celery for async tasks

**Cloud Services (Tencent Cloud):**
- COS for file storage
- TDSQL-C PostgreSQL for database
- Redis for caching
- CI (Cloud Infinite) for PPT preview

## Commands

### Backend (from `backend/` directory)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run single test file
pytest tests/unit/test_services/document_service.py -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend (from `frontend/` directory)

```bash
# Install dependencies
npm install

# Run development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Type check + build
npm run build:check

# Lint code
npm run lint

# Run unit tests
npm run test

# Run single test file
npx vitest run path/to/test.spec.ts

# Run E2E tests (requires backend running)
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Debug E2E tests
npm run test:e2e:debug

# View E2E test report
npm run test:e2e:report
```

## Architecture

### Frontend Structure

```
frontend/src/
├── api/           # API client (Axios) - one file per domain
├── components/    # Shared components (PPTViewer, Layout)
├── pages/         # Route-based pages
│   ├── Library/      # Document library management
│   ├── Outline/      # PPT outline design (smart/wizard generation)
│   ├── Assembly/     # PPT assembly from library slides
│   ├── Refinement/   # PPT page refinement with AI
│   ├── Generation/   # AI-powered PPT generation
│   └── Drafts/       # Draft management
├── stores/        # Zustand state stores (one per domain)
├── types/         # TypeScript type definitions
└── utils/         # Utility functions
```

**Key patterns:**
- Each page has its own directory with `index.tsx` and `components/` subdirectory
- State management uses Zustand stores (e.g., `outlineStore.ts`, `assemblyStore.ts`)
- API calls are centralized in `src/api/` with typed responses

### Backend Structure

```
backend/app/
├── api/v1/endpoints/   # REST API endpoints
│   ├── documents.py    # Document upload, preview, vectorization
│   ├── outline.py      # Outline generation (smart/wizard)
│   ├── assembly.py     # PPT assembly operations
│   ├── refinement.py   # Page refinement with AI
│   └── generation.py   # AI-powered PPT generation
├── models/             # SQLAlchemy database models
├── schemas/            # Pydantic request/response schemas
├── services/           # Business logic layer
│   ├── ppt_parser.py      # PPT parsing and slide extraction
│   ├── vectorization.py   # Slide embedding for similarity search
│   ├── cos_upload.py      # Tencent COS file operations
│   └── slide_recommendation.py  # Slide similarity search
├── core/               # Configuration, security, exceptions
├── db/                 # Database session and base classes
└── infrastructure/     # External services (LLM, vector DB, storage)
```

**Key patterns:**
- Endpoints are thin controllers, business logic goes in services
- Database models use SQLAlchemy with relationship definitions
- Pydantic schemas validate API input/output separately from DB models

### Data Flow

1. **Document Upload:** Frontend → `/api/documents` → Upload to COS → Parse PPT → Vectorize slides → Store in DB/ChromaDB
2. **Outline Generation:** Frontend → `/api/outlines` → LLM service → Return outline structure
3. **Assembly:** Frontend → `/api/assembly` → Search similar slides from ChromaDB → Return recommendations → Export PPT
4. **Refinement:** Frontend → `/api/refinement` → AI editing → Version management

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point, CORS config, lifespan |
| `backend/app/core/config.py` | All environment variables and settings |
| `backend/app/api/v1/__init__.py` | API router registration |
| `frontend/src/router.tsx` | React Router route definitions |
| `frontend/src/api/client.ts` | Axios instance with base URL |

## Environment Setup

1. Copy `.env.example` to `.env` in project root
2. Required for basic operation:
   - `DATABASE_URL` - SQLite for dev, PostgreSQL for production
   - `REDIS_URL` - Redis connection string
   - `COS_*` variables - Tencent Cloud COS for file storage
3. For AI features, configure at least one LLM provider:
   - `LLM_PROVIDER` - Choose: `qwen`, `openai`, `claude`, `hunyuan`
   - Corresponding API keys for the provider

## Testing Notes

- E2E tests in `frontend/e2e/` use Playwright
- The backend must be running at `http://localhost:8000` for E2E tests
- Frontend dev server starts automatically during E2E tests (configured in `playwright.config.ts`)
- Unit tests use Vitest with jsdom environment
