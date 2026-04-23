# Architecture

## Core Decision

Use a local PostgreSQL database as the system of record and durable job queue.

The collector must be thin. It captures Zalo messages and writes raw data. The AI worker owns all expensive and failure-prone processing.

## Service Boundaries

```text
apps/zalo-collector
  Owns Zalo listening and raw message capture.

apps/ai-worker
  Owns extraction, matching, verification, and accepted/rejected writes.

apps/api
  Owns dashboard-facing HTTP API, auth, and review actions.

apps/dashboard
  Owns user interface only.

infra/postgres
  Owns database migrations and local infrastructure.
```

## Dependency Direction

```text
domain
  Pure rules and entities.

application
  Use cases. Calls ports. Does not know concrete infrastructure.

ports
  Interfaces/contracts for repositories, gateways, queues, writers.

infrastructure
  PostgreSQL, Zalo, 9router or another LLM gateway, file system, HTTP clients.

main/interface
  Composition root. Wires config and concrete implementations.
```

## Important Policies

Property verification policy:

```text
no property match       -> reject
score < 0.4             -> reject
0.4 <= score <= 0.7     -> LLM verifier true/false
score > 0.7             -> accept as high confidence
```

Verifier failure policy:

```text
AI_VERIFY_FAIL_OPEN=false
```

Meaning: if the verifier fails, do not accept medium-confidence records.

## Why Not Direct JSONL As Final Storage

JSONL is useful for audit and replay, but it is not enough for a multi-user dashboard.

PostgreSQL is needed for:

- Search/filter.
- Review workflow.
- User access.
- Metrics.
- Dedup/idempotency.
- Backfill.
- Audit trail.
