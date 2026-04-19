# Phase 4 — Frontend Delivery & API Client

**Prerequisites:** [Phase 3 — HTTP API](phase-3-api.md) complete. All four API endpoints must respond correctly under `TestClient`.

**Phase Goal:** Make the app actually runnable in the browser. Mount `frontend/` as static files, land the PowerShell launcher so `.\run.ps1` starts Uvicorn, and add the fetch-based API client module the components will use in Phase 5.

**Completion Criteria:**
- `pytest tests/test_api.py -v` shows 10 PASSED (9 from Phase 3 + new `test_root_serves_frontend_index`)
- `.\setup.ps1` completes without error and produces `frontend/vendor/vue.esm-browser.prod.js`
- `.\run.ps1` starts Uvicorn without error, `http://127.0.0.1:8765/api/health` returns `{"status":"ok"}`, and the placeholder HTML renders at `/`
- From the browser DevTools console, `(await import("/api.js")).api.getSession()` resolves successfully

**Next Phase:** [Phase 5 — Frontend Components](phase-5-frontend-components.md)

---

## Task 10: Static Frontend Mount

**Files:**
- Modify: `backend/main.py`
- Create: `frontend/index.html` (minimal placeholder)

- [ ] **Step 1: Create a placeholder frontend page**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Boardroom</title>
</head>
<body>
  <div id="app">AI Boardroom — loading…</div>
</body>
</html>
```

- [ ] **Step 2: Add a failing test that the root serves HTML**

Append to `tests/test_api.py`:

```python
def test_root_serves_frontend_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI Boardroom" in resp.text
    assert resp.headers["content-type"].startswith("text/html")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_root_serves_frontend_index -v`
Expected: FAIL (404).

- [ ] **Step 4: Mount frontend in main.py**

Modify `backend/main.py` — replace the body of `create_app()` with:

```python
def create_app() -> FastAPI:
    storage.init_storage(PROJECT_ROOT)
    app = FastAPI(title="AI Boardroom", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: 9 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py frontend/index.html tests/test_api.py
git commit -m "feat: serve frontend directory as static files"
```

---

## Task 11: Setup and Run Scripts

Setup is a one-time (or on-dependency-change) concern — venv creation, `pip
install`, Playwright browser install, and vendoring the Vue runtime. Runtime
is a fast-path: activate venv, start Uvicorn. Keeping them separate makes
failures easier to localize and cuts startup from seconds to sub-second.

**Files:**
- Create: `setup.ps1`
- Create: `run.ps1`

- [ ] **Step 1: Create `setup.ps1`**

Create `setup.ps1`:

```powershell
# AI Boardroom one-time setup
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium

# Vendor Vue 3 so the app does not depend on a CDN at runtime.
$VendorDir = ".\frontend\vendor"
$VueFile   = "$VendorDir\vue.esm-browser.prod.js"
if (-not (Test-Path $VueFile)) {
    New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
    Write-Host "Downloading Vue 3 runtime..."
    Invoke-WebRequest `
        -Uri "https://unpkg.com/vue@3.4.38/dist/vue.esm-browser.prod.js" `
        -OutFile $VueFile
}

Write-Host "Setup complete. Run .\run.ps1 to start the app."
```

- [ ] **Step 2: Create `run.ps1`**

Create `run.ps1`:

```powershell
# AI Boardroom runtime launcher
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Error "No .venv found. Run .\setup.ps1 first."
    exit 1
}

& .\.venv\Scripts\Activate.ps1

Write-Host "Starting AI Boardroom on http://$ListenHost`:$Port"
uvicorn backend.main:app --host $ListenHost --port $Port --reload
```

- [ ] **Step 3: Manual smoke check**

Run (PowerShell, from project root):
```powershell
.\setup.ps1
.\run.ps1
```

Expected:
- `setup.ps1` installs deps, Playwright browser, and `frontend/vendor/vue.esm-browser.prod.js` (~60 KB).
- `run.ps1` starts Uvicorn, prints "Application startup complete."
- `http://127.0.0.1:8765/api/health` returns `{"status":"ok"}`.
- `http://127.0.0.1:8765/` returns the placeholder HTML.

Press Ctrl+C to stop.

- [ ] **Step 4: Commit**

```bash
git add setup.ps1 run.ps1
git commit -m "chore: split setup and run scripts; vendor Vue via setup"
```

---

## Task 12: Frontend API Client

**Files:**
- Create: `frontend/api.js`

- [ ] **Step 1: Write the API client**

Create `frontend/api.js`:

```javascript
const JSON_HEADERS = { "Content-Type": "application/json", Accept: "application/json" };

async function request(path, init = {}) {
  const resp = await fetch(path, init);
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${init.method || "GET"} ${path} failed: ${resp.status} ${body}`);
  }
  return resp.json();
}

export const api = {
  getSession: () => request("/api/session"),
  getParticipants: () => request("/api/participants"),
  getMessages: () => request("/api/messages"),
  postMessage: (message) =>
    request("/api/messages", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(message),
    }),
};
```

- [ ] **Step 2: Manual console smoke check**

Start the server (`.\run.ps1`). Open `http://127.0.0.1:8765/` in Chrome. Open DevTools console and run:

```javascript
const { api } = await import("/api.js");
await api.getSession();
await api.getParticipants();
```

Expected: both calls resolve and print objects.

- [ ] **Step 3: Commit**

```bash
git add frontend/api.js
git commit -m "feat: frontend API client module"
```
