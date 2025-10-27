#!/usr/bin/env python3
"""
Minimal OAuth2 Authentication Test Script for UiPath Cloud
Reads configuration from .uipathcloud.env file
Provides detailed logging and debugging output
"""

import json
import logging
import sys
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, parse_qs, urlparse

import requests
from dotenv import dotenv_values

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oauth2_debug.log')
    ]
)

logger = logging.getLogger(__name__)

# UiPath Cloud endpoints
UIPATH_BASE_URL = "https://cloud.uipath.com"
AUTHORIZATION_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/authorize"
TOKEN_ENDPOINT = f"{UIPATH_BASE_URL}/identity_/connect/token"

class UiPathOAuth2:
    """Minimal OAuth2 client for UiPath Cloud with debugging"""

    def __init__(self, config_file: str = ".uipathcloud.env"):
        """Initialize OAuth2 client from .env file"""
        logger.info(f"Initializing OAuth2 client from {config_file}")

        self.config_path = Path(config_file)
        if not self.config_path.exists():
            logger.error(f"Configuration file not found: {config_file}")
            raise FileNotFoundError(f"Config file not found: {config_file}")

        # Load configuration
        self.config = dotenv_values(config_file)
        logger.debug(f"Loaded configuration keys: {list(self.config.keys())}")

        # Extract OAuth2 settings
        self.client_id = self.config.get('CLIENT_ID')
        self.client_secret = self.config.get('CLIENT_SECRET')
        self.scope = self.config.get('SCOPE', 'OR.Administration OR.Execution OR.Monitoring')
        self.redirect_uri = self.config.get('REDIRECT_URI', 'http://localhost:8000/oauth2-redirect.html')
        self.grant_type = self.config.get('GRANT_TYPE', 'client_credentials')

        # Account identifiers
        self.account_logical_name = self.config.get('ACCOUNT_LOGICAL_NAME')
        self.tenant_logical_name = self.config.get('TENANT_LOGICAL_NAME')

        # Validate required fields
        self._validate_config()

        self.access_token: Optional[str] = None
        self.token_type: Optional[str] = None
        self.expires_in: Optional[int] = None

        logger.info("OAuth2 client initialized successfully")
        logger.debug(f"Grant type: {self.grant_type}")
        logger.debug(f"Client ID: {self.client_id[:10]}...")
        logger.debug(f"Scope: {self.scope}")

    def _validate_config(self):
        """Validate required configuration parameters"""
        logger.info("Validating configuration...")

        missing = []
        if not self.client_id:
            missing.append('CLIENT_ID')
        if not self.client_secret:
            missing.append('CLIENT_SECRET')

        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        logger.info("Configuration validation passed")

    def get_token_client_credentials(self) -> dict:
        """
        Get access token using client credentials flow (for machine-to-machine)
        This is the simplest flow - no user interaction needed
        """
        logger.info("=" * 80)
        logger.info("Starting CLIENT CREDENTIALS flow")
        logger.info("=" * 80)

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }

        logger.debug("Token request parameters:")
        logger.debug(f"  Endpoint: {TOKEN_ENDPOINT}")
        logger.debug(f"  Grant type: {data['grant_type']}")
        logger.debug(f"  Client ID: {self.client_id[:10]}...")
        logger.debug(f"  Scope: {data['scope']}")
        logger.debug(f"  Client secret: {'*' * 10}")

        try:
            logger.info("Sending POST request to token endpoint...")
            response = requests.post(
                TOKEN_ENDPOINT,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                token_data = response.json()
                logger.info("✓ Token retrieved successfully!")
                logger.debug(f"Token response: {json.dumps(token_data, indent=2)}")

                self.access_token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'Bearer')
                self.expires_in = token_data.get('expires_in')

                logger.info(f"Token type: {self.token_type}")
                logger.info(f"Expires in: {self.expires_in} seconds")
                logger.info(f"Access token (first 20 chars): {self.access_token[:20]}...")

                return token_data
            else:
                logger.error(f"✗ Token request failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Request failed: {str(e)}")
            raise

    def get_authorization_url(self) -> str:
        """
        Generate authorization URL for authorization code flow
        (requires user to login in browser)
        """
        logger.info("=" * 80)
        logger.info("Generating AUTHORIZATION CODE flow URL")
        logger.info("=" * 80)

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
            'state': 'random_state_string_123'  # Should be random in production
        }

        auth_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

        logger.info("Authorization URL generated:")
        logger.info(auth_url)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Open this URL in your browser")
        logger.info("2. Login and authorize the application")
        logger.info("3. Copy the 'code' parameter from the redirect URL")
        logger.info("4. Call exchange_code_for_token(code) with that code")

        return auth_url

    def exchange_code_for_token(self, authorization_code: str) -> dict:
        """
        Exchange authorization code for access token
        """
        logger.info("=" * 80)
        logger.info("Exchanging authorization code for access token")
        logger.info("=" * 80)

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }

        logger.debug("Token exchange parameters:")
        logger.debug(f"  Code: {authorization_code[:20]}...")
        logger.debug(f"  Redirect URI: {self.redirect_uri}")

        try:
            logger.info("Sending POST request to token endpoint...")
            response = requests.post(
                TOKEN_ENDPOINT,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            logger.debug(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()
                logger.info("✓ Token retrieved successfully!")
                logger.debug(f"Token response: {json.dumps(token_data, indent=2)}")

                self.access_token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'Bearer')
                self.expires_in = token_data.get('expires_in')

                return token_data
            else:
                logger.error(f"✗ Token exchange failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Request failed: {str(e)}")
            raise

    def test_token(self) -> dict:
        """
        Test the access token by making an API call to get current user
        """
        logger.info("=" * 80)
        logger.info("Testing access token with API call")
        logger.info("=" * 80)

        if not self.access_token:
            logger.error("No access token available. Call get_token_client_credentials() first")
            raise ValueError("No access token available")

        headers = {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Build API URL with account/tenant if provided
        api_url = f"{UIPATH_BASE_URL}"
        if self.account_logical_name:
            api_url += f"/{self.account_logical_name}"
            if self.tenant_logical_name:
                api_url += f"/{self.tenant_logical_name}"
        api_url += "/odata/Users/UiPath.Server.Configuration.OData.GetCurrentUser"

        logger.info(f"Making GET request to: {api_url}")
        logger.debug(f"Headers: {{'Authorization': '{self.token_type} ***', 'Content-Type': 'application/json'}}")

        try:
            response = requests.get(api_url, headers=headers)

            logger.debug(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                user_data = response.json()
                logger.info("✓ API call successful!")
                logger.info("Current user information:")
                logger.info(json.dumps(user_data, indent=2, default=str))
                return user_data
            else:
                logger.error(f"✗ API call failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")

                if response.status_code == 401:
                    logger.error("Token appears to be invalid or expired")
                elif response.status_code == 403:
                    logger.error("Token is valid but doesn't have required permissions")

                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API request failed: {str(e)}")
            raise


def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("UiPath OAuth2 Authentication Test Script")
    print("=" * 80 + "\n")

    try:
        # Initialize OAuth2 client
        oauth = UiPathOAuth2()

        print("\nSelect authentication flow:")
        print("1. Client Credentials (machine-to-machine, recommended for testing)")
        print("2. Authorization Code (user login via browser)")

        choice = input("\nEnter choice (1 or 2): ").strip()

        if choice == '1':
            # Client credentials flow
            token_data = oauth.get_token_client_credentials()
            print(f"\n✓ Access token obtained: {oauth.access_token[:30]}...")

            # Test the token
            input("\nPress Enter to test the token with an API call...")
            user_data = oauth.test_token()

        elif choice == '2':
            # Authorization code flow
            auth_url = oauth.get_authorization_url()

            print("\nOpening browser...")
            webbrowser.open(auth_url)

            print("\nAfter authorizing, you'll be redirected to a URL like:")
            print("http://localhost:8000/oauth2-redirect.html?code=XXXXX&state=...")

            auth_code = input("\nPaste the 'code' parameter value here: ").strip()

            if auth_code:
                token_data = oauth.exchange_code_for_token(auth_code)
                print(f"\n✓ Access token obtained: {oauth.access_token[:30]}...")

                # Test the token
                input("\nPress Enter to test the token with an API call...")
                user_data = oauth.test_token()
            else:
                print("No authorization code provided")
        else:
            print("Invalid choice")
            return

        print("\n" + "=" * 80)
        print("✓ Authentication test completed successfully!")
        print("=" * 80)
        print(f"\nCheck 'oauth2_debug.log' for detailed logs")

    except FileNotFoundError as e:
        print(f"\n✗ Configuration file not found: {e}")
        print("\nCreate a .uipathcloud.env file with your OAuth2 credentials")
        print("See .uipathcloud.env.example for the required format")
        sys.exit(1)

    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nCheck your .uipathcloud.env file has all required fields")
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n✗ Error: {e}")
        print(f"\nCheck oauth2_debug.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
