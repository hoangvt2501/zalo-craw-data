# API

Python FastAPI backend.

Responsibility:

- Serve dashboard data.
- Handle auth/users.
- Expose deal search, review, metrics, and audit endpoints.
- Keep PostgreSQL private from dashboard users.

Current endpoints:

- `GET /health`
- `GET /metrics/summary`
- `GET /deals`
- `GET /deals/rejected`
- `GET /deals/{deal_id}`
- `GET /messages`
- `GET /messages/{raw_message_id}`
- `GET /messages/{raw_message_id}/events`
