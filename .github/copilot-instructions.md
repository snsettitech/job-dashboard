# Copilot Project Instructions

Purpose: Enable AI coding agents to work productively in this repo in minutes.
Keep responses concise, reference concrete files, and preserve existing patterns.

## 1. Architecture Overview
- Monorepo-style layout with duplicated CRA scaffold (`/` and `/frontend`) plus FastAPI backend at `/backend`.
- Frontend: Create React App (TypeScript) with main code in `/frontend/src/` (use this as the authoritative UI moving forward; root-level `src/` appears legacy / to be removed).
- Backend: FastAPI app. Two parallel API surfaces:
  1. Simplified implementation in `backend/main.py` (stand‑alone FastAPI with inline routes + mock + optional OpenAI usage).
  2. Modular implementation under `backend/app/` with routers (`routers/ai_routes.py`) and services (`services/`). Prefer extending the modular service-oriented version for new capabilities.
- AI / OpenAI integration encapsulated in `backend/app/services/ai_service.py` (production-style) and fallback / mock logic inside `backend/main.py` (demo mode) plus `ai_service` fallback methods.
- File ingestion & resume parsing pipeline in `backend/app/services/file_processor.py` producing structured resume analysis consumed by routes.
- Data model layer currently minimal: only pydantic models defined inline in router files. No persistent database configured yet (no ORM session management present).

## 2. Execution & Dev Workflows
Backend (modular):
```bash
cd backend
# (create / activate venv outside repo or ensure venv is gitignored)
pip install -r requirements.txt
uvicorn app.routers.ai_routes:router  # NOT correct; run full FastAPI app assembly
# Current entry script actually is main.py
python main.py
```
Notes:
- `main.py` starts a FastAPI instance directly. The modular router in `app/routers/ai_routes.py` is NOT currently mounted in `main.py`. If unifying, import and include `router`.
- OpenAI features activate when `OPENAI_API_KEY` is present in environment (`.env` or system env). Without it, mock logic returns deterministic heuristic results.

Frontend:
```bash
cd frontend
npm install
npm start
```
- Default dev server: http://localhost:3000 (CORS in backend allows all origins).
- Build with `npm run build`.

## 3. Key Conventions & Patterns
- AI calls: Always go through `AIService` for embeddings & optimization; do not call OpenAI client directly elsewhere. Maintain JSON-only responses from OpenAI chat completion (see explicit JSON schema in `ai_service.py`).
- Fallback behavior: On any OpenAI exception, return safe heuristic data (`_fallback_optimization`). New AI features must also provide graceful degradation.
- Resume processing: Use `FileProcessor.extract_text` then pass `cleaned_text` along. Preserve metadata & structured_info shape `{contact_info, skills, experience, education, sections}`.
- Scoring outputs: Maintain numeric 0–1 floats rounded to 3 decimals for similarity scores (`overall`, `skills`, `experience`, etc.).
- Endpoints returning composite objects follow the pattern in `upload_analyze_and_optimize_resume`: top-level keys: status, processing_date, file_info, original_resume, job_match_analysis, optimization, next_steps. Reuse this contract for consistency.
- Avoid fabricating user data: Prompts strictly forbid fabrication; ensure any new prompts restate honesty rule.

## 4. Adding / Modifying Backend Features
1. Put new AI or processing logic under `backend/app/services/` (create a new service file if cohesive).
2. Expose via a router in `backend/app/routers/`; group related endpoints with a shared prefix and tag.
3. Update (or create) an application factory (future improvement) or modify `main.py` to include new routers: `from app.routers import ai_routes; app.include_router(ai_routes.router)`.
4. Preserve fallback pathways; wrap network/model calls in try/except returning deterministic structures.

## 5. Frontend Consumption Expectations
- Upload endpoint expects multipart with fields: `file`, `job_description`, optional `company_name`, `job_title`.
- Optimized resume download endpoint posts `optimized_text` + `filename` and returns a text file.
- Future batch compare uses `/api/ai/batch-analyze-jobs` with `resume_text` and JSON string `job_descriptions`.

## 6. Error Handling
- Use `HTTPException` with clear user-facing `detail` messages for validation failures (length checks, unsupported file types, file too large).
- Catch broad exceptions at route boundary, log internally, return 500 with sanitized message (pattern already present).

## 7. Environment & Secrets
- `OPENAI_API_KEY` drives enhanced mode. Detect via `os.getenv` only; do not hardcode. Document required env variables in README if expanded.
- Ensure `.env` and any virtual environment directories stay out of git (update `.gitignore` if adding new secrets or artifacts).

## 8. Tech Debt / Improvement Targets (for agents)
- Consolidate duplicate CRA roots (migrate all active code to `/frontend`, remove obsolete root `src/`).
- Introduce an app factory pattern: `create_app()` to mount routers & share middlewares.
- Add tests (none present) for: file processing edge cases, AI fallback, batch analysis ranking logic.
- Extract repeated recommendation logic (`_get_match_recommendation`) into a shared utility.

## 9. Examples
Mount router in `main.py` (future):
```python
from app.routers import ai_routes
app.include_router(ai_routes.router)
```
Calling optimization inside new endpoint:
```python
service = AIService()
result = await service.optimize_resume_for_job(resume_text, job_desc, structured_info)
```

## 10. What NOT to Do
- Do not invent database persistence until schema decisions are formalized.
- Do not bypass `AIService` for OpenAI calls.
- Do not remove fallback logic or the honesty constraints in prompts.
- Do not commit large binary resumes or virtual environments.

---
Questions / gaps to clarify: (a) Preferred final backend structure (single vs modular), (b) Which CRA root to keep, (c) Testing framework preference (pytest?).
