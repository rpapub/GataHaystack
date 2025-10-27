#!/usr/bin/env python3
"""
Standalone MCVE: OAuth2 Handler for Multiple UiPath External Applications
Profile-based configuration supporting both client_credentials and authorization_code with PKCE

Supports:
- Client Credentials flow (confidential apps with client_secret)
- Authorization Code with PKCE flow (non-confidential apps)
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from dotenv import dotenv_values
import httpx
import logging
from typing import Dict, Optional, List
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = dotenv_values(".env")

# Common configuration
ACCOUNT_LOGICAL_NAME = config.get("ACCOUNT_LOGICAL_NAME", "rpapub")
TENANT_LOGICAL_NAME = config.get("TENANT_LOGICAL_NAME", "playground")
BASE_URL = config.get("BASE_URL", "https://cloud.uipath.com")
PUBLIC_URL = config.get("PUBLIC_URL", "http://localhost:8000")
DEFAULT_PROFILE = config.get("DEFAULT_PROFILE", "c01")

# OAuth endpoints
AUTHORIZE_URL = f"{BASE_URL}/identity_/connect/authorize"
TOKEN_URL = f"{BASE_URL}/identity_/connect/token"

# Parse profiles from environment
def load_profiles() -> Dict[str, Dict]:
    """Load all PROFILE_* entries from config"""
    profiles = {}

    # Find all unique profile names - only look for profiles with CLIENT_ID
    profile_pattern = re.compile(r'^PROFILE_(\w+)_CLIENT_ID$')
    profile_names = set()

    for key in config.keys():
        match = profile_pattern.match(key)
        if match:
            profile_names.add(match.group(1))

    # Build profile configuration
    for profile_name in profile_names:
        prefix = f"PROFILE_{profile_name}_"

        profile_config = {
            "name": profile_name,
            "client_id": config.get(f"{prefix}CLIENT_ID"),
            "client_secret": config.get(f"{prefix}CLIENT_SECRET"),
            "grant": config.get(f"{prefix}GRANT", "client_credentials"),
            "scopes": config.get(f"{prefix}SCOPES", "OR.Execution"),
            "redirect": config.get(f"{prefix}REDIRECT"),
        }

        # Set callback path from redirect URL
        if profile_config["redirect"]:
            # Extract path from full URL
            redirect_url = profile_config["redirect"]
            if PUBLIC_URL in redirect_url:
                profile_config["callback_path"] = redirect_url.replace(PUBLIC_URL, "")
            else:
                # Fallback to default path
                profile_config["callback_path"] = f"/cb/orch/dev/{ACCOUNT_LOGICAL_NAME}/{TENANT_LOGICAL_NAME}/fullrw/{profile_name}"
        else:
            profile_config["callback_path"] = f"/cb/orch/dev/{ACCOUNT_LOGICAL_NAME}/{TENANT_LOGICAL_NAME}/fullrw/{profile_name}"

        # Determine flow type
        if profile_config["grant"] == "client_credentials":
            profile_config["flow_type"] = "Client Credentials"
            profile_config["requires_secret"] = True
        elif profile_config["grant"] == "authorization_code_pkce":
            profile_config["flow_type"] = "Authorization Code + PKCE"
            profile_config["requires_secret"] = False
        elif profile_config["grant"] == "authorization_code":
            profile_config["flow_type"] = "Authorization Code"
            profile_config["requires_secret"] = True
        else:
            profile_config["flow_type"] = "Unknown"
            profile_config["requires_secret"] = False

        profiles[profile_name] = profile_config

        logger.info(f"Loaded profile '{profile_name}': {profile_config['flow_type']}")

    return profiles

PROFILES = load_profiles()

# Token storage (in production, use secure storage like Redis)
token_storage: Dict[str, Dict] = {profile: {} for profile in PROFILES.keys()}

# State storage for CSRF protection
state_storage: Dict[str, Dict] = {}

# PKCE verifier storage
pkce_storage: Dict[str, str] = {}

app = FastAPI(
    title="Multi-Profile OAuth2 Handler",
    description="Handles OAuth2 for multiple UiPath external applications with different grant types"
)


def generate_state(profile_name: str) -> str:
    """Generate secure state token for CSRF protection"""
    state = secrets.token_urlsafe(32)
    state_storage[state] = {
        "profile": profile_name,
        "created_at": datetime.utcnow()
    }
    # Clean old states (older than 10 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    expired = [s for s, data in state_storage.items() if data["created_at"] < cutoff]
    for s in expired:
        del state_storage[s]
    return state


def verify_state(state: str) -> Optional[str]:
    """Verify state token and return profile name"""
    data = state_storage.get(state)
    if not data:
        return None
    del state_storage[state]
    return data["profile"]


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge"""
    # Generate random code_verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    # Generate code_challenge from code_verifier using S256
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


