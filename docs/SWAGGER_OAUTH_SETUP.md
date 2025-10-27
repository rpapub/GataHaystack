# Swagger UI OAuth2 Setup Guide

## Problem: Error (#200) when authorizing in Swagger UI

This happens because the External Application in UiPath Cloud needs specific configuration for the redirect URI.

## Quick Fix Checklist

If you're getting **Error (#200)**, follow these steps:

1. ✅ **Check your ngrok URL** - Copy the current ngrok forwarding URL
2. ✅ **Update UiPath redirect URI** - Go to External Applications and set redirect URI to: `https://YOUR-NGROK-URL/oauth2-redirect.html`
3. ✅ **Save the External Application** in UiPath Cloud
4. ✅ **Access Swagger via ngrok** - Open `https://YOUR-NGROK-URL/swagger.html` (NOT localhost)
5. ✅ **Use the SAME client_id** from your External Application

## Using with ngrok (Recommended)

Since OAuth2 requires HTTPS for security, using **ngrok** is recommended:

### Complete Setup with ngrok

1. **Start the HTTP server** (Terminal 1):
   ```bash
   cd docs
   python -m http.server 8000
   ```

2. **Start ngrok** (Terminal 2):
   ```bash
   ngrok http 8000
   ```

3. **Copy the ngrok URL** (looks like `https://abcd-1234-5678.ngrok.io`)
   ```
   Forwarding  https://abcd-1234-5678.ngrok.io -> http://localhost:8000
   ```

4. **Important**: Note your ngrok URL - you'll need it for step 5 and step 7

5. **Configure redirect URI in UiPath** using your ngrok URL:
   ```
   https://abcd-1234-5678.ngrok.io/oauth2-redirect.html
   ```
   (Replace `abcd-1234-5678` with YOUR actual ngrok subdomain)

6. **Save the External Application** in UiPath Cloud

7. **Open Swagger UI** using your ngrok URL:
   ```
   https://abcd-1234-5678.ngrok.io/swagger.html
   ```
   **Do NOT use localhost** - must use the same URL as redirect URI

## Solution: Configure Your UiPath External Application

### Step 1: Go to UiPath Cloud Admin
1. Open https://cloud.uipath.com/portal_/admin/external-applications
2. Find your application (or create a new one)

### Step 2: Configure Application Settings

**Application Type:**
- ✅ Select: **Confidential Application** (if you want to use client_secret)
- ✅ OR Select: **Public Application** (for browser-only, no secret)

**Grant Types** (check BOTH):
- ✅ Authorization Code
- ✅ Client Credentials

**Redirect URIs** (add the URL you'll use):

For **ngrok** (recommended):
```
https://your-ngrok-url.ngrok.io/oauth2-redirect.html
```
Example: `https://abcd-1234-5678.ngrok.io/oauth2-redirect.html`

For **localhost** (testing only, may not work due to HTTPS requirement):
```
http://localhost:8000/oauth2-redirect.html
```

**IMPORTANT**: The redirect URI in UiPath Cloud must EXACTLY match where you access Swagger UI from

**Scopes** (select the ones you need):
- ✅ OR.Administration, OR.Administration.Read, OR.Administration.Write
- ✅ OR.Assets, OR.Assets.Read, OR.Assets.Write
- ✅ OR.Execution, OR.Execution.Read, OR.Execution.Write
- ✅ OR.Folders, OR.Folders.Read, OR.Folders.Write
- ✅ OR.Jobs, OR.Jobs.Read, OR.Jobs.Write
- ✅ OR.Monitoring, OR.Monitoring.Read, OR.Monitoring.Write
- ✅ OR.Robots, OR.Robots.Read, OR.Robots.Write
- ✅ OR.Users, OR.Users.Read, OR.Users.Write

### Step 3: Save and Copy Credentials
- Copy the **Client ID**
- Copy the **Client Secret** (if using Confidential Application)

## Using Swagger UI

### Option A: Authorization Code Flow (RECOMMENDED for Swagger UI)

1. **Start the HTTP server** (if not running):
   ```bash
   uv run python -m http.server 8000 --directory docs
   ```

2. **Open Swagger UI**:
   ```
   http://localhost:8000/swagger.html
   ```

3. **Fill in the Server Variables** at the top:
   - `account`: Your account name (e.g., `cprimadotnet`)
   - `tenant`: Your tenant name (e.g., `cprima`)

4. **Click "Authorize"** button (top right)

5. **In the oauth2 (authorizationCode) section**:
   - **client_id**: Paste your Client ID (e.g., `a9540c02-22be-4673-bed6-90f0d827d23a`)
   - **client_secret**:
     - If **Confidential Application**: Paste your secret
     - If **Public Application**: Leave EMPTY
   - **Select scopes**: Check the scopes you need
   - Click **"Authorize"**

6. **Login in browser**:
   - You'll be redirected to UiPath Cloud
   - Login with your credentials
   - Authorize the application
   - You'll be redirected back to localhost

7. **Done!** You should see "Authorized" in Swagger UI

### Option B: Client Credentials Flow (for scripts)

Use the Python test scripts:
```bash
# Automatic test
uv run python test_oauth2_auto.py

# Interactive authorization code test
uv run python test_oauth2_authcode.py
```

## Troubleshooting

### Error: "Error (#200)" or "An unknown error has occurred"

**Cause**: Redirect URI doesn't match in UiPath External Application

**Solution**:
1. Check External Application settings in UiPath Cloud
2. Ensure redirect URI EXACTLY matches where you're accessing Swagger:
   - If using ngrok: `https://your-ngrok-url.ngrok.io/oauth2-redirect.html`
   - If using localhost: `http://localhost:8000/oauth2-redirect.html`
3. No trailing slash
4. Must be lowercase
5. Port must match (8000)
6. Protocol must match (http vs https)

**ngrok specific**:
- Each time you restart ngrok, you get a NEW URL
- You must UPDATE the redirect URI in UiPath Cloud with the new ngrok URL
- OR use ngrok paid plan for a static subdomain

### Error: "invalid_client"

**Cause**: Client ID or Secret is wrong

**Solution**:
- Double-check you copied the correct credentials
- Try creating a new External Application

### Error: "unauthorized_client"

**Cause**: Authorization Code grant type not enabled

**Solution**:
1. Edit External Application
2. Check "Authorization Code" under Grant Types
3. Save

### Error: "access_denied"

**Cause**: User declined authorization OR insufficient permissions

**Solution**:
- Make sure you click "Authorize" in the UiPath login page
- Check your user has permissions for the selected scopes

### API returns 403 "You are not authorized"

**Cause**: Token is valid but lacks permissions for specific API

**Solution**:
1. Check which scopes the API endpoint requires (in the description)
2. Ensure those scopes are:
   - Selected in Swagger UI during authorization
   - Enabled in your External Application
   - Granted to your user account

## Testing OAuth2 Configuration

Run the test scripts to verify your setup:

```bash
# Test client credentials (machine-to-machine)
uv run python test_oauth2_auto.py

# Test authorization code (user login)
uv run python test_oauth2_authcode.py
```

Both will create detailed log files for debugging.

## Notes

- **Client Credentials** is for automation/scripts (no user login)
- **Authorization Code** is for interactive use (requires user login)
- Swagger UI works best with **Authorization Code with PKCE**
- For Swagger UI, you can use a **Public Application** (no secret needed)
