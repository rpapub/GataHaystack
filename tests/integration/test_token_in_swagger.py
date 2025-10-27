#!/usr/bin/env python3
"""
Test if the token works with different API endpoints
"""

import requests
from dotenv import dotenv_values

# Load config
config = dotenv_values(".uipathcloud.env")

client_id = config.get('CLIENT_ID')
client_secret = config.get('CLIENT_SECRET')
account = config.get('ACCOUNT_LOGICAL_NAME')
tenant = config.get('TENANT_LOGICAL_NAME')

print("\n" + "=" * 80)
print("Token Testing for Swagger UI")
print("=" * 80 + "\n")

# Get token
print("Step 1: Getting access token...")
token_response = requests.post(
    "https://cloud.uipath.com/identity_/connect/token",
    data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'OR.Administration OR.Execution OR.Monitoring OR.Assets OR.Jobs OR.Folders OR.Robots'
    }
)

if token_response.status_code != 200:
    print(f"[FAIL] Token request failed: {token_response.status_code}")
    print(token_response.text)
    exit(1)

token = token_response.json()['access_token']
print(f"[OK] Got token: {token[:30]}...")

# Test different API endpoints
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'X-UIPATH-OrganizationUnitId': ''  # Will be set per request
}

print("\n" + "-" * 80)
print("Step 2: Testing API Endpoints")
print("-" * 80)

# Test 1: Folders (simpler endpoint)
print("\n[TEST 1] GET /odata/Folders")
url1 = f"https://cloud.uipath.com/{account}/{tenant}/odata/Folders"
print(f"URL: {url1}")

response1 = requests.get(url1, headers=headers)
print(f"Status: {response1.status_code}")

if response1.status_code == 200:
    data = response1.json()
    print(f"[OK] Success! Found {data.get('@odata.count', len(data.get('value', [])))} folders")
    if data.get('value'):
        print(f"     First folder: {data['value'][0].get('DisplayName', 'N/A')}")
elif response1.status_code == 401:
    print(f"[FAIL] 401 Unauthorized - Token invalid or expired")
elif response1.status_code == 403:
    print(f"[FAIL] 403 Forbidden - Token lacks permissions")
    print(f"       Response: {response1.text[:200]}")
else:
    print(f"[FAIL] {response1.status_code} - {response1.text[:200]}")

# Test 2: Releases (common endpoint)
print("\n[TEST 2] GET /odata/Releases")
url2 = f"https://cloud.uipath.com/{account}/{tenant}/odata/Releases"
print(f"URL: {url2}")

response2 = requests.get(url2, headers=headers)
print(f"Status: {response2.status_code}")

if response2.status_code == 200:
    data = response2.json()
    print(f"[OK] Success! Found {data.get('@odata.count', len(data.get('value', [])))} releases")
elif response2.status_code == 401:
    print(f"[FAIL] 401 Unauthorized - Token invalid")
elif response2.status_code == 403:
    print(f"[FAIL] 403 Forbidden - Need OR.Execution or OR.Execution.Read scope")
else:
    print(f"[FAIL] {response2.status_code} - {response2.text[:200]}")

# Test 3: Assets
print("\n[TEST 3] GET /odata/Assets")
url3 = f"https://cloud.uipath.com/{account}/{tenant}/odata/Assets"
print(f"URL: {url3}")

response3 = requests.get(url3, headers=headers)
print(f"Status: {response3.status_code}")

if response3.status_code == 200:
    data = response3.json()
    print(f"[OK] Success! Found {data.get('@odata.count', len(data.get('value', [])))} assets")
elif response3.status_code == 403:
    print(f"[FAIL] 403 Forbidden - Need OR.Assets or OR.Assets.Read scope")
else:
    print(f"[FAIL] {response3.status_code}")

# Summary
print("\n" + "=" * 80)
print("SWAGGER UI SETUP")
print("=" * 80)
print("\n1. Copy this token:")
print(f"\n{token}\n")
print("2. In Swagger UI (https://8c7d84249f83.ngrok-free.app/swagger.html):")
print("   - At the top, set server variables:")
print(f"     * account: {account}")
print(f"     * tenant: {tenant}")
print("   - Click 'Authorize' button")
print("   - In 'bearerAuth', paste the token above")
print("   - Click 'Authorize', then 'Close'")
print("\n3. Try the endpoints that returned [OK] above")
print("\nNote: If you get 403 Forbidden, that endpoint needs different scopes")
print("      than what your External Application has enabled.")
print()
