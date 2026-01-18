import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const backendUrl = "http://127.0.0.1:8000/chat/stream";

    const res = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      // forward the client's abort signal so upstream work can be cancelled
      // when the browser aborts the request
      signal: (request as Request).signal,
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        { error: "upstream_error", details: errText },
        { status: res.status },
      );
    }

    // Forward the raw streaming body from the backend to the client.
    const contentType =
      res.headers.get("content-type") || "text/plain; charset=utf-8";
    const bodyStream = res.body;

    return new NextResponse(bodyStream, {
      status: res.status,
      headers: { "Content-Type": contentType },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "proxy_error", details: String(err) },
      { status: 500 },
    );
  }
}
