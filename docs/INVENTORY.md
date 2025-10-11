# Codebase Inventory – Gata Haystack

This document captures the current state of the repository as a baseline for a rewrite. It summarizes structure, purpose, configuration, routes, models, and notable gaps.

## Purpose
- FastAPI application that wraps UiPath Automation Cloud (Orchestrator) APIs.
- Minimal HTML frontend to drive OAuth2 Authorization Code flow and render basic resources.

## Entry Points
- `uipathcloud/main.py`
  - Creates `FastAPI` app, mounts static files, sets up templates.
  - Includes routers: tenants, packages, libraries, machines, processes, assets, folders, oauth2_uipath, rnd_loop.
  - Routes:
    - `GET /` renders `templates/index.html` with masked settings.
    - `GET /info` returns application settings (masked) via dependency.
    - `GET /favicon.ico` serves `favicon.ico` from repo root.
  - OAuth-related middleware exists but is commented out.

## Configuration
- `uipathcloud/config.py`
  - `Settings` via `pydantic-settings` reads `.uipathcloud.env`.
  - Key fields: `uipathcloud_baseurl`, `uipathcloud_authorization_endpoint`, `uipathcloud_token_endpoint`, `uipathcloud_organizations: List[Organization]`.
  - `mask_sensitive_data()` masks client secrets and token values in nested structures.
  - Note: Debug prints on import output masked settings to stdout.

- README env guidance
  - `.uipathcloud.env` must define `UIPATHCLOUD_ORGANIZATIONS` as JSON: array of orgs → applications with OAuth credentials, scope, redirect URL, and grant types.

## OAuth2 Flow
- `uipathcloud/routers/oauth2_uipath.py`
  - `GET /oauth2_uipath/request_access_token_with_clientid` constructs authorize URL from the first configured org/app and redirects.
  - Callback handler (present in file) exchanges `code` for token against `uipathcloud_token_endpoint` and computes expiry.
  - `update_access_token(settings, org, app, token_data)` updates/inserts token by `grant_type` in `settings.uipathcloud_organizations`.
  - `GET /oauth2_uipath/debug` returns settings via dependency.

- Middleware (not enabled in `main.py`)
  - `uipathcloud/middleware/oauth2a.py`: Client Credentials flow; stores token and expiry; attaches `request.state.access_token`.
  - `uipathcloud/middleware/oauth2_uipath.py`: Similar pattern (variable names prefixed `appl_`).

## Routers
- `uipathcloud/routers/machines.py`
  - `GET /uipathcloud/machines` uses `settings.uipathcloud_organizations[0].applications[0].access_tokens[0]` to call Orchestrator `odata/Machines`.
  - Currently hardcodes org/tenant path `cprimadotnet/homelab23` in the URL.
  - Returns JSON (stringifying UUIDs) or renders `templates/machines.html`.
  - Other CRUD endpoints are stubs.

- `uipathcloud/routers/rnd_loop.py`
  - `GET /uipathcloud/loop` discovers tenants and fetches Machines, Folders (and per-folder Processes), Packages (Releases), and Libraries per tenant.
  - Updates `settings.uipathcloud_organizations[i].tenants` with parsed Pydantic models.
  - Renders `templates/test.html` or returns JSON.

- Other routers: `tenants.py`, `packages.py`, `libraries.py`, `assets.py`, `folders.py`, `processes.py`
  - Provide list endpoints with dummy data and CRUD stubs.

## Data Models
- `uipathcloud/models/uipathcloud.py`
  - OAuth/Config: `Organization`, `Application`, `AccessToken`, `TokenInfo`, `UiPathCloudOauth2`.
  - Orchestrator resources: `Machine`, `Library`, `Process`, `Folder`, `Tenant`, `Feed`, and helper models.
  - `VALID_GRANT_TYPES = ["authorization_code", "client_credentials", "refresh_token"]` with validators.
  - Some optional fields and `Any` types where API shape is flexible or unspecified.

## Utilities & Dependencies
- `uipathcloud/common.py`
  - `SecureDumpModel` masks `client_id` and `client_secret` recursively in models/dicts.
  - `Tags` enum used for tagging routes (limited use).

- `uipathcloud/dependencies.py`
  - Simple header and query token guards (not wired into main app).

## Templates & Static
- Templates: `templates/base.html`, `index.html`, `machines.html`, `test.html`.
  - `base.html` provides header, nav to Auth/Deauth/Swagger/UiPath Cloud/debug, footer, and loads `static/css/style.css`.
- Static: `static/css/style.css` (Solarized Light theme), `static/js/script.js`.

## Requirements
- `requirements.txt`: fastapi, uvicorn, jinja2, httpx, pydantic>=2.3.0, pydantic-settings, python-dotenv, authlib>=1.3.0, itsdangerous, email-validator.

## Tests
- `tests/` exists but is empty; no automated tests.

## Notable Gaps / Risks
- Hardcoded org/tenant in `machines.py`.
- Tokens are stored in-memory; not persisted across restarts.
- OAuth2 state is a deterministic hash; no per-session state storage/validation.
- Callback route path is implicit; README does not document the exact callback endpoint expected by UiPath.
- Many routers return dummy data; the API surface is uneven.
- Import-time prints in `config.py` may leak structure to stdout and add noise.
- Minimal error handling for missing/expired tokens in routes that require them.
- No tests, CI, or lint/format configuration.

## Suggested Next Steps for Rewrite
- Centralize and harden configuration (remove import-time prints, add logging with sensitive filtering).
- Define and document explicit OAuth2 callback path; store state per-session.
- Abstract token storage with optional persistence (file/DB) and refresh handling.
- Remove hardcoded URLs; pass org/tenant via config or request parameters.
- Normalize router patterns: consistent paths, error handling, and response schemas.
- Add smoke tests for `/`, `/info`, router wiring; mock UiPath calls for unit tests.
- Provide a `.uipathcloud.env.example` and a `run` script/Makefile for local startup.