@app.get("/")
async def root():
    """Landing page with links to authorize all profiles"""

    profile_cards = []
    for profile_name, profile in PROFILES.items():
        token_info = token_storage.get(profile_name, {})
        is_authorized = bool(token_info.get("access_token"))

        card_html = f"""
        <div class="app-card">
            <h2>Profile: {profile_name}</h2>
            <p><strong>Flow:</strong> {profile['flow_type']}</p>
            <p><strong>Client ID:</strong> {profile['client_id'][:20]}...</p>
            <p><strong>Scopes:</strong> {profile['scopes']}</p>
            <div class="status {'authorized' if is_authorized else 'not-authorized'}">
                {'✓ Authorized' if is_authorized else '✗ Not Authorized'}
            </div>
            {f'<div class="token-info">Expires: {token_info.get("expires_at")}</div>' if is_authorized else ''}
            <a href="/authorize/{profile_name}" class="btn">Authorize {profile_name}</a>
            {f'<a href="/test/{profile_name}" class="btn" style="background:#4caf50">Test API Call</a>' if is_authorized else ''}
        </div>
        """
        profile_cards.append(card_html)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Profile OAuth2 Demo</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
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
                margin: 10px 5px 10px 0;
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
            }}
            .config-card {{
                background: #e3f2fd;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
                border-left: 4px solid #2196f3;
            }}
        </style>
    </head>
    <body>
        <h1>Multi-Profile OAuth2 Demo</h1>
        <p>Profile-based OAuth2 handler supporting multiple grant types</p>

        {''.join(profile_cards)}

        <div class="config-card">
            <h3>Configuration</h3>
            <p><strong>Account:</strong> {ACCOUNT_LOGICAL_NAME}</p>
            <p><strong>Tenant:</strong> {TENANT_LOGICAL_NAME}</p>
            <p><strong>Public URL:</strong> {PUBLIC_URL}</p>
            <p><strong>Default Profile:</strong> {DEFAULT_PROFILE}</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/authorize/{profile_name}")
