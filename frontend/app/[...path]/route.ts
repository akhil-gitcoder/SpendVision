/** Same-origin API bridge: the browser's HttpOnly cookie stays first-party. */
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const ALLOWED_ROOTS = new Set(["auth", "transactions", "analytics", "ai", "anomalies", "health"]);
const COOKIE_NAME = "spendvision_session";

async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname.replace(/^\/api\/?/, "").split("/").filter(Boolean);
  if (!path.length || !ALLOWED_ROOTS.has(path[0]) || path.some((part) =>
    part === "." || part === ".." || part.includes("/") || part.includes("\\")
  )) {
    return NextResponse.json({ detail: "Unknown API endpoint." }, { status: 404 });
  }

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const origin = request.headers.get("origin");
  if (origin) headers.set("origin", origin);
  // Do not forward unrelated frontend cookies, browser headers or credentials.
  const session = request.cookies.get(COOKIE_NAME)?.value;
  if (session) headers.set("cookie", `${COOKIE_NAME}=${encodeURIComponent(session)}`);

  const backend = process.env.BACKEND_API_URL || "http://localhost:8000";
  const target = `${backend.replace(/\/$/, "")}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
    });
    const responseHeaders = new Headers({
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    const type = upstream.headers.get("content-type");
    if (type) responseHeaders.set("content-type", type);
    const disposition = upstream.headers.get("content-disposition");
    if (disposition) responseHeaders.set("content-disposition", disposition);
    const retryAfter = upstream.headers.get("retry-after");
    if (retryAfter) responseHeaders.set("retry-after", retryAfter);
    for (const cookie of upstream.headers.getSetCookie()) responseHeaders.append("set-cookie", cookie);
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the server. Please try again shortly." },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as HEAD };