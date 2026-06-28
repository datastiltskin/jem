# JEM — LinkedIn sign-in setup

JEM uses **Sign In with LinkedIn using OpenID Connect** for researcher accounts (correction proposals, upvotes, admin queue). Dev mock login remains available when `JEM_AUTH_MODE=dev`.

---

## 1. Create a LinkedIn app

1. Open [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps) → **Create app**.
2. Fill in app name, LinkedIn Page, and logo (required by LinkedIn).
3. Go to **Products** → request **Sign In with LinkedIn using OpenID Connect** (approval is usually immediate for dev apps).
4. Go to **Auth** → **Authorized redirect URLs for your app** and add:

   ```
   http://127.0.0.1:8001/api/v1/auth/linkedin/callback
   ```

   For production, add your HTTPS URL with the same path, e.g.:

   ```
   https://friedso.com/api/v1/auth/linkedin/callback
   ```

5. Copy **Client ID** and **Client Secret** from the **Auth** tab.

The redirect URL must match `JEM_BASE_URL` + `/api/v1/auth/linkedin/callback` exactly (scheme, host, port, path).

---

## 2. Configure local environment

```bash
cd jem
cp .env.example .env   # skip if .env already exists
```

Edit `jem/.env`:

| Variable | Value |
|----------|--------|
| `JEM_BASE_URL` | `http://127.0.0.1:8001` (must match uvicorn port) |
| `LINKEDIN_CLIENT_ID` | From LinkedIn Auth tab |
| `LINKEDIN_CLIENT_SECRET` | From LinkedIn Auth tab |
| `JEM_SESSION_SECRET` | Random string (cookie signing) |
| `JEM_MAINTAINER_OAUTH_SUBS` | Optional — LinkedIn `sub` IDs that get `maintainer` on first login |

The API loads `.env` automatically on startup (`python-dotenv` in `api/main.py`).

---

## 3. Run and verify

```bash
cd jem
pip install -r scripts/requirements-dev.txt
python scripts/migrate_schema.py   # if users table not yet applied
python3 -m uvicorn api.main:app --reload --port 8001
```

Check configuration:

```bash
curl -s http://127.0.0.1:8001/api/v1/auth/providers | jq .
```

Expected when configured:

```json
{
  "mode": "dev",
  "linkedin": true,
  "dev_login": true,
  "linkedin_login_url": "/api/v1/auth/linkedin/login"
}
```

Open `http://127.0.0.1:8001/api/v1/auth/linkedin/login` — you should be redirected to LinkedIn (not a 503 JSON error).

After login, the callback sets a session cookie and redirects to `/admin/`.

---

## 4. Map UI (static web)

The map at `jem/web/` points at the API via `web/public/api-config.js`:

```js
window.JEM_API_BASE = 'http://127.0.0.1:8001/api/v1';
```

Serve the map separately:

```bash
cd jem/web && python3 -m http.server 8080
```

The **Sign in with LinkedIn** link on correction proposals uses that API base.

---

## 5. Dev login (no LinkedIn)

When `JEM_AUTH_MODE=dev`, you can sign in without OAuth:

```bash
curl -s -X POST http://127.0.0.1:8001/api/v1/auth/dev/login \
  -H 'Content-Type: application/json' \
  -d '{"display_name":"Local Dev","sub":"dev1"}' \
  -c cookies.txt
```

Use the `jem_session` cookie for subsequent requests.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `LinkedIn OAuth not configured` | Set both `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` in `.env`; restart uvicorn |
| `redirect_uri doesn't match` | LinkedIn redirect URL must exactly match `{JEM_BASE_URL}/api/v1/auth/linkedin/callback` |
| `Invalid OAuth state` | State is in-memory; restart clears it — start login again from `/auth/linkedin/login` |
| Login works but map shows sign-in | Ensure `JEM_API_BASE` matches API port; check browser cookies / CORS |
| Need maintainer on admin | Set your LinkedIn `sub` in `JEM_MAINTAINER_OAUTH_SUBS` before first login, or promote via admin UI |

To find your LinkedIn `sub` after first login: query `users` in `jem.db` or call `GET /api/v1/auth/me` while signed in.
