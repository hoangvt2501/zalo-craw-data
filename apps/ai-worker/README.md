# AI Worker

Python service.

Responsibility:

- Poll `raw_messages` from PostgreSQL.
- Filter/dedup messages.
- Extract hotel deals through `9router` or another OpenAI-compatible LLM gateway.
- Match extracted hotels against `properties`.
- Verify medium-confidence property matches with LLM.
- Write accepted deals or rejected logs.

This is where most business processing belongs.

## Current MVP Behavior

The worker reads `raw_messages` with `status = 'pending'` from PostgreSQL.

For each message:

1. Claim job with `FOR UPDATE SKIP LOCKED`.
2. Run rule-based pre-filter.
3. If filter fails, write `rejected_deals` and mark raw message `ignored`.
4. If filter passes, call the LLM extractor through `9router`.
5. Match extracted hotel against `properties`.
6. If score is `0.4 - 0.7`, call LLM verifier.
7. Write accepted deals to `hotel_deals` and rooms to `deal_rooms`.
8. Write failed candidates to `rejected_deals`.
9. Mark raw message `done`, `rejected`, `ignored`, or `error`.

## Setup

Python is required. Recommended version: Python 3.11 or 3.12.

Run from this folder:

```powershell
cd C:\Users\Admin\Desktop\hotel-intel\hotel-intel-pipeline\apps\ai-worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Local LLM Gateway

Current local default:

- `9router` dashboard: `http://localhost:20128/dashboard`
- OpenAI-compatible API: `http://127.0.0.1:20128/v1`

Typical local startup:

```powershell
npm install -g 9router
9router
```

Then in the `9router` dashboard:

1. Open `Providers`.
2. Connect at least one provider account.
3. Copy or set the model IDs you want the worker to use.

Current `.env` defaults in this repo:

```env
CLIPPROXYAPI_BASE_URL=http://127.0.0.1:20128/v1
CLIPPROXYAPI_API_KEY=local-9router
EXTRACTOR_MODEL=gc/gemini-3-flash-preview
VERIFIER_MODEL=gc/gemini-3-flash-preview
```

Important:

- `9router` must have at least one active provider connection before the worker can process LLM-backed messages.
- If no provider is connected, the worker will fail with a provider-credentials error from `9router`.

## Seed Property DB

Before matching can work, import the current hotel CSV into PostgreSQL:

```powershell
python scripts\seed_properties_from_csv.py
```

This reads:

```text
C:\Users\Admin\Desktop\hotel-intel\services\data\hotels.csv
```

and upserts rows into table `properties`.

## Run One Batch

```powershell
python -m app.main --once --limit 5
```

## Run Continuously

```powershell
python -m app.main
```

The worker reads config from:

```text
C:\Users\Admin\Desktop\hotel-intel\hotel-intel-pipeline\.env
```
