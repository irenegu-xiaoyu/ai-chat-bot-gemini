import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    // Use an env var for backend URL in production; default to local FastAPI dev server
    const backendUrl = process.env.API_URL || "http://127.0.0.1:8000/chat";

    const res = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json(
      { error: "proxy_error", details: String(err) },
      { status: 500 }
    );
  }
}
