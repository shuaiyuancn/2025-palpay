# Project Template: Hybrid FastHTML on Windows/Podman

This document defines the operational context and workflow for this project. It serves as the primary instruction set for the Gemini Agent.

## 1. System Architecture & Environment

*   **Host OS:** Windows 11 (NTFS Filesystem).
*   **Runtime Environment:** Podman (Linux Containers) via `podman-compose`.
*   **Networking:** Host `localhost:5001` maps to Container `5001`.
*   **Codebase:** Located on Windows Host, mounted into the container at `/app`.

**Constraint:** The application code (`main.py`) runs **exclusively** inside the Podman container. The agent must NEVER attempt to run `python main.py` or `uvicorn` directly on the Windows host.

## 2. Technology Stack

*   **Language:** Python 3.12+
*   **Web Framework:** [FastHTML](https://fastht.ml/) (Hypermedia-driven UI).
*   **Database:** PostgreSQL (Production) / `psycopg2` driver.
    *   **ORM:** [FastSQL](https://github.com/AnswerDotAI/fastsql) (SQLAlchemy wrapper).
*   **Package Manager:** [uv](https://github.com/astral-sh/uv) (Managed via `pyproject.toml` and `uv.lock`).
*   **Deployment:** Vercel (Serverless).

## 3. Development Workflow

### A. dependency Management
*   The `uv.lock` file is the source of truth.
*   **To Add a Library:**
    1.  Run `uv add <package>` on the **Windows Host** (PowerShell).
    2.  Restart the container (`podman-compose restart web`) or run `uv sync` inside the container to apply changes.

### B. Running the App
*   **Start:** `podman-compose up -d`
*   **Stop:** `podman-compose down`
*   **Logs:** `podman logs -f todo_dev`
*   **Access:** Open `http://localhost:5001` in the browser.

### C. Testing
*   Tests must run **inside** the Linux container to match the production environment.
*   **Command:** `podman exec todo_dev uv run pytest`

### D. Database & Environment
*   **Local Default:** `compose.yaml` defaults to a local Postgres container (`db:5432`).
*   **Remote Testing:**
    1.  Uncomment `DATABASE_URL` in `.env`.
    2.  Set it to the remote Supabase/Postgres URL (Must start with `postgresql://`).
    3.  Restart the container.
    4.  **WARNING:** Do not commit `.env` with real credentials.

## 4. Deployment (Vercel)

*   **Config:** `vercel.json` maps the Python runtime.
*   **Command:** `vercel --prod`
*   **Environment Variables:**
    *   Set `POSTGRES_URL_NON_POOLING` in Vercel Project Settings for the database connection.
    *   Ensure the URL protocol is `postgresql://` (replace `postgres://` if copying from Supabase).

## 5. Agent Instructions

When asked to implement features:
1.  **Verify First:** Check `podman ps` to ensure the environment is active.
2.  **Edit on Host:** specific file paths `C:\workspace\...`.
3.  **Run in Container:** Use `podman exec ...` for scripts/tests.
4.  **Hypermedia First:** Prefer server-side rendering with HTMX (`hx-*` attributes) over client-side JS.
5.  **Restart on Config Change:** If `pyproject.toml` or `.env` changes, restart the container.