async def authorize(profile_name: str):
    """Start OAuth authorization flow for a profile"""
    if profile_name not in PROFILES:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = PROFILES[profile_name]

    # Client credentials flow - auto-fetch token
    if profile["grant"] == "client_credentials":
        logger.info(f"Profile '{profile_name}': Using client_credentials flow")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": profile["client_id"],
                        "client_secret": profile["client_secret"],
                        "scope": profile["scopes"]
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code == 200:
                    token_data = response.json()
                    token_storage[profile_name] = {
                        "access_token": token_data.get("access_token"),
                        "token_type": token_data.get("token_type"),
                        "expires_in": token_data.get("expires_in"),
                        "expires_at": datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                    }
                    logger.info(f"Profile '{profile_name}': Successfully obtained token")

                    return HTMLResponse(
                        content=f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                            <h1>✓ Authorization Successful</h1>
                            <p>Profile <strong>{profile_name}</strong> has been authorized using client credentials!</p>
                            <p>Token expires in {token_data.get('expires_in')} seconds</p>
                            <a href="/" style="background:#fa4616;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Go back</a>
                        </body>
                        </html>
                        """
                    )
                else:
                    error_detail = response.text
                    logger.error(f"Profile '{profile_name}': Token request failed: {error_detail}")
                    raise HTTPException(status_code=500, detail=f"Token request failed: {error_detail}")

        except Exception as e:
            logger.error(f"Profile '{profile_name}': Exception: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # Authorization code flows - redirect to UiPath
    else:
        state = generate_state(profile_name)
        redirect_uri = f"{PUBLIC_URL}{profile['callback_path']}"

        auth_params = {
            "client_id": profile["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": profile["scopes"],
            "state": state
        }

        # Add PKCE for authorization_code_pkce
        if profile["grant"] == "authorization_code_pkce":
            code_verifier, code_challenge = generate_pkce_pair()
            pkce_storage[state] = code_verifier
            auth_params["code_challenge"] = code_challenge
            auth_params["code_challenge_method"] = "S256"
            logger.info(f"Profile '{profile_name}': Using PKCE (code_challenge: {code_challenge[:20]}...)")

        # Build authorization URL
        auth_url = AUTHORIZE_URL + "?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])

        logger.info(f"Profile '{profile_name}': Redirecting to authorization")
        logger.info(f"Redirect URI: {redirect_uri}")

        return RedirectResponse(url=auth_url)


# Dynamic callback routes
@app.api_route("/cb/orch/dev/{account}/{tenant}/fullrw/{profile_name}", methods=["GET"])
async def callback_handler(
    account: str,
    tenant: str,
    profile_name: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """OAuth callback handler for all profiles"""
    return await handle_callback(profile_name, code, state, error)


async def handle_callback(profile_name: str, code: Optional[str], state: Optional[str], error: Optional[str]):
    """Handle OAuth callback and exchange code for token"""

    if profile_name not in PROFILES:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = PROFILES[profile_name]

    # Check for errors
    if error:
        logger.error(f"Profile '{profile_name}': Authorization error: {error}")
        return HTMLResponse(
            content=f"<html><body><h1>Authorization Failed</h1><p>Error: {error}</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    # Verify state
    if not state or verify_state(state) != profile_name:
        logger.error(f"Profile '{profile_name}': Invalid state token")
        return HTMLResponse(
            content="<html><body><h1>Invalid State</h1><p>CSRF check failed</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    # Verify code
    if not code:
        logger.error(f"Profile '{profile_name}': No authorization code received")
        return HTMLResponse(
            content="<html><body><h1>No Code</h1><p>Authorization code missing</p><a href='/'>Go back</a></body></html>",
            status_code=400
        )

    logger.info(f"Profile '{profile_name}': Received authorization code")

    # Exchange code for token
    redirect_uri = f"{PUBLIC_URL}{profile['callback_path']}"

    token_params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": profile["client_id"]
    }

    # Add client_secret if required
    if profile["requires_secret"] and profile["client_secret"]:
        token_params["client_secret"] = profile["client_secret"]

    # Add PKCE code_verifier if this was a PKCE flow
    if profile["grant"] == "authorization_code_pkce":
        code_verifier = pkce_storage.pop(state, None)
        if code_verifier:
            token_params["code_verifier"] = code_verifier
            logger.info(f"Profile '{profile_name}': Using PKCE code_verifier")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TOKEN_URL,
                data=token_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            logger.info(f"Profile '{profile_name}': Token exchange status: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()
                token_storage[profile_name] = {
                    "access_token": token_data.get("access_token"),
                    "token_type": token_data.get("token_type"),
                    "expires_in": token_data.get("expires_in"),
                    "expires_at": datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                }
                logger.info(f"Profile '{profile_name}': Successfully obtained access token")

                return HTMLResponse(
                    content=f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                        <h1>✓ Authorization Successful</h1>
                        <p>Profile <strong>{profile_name}</strong> has been authorized!</p>
                        <p>Grant type: {profile['grant']}</p>
                        <p>Token expires in {token_data.get('expires_in')} seconds</p>
                        <a href="/" style="background:#fa4616;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Go back to dashboard</a>
                    </body>
                    </html>
                    """
                )
            else:
                error_detail = response.text
                logger.error(f"Profile '{profile_name}': Token exchange failed: {error_detail}")
                return HTMLResponse(
                    content=f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                        <h1>Token Exchange Failed</h1>
                        <p>Profile: {profile_name}</p>
                        <p>Status: {response.status_code}</p>
                        <pre style="background:#f5f5f5;padding:15px;border-radius:4px;overflow-x:auto;">{error_detail}</pre>
                        <a href="/" style="background:#fa4616;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Go back</a>
                    </body>
                    </html>
                    """,
                    status_code=400
                )

        except Exception as e:
            logger.error(f"Profile '{profile_name}': Exception during token exchange: {str(e)}")
            return HTMLResponse(
                content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1>Error</h1>
                    <p>{str(e)}</p>
                    <a href="/" style="background:#fa4616;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Go back</a>
                </body>
                </html>
                """,
                status_code=500
            )


