# Deploy

Backend (FastAPI) → **Railway**; frontend (Next.js in `web/`) → **Vercel**. Push to
GitHub first.

## Backend → Railway
1. New Project → Deploy from GitHub repo → `ai-code-reviewer`. Uses the `Dockerfile`.
2. **Variables:** `ANTHROPIC_API_KEY` (+ `REVIEWER_CORS_ORIGINS` = your custom domain
   if you attach one; the `*.vercel.app` URL is already allowed by regex).
3. Settings → **Networking → Generate Domain**. Set the domain's target port to the
   one in the deploy logs (`Uvicorn running on http://0.0.0.0:XXXX`).
4. `GET /health` → `{"ok":true,"configured":true}`.

## Frontend → Vercel
1. Import `ai-code-reviewer`, **Root Directory = `web`**.
2. Env var `NEXT_PUBLIC_API_URL` = the Railway URL.
3. Deploy. Optionally attach `reviewer.kareemghazal.com` and add it to `REVIEWER_CORS_ORIGINS`.
