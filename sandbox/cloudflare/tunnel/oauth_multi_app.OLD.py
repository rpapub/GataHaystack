#!/usr/bin/env python3
"""
Standalone MCVE: OAuth2 Handler for Multiple UiPath External Applications
Uses Cloudflare Tunnel for public callback URLs

This example demonstrates handling OAuth2 Authorization Code flow
for 2 separate UiPath external applications simultaneously.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import dotenv_values
import httpx
import logging
from typing import Dict, Optional
import secrets
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = dotenv_values(".env")

# UiPath OAuth endpoints
UIPATH_BASE_URL = "https://cloud.uipath.com"
AUTHORIZE_URL = f"{UIPATH_BASE_URL}/identity_/connect/authorize"
TOKEN_URL = f"{UIPATH_BASE_URL}/identity_/connect/token"

# Configuration for both apps
APP_CONFIGS = {
    "app1": {
        "client_id": config.get("APP1_CLIENT_ID"),
        "client_secret": config.get("APP1_CLIENT_SECRET"),
        "callback_path": config.get("APP1_CALLBACK_PATH", "/cb/orch/dev/rpb/gthy/fullrw/c01"),
        "scopes": "OR.Administration OR.Execution OR.Monitoring OR.Assets OR.Jobs OR.Folders OR.Robots",
        "name": "Full RW Confidential App"
    },
    "app2": {
        "client_id": config.get("APP2_CLIENT_ID"),
        "client_secret": config.get("APP2_CLIENT_SECRET"),
        "callback_path": config.get("APP2_CALLBACK_PATH", "/cb/orch/dev/rpb/gthy/fullrw/nc02"),
        "scopes": "OR.Folders OR.Robots OR.Users OR.Machines OR.Monitoring",
        "name": "Non-Confidential App"
    }
}

# Get public URL from config (Cloudflare tunnel URL)
PUBLIC_URL = config.get("PUBLIC_URL", "http://localhost:8000")

# Token storage (in production, use secure storage like Redis)
token_storage: Dict[str, Dict] = {
    "app1": {},
    "app2": {}
}

# State storage for CSRF protection
state_storage: Dict[str, Dict] = {}

app = FastAPI(
    title="Multi-App OAuth2 Handler",
    description="Handles OAuth2 for multiple UiPath external applications"
)


def generate_state(app_id: str) -> str:
    """Generate secure state token for CSRF protection"""
    state = secrets.token_urlsafe(32)
    state_storage[state] = {
        "app_id": app_id,
        "created_at": datetime.utcnow()
    }
    # Clean old states (older than 10 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    expired = [s for s, data in state_storage.items() if data["created_at"] < cutoff]
    for s in expired:
        del state_storage[s]
    return state


def verify_state(state: str) -> Optional[str]:
    """Verify state token and return app_id"""
    data = state_storage.get(state)
    if not data:
        return None
    del state_storage[state]
    return data["app_id"]


@app.get("/")
async def root():
    """Landing page with links to authorize both apps"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-App OAuth2 Demo</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .app-card {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .app-card h2 {{
                margin-top: 0;
                color: #fa4616;
            }}
            .status {{
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }}
            .authorized {{
                background: #e8f5e9;
                color: #2e7d32;
            }}
            .not-authorized {{
                background: #fff3e0;
                color: #e65100;
            }}
            .btn {{
                background: #fa4616;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                display: inline-block;
                margin: 10px 0;
            }}
            .btn:hover {{
                background: #d63a0f;
            }}
            .token-info {{
                background: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        <h1>Multi-App OAuth2 Demo</h1>
        <p>This demo shows handling OAuth2 for multiple UiPath external applications.</p>

        <div class="app-card">
            <h2>{APP_CONFIGS['app1']['name']}</h2>
            <p><strong>Client ID:</strong> {APP_CONFIGS['app1']['client_id']}</p>
            <p><strong>Scopes:</strong> {APP_CONFIGS['app1']['scopes']}</p>
            <div class="status {'authorized' if token_storage['app1'].get('access_token') else 'not-authorized'}">
                {'✓ Authorized' if token_storage['app1'].get('access_token') else '✗ Not Authorized'}
            </div>
            {f'<div class="token-info">Token expires: {token_storage["app1"].get("expires_at")}</div>' if token_storage['app1'].get('access_token') else ''}
            <a href="/authorize/app1" class="btn">Authorize App 1</a>
            {f'<a href="/test/app1" class="btn" style="background:#4caf50">Test API Call</a>' if token_storage['app1'].get('access_token') else ''}
        </div>

        <div class="app-card">
            <h2>{APP_CONFIGS['app2']['name']}</h2>
            <p><strong>Client ID:</strong> {APP_CONFIGS['app2']['client_id']}</p>
            <p><strong>Scopes:</strong> {APP_CONFIGS['app2']['scopes']}</p>
            <div class="status {'authorized' if token_storage['app2'].get('access_token') else 'not-authorized'}">
                {'✓ Authorized' if token_storage['app2'].get('access_token') else '✗ Not Authorized'}
            </div>
            {f'<div class="token-info">Token expires: {token_storage["app2"].get("expires_at")}</div>' if token_storage['app2'].get('access_token') else ''}
            <a href="/authorize/app2" class="btn">Authorize App 2</a>
            {f'<a href="/test/app2" class="btn" style="background:#4caf50">Test API Call</a>' if token_storage['app2'].get('access_token') else ''}
        </div>

        <div class="app-card">
            <h3>Configuration</h3>
            <p><strong>Public URL:</strong> {PUBLIC_URL}</p>
            <p><strong>App 1 Callback:</strong> {PUBLIC_URL}{APP_CONFIGS['app1']['callback_path']}</p>
            <p><strong>App 2 Callback:</strong> {PUBLIC_URL}{APP_CONFIGS['app2']['callback_path']}</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/authorize/{app_id}")
async def authorize(app_id: str):
    """Redirect to UiPath OAuth authorization endpoint"""
    if app_id not in APP_CONFIGS:
        raise HTTPException(status_code=404, detail="App not found")

    config = APP_CONFIGS[app_id]
    state = generate_state(app_id)
    redirect_uri = f"{PUBLIC_URL}{config['callback_path']}"

    # Build authorization URL
    auth_url = (
        f"{AUTHORIZE_URL}"
        f"?client_id={config['client_id']}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={config['scopes']}"
        f"&state={state}"
    )

    logger.info(f"Redirecting to authorize {config['name']}")
    logger.info(f"Redirect URI: {redirect_uri}")
    logger.info(f"State: {state}")

    return HTMLResponse(
        content=f'<html><body>Redirecting to UiPath...<script>window.location.href="{auth_url}";</script></body></html>',
        status_code=302,
        headers={"Location": auth_url}
    )


@app.get("/cb/orch/dev/rpb/gthy/fullrw/c01")
async def callback_app1(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """OAuth callback for App 1 - Full RW Confidential"""
    return await handle_callback("app1", code, state, error)


@app.get("/cb/orch/dev/rpb/gthy/fullrw/nc02")
async def callback_app2(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """OAuth callback for App 2 - Non-Confidential"""
    return await handle_callback("app2", code, state, error)


async def handle_callback(app_id: str, code: Optional[str], state: Optional[str], error: Optional[str]):
    """Handle OAuth callback and exchange code for token"""
    config = APP_CONFIGS[app_id]

    # Check for errors
    if error:
        logger.error(f"{config['name']} authorization error: {error}")
        return HTMLResponse(
            content=f"<html><body><h1>Authorization Failed</h1><p>Error: {error}</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    # Verify state
    if not state or verify_state(state) != app_id:
        logger.error(f"{config['name']} invalid state token")
        return HTMLResponse(
            content="<html><body><h1>Invalid State</h1><p>CSRF check failed</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    # Verify code
    if not code:
        logger.error(f"{config['name']} no authorization code received")
        return HTMLResponse(
            content="<html><body><h1>No Code</h1><p>Authorization code missing</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    logger.info(f"{config['name']} received authorization code: {code[:10]}...")

    # Exchange code for token
    redirect_uri = f"{PUBLIC_URL}{config['callback_path']}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": config['client_id'],
                    "client_secret": config['client_secret']
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

            logger.info(f"{config['name']} token exchange status: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()
                token_storage[app_id] = {
                    "access_token": token_data.get("access_token"),
                    "token_type": token_data.get("token_type"),
                    "expires_in": token_data.get("expires_in"),
                    "expires_at": datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                }
                logger.info(f"{config['name']} successfully obtained access token")

                return HTMLResponse(
                    content=f"""
                    <html>
                    <body>
                        <h1>✓ Authorization Successful</h1>
                        <p>{config['name']} has been authorized!</p>
                        <p>Token expires in {token_data.get('expires_in')} seconds</p>
                        <a href="/">Go back to dashboard</a>
                    </body>
                    </html>
                    """
                )
            else:
                error_detail = response.text
                logger.error(f"{config['name']} token exchange failed: {error_detail}")
                return HTMLResponse(
                    content=f"""
                    <html>
                    <body>
                        <h1>Token Exchange Failed</h1>
                        <p>Status: {response.status_code}</p>
                        <pre>{error_detail}</pre>
                        <a href="/">Go back</a>
                    </body>
                    </html>
                    """,
                    status_code=400
                )

        except Exception as e:
            logger.error(f"{config['name']} exception during token exchange: {str(e)}")
            return HTMLResponse(
                content=f"""
                <html>
                <body>
                    <h1>Error</h1>
                    <p>{str(e)}</p>
                    <a href="/">Go back</a>
                </body>
                </html>
                """,
                status_code=500
            )


@app.get("/test/{app_id}")
async def test_api(app_id: str):
    """Test API call using the app's token"""
    if app_id not in APP_CONFIGS:
        raise HTTPException(status_code=404, detail="App not found")

    config = APP_CONFIGS[app_id]
    token_data = token_storage.get(app_id, {})

    if not token_data.get("access_token"):
        return HTMLResponse(
            content=f"<html><body><h1>Not Authorized</h1><p>{config['name']} is not authorized yet</p><a href='/'>Go back</a></body></html>",
            status_code=401
        )

    # Test API call to get folders
    account = config.get("ACCOUNT_LOGICAL_NAME", "cprimadotnet")
    tenant = config.get("TENANT_LOGICAL_NAME", "cprima")
    api_url = f"{UIPATH_BASE_URL}/{account}/{tenant}/orchestrator_/api/Folders/GetAllForCurrentUser"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Accept": "application/json"
                }
            )

            logger.info(f"{config['name']} test API call status: {response.status_code}")

            return HTMLResponse(
                content=f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                        pre {{ background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }}
                    </style>
                </head>
                <body>
                    <h1>API Test: {config['name']}</h1>
                    <p><strong>Endpoint:</strong> GET /api/Folders/GetAllForCurrentUser</p>
                    <p><strong>Status:</strong> {response.status_code}</p>
                    <h3>Response:</h3>
                    <pre>{response.text}</pre>
                    <a href="/">Go back</a>
                </body>
                </html>
                """
            )

        except Exception as e:
            logger.error(f"{config['name']} API test failed: {str(e)}")
            return HTMLResponse(
                content=f"""
                <html>
                <body>
                    <h1>API Test Failed</h1>
                    <p>{str(e)}</p>
                    <a href="/">Go back</a>
                </body>
                </html>
                """,
                status_code=500
            )


@app.get("/status")
async def status():
    """Return status of both apps"""
    return JSONResponse({
        "app1": {
            "name": APP_CONFIGS["app1"]["name"],
            "authorized": bool(token_storage["app1"].get("access_token")),
            "expires_at": str(token_storage["app1"].get("expires_at")) if token_storage["app1"].get("expires_at") else None
        },
        "app2": {
            "name": APP_CONFIGS["app2"]["name"],
            "authorized": bool(token_storage["app2"].get("access_token")),
            "expires_at": str(token_storage["app2"].get("expires_at")) if token_storage["app2"].get("expires_at") else None
        },
        "public_url": PUBLIC_URL
    })


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("Multi-App OAuth2 Handler")
    print("=" * 80)
    print(f"\nPublic URL: {PUBLIC_URL}")
    print(f"\nApp 1 Callback: {PUBLIC_URL}{APP_CONFIGS['app1']['callback_path']}")
    print(f"App 2 Callback: {PUBLIC_URL}{APP_CONFIGS['app2']['callback_path']}")
    print("\n⚠️  Make sure to:")
    print("1. Configure these callback URLs in UiPath External Applications")
    print("2. Start Cloudflare tunnel pointing to localhost:8000")
    print("3. Update PUBLIC_URL in .env to match your Cloudflare tunnel URL")
    print("\nStarting server on http://localhost:8000")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
