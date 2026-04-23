# Database Design

PostgreSQL is the source of truth.

Core tables:

```text
raw_messages
properties
hotel_deals
deal_rooms
match_attempts
rejected_deals
ai_call_logs
processing_events
app_users
audit_logs
```

## Raw Messages

`raw_messages` stores every captured Zalo message before AI processing.

Important fields:

- `source`
- `group_id`
- `group_name`
- `sender_id`
- `sender_name`
- `message_id`
- `text`
- `status`
- `processing_attempts`
- `locked_at`
- `processed_at`

## Processing Status

Allowed statuses:

```text
pending
processing
done
rejected
error
ignored
```

## Accepted Deals

`hotel_deals` stores only records that passed quality gates.

Quality fields:

- `property_id`
- `match_score`
- `verification_method`
- `property_verified`
- `ai_verified`
- `ai_verification_reason`

## Rejected Deals

`rejected_deals` stores failed matches/extractions for later review.

This keeps bad data out of `hotel_deals` while preserving enough context to debug.

## Tables Not Yet Populated

The following tables exist in the schema for future use:

- `match_attempts` — designed to log each candidate match attempt per extracted row, not yet written by the AI worker
- `ai_call_logs` — designed to log LLM API calls (provider, model, latency, errors), not yet written by the AI worker

The AI worker currently writes observability data to `processing_events` and file-based audit logs (`var/logs/`, `var/exports/`).


