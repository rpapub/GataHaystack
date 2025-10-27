#!/usr/bin/env python3
"""
Test if Swagger UI OAuth2 configuration will work
Simulates what Swagger UI does when you click Authorize
"""

import json
import sys
import secrets
from urllib.parse import urlencode
from dotenv import dotenv_values

print("\n" + "=" * 80)
print("Swagger UI OAuth2 Configuration Test")
print("=" * 80 + "\n")

# Load config
config = dotenv_values(".uipathcloud.env")

client_id = config.get('CLIENT_ID')
client_secret = config.get('CLIENT_SECRET')
redirect_uri = "https://8c7d84249f83.ngrok-free.app/oauth2-redirect.html"

print(f"Client ID: {client_id}")
print(f"Client Secret: {'*' * 20}")
print(f"Redirect URI: {redirect_uri}")
print()

# Test 1: Authorization URL WITHOUT PKCE (Confidential Application)
print("-" * 80)
print("TEST 1: Authorization URL (WITHOUT PKCE - for Confidential Apps)")
print("-" * 80)

state = secrets.token_urlsafe(32)

auth_params_no_pkce = {
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'response_type': 'code',
    'scope': 'OR.Administration OR.Execution OR.Monitoring OR.Assets OR.Jobs',
    'state': state
}

auth_url = f"https://cloud.uipath.com/identity_/connect/authorize?{urlencode(auth_params_no_pkce)}"

print("\n[OK] Authorization URL (what Swagger will use):")
print(auth_url)
print("\nThis URL should:")
print("  [1] Redirect you to UiPath login")
print("  [2] After login, redirect back to: " + redirect_uri)
print("  [3] NOT show Error #200")

# Test 2: What needs to match
print("\n" + "-" * 80)
print("TEST 2: Configuration Validation")
print("-" * 80)

print("\nIn UiPath Cloud External Application, verify:")
print(f"  [1] Client ID matches: {client_id}")
print(f"  [2] Application Type: Confidential Application")
print(f"  [3] Grant Types includes: Authorization Code")
print(f"  [4] Redirect URI includes: {redirect_uri}")
print(f"  [5] Client secret is: {client_secret[:20]}...")

print("\nIn Swagger UI (https://8c7d84249f83.ngrok-free.app/swagger.html):")
print("  [1] Click Authorize")
print(f"  [2] Enter client_id: {client_id}")
print(f"  [3] Enter client_secret: (from .env file)")
print("  [4] Select scopes")
print("  [5] Click Authorize")

# Test 3: Key difference
print("\n" + "-" * 80)
print("TEST 3: PKCE Status (Critical for Confidential Apps)")
print("-" * 80)

# Check swagger.html
swagger_html_path = "docs/swagger.html"
try:
    with open(swagger_html_path, 'r') as f:
        content = f.read()

    if "usePkceWithAuthorizationCodeGrant: false" in content:
        print("\n[OK] PKCE is DISABLED in swagger.html")
        print("     This is CORRECT for Confidential Applications")
    elif "usePkceWithAuthorizationCodeGrant: true" in content:
        print("\n[FAIL] PKCE is ENABLED in swagger.html")
        print("       This is WRONG for Confidential Applications")
        print("       UiPath rejects: Confidential App + PKCE = Error #200")
    else:
        print("\n[WARN] Could not find PKCE setting in swagger.html")

except Exception as e:
    print(f"\n[ERROR] Could not read swagger.html: {e}")

# Summary
print("\n" + "=" * 80)
print("EXPECTED BEHAVIOR")
print("=" * 80)

print("\nWhen you click Authorize in Swagger UI:")
print("  1. Browser opens UiPath login page")
print("  2. You log in with your UiPath credentials")
print("  3. You see: 'Authorize UiPath Orchestrator API Explorer'")
print("  4. You click 'Allow'")
print("  5. Browser redirects back to Swagger UI")
print("  6. You see 'Authorized' with a checkmark")
print("\nIf you see Error #200, the redirect URI doesn't match in UiPath Cloud.")
print("\nTo test: Open the authorization URL above in your browser manually.")
print("After login, it should redirect to the ngrok URL, not show an error.")
print()
