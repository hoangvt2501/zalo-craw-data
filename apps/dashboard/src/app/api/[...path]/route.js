export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "transfer-encoding",
]);

function trimOrigin(origin) {
  return String(origin || "").replace(/\/+$/, "");
}

function getUpstreamOrigin() {
  return trimOrigin(
    process.env.INTERNAL_API_BASE_URL ||
    process.env.API_PROXY_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.PUBLIC_API_BASE_URL ||
    "http://127.0.0.1:8000",
  );
}

function buildUpstreamUrl(pathSegments, requestUrl) {
  const origin = getUpstreamOrigin();
  const path = Array.isArray(pathSegments) ? pathSegments.join("/") : "";
  const upstreamUrl = new URL(`${origin}/${path}`);
  upstreamUrl.search = new URL(requestUrl).search;
  return upstreamUrl.toString();
}

function buildUpstreamHeaders(request) {
  const headers = new Headers();

  for (const [key, value] of request.headers.entries()) {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  }

  const proxyToken = process.env.API_PROXY_TOKEN || process.env.INTERNAL_API_TOKEN;
  if (proxyToken) {
    headers.set("X-Internal-Token", proxyToken);
  }

  return headers;
}

function buildResponseHeaders(upstream) {
  const headers = new Headers();
  const allowedHeaders = [
    "cache-control",
    "content-type",
    "etag",
    "last-modified",
  ];

  for (const key of allowedHeaders) {
    const value = upstream.headers.get(key);
    if (value) {
      headers.set(key, value);
    }
  }

  return headers;
}

async function proxyRequest(request, context) {
  const params = await Promise.resolve(context.params);
  const pathSegments = params?.path || [];
  const upstreamUrl = buildUpstreamUrl(pathSegments, request.url);
  const requestInit = {
    method: request.method,
    headers: buildUpstreamHeaders(request),
    cache: "no-store",
    redirect: "manual",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    requestInit.body = await request.arrayBuffer();
  }

  let upstream;
  try {
    upstream = await fetch(upstreamUrl, requestInit);
  } catch (error) {
    return Response.json(
      {
        detail: "Dashboard API proxy could not reach upstream API",
        upstream: upstreamUrl,
        error: String(error?.message || error),
      },
      { status: 502 },
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: buildResponseHeaders(upstream),
  });
}

export async function GET(request, context) {
  return proxyRequest(request, context);
}

export async function POST(request, context) {
  return proxyRequest(request, context);
}

export async function PUT(request, context) {
  return proxyRequest(request, context);
}

export async function PATCH(request, context) {
  return proxyRequest(request, context);
}

export async function DELETE(request, context) {
  return proxyRequest(request, context);
}
