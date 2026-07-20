"use client";

import { useState } from "react";
import { review } from "@/lib/api";
import type { ReviewResult } from "@/lib/types";

const EXAMPLE_DIFF = `diff --git a/api/users.py b/api/users.py
--- a/api/users.py
+++ b/api/users.py
@@ -12,6 +12,14 @@ from .db import get_connection
 def get_user(user_id):
     conn = get_connection()
     cur = conn.cursor()
-    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
+    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
+    cur.execute(query)
     row = cur.fetchone()
     return {"id": row[0], "email": row[1]}`;

export default function Home() {
  const [diff, setDiff] = useState("");
  const [pr, setPr] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewResult | null>(null);

  async function onReview() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await review(pr.trim() ? { pr: pr.trim() } : { diff }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = (pr.trim().length > 3 || diff.trim().length > 20) && !loading;

  return (
    <div className="container">
      <header>
        <h1>ai-code-reviewer</h1>
        <p>
          Paste a diff (or a public GitHub PR link) and get a review focused on{" "}
          <strong>real bugs + security issues, not style</strong>. Every finding is
          tied to a line the diff actually changed.
        </p>
      </header>

      <label htmlFor="pr">Public GitHub PR (optional)</label>
      <input
        id="pr"
        type="text"
        value={pr}
        onChange={(e) => setPr(e.target.value)}
        placeholder="owner/repo#123  or  https://github.com/owner/repo/pull/123"
      />
      <label htmlFor="diff">…or paste a unified diff</label>
      <textarea id="diff" value={diff} onChange={(e) => setDiff(e.target.value)} />

      <div className="actions">
        <button onClick={onReview} disabled={!canSubmit}>
          {loading ? "Reviewing…" : "Review"}
        </button>
        <button
          className="ghost"
          onClick={() => {
            setPr("");
            setDiff(EXAMPLE_DIFF);
          }}
          disabled={loading}
        >
          Load example
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}
      {result && <Result result={result} />}
    </div>
  );
}

function Result({ result }: { result: ReviewResult }) {
  const { review: r, changed_line_count } = result;
  return (
    <>
      <section className="panel">
        <h2>Summary</h2>
        <p>{r.summary}</p>
        <p style={{ color: "var(--muted)", fontSize: 13 }}>
          {r.findings.length} finding{r.findings.length === 1 ? "" : "s"} across{" "}
          {changed_line_count} changed line{changed_line_count === 1 ? "" : "s"}.
        </p>
      </section>

      {r.findings.length === 0 ? (
        <section className="panel">
          <p style={{ color: "var(--good)" }}>No issues found on the changed lines.</p>
        </section>
      ) : (
        <section className="panel">
          <h2>Findings</h2>
          {r.findings.map((f, i) => (
            <div className="finding" key={i}>
              <div>
                <span className={`sev ${f.severity}`}>{f.severity}</span>
                <span style={{ color: "var(--muted)" }}>{f.category}</span> ·{" "}
                <span className="loc">
                  {f.file}:{f.line}
                </span>
              </div>
              <div className="snip">{f.snippet}</div>
              <div>{f.issue}</div>
              <div className="fix">→ {f.suggestion}</div>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
