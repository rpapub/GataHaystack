#!/usr/bin/env python3
"""
OAuth2 Authorization Code Flow with PKCE - Step-by-step test
Simulates exactly what Swagger UI does when you click "Authorize"
"""

import json
import logging
import sys
import secrets
import hashlib
import base64
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

import requests
from dotenv import dotenv_values

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oauth2_authcode_debug.log')
    ]
)

logger = logging.getLogger(__name__)

# UiPath Cloud endpoints
UIPATH_BASE_URL = "https://cloud.uipath.com"
AUTHORIZATION_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/authorize"
TOKEN_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/token"

# Global variable to capture the authorization code
authorization_response = {}


class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth2 callback"""

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"Callback server: {format % args}")

    def do_GET(self):
        """Handle GET request (OAuth2 callback)"""
        global authorization_response

        logger.info("=" * 80)
        logger.info("CALLBACK RECEIVED")
        logger.info("=" * 80)
        logger.info(f"Full path: {self.path}")

        # Parse the query string
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        logger.debug(f"Parsed parameters: {params}")

        # Store the response
        authorization_response = {
            'code': params.get('code', [None])[0],
            'state': params.get('state', [None])[0],
            'error': params.get('error', [None])[0],
            'error_description': params.get('error_description', [None])[0]
        }

        if authorization_response['error']:
            logger.error(f"OAuth error: {authorization_response['error']}")
            logger.error(f"Description: {authorization_response['error_description']}")

            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
            <body>
                <h1>Authorization Failed</h1>
                <p><strong>Error:</strong> {authorization_response['error']}</p>
                <p><strong>Description:</strong> {authorization_response['error_description']}</p>
                <p>Check the terminal for detailed logs.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            logger.info(f"Authorization code received: {authorization_response['code'][:20]}...")

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge"""
    logger.info("Generating PKCE parameters...")

    # Generate code_verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    logger.debug(f"Code verifier: {code_verifier}")

    # Generate code_challenge (SHA256 hash of verifier)
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    logger.debug(f"Code challenge: {code_challenge}")

    return code_verifier, code_challenge


