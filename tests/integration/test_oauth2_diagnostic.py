#!/usr/bin/env python3
"""
OAuth2 Diagnostic Script - Non-interactive validation
Tests OAuth2 configuration without requiring browser interaction
"""

import json
import logging
import sys
import secrets
import hashlib
import base64
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

import requests
from dotenv import dotenv_values

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

UIPATH_BASE_URL = "https://cloud.uipath.com"
AUTHORIZATION_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/authorize"
TOKEN_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/token"

def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def main():
    print("\n" + "=" * 80)
    print("OAuth2 Configuration Diagnostic")
    print("=" * 80 + "\n")

    # Load config
    config_file = ".uipathcloud.env"
    if not Path(config_file).exists():
        print(f"ERROR: {config_file} not found")
        sys.exit(1)

    config = dotenv_values(config_file)

    # Test different client_ids
    client_ids = [
        ("From .env file", config.get('CLIENT_ID')),
        ("Mentioned for Swagger", "a9540c02-22be-4673-bed6-90f0d827d23a")
    ]

    client_secret = config.get('CLIENT_SECRET')
    account_name = config.get('ACCOUNT_LOGICAL_NAME')
    tenant_name = config.get('TENANT_LOGICAL_NAME')

    print("Configuration loaded:")
    print(f"  Account: {account_name}")
    print(f"  Tenant: {tenant_name}")
    print()

    # Test 1: Client Credentials flow (works without browser)
    print("-" * 80)
    print("TEST 1: Client Credentials Flow (machine-to-machine)")
    print("-" * 80)

    for source, client_id in client_ids:
        if not client_id:
            continue

        print(f"\nTesting with client_id {source}: {client_id[:20]}...")

        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'OR.Administration OR.Execution OR.Monitoring'
        }

        try:
            response = requests.post(TOKEN_ENDPOINT, data=data)

            if response.status_code == 200:
                token_data = response.json()
                print(f"  [OK] SUCCESS - Got access token")
                print(f"       Token expires in: {token_data.get('expires_in')} seconds")
                print(f"       Token type: {token_data.get('token_type')}")
            elif response.status_code == 400:
                error = response.json()
                print(f"  [FAIL] FAILED - {error.get('error')}")
                print(f"         Description: {error.get('error_description')}")
            else:
                print(f"  [FAIL] FAILED - Status {response.status_code}")
                print(f"         Response: {response.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    # Test 2: Validate Authorization URL construction
    print("\n" + "-" * 80)
    print("TEST 2: Authorization Code Flow - URL Validation")
    print("-" * 80)

    redirect_uris = [
        ("ngrok", "https://8c7d84249f83.ngrok-free.app/oauth2-redirect.html"),
        ("localhost", "http://localhost:8000/oauth2-redirect.html")
    ]

    for source, client_id in client_ids:
        if not client_id:
            continue

        print(f"\nClient ID {source}: {client_id[:20]}...")

        for uri_type, redirect_uri in redirect_uris:
            code_verifier, code_challenge = generate_pkce_pair()
            state = secrets.token_urlsafe(32)

            auth_params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'OR.Administration OR.Execution OR.Monitoring',
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            }

            auth_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(auth_params)}"

            print(f"\n  {uri_type.upper()} redirect URI: {redirect_uri}")
            print(f"  Authorization URL: {auth_url[:100]}...")

            # Check if the authorization endpoint is reachable
            try:
                # Don't follow redirects, just check if endpoint responds
                response = requests.get(AUTHORIZATION_ENDPOINT, params={'client_id': client_id}, allow_redirects=False, timeout=5)

                if response.status_code in [200, 302, 303]:
                    print(f"    [OK] Authorization endpoint is reachable")
                else:
                    print(f"    [WARN] Authorization endpoint returned status {response.status_code}")
            except Exception as e:
                print(f"    [FAIL] Could not reach authorization endpoint: {e}")

    # Test 3: Swagger UI configuration check
    print("\n" + "-" * 80)
    print("TEST 3: Swagger UI Configuration Check")
    print("-" * 80)

    swagger_html = Path("docs/swagger.html")
    if swagger_html.exists():
        content = swagger_html.read_text()

        # Check OAuth2 redirect URL configuration
        if "oauth2RedirectUrl:" in content:
            print("  [OK] oauth2RedirectUrl is configured in swagger.html")
            if "window.location.origin" in content:
                print("    [OK] Using dynamic URL (works with ngrok)")
            else:
                print("    [WARN] Using hardcoded URL (may not work with ngrok)")
        else:
            print("  [FAIL] oauth2RedirectUrl not found in swagger.html")

        # Check if PKCE is enabled
        if "usePkceWithAuthorizationCodeGrant: true" in content:
            print("  [OK] PKCE is enabled")
        else:
            print("  [WARN] PKCE is not enabled")

        # Check initOAuth
        if "initOAuth" in content:
            print("  [OK] initOAuth is configured")
        else:
            print("  [FAIL] initOAuth not found")
    else:
        print("  [FAIL] swagger.html not found")

    # Test 4: Check if oauth2-redirect.html exists
    print("\n" + "-" * 80)
    print("TEST 4: OAuth2 Redirect Handler Check")
    print("-" * 80)

    redirect_html = Path("docs/oauth2-redirect.html")
    if redirect_html.exists():
        print("  [OK] oauth2-redirect.html exists")
        content = redirect_html.read_text()
        if "swaggerUIRedirectOauth2" in content:
            print("    [OK] Contains Swagger OAuth2 redirect handler")
        else:
            print("    [WARN] May not be the correct redirect handler")
    else:
        print("  [FAIL] oauth2-redirect.html not found")

    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print("\nTo fix Error #200 in Swagger UI:")
    print("1. Use the client_id that successfully passed TEST 1 (Client Credentials)")
    print("2. In UiPath Cloud External Applications:")
    print("   - Find the app with that client_id")
    print("   - Ensure 'Authorization Code' grant type is enabled")
    print("   - Set redirect URI to: https://8c7d84249f83.ngrok-free.app/oauth2-redirect.html")
    print("3. In Swagger UI, use that same client_id and its secret")
    print("4. Access Swagger via: https://8c7d84249f83.ngrok-free.app/swagger.html")
    print("\nFor detailed logs, check oauth2_debug.log")

if __name__ == "__main__":
    main()
