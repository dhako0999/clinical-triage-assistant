# Clinical Site Query Triage Assistant

A full-stack AI-assisted application designed to help a fictional clinical operations team triage incoming study-site queries, identify potential safety concerns, route queries to the appropriate team, and prepare draft responses for human review.

Built as a technical demonstration using React, TypeScript, FastAPI, PostgreSQL, and OpenAI.

## Features

- **AI classification:** Categorizes incoming study-site queries as regulatory, safety, logistics, data query, or other.
- **Escalation detection:** Determines whether a query requires human escalation.
- **Team routing:** Assigns a responsible team based on the query.
- **Draft response generation:** Uses an LLM to generate a proposed response.
- **Human-in-the-loop review:** Allows reviewers to approve, edit and approve, or reject an AI-generated draft.
- **Persistent storage:** Saves queries and review actions in PostgreSQL.
- **Safety override:** Applies deterministic keyword-based escalation checks.
- **Mock AI mode:** Supports triage without requiring OpenAI API access.
- **Live dashboard metrics:** Displays total queries, pending reviews, escalations, and completed reviews.
- **Query status filtering:** Filters queries by All, Pending Review, Approved, or Rejected.

## Screenshots

### Dashboard Overview

![Study-Site Dashboard](screenshots/dashboard-overview.png)

### Human Review Workflow

![Human Review and Safety Escalation](screenshots/human-review-workflow.png)

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- CSS

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- OpenAI API

### Database
- PostgreSQL (Supabase-hosted)

## Architecture

```text
React + TypeScript Frontend
           |
           | HTTP / REST API
           v
      FastAPI Backend
           |
           +----> OpenAI LLM or Mock Triage
           |             |
           |             v
           |      Safety Override
           |
           +----> PostgreSQL Database
           |
           +----> Human Review Workflow
```

The frontend communicates with FastAPI through REST endpoints. The backend performs AI triage, applies a safety escalation rule, persists results, and processes reviewer decisions.

## Application Workflow

1. A user enters a study-site identifier and free-text query.

2. FastAPI sends the query to the configured AI triage service.

3. The AI returns a category, escalation decision, assigned team, and draft response.

4. A deterministic safety check can override the classification and escalation decision.

5. The query is stored in PostgreSQL with a `pending_review` status.

6. A human reviewer can approve the original response, edit and approve it, or reject it.

7. The review action is recorded, and any approved final response is available in the dashboard.

**Important:** This demonstration does not automatically send responses to study sites or notify assigned teams. Routing represents an internal assignment recommendation.

## Running Locally

### Backend

From the project root:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` using `backend/.env.example` as a template. Configure a PostgreSQL connection and choose an AI mode.

```dotenv
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE
AI_MODE=mock
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=your_openai_api_key_here
```

For OpenAI mode, set `AI_MODE=openai` and provide a valid API key.

### Initialize the Database

After configuring the PostgreSQL connection, create the database tables:

```bash
python init_db.py
```

This command creates missing tables defined by the SQLAlchemy models without deleting existing records. It does not perform schema migrations.

### Start the Backend

```bash
uvicorn app.main:app --reload
```

Backend API: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

### Frontend

Open a second terminal from the project root and run:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

Vite proxies requests beginning with `/api` to the FastAPI backend.

## Testing

The project includes automated backend tests covering AI triage behavior, safety escalation rules, and the human review workflow.

### Backend Tests

From the `backend` directory, with the Python virtual environment activated:

```bash
python -m pytest tests/ -v
```

The current test suite includes eight tests covering:

- AI classification and mock triage behavior.
- Safety keyword detection and escalation overrides.
- Regression testing for safety keyword word boundaries.
- Human review status transitions and duplicate-review prevention.

The review workflow test uses an isolated SQLite test database rather than the production PostgreSQL database.

### Frontend Production Build

From the `frontend` directory:

```bash
npm run build
```

This runs TypeScript build checks and generates optimized production assets using Vite.


## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check backend health |
| POST | `/api/queries` | Submit and triage a new query |
| GET | `/api/queries` | Retrieve submitted queries |
| GET | `/api/queries/{id}` | Retrieve query details and review history |
| POST | `/api/queries/{id}/review` | Approve, edit, or reject a draft |

## Safety and Human Oversight

The application is designed around human review rather than autonomous clinical decision-making.

AI-generated responses remain drafts until reviewed.

Safety-related keywords trigger a deterministic escalation override.

The original AI draft is retained even when a reviewer edits the response.

Review decisions are stored for traceability.

The AI is instructed not to provide medical advice or claim that an action has already occurred.

The keyword-based safety override is a demonstration safeguard, not a comprehensive clinical safety detection system. The application is not validated for real clinical operations or patient data.

## Reliability, Monitoring, and Model Drift

In a production implementation, I would introduce:

Structured logging: Capture request IDs, processing time, AI model version, classification results, and errors while avoiding sensitive query content in logs.

Operational metrics: Track request volume, latency, API failures, and AI processing failures.

Quality metrics: Measure classification accuracy, escalation recall, human override frequency, and draft rejection rates.

Drift monitoring: Compare classification and escalation patterns over time, and evaluate a labeled test dataset after model or prompt changes.

Uncertainty handling: Flag ambiguous or low-confidence results for manual triage rather than automatically trusting the model.

Fallback handling: Return clear errors for AI or database failures and consider retry policies for transient failures.

The current demonstration includes basic error handling and persisted review actions. The monitoring and drift-detection capabilities above are proposed production enhancements, not fully implemented features.

## Production Considerations

Before deploying a system like this in a real clinical environment, additional work would be required:

Authentication and role-based access control

Stronger validation and escalation rules

Formal clinical safety review and evaluation

Privacy protections and secure handling of sensitive information

Comprehensive audit trails

Observability and alerting

Expanded automated test coverage and CI/CD deployment pipelines

Human-reviewed notification and response delivery integrations

## Project Scope

This project demonstrates a working AI-assisted clinical query triage workflow with persistent storage and human oversight. It is intended for technical evaluation using fictional study-site data, not production clinical use.