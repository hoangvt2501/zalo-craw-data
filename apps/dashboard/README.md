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

- the dashboard now proxies all browser requests through `src/app/api/[...path]/route.js`
- browser code always calls same-origin `/api/...`, so public deploys do not need direct CORS to the API
- set `INTERNAL_API_BASE_URL` for the dashboard runtime:
  - local dev: `http://127.0.0.1:8000`
  - Cloudflare tunnel / public API: `https://xxxxx.trycloudflare.com`
- optional: set `API_PROXY_TOKEN` and validate `X-Internal-Token` in the API if you want a shared secret between dashboard and backend
- if API loading fails, the UI still keeps JSON/JSONL upload support for manual review
