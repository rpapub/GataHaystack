from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx
from ..config import Settings  # Adjust the import path to match your project structure.

class OAuth2AuthCodeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.appl_access_token = None
        self.token_expires = datetime.utcnow()

    async def dispatch(self, request: Request, call_next):
        print(f"Dispatching request: {request.url}")

        if self.appl_access_token is None or datetime.utcnow() >= self.token_expires - timedelta(seconds=60):
            print("Access token is missing or expired. Fetching new access token.")
            async with httpx.AsyncClient() as client:
                #headers = {}
                # if self.cookie:
                #     headers['Cookie'] = self.cookie
                #     print(f"Including cookie in token request: {self.cookie}")
                
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.settings.uipath_applscope_client_id,
                    'client_secret': self.settings.uipath_applscope_client_secret,
                    'scope': self.settings.uipath_appl_scope
                }
                print(data)

                auth_response = await client.post(
                    self.settings.uipath_access_token_url,
                    #headers=headers,
                    data=data,
                )

                print(f"Token request response status: {auth_response.status_code}")

                # Check for Set-Cookie in the response and store it
                if 'set-cookie' in auth_response.headers:
                    request.state.cookie = auth_response.headers['set-cookie']
                    print(f"Received new cookie: {request.state.cookie}")

            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                self.appl_access_token = auth_data['access_token']
                # Calculate the expiration time as current time + expires_in seconds
                self.token_expires = datetime.utcnow() + timedelta(seconds=auth_data['expires_in'])
                print(f"New access token obtained. Expires in {auth_data['expires_in']} seconds.")
            else:
                print("Failed to obtain access token.")
                print(auth_response)
                return JSONResponse({"error": "Authentication failed"}, status_code=auth_response.status_code)

        else:
            print("Using existing access token.")

        # Set the access token in request state
        request.state.appl_access_token = self.appl_access_token

        # Proceed with the request
        response = await call_next(request)
        return response