# Local Runbook

## Local Development Order

1. Start PostgreSQL.
2. Apply migrations.
3. Start `9router`.
4. In the `9router` dashboard, connect at least one provider.
5. Start `apps/zalo-collector`.
6. Start `apps/ai-worker`.
7. Start `apps/api`.
8. Start `apps/dashboard`.

## Suggested Ports

```text
PostgreSQL: 5432
9router dashboard: 20128
9router OpenAI API: 20128
API: 8000
Dashboard: 3000
```

## One-Command Smoke Test

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\smoke-test.ps1
```

Or:

```powershell
.\scripts\maintenance\smoke-test.cmd
```

Default behavior:

- apply the initial schema migration
- reset runtime tables
- keep existing `properties`
- seed `properties` only if they are empty
- start `9router` if needed
- insert one fake raw message
- run `ai-worker` once
- print a DB summary

Useful flags:

```powershell
.\scripts\maintenance\smoke-test.ps1 -ReseedProperties
.\scripts\maintenance\smoke-test.ps1 -SkipResetRuntime
.\scripts\maintenance\smoke-test.ps1 -SkipStart9Router
```

## One-Command Real Flow

This starts the real collector and the real worker:

```powershell
.\scripts\maintenance\run-real-pipeline.cmd
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\run-real-pipeline.ps1
```

What it does:

- ensures `9router` is up
- checks that `9router` has at least one connected provider
- applies the initial schema migration
- optionally resets runtime tables
- seeds `properties` if needed
- starts `ai-worker` in the background
- starts `zalo-collector` in the current terminal for QR login

Real-flow flags:

```powershell
.\scripts\maintenance\run-real-pipeline.ps1 -ResetRuntime
.\scripts\maintenance\run-real-pipeline.ps1 -ReseedProperties
.\scripts\maintenance\run-real-pipeline.ps1 -SkipStart9Router
```

Useful companion commands:

```powershell
.\scripts\maintenance\status-real-pipeline.ps1
.\scripts\maintenance\stop-real-pipeline.ps1
```

## Start API And Dashboard

Start the API:

```powershell
.\scripts\maintenance\start-api.cmd
```

Start the dashboard:

```powershell
.\scripts\maintenance\start-dashboard.cmd
```

Notes:

- `start-api.cmd` expects local API packages under `apps/api/.packages`
- `start-dashboard.cmd` expects `apps/dashboard/node_modules`
- the dashboard defaults to `http://localhost:8000` and can be overridden with `NEXT_PUBLIC_API_BASE_URL`

## AI Worker Audit Outputs

When `apps/ai-worker` runs, it now writes four audit outputs:

- human-readable log: `var/logs/ai-worker-audit.log`
- structured JSONL log: `var/logs/ai-worker-events.jsonl`
- CSV decision export: `var/exports/ai-worker-decisions.csv`
- DB event trail: `processing_events`

What the CSV is for:

- review extracted hotel rows before they are written to `hotel_deals`
- see whether a message was ignored, rejected, or accepted
- inspect filter signals such as `has_price`, `has_hotel_kw`, `has_tour_kw`, and `is_per_person`
- inspect location mapping fields such as `location_query_norm`, `location_province_norm`, matched property province, and best-candidate score

Typical decision values:

- `ignored`: filtered out early, such as tours, flights, transport, or non-hotel messages
- `rejected`: extractor found no usable hotels, no property matched, or LLM verification rejected the candidate
- `accepted`: row is ready for `hotel_deals`

## Local Security

- Do not expose PostgreSQL to the public internet.
- Dashboard users must go through API auth.
- Keep `.env` out of git.
- Backup PostgreSQL daily with `pg_dump`.

## First Production Hardening Steps

1. Add database backups.
2. Add API authentication.
3. Add AI call logs and quota error metrics.
4. Add worker retry/backoff.
5. Add dashboard review actions.