@app.get("/test/{profile_name}")
async def test_api(profile_name: str):
    """Test API call using the profile's token"""
    if profile_name not in PROFILES:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = PROFILES[profile_name]
    token_data = token_storage.get(profile_name, {})

    if not token_data.get("access_token"):
        return HTMLResponse(
            content=f"<html><body><h1>Not Authorized</h1><p>Profile '{profile_name}' is not authorized yet</p><a href='/'>Go back</a></body></html>",
            status_code=401
        )

    # Test API call to get folders
    api_url = f"{BASE_URL}/{ACCOUNT_LOGICAL_NAME}/{TENANT_LOGICAL_NAME}/orchestrator_/api/Folders/GetAllForCurrentUser"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Accept": "application/json"
                }
            )

            logger.info(f"Profile '{profile_name}': Test API call status: {response.status_code}")

            return HTMLResponse(
                content=f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                        pre {{ background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }}
                        .btn {{ background: #fa4616; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }}
                    </style>
                </head>
                <body>
                    <h1>API Test: Profile {profile_name}</h1>
                    <p><strong>Grant Type:</strong> {profile['grant']}</p>
                    <p><strong>Endpoint:</strong> GET /api/Folders/GetAllForCurrentUser</p>
                    <p><strong>Status:</strong> {response.status_code}</p>
                    <h3>Response:</h3>
                    <pre>{response.text}</pre>
                    <a href="/" class="btn">Go back</a>
                </body>
                </html>
                """
            )

        except Exception as e:
            logger.error(f"Profile '{profile_name}': API test failed: {str(e)}")
            return HTMLResponse(
                content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1>API Test Failed</h1>
                    <p>{str(e)}</p>
                    <a href="/" style="background:#fa4616;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Go back</a>
                </body>
                </html>
                """,
                status_code=500
            )


@app.get("/status")
async def status():
    """Return status of all profiles"""
    profile_status = {}

    for profile_name, profile in PROFILES.items():
        token_info = token_storage.get(profile_name, {})
        profile_status[profile_name] = {
            "flow_type": profile["flow_type"],
            "grant": profile["grant"],
            "authorized": bool(token_info.get("access_token")),
            "expires_at": str(token_info.get("expires_at")) if token_info.get("expires_at") else None,
            "scopes": profile["scopes"]
        }

    return JSONResponse({
        "account": ACCOUNT_LOGICAL_NAME,
        "tenant": TENANT_LOGICAL_NAME,
        "public_url": PUBLIC_URL,
        "profiles": profile_status
    })


if __name__ == "__main__":
    import uvicorn
    import os

    # Determine if we should use HTTPS based on cert files
    use_https = os.path.exists("cert.pem") and os.path.exists("key.pem")
    port = 3701 if use_https else 8000
    protocol = "https" if use_https else "http"

    print("\n" + "=" * 80)
    print("Multi-Profile OAuth2 Handler")
    print("=" * 80)
    print(f"\nAccount: {ACCOUNT_LOGICAL_NAME}")
    print(f"Tenant: {TENANT_LOGICAL_NAME}")
    print(f"Public URL: {PUBLIC_URL}")
    print(f"\nLoaded {len(PROFILES)} profile(s):")
    for name, profile in PROFILES.items():
        print(f"  - {name}: {profile['flow_type']}")
        print(f"    Callback: {PUBLIC_URL}{profile['callback_path']}")
    print(f"\nDefault Profile: {DEFAULT_PROFILE}")
    print(f"\nStarting server on {protocol}://localhost:{port}")
    print("=" * 80 + "\n")

    if use_https:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            ssl_keyfile="key.pem",
            ssl_certfile="cert.pem"
        )
    else:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
