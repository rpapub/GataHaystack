#!/usr/bin/env python3
"""
FastAPI Proxy Server for UiPath Orchestrator API
Solves CORS issues by proxying requests from Swagger UI to UiPath Cloud
"""

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from pathlib import Path
from dotenv import dotenv_values
from typing import Optional
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = dotenv_values(".uipathcloud.env")

UIPATH_BASE_URL = "https://cloud.uipath.com"
CLIENT_ID = config.get('CLIENT_ID')
CLIENT_SECRET = config.get('CLIENT_SECRET')
ACCOUNT = config.get('ACCOUNT_LOGICAL_NAME')
TENANT = config.get('TENANT_LOGICAL_NAME')

# Token cache
token_cache = {
    'access_token': None,
    'expires_at': 0
}

app = FastAPI(
    title="UiPath Orchestrator API Proxy",
    description="CORS-enabled proxy for UiPath Cloud API",
    version="1.0.0"
)

# Enable CORS for all origins (since we're the proxy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_access_token() -> str:
    """Get or refresh access token"""
    current_time = time.time()

    # Return cached token if still valid (with 60 second buffer)
    if token_cache['access_token'] and token_cache['expires_at'] > current_time + 60:
        logger.info("Using cached access token")
        return token_cache['access_token']

    # Get new token
    logger.info("Requesting new access token")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UIPATH_BASE_URL}/identity_/connect/token",
            data={
                'grant_type': 'client_credentials',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'scope': 'OR.Administration OR.Execution OR.Monitoring OR.Assets OR.Jobs OR.Folders OR.Robots'
            }
        )

        if response.status_code != 200:
            logger.error(f"Token request failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to get access token")

        token_data = response.json()
        token_cache['access_token'] = token_data['access_token']
        token_cache['expires_at'] = current_time + token_data.get('expires_in', 3600)

        logger.info(f"New token obtained, expires in {token_data.get('expires_in')} seconds")
        return token_cache['access_token']


@app.get("/")
async def root():
    """Redirect to Swagger UI"""
    return FileResponse("docs/swagger-proxy.html")


@app.get("/swagger")
async def swagger_ui():
    """Serve Swagger UI"""
    return FileResponse("docs/swagger-proxy.html")


@app.get("/openapi.json")
async def openapi_spec():
    """Serve modified OpenAPI spec pointing to proxy"""
    return FileResponse("docs/openapi-proxy.yml")


# Serve static files
app.mount("/static", StaticFiles(directory="docs"), name="static")


@app.api_route("/proxy/{account}/{tenant}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(
    account: str,
    tenant: str,
    path: str,
    request: Request,
    token: str = Depends(get_access_token)
):
    """
    Proxy all API requests to UiPath Cloud

    This endpoint forwards requests to cloud.uipath.com and returns the response,
    solving CORS issues that prevent direct browser access.
    """

    # Build target URL
    target_url = f"{UIPATH_BASE_URL}/{account}/{tenant}/orchestrator_/{path}"

    # Get query parameters
    query_params = dict(request.query_params)

    # Get request body
    try:
        body = await request.body()
    except:
        body = None

    # Prepare headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': request.headers.get('content-type', 'application/json'),
        'Accept': request.headers.get('accept', 'application/json'),
    }

    # Remove hop-by-hop headers
    for header in ['host', 'connection', 'keep-alive', 'transfer-encoding']:
        headers.pop(header, None)

    logger.info(f"Proxying {request.method} {target_url}")

    # Forward request to UiPath
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers
            )

            # Filter response headers - remove hop-by-hop and problematic headers
            response_headers = {}
            exclude_headers = {
                'transfer-encoding', 'content-encoding', 'connection',
                'keep-alive', 'proxy-authenticate', 'proxy-authorization',
                'te', 'trailers', 'upgrade', 'content-length'
            }
            for key, value in response.headers.items():
                if key.lower() not in exclude_headers:
                    response_headers[key] = value

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get('content-type')
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout while proxying to {target_url}")
            raise HTTPException(status_code=504, detail="Gateway Timeout")
        except Exception as e:
            logger.error(f"Error proxying request: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        token = await get_access_token()
        return {
            "status": "healthy",
            "uipath_base": UIPATH_BASE_URL,
            "account": ACCOUNT,
            "tenant": TENANT,
            "token_cached": token_cache['access_token'] is not None
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/token")
async def get_current_token(token: str = Depends(get_access_token)):
    """Get current access token (for debugging)"""
    return {
        "access_token": token,
        "expires_at": token_cache['expires_at'],
        "account": ACCOUNT,
        "tenant": TENANT
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("UiPath Orchestrator API Proxy Server")
    print("=" * 80)
    print(f"\nAccount: {ACCOUNT}")
    print(f"Tenant: {TENANT}")
    print(f"\nStarting server on http://localhost:8000")
    print("\nOpen Swagger UI at: http://localhost:8000/swagger")
    print("\nProxy endpoint: http://localhost:8000/proxy/{account}/{tenant}/{path}")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