def start_callback_server(port=8000):
    """Start HTTP server to receive OAuth2 callback"""
    server = HTTPServer(('localhost', port), OAuth2CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Callback server started on http://localhost:{port}")
    return server


def main():
    print("\n" + "=" * 80)
    print("OAuth2 Authorization Code Flow with PKCE Test")
    print("Simulating Swagger UI OAuth2 flow")
    print("=" * 80 + "\n")

    # Load config
    config_file = ".uipathcloud.env"
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_file}")
        sys.exit(1)

    config = dotenv_values(config_file)

    # Get credentials - allow override via user input
    print("Using credentials from .uipathcloud.env")
    client_id = input(f"Client ID [{config.get('CLIENT_ID', '')[:20]}...]: ").strip() or config.get('CLIENT_ID')

    # Ask if user wants to enter a different client_id (like in Swagger)
    use_different = input("Use different client_id? (y/n): ").strip().lower()
    if use_different == 'y':
        client_id = input("Enter client_id: ").strip()
        client_secret = input("Enter client_secret: ").strip()
    else:
        client_secret = config.get('CLIENT_SECRET')

    account_name = config.get('ACCOUNT_LOGICAL_NAME')
    tenant_name = config.get('TENANT_LOGICAL_NAME')

    # Scopes - allow selection
    all_scopes = [
        "OR.Administration", "OR.Administration.Read", "OR.Administration.Write",
        "OR.Assets", "OR.Assets.Read", "OR.Assets.Write",
        "OR.Execution", "OR.Execution.Read", "OR.Execution.Write",
        "OR.Folders", "OR.Folders.Read", "OR.Folders.Write",
        "OR.Jobs", "OR.Jobs.Read", "OR.Jobs.Write",
        "OR.Monitoring", "OR.Monitoring.Read", "OR.Monitoring.Write",
        "OR.Robots", "OR.Robots.Read", "OR.Robots.Write",
        "OR.Users", "OR.Users.Read", "OR.Users.Write"
    ]

    print("\nSelect scopes (like in Swagger UI):")
    print("1. All scopes (default)")
    print("2. Custom selection")
    choice = input("Choice (1 or 2): ").strip() or "1"

    if choice == "2":
        print("\nAvailable scopes:")
        for i, scope in enumerate(all_scopes, 1):
            print(f"{i}. {scope}")
        selected = input("Enter scope numbers (comma-separated): ").strip()
        indices = [int(x.strip())-1 for x in selected.split(",")]
        scopes = [all_scopes[i] for i in indices]
    else:
        scopes = all_scopes

    scope_string = " ".join(scopes)

    logger.info("=" * 80)
    logger.info("CONFIGURATION")
    logger.info("=" * 80)
    logger.info(f"Client ID: {client_id[:20]}...")
    logger.info(f"Account: {account_name}")
    logger.info(f"Tenant: {tenant_name}")
    logger.info(f"Scopes: {scope_string}")

    redirect_uri = "http://localhost:8000/callback"

    # STEP 1: Generate PKCE parameters
    print("\n" + "-" * 80)
    print("STEP 1: Generating PKCE parameters")
    print("-" * 80)
    code_verifier, code_challenge = generate_pkce_pair()
    print(f"✓ PKCE parameters generated")

    # STEP 2: Start callback server
    print("\n" + "-" * 80)
    print("STEP 2: Starting OAuth2 callback server")
    print("-" * 80)
    server = start_callback_server(8000)
    print(f"✓ Server listening on http://localhost:8000")

    # STEP 3: Build authorization URL
    print("\n" + "-" * 80)
    print("STEP 3: Building authorization URL")
    print("-" * 80)

    state = secrets.token_urlsafe(32)

    auth_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope_string,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }

    auth_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(auth_params)}"

    logger.info(f"Authorization URL: {auth_url}")
    print(f"\n✓ Authorization URL built")
    print(f"\nURL: {auth_url[:100]}...")

    # STEP 4: Open browser
    print("\n" + "-" * 80)
    print("STEP 4: Opening browser for authorization")
    print("-" * 80)
    print("You will be redirected to UiPath Cloud to authorize the application.")
    print("After authorization, you'll be redirected back to localhost.")

    input("\nPress Enter to open browser...")

    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"Please manually open: {auth_url}")

    # STEP 5: Wait for callback
    print("\n" + "-" * 80)
    print("STEP 5: Waiting for OAuth2 callback...")
    print("-" * 80)
    print("Waiting for you to authorize in the browser...")

    # Wait for callback (with timeout)
    import time
    timeout = 300  # 5 minutes
    start_time = time.time()

    while not authorization_response.get('code') and not authorization_response.get('error'):
        if time.time() - start_time > timeout:
            print("\n✗ Timeout waiting for authorization")
            server.shutdown()
            sys.exit(1)
        time.sleep(0.5)

    server.shutdown()

    if authorization_response.get('error'):
        print(f"\n✗ Authorization failed!")
        print(f"Error: {authorization_response['error']}")
        print(f"Description: {authorization_response['error_description']}")
        sys.exit(1)

    auth_code = authorization_response['code']
    print(f"\n✓ Authorization code received: {auth_code[:20]}...")

    # Verify state
    if authorization_response['state'] != state:
        print("\n✗ State mismatch! Possible CSRF attack")
        sys.exit(1)
    print("✓ State verified")

    # STEP 6: Exchange code for token
    print("\n" + "-" * 80)
    print("STEP 6: Exchanging authorization code for access token")
    print("-" * 80)

    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }

    logger.info(f"POST {TOKEN_ENDPOINT}")
    logger.debug("Token request parameters:")
    for key, value in token_data.items():
        if key in ['client_secret', 'code', 'code_verifier']:
            logger.debug(f"  {key}: {value[:20] if value else 'None'}...")
        else:
            logger.debug(f"  {key}: {value}")

    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        print(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            token_response = response.json()
            print("\n✓ Access token received!")

            access_token = token_response.get('access_token')
            token_type = token_response.get('token_type', 'Bearer')
            expires_in = token_response.get('expires_in')

            print(f"\nToken type: {token_type}")
            print(f"Expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
            print(f"Access token (first 30 chars): {access_token[:30]}...")

            logger.debug(f"Full token response: {json.dumps(token_response, indent=2)}")

            # STEP 7: Test the token
            print("\n" + "-" * 80)
            print("STEP 7: Testing access token with API call")
            print("-" * 80)

            api_url = f"{UIPATH_BASE_URL}/{account_name}/{tenant_name}/odata/Users/UiPath.Server.Configuration.OData.GetCurrentUser"

            headers = {
                'Authorization': f'{token_type} {access_token}',
                'Content-Type': 'application/json'
            }

            print(f"API URL: {api_url}")

            api_response = requests.get(api_url, headers=headers)
            print(f"Response status: {api_response.status_code}")

            if api_response.status_code == 200:
                user_data = api_response.json()
                print("\n✓ API call successful!")
                print(f"\nUsername: {user_data.get('UserName')}")
                print(f"Email: {user_data.get('EmailAddress')}")
                print(f"Full Name: {user_data.get('FullName')}")

            else:
                print(f"\n✗ API call failed")
                print(f"Response: {api_response.text}")

        else:
            print(f"\n✗ Token exchange failed!")
            print(f"Response: {response.text}")
            logger.error(f"Token exchange failed: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception("Token exchange failed")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("✓ AUTHORIZATION CODE FLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nCheck 'oauth2_authcode_debug.log' for detailed logs\n")


if __name__ == "__main__":
    main()
