# Development Tools

Utility scripts for development, testing, and debugging.

## swagger_proxy.py

FastAPI proxy server that solves CORS issues when using Swagger UI with UiPath Cloud API.

**Usage:**
```bash
python tools/swagger_proxy.py
```

Then access Swagger UI at `http://localhost:8000/swagger.html`

**Features:**
- Proxies API requests to UiPath Cloud (bypasses CORS)
- Handles OAuth2 authentication server-side
- Serves static Swagger UI files
- Token management and refresh

**Configuration:**
Requires `.uipathcloud.env` file with OAuth2 credentials.
