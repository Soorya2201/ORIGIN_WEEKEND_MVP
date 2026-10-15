# Clarity Health — lab-results ingestion and health insights backend

**A weekend MVP: upload a photo or PDF of lab results, extract structured analytes with Gemini Vision, redact PII, and turn the results into rule-based health insights and a clinician summary.**

## Pipeline

```
lab image / PDF ─► PII redaction ─► Gemini Vision extraction (Jinja prompt) ─► post-processing
                                                                                │  normalize analyte names & units,
                                                                                │  attach reference ranges → normal/high/low
                                                                                ▼
                                           Postgres (JSON "data lake") ─► rule-based insights ─► LLM clinician summary
```

| Stage | Code |
|---|---|
| Extraction prompt | `backend/prompts/vision_extract_labs.md.j2` |
| Gemini extraction | `backend/app/ingest/gemini_extract.py` |
| PII redaction | `backend/app/ingest/redactor.py` |
| Normalization and reference ranges | `backend/app/ingest/postprocess.py` |
| Deterministic insights | `backend/app/insights/rules.py` |
| Clinician summary | `backend/app/insights/llm_summary.py`, `backend/prompts/clinician_summary.md.j2` |
| Health scores (sleep, hydration, nutrition, activity) | `backend/app/services/health_assessment.py` |
| Context-aware health chat | `backend/app/services/chat_service.py` |
| Audit logging | `backend/app/observability/audit.py` |

## API (FastAPI)

- `POST /labs/ingest_from_media` uploads and extracts a lab report
- `POST /insights/run` and `POST /insights/summaries/clinician` generate insights and the clinician summary
- `/mvp/users`, `/mvp/dashboard/{user_id}`, `/mvp/health-assessments`, `/mvp/wearables` (sync is mocked in this MVP), `/mvp/chat/*`, `/mvp/data-lake`
- `GET /admin/healthz`, `/admin/envcheck`, `/admin/gemini_check`

Full endpoint and schema docs: [`backend/README.md`](backend/README.md) and [`backend/README_MVP.md`](backend/README_MVP.md).

## Stack

FastAPI · SQLAlchemy 2 + Alembic · PostgreSQL · Celery + Redis · Pydantic v2 · Google Gemini · Docker Compose · pytest (unit, integration, e2e)

## Run

Requires Python 3.11+, Docker, and a Google Gemini API key.

```bash
cd backend
./start -local      # creates a venv, installs deps, prompts for GEMINI_API_KEY,
                    # starts Postgres + Redis, runs migrations, serves on :8000
```

API docs are served at http://127.0.0.1:8000/docs. Tests: `make test` (or `make test-full` for the end-to-end run). `./test_workflow.sh` from the repo root uploads `sample_lab_results.png` end to end.

> The React frontend described in `demo.md` is not included in this repository; this repo is the backend.
