from fastapi import APIRouter, Depends, HTTPException, Query, Request
import httpx
import secrets
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse
from functools import lru_cache
from typing import Annotated
from ..config import Settings, get_settings
from ..models.uipathcloud import UiPathCloudOauth2
import urllib.parse
import hashlib
from datetime import datetime, timedelta
from ..models.uipathcloud import Organization, Application, AccessToken


router = APIRouter(
    prefix="/oauth2_uipath",
    tags=["oauth2", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)


def generate_state(client_id: str, client_secret: str) -> str:
    """
    Generates a one-directional hash using client_id and client_secret.
    """
    # Combine client_id and client_secret with a delimiter for the hash input
    hash_input = f"{client_id}:{client_secret}"
    # Create a SHA-256 hash of the combined string
    return hashlib.sha256(hash_input.encode()).hexdigest()

####################### needs to be imported, to work in the middleware as well
def update_access_token(settings: Settings, org_name: str, app_name: str, new_token_data: dict):
    """
    Update or add an access token for a specific application within an organization,
    ensuring that the existing token is matched based on the grant_type.

    Args:
    settings (Settings): The current application settings.
    org_name (str): The name of the organization.
    app_name (str): The name of the application.
    new_token_data (dict): A dictionary with the new token data, including grant_type.

    Returns:
    bool: True if the token was successfully updated or added, False otherwise.
    """
    for org in settings.uipathcloud_organizations:
        if org.name == org_name:
            for app in org.applications:
                if app.app_name == app_name:
                    # Check for an existing token with the same grant_type
                    existing_token = next((token for token in app.access_tokens if token.grant_type == new_token_data['grant_type']), None)
                    
                    # Create or update the AccessToken instance
                    if existing_token:
                        # Update existing token with new data
                        existing_token.access_token = new_token_data.get('access_token', existing_token.access_token)
                        existing_token.refresh_token = new_token_data.get('refresh_token', existing_token.refresh_token)
                        existing_token.token_expires = new_token_data.get('token_expires', existing_token.token_expires)
                        existing_token.token_type = new_token_data.get('token_type', existing_token.token_type)
                    else:
                        # Add new token if an existing one with the same grant_type wasn't found
                        new_access_token = AccessToken(**new_token_data)
                        app.access_tokens.append(new_access_token)
                    
                    return True
    return False

@router.get('/debug')
async def debug(settings: Annotated[Settings, Depends(get_settings)]):
    return settings

@router.get('/request_access_token_with_clientid')
async def oauth2_request_access_token_with_clientid(settings: Annotated[Settings, Depends(get_settings)]):
    """
    Redirect to Authorization Server

    Initiates the OAuth 2.0 authorization flow by redirecting the client's user agent to the authorization server.
    This step is typically used to obtain user authorization before exchanging the authorization code for an access token.
    The redirection to the authorization server is constructed using the provided `clientid` and configurations obtained from `settings`.

    Parameters:
    - clientid (str): Client identifier as registered with the authorization server.
    - settings (Settings): Application settings object, obtained via dependency injection, containing necessary configuration such as the authorization server URL.

    Returns:
    - A redirect response leading the user agent to the authorization server's consent page.
    """
    # Assuming the first organization and its first application are targeted
    if not settings.uipathcloud_organizations or not settings.uipathcloud_organizations[0].applications:
        raise HTTPException(status_code=404, detail="No organizations or applications configured")

    application = settings.uipathcloud_organizations[0].applications[0]  # Access the first application
    client_id = application.client_id
    client_secret = application.client_secret  # Assuming you need it for state generation
    scopes = urllib.parse.quote(application.scope)
    redirect_url = urllib.parse.quote(application.redirect_url, safe='')
    state = generate_state(client_id, client_secret)

    url = f"{settings.uipathcloud_authorization_endpoint}?response_type=code&client_id={client_id}&scope={scopes}&redirect_uri={redirect_url}&state={state}"
    print(url)
    return RedirectResponse(url=url)

from pprint import pprint

@router.get('/receive_authcode')
async def oauth2_receive_authcode(request: Request, code: str, settings: Annotated[Settings, Depends(get_settings)], state: str = Query(...)):
    """
    OAuth 2.0 Authorization Code Receiver

    This endpoint serves as the redirection URI that receives the authorization code from the authorization server.
    It is part of the OAuth 2.0 authorization code flow. The client application must register this redirect URI with
    the authorization server ahead of time. The authorization server may validate the URI for security purposes before
    sending the authorization code to it.

    Upon receiving the authorization code, the client application can proceed to exchange it for an access token at the
    token endpoint of the authorization server.

    Parameters:
    - code (str): The authorization code sent by the authorization server as a response to the client's authorization request.

    Returns:
    - A confirmation that the code has been received, which may include further instructions on how to exchange the code for an access token.
    """
    matched_app = None
    for org in settings.uipathcloud_organizations:
        for appl in org.applications:
            # Assuming generate_state uses app.client_id and app.client_secret
            if generate_state(appl.client_id, appl.client_secret) == state:
                matched_app = appl
                organization_name = org.name
                application_name = appl.app_name
                break
        if matched_app:
            break

    if not matched_app:
        raise HTTPException(status_code=404, detail="No matching application found for the provided state.")
    
    # Data payload for token exchange uses matched application details
    data = {
        "grant_type": "authorization_code",  # Always "authorization_code" for this flow
        "code": code,
        "redirect_uri": matched_app.redirect_url,
        "client_id": matched_app.client_id,
        "client_secret": matched_app.client_secret
    }
    headers = {"Accept": "application/json"}

    # Exchange the authorization code for an access token
    async with httpx.AsyncClient() as client:
        response = await client.post(url=settings.uipathcloud_token_endpoint, data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to exchange authorization code for access token.")
        
        response_json = response.json()
        access_token = response_json.get("access_token")
        token_type = response_json.get("token_type", "Bearer")
        expires_in = response_json.get("expires_in")  # Time in seconds until the token expires
        refresh_token_str = response_json.get("refresh_token", None)

        # Calculate the expiry timestamp for the new token
        token_expiry_timestamp = datetime.now() + timedelta(seconds=expires_in)

        # Create a new AccessToken instance with the obtained details
        new_access_token = AccessToken(
            grant_type="authorization_code",  # This flow is for authorization_code
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_expires=int(token_expiry_timestamp.timestamp()),  # Convert to UNIX timestamp
            token_type=token_type
        )

        current_settings = get_settings()
        success = update_access_token(current_settings, organization_name, application_name, new_access_token.dict())
        print("#------------------")
        print(settings)
        print("------------------")

        # check status_code
        if not success:
            raise HTTPException(status_code=404, detail="Organization or application not found.")


        # The matched_app is updated in-place, and since it's a reference within the settings.uipathcloud_organizations list,
        # the update is reflected across the entire settings structure without additional action.
    return RedirectResponse(url="/")
    
    # # Construct the URL for the API call to verify the access token
    # # Assuming 'settings' is already available here, either passed as a parameter or accessible globally
    # cloud_url = settings.uipathcloud_baseurl
    # # Assuming you have determined which organization and application you are working with
    # # For demonstration, using hardcoded values; replace or derive these from your actual logic
    # cloud_org_name = "cprimadotnet"  # Example, replace with dynamic value if necessary
    # cloud_tenant_name = "homelab23"  # Example, replace with dynamic value if necessary
    # api_url = f"{cloud_url}/{cloud_org_name}/{cloud_tenant_name}/orchestrator_/odata/Machines"
    
    # # Make the API call to verify the access token
    # headers = {'Authorization': f"Bearer {access_token}", 'Content-Type': 'application/json'}
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(api_url, headers=headers)
    #     if response.status_code != 200:
    #         # Log or handle failed requests, depending on your application's needs
    #         raise HTTPException(status_code=response.status_code, detail=f"Failed to verify access token with the API call. Response: {response.text}")
        
    #     # Assuming successful request, process the response as needed
    #     return response.json()


@router.get('/request_access_token_with_refreshtoken_foo')
async def oauth2_request_access_token_with_refreshtoken_foo(refresh_token: str):
    """
    Request Access Token using Refresh Token Foo

    This endpoint allows obtaining a new access token using a refresh token, bypassing the need for re-authentication by the resource owner. Employing a refresh token—a secure and long-lived token—facilitates the generation of new access tokens, enhancing security by limiting exposure if an access token is compromised.

    Parameters:
    - refresh_token (str): The refresh token previously issued to the client during the access token exchange process.

    Returns:
    - A new access token along with its expiry time and optionally, a new refresh token.
    """
    pass

@router.get('/request_openid_configuration')
async def oauth2_request_openid_configuration():
    """
    Request OpenID Configuration

    This endpoint provides the OpenID Provider Configuration Information. It's part of the OpenID Connect
    discovery mechanism enabling clients to dynamically discover OpenID Connect and OAuth 2.0 endpoints.

    Parameters:
    - None

    Returns:
    - The OpenID Configuration in a JSON structure.
    """
    pass