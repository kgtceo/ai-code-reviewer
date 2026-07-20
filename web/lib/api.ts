import type { ReviewResult } from "./types";

// Strip any trailing slash so `${API_URL}/api/...` never becomes `...//api/...` (404).
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export async function review(input: {
  diff?: string;
  pr?: string;
}): Promise<ReviewResult> {
  const res = await fetch(`${API_URL}/api/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}
