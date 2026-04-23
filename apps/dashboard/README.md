# Dashboard

Web dashboard for multiple users.

Responsibility:

- Deal list/search/filter.
- Rejected deal review.
- Metrics.
- User-facing workflow.

The dashboard must call `apps/api`; it should not access PostgreSQL directly.

Current folder split:

- `prototypes/`: preserved standalone HTML concepts and visual references
- `src/app/`: Next.js entrypoints and global styles
- `src/components/`: interactive dashboard UI
- `src/lib/`: sample data and view-layer helpers

Runtime notes:

- the dashboard now loads live data from the API by default
- set `NEXT_PUBLIC_API_BASE_URL` if the API is not running at `http://localhost:8000`
- if API loading fails, the UI falls back to sample data and keeps JSON/JSONL upload support
