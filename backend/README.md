# FounderOS AI — Backend

Production-style FastAPI backend for the FounderOS AI platform.

## Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── generations.py   # POST /generate/prd|roadmap|architecture
│   │       │   ├── workflows.py     # POST /workflows/analyze
│   │       │   └── health.py        # GET  /health
│   │       └── router.py            # Mounts all v1 endpoints
│   ├── core/
│   │   ├── config.py        # pydantic-settings (reads env vars)
│   │   ├── dependencies.py  # OpenAI + Supabase client singletons
│   │   ├── errors.py        # Global exception handlers
│   │   └── logging.py       # Structured logging setup
│   ├── db/
│   │   └── supabase_schema.sql  # Run in Supabase SQL editor
│   ├── models/
│   │   ├── common.py        # APIResponse, PaginatedResponse, ErrorResponse
│   │   ├── generation.py    # PRD/Roadmap/Architecture request+response models
│   │   └── workflow.py      # WorkflowRun, WorkflowStep, FullStartupAnalysis models
│   ├── services/
│   │   ├── openai_service.py      # GPT calls with fallback model support
│   │   ├── supabase_service.py    # DB read/write helpers
│   │   └── generation_service.py  # Orchestrates AI + persistence
│   ├── workflows/
│   │   ├── base.py                # BaseWorkflow with step tracking
│   │   └── startup_analysis.py    # PRD → (Roadmap ∥ Architecture) → Persist
│   └── main.py              # FastAPI app, CORS, router registration
├── .env.example
├── requirements.txt
└── README.md
```

## Running

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health + integration status |
| POST | `/api/v1/generate/prd` | Generate Product Requirements Doc |
| POST | `/api/v1/generate/roadmap` | Generate phased Product Roadmap |
| POST | `/api/v1/generate/architecture` | Generate System Architecture |
| POST | `/api/v1/workflows/analyze` | Full analysis: PRD + Roadmap + Architecture in one call |

## Database Setup

Run `app/db/supabase_schema.sql` in your Supabase SQL editor to create the `generations` and `workflow_runs` tables with RLS policies.
