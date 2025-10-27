#!/usr/bin/env python3
"""
Automatic OAuth2 Authentication Test Script for UiPath Cloud
Runs client_credentials flow automatically without user input
"""

import json
import logging
import sys
from pathlib import Path

import requests
from dotenv import dotenv_values

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oauth2_debug.log')
    ]
)

logger = logging.getLogger(__name__)

# UiPath Cloud endpoints
UIPATH_BASE_URL = "https://cloud.uipath.com"
TOKEN_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/token"

def main():
    print("\n" + "=" * 80)
    print("UiPath OAuth2 - Automatic Client Credentials Test")
    print("=" * 80 + "\n")

    # Load config
    config_file = ".uipathcloud.env"
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_file}")
        print("Please create it from .uipathcloud.env.example")
        sys.exit(1)

    config = dotenv_values(config_file)
    logger.info(f"Loaded config keys: {list(config.keys())}")

    client_id = config.get('CLIENT_ID')
    client_secret = config.get('CLIENT_SECRET')
    scope = config.get('SCOPE', 'OR.Administration OR.Execution OR.Monitoring')
    account_name = config.get('ACCOUNT_LOGICAL_NAME')
    tenant_name = config.get('TENANT_LOGICAL_NAME')

    if not client_id or not client_secret:
        print("ERROR: CLIENT_ID and CLIENT_SECRET are required in .uipathcloud.env")
        sys.exit(1)

    print(f"Client ID: {client_id[:20]}...")
    print(f"Scope: {scope}")
    print(f"Account: {account_name}")
    print(f"Tenant: {tenant_name}")
    print()

    # Step 1: Get access token
    print("-" * 80)
    print("STEP 1: Getting access token (client_credentials flow)")
    print("-" * 80)

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope
    }

    logger.info(f"POST {TOKEN_ENDPOINT}")
    logger.debug(f"Request data: grant_type={data['grant_type']}, scope={scope}")

    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        print(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            token_data = response.json()
            print("SUCCESS: Token retrieved!\n")

            access_token = token_data.get('access_token')
            token_type = token_data.get('token_type', 'Bearer')
            expires_in = token_data.get('expires_in')

            print(f"Token type: {token_type}")
            print(f"Expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
            print(f"Access token (first 30 chars): {access_token[:30]}...")
            print(f"Access token (last 30 chars): ...{access_token[-30:]}")

            logger.debug(f"Full token response: {json.dumps(token_data, indent=2)}")

        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            logger.error(f"Token request failed: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        logger.exception("Token request failed")
        sys.exit(1)

    # Step 2: Test the token with an API call
    print("\n" + "-" * 80)
    print("STEP 2: Testing token with API call (GetCurrentUser)")
    print("-" * 80)

    headers = {
        'Authorization': f'{token_type} {access_token}',
        'Content-Type': 'application/json'
    }

    # Build API URL
    api_url = f"{UIPATH_BASE_URL}"
    if account_name:
        api_url += f"/{account_name}"
        if tenant_name:
            api_url += f"/{tenant_name}"
    api_url += "/odata/Users/UiPath.Server.Configuration.OData.GetCurrentUser"

    print(f"API URL: {api_url}")
    logger.info(f"GET {api_url}")

    try:
        response = requests.get(api_url, headers=headers)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            user_data = response.json()
            print("SUCCESS: API call worked!\n")
            print("Current User Info:")
            print(f"  Username: {user_data.get('UserName')}")
            print(f"  Email: {user_data.get('EmailAddress')}")
            print(f"  Full Name: {user_data.get('FullName')}")
            print(f"  Tenant: {user_data.get('TenancyName')}")
            print(f"  User ID: {user_data.get('Id')}")

            logger.debug(f"Full user data: {json.dumps(user_data, indent=2, default=str)}")

        elif response.status_code == 401:
            print("FAILED: Token is invalid or expired (401 Unauthorized)")
            print(f"Response: {response.text}")
            logger.error(f"Authentication failed: {response.text}")
            sys.exit(1)

        elif response.status_code == 403:
            print("FAILED: Token is valid but lacks permissions (403 Forbidden)")
            print(f"Response: {response.text}")
            logger.error(f"Authorization failed: {response.text}")
            sys.exit(1)

        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            logger.error(f"API request failed: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        logger.exception("API request failed")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print("\nYour OAuth2 configuration is working correctly.")
    print("Check 'oauth2_debug.log' for detailed debug information.\n")

if __name__ == "__main__":
    main()
