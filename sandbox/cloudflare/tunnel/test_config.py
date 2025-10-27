#!/usr/bin/env python3
"""
Configuration validator for multi-profile OAuth setup
Tests that all required environment variables are present and valid
"""

from dotenv import dotenv_values
import sys
import re

def validate_config():
    """Validate configuration and report any issues"""

    print("=" * 80)
    print("Multi-Profile OAuth2 Configuration Validator")
    print("=" * 80)
    print()

    # Load config
    try:
        config = dotenv_values(".env")
    except Exception as e:
        print(f"[ERR] ERROR: Cannot load .env file: {e}")
        print()
        print("Make sure you have created .env from .env.example:")
        print("  cp .env.example .env")
        return False

    if not config:
        print("[ERR] ERROR: .env file is empty or not found")
        print()
        print("Make sure you have created .env from .env.example:")
        print("  cp .env.example .env")
        return False

    print("[OK] Found .env file")
    print()

    # Required base fields
    base_fields = {
        "ACCOUNT_LOGICAL_NAME": "UiPath account name",
        "TENANT_LOGICAL_NAME": "UiPath tenant name",
        "BASE_URL": "UiPath base URL",
        "PUBLIC_URL": "Public URL for OAuth callbacks",
    }

    all_valid = True

    # Check base configuration
    print("Base Configuration:")
    print("-" * 80)

    for field, description in base_fields.items():
        value = config.get(field)

        if not value or value.startswith("your-"):
            print(f"[ERR] {field}: Missing or not configured")
            print(f"   -> {description}")
            all_valid = False
        else:
            print(f"[OK] {field}: {value}")
        print()

    # Discover profiles
    print("Profile Discovery:")
    print("-" * 80)

    # Only look for profiles that have CLIENT_ID defined
    profile_pattern = re.compile(r'^PROFILE_(\w+)_CLIENT_ID$')
    profile_names = set()

    for key in config.keys():
        match = profile_pattern.match(key)
        if match:
            profile_names.add(match.group(1))

    if not profile_names:
        print("[ERR] No profiles found!")
        print("   -> Add PROFILE_<name>_* variables to .env")
        print()
        print("Example:")
        print("  PROFILE_c01_CLIENT_ID=your-client-id")
        print("  PROFILE_c01_CLIENT_SECRET=your-secret")
        print("  PROFILE_c01_GRANT=client_credentials")
        print("  PROFILE_c01_SCOPES=OR.Execution OR.Assets")
        all_valid = False
    else:
        print(f"[OK] Found {len(profile_names)} profile(s): {', '.join(sorted(profile_names))}")
    print()

    # Validate each profile
    for profile_name in sorted(profile_names):
        print(f"Profile: {profile_name}")
        print("-" * 80)

        prefix = f"PROFILE_{profile_name}_"

        # Required fields
        client_id = config.get(f"{prefix}CLIENT_ID")
        grant = config.get(f"{prefix}GRANT")
        scopes = config.get(f"{prefix}SCOPES")

        # Check CLIENT_ID
        if not client_id or client_id.startswith("your-"):
            print(f"[ERR] {prefix}CLIENT_ID: Missing or not configured")
            all_valid = False
        else:
            print(f"[OK] {prefix}CLIENT_ID: {client_id}")

        # Check GRANT
        if not grant:
            print(f"[ERR] {prefix}GRANT: Missing")
            all_valid = False
        elif grant not in ["client_credentials", "authorization_code", "authorization_code_pkce"]:
            print(f"[WARN]  {prefix}GRANT: Unknown value '{grant}'")
            print(f"   -> Should be: client_credentials, authorization_code, or authorization_code_pkce")
            all_valid = False
        else:
            print(f"[OK] {prefix}GRANT: {grant}")

        # Check SCOPES
        if not scopes:
            print(f"[WARN]  {prefix}SCOPES: Missing (will use defaults)")
        else:
            print(f"[OK] {prefix}SCOPES: {scopes}")

        # Grant-specific validation
        if grant == "client_credentials":
            # Requires CLIENT_SECRET
            client_secret = config.get(f"{prefix}CLIENT_SECRET")
            if not client_secret or client_secret.startswith("your-"):
                print(f"[ERR] {prefix}CLIENT_SECRET: Required for client_credentials grant")
                all_valid = False
            else:
                masked_secret = f"{client_secret[:8]}...{client_secret[-4:]}" if len(client_secret) > 12 else "***"
                print(f"[OK] {prefix}CLIENT_SECRET: {masked_secret}")

        elif grant in ["authorization_code", "authorization_code_pkce"]:
            # Requires REDIRECT
            redirect = config.get(f"{prefix}REDIRECT")
            if not redirect or redirect.startswith("your-"):
                print(f"[ERR] {prefix}REDIRECT: Required for authorization code flows")
                all_valid = False
            else:
                print(f"[OK] {prefix}REDIRECT: {redirect}")

                # Validate redirect URL format
                if not redirect.startswith("http://") and not redirect.startswith("https://"):
                    print(f"[WARN]  {prefix}REDIRECT: Should start with http:// or https://")
                    all_valid = False

            # Check if CLIENT_SECRET is present (optional for authorization_code_pkce, required for authorization_code)
            client_secret = config.get(f"{prefix}CLIENT_SECRET")
            if grant == "authorization_code_pkce":
                if client_secret:
                    print(f"[INFO] {prefix}CLIENT_SECRET: Present (not required for PKCE, but allowed)")
                else:
                    print(f"[INFO] {prefix}CLIENT_SECRET: Not set (correct for PKCE flow)")
            elif grant == "authorization_code":
                if not client_secret or client_secret.startswith("your-"):
                    print(f"[ERR] {prefix}CLIENT_SECRET: Required for authorization_code grant")
                    all_valid = False
                else:
                    masked_secret = f"{client_secret[:8]}...{client_secret[-4:]}" if len(client_secret) > 12 else "***"
                    print(f"[OK] {prefix}CLIENT_SECRET: {masked_secret}")

        print()

    # Validate URLs
    print("URL Validation:")
    print("-" * 80)

    public_url = config.get("PUBLIC_URL", "")

    if public_url:
        if not public_url.startswith("http://") and not public_url.startswith("https://"):
            print(f"[WARN]  PUBLIC_URL should start with http:// or https://")
            print(f"   Current: {public_url}")
            all_valid = False
        else:
            print(f"[OK] PUBLIC_URL format looks valid")

        if public_url.endswith("/"):
            print(f"[WARN]  PUBLIC_URL should not end with a slash")
            print(f"   Current: {public_url}")
            print(f"   Should be: {public_url.rstrip('/')}")
            all_valid = False

        # Build full callback URLs for profiles with REDIRECT
        account = config.get("ACCOUNT_LOGICAL_NAME", "")
        tenant = config.get("TENANT_LOGICAL_NAME", "")

        print()
        print("Callback URLs:")
        for profile_name in sorted(profile_names):
            prefix = f"PROFILE_{profile_name}_"
            grant = config.get(f"{prefix}GRANT")
            redirect = config.get(f"{prefix}REDIRECT")

            if grant in ["authorization_code", "authorization_code_pkce"]:
                if redirect:
                    print(f"\n[OK] Profile '{profile_name}' callback URL:")
                    print(f"  {redirect}")
                    print(f"  -> Configure this in UiPath External Application for '{profile_name}'")
                else:
                    # Generate default callback path
                    default_path = f"/cb/orch/dev/{account}/{tenant}/fullrw/{profile_name}"
                    full_url = f"{public_url}{default_path}"
                    print(f"\n[INFO] Profile '{profile_name}' default callback URL:")
                    print(f"  {full_url}")
                    print(f"  -> Will use this if REDIRECT not specified")

    print()
    print("=" * 80)

    if all_valid:
        print("[OK] Configuration is valid!")
        print()
        print("Next steps:")
        print("1. Verify callback URLs are configured in UiPath External Applications")
        print("2. Make sure your reverse proxy/tunnel routes to localhost:8000")
        print("3. Run: make run")
        print("   (or: uv run python oauth_multi_app_v2.py)")
        print("4. Open: " + public_url)
    else:
        print("[ERR] Configuration has errors - please fix them before running")
        print()
        print("Edit .env file and provide the required values")

    print("=" * 80)
    print()

    return all_valid


if __name__ == "__main__":
    valid = validate_config()
    sys.exit(0 if valid else 1)
