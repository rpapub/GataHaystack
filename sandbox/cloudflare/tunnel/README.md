# UiPath OAuth2 Tester

Test your UiPath OAuth2 apps before using them with Swagger or other tools.

## What This Does

You have UiPath OAuth applications configured. This tool lets you:

1. **Test if they work** - Quick validation before wiring them up
2. **See the actual tokens** - Verify OAuth flow completes successfully
3. **Make test API calls** - Confirm tokens work with UiPath Orchestrator
4. **Predict Swagger compatibility** - Know if your apps will work with Swagger UI

## Quick Start

### Step 1: Install Dependencies

```bash
cd sandbox/cloudflare/tunnel
make install
```

### Step 2: Configure Your Apps

```bash
make setup  # Creates .env from .env.example (skips if .env exists)
```

Edit `.env` with your UiPath app details:

```bash
# Your UiPath account
ACCOUNT_LOGICAL_NAME=rpapub
TENANT_LOGICAL_NAME=playground
BASE_URL=https://cloud.uipath.com

# Your public URL (Cloudflare tunnel, ngrok, etc.)
PUBLIC_URL=https://oauthedge.darpas.jerm.uk

# App 1: Client Credentials (confidential)
PROFILE_c01_CLIENT_ID=d928a27c-c2f9-431d-bc16-b292b4cafbed
PROFILE_c01_CLIENT_SECRET=your-secret-here
PROFILE_c01_GRANT=client_credentials
PROFILE_c01_SCOPES=OR.Execution OR.Assets

# App 2: Authorization Code with PKCE (non-confidential)
PROFILE_nc02_CLIENT_ID=6449b8f6-c2a8-4b0d-826e-ef97c4a39fe5
PROFILE_nc02_GRANT=authorization_code_pkce
PROFILE_nc02_SCOPES=OR.Assets.Read
PROFILE_nc02_REDIRECT=https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/nc02
```

### Step 3: Validate Configuration

```bash
make check
```

You should see:
```
[OK] Configuration is valid!
```

### Step 4: Run the Test Server

```bash
make run
```

### Step 5: Test Your Apps

Open your public URL in a browser:
```
https://oauthedge.darpas.jerm.uk
```

For each app:
1. Click **"Authorize"**
2. Complete the OAuth flow
3. Click **"Test API Call"**
4. Verify you get data back

**If all tests pass** → Your apps are configured correctly and will work with Swagger!

## Understanding Your Apps

### Client Credentials (c01)

**What it is:**
- Server-to-server authentication
- No user interaction
- Requires CLIENT_SECRET

**When it works:**
- ✅ Backend services
- ✅ Automation scripts
- ❌ Browser-based Swagger (needs CORS proxy)

**How to test:**
- Click "Authorize" → Token appears immediately
- No login required

### Authorization Code + PKCE (nc02)

**What it is:**
- Interactive user login
- Browser-based flow
- Public client (no secret needed)

**When it works:**
- ✅ Web applications
- ✅ Mobile apps
- ⚠️ Browser Swagger (if CORS allowed, otherwise needs proxy)

**How to test:**
- Click "Authorize" → Redirected to UiPath login
- Log in → Redirected back with token
- Token should appear

## Will This Work With Swagger?

### Direct Swagger UI (Browser)

**Client Credentials:**
- ❌ **Won't work** - Browser CORS blocks token requests
- ✅ **Solution:** Use FastAPI proxy (like `swagger_proxy.py` in parent dir)

**Authorization Code + PKCE:**
- ⚠️ **Maybe** - Depends on UiPath CORS policy
- ✅ **Solution:** Use FastAPI proxy if CORS blocked

### Swagger via Proxy

Both app types work perfectly through a proxy server:
- ✅ Client Credentials
- ✅ Authorization Code + PKCE

**See:** `../swagger_proxy.py` for a working proxy example.

## Common Issues

### "Configuration invalid" error

Run validator to see what's wrong:
```bash
make check
```

Fix any `[ERR]` items in the output.

### "Invalid redirect_uri" in UiPath

The callback URL in your UiPath External Application must **exactly** match `PROFILE_*_REDIRECT`:

**In UiPath:**
```
https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/nc02
```

**In .env:**
```bash
PROFILE_nc02_REDIRECT=https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/nc02
```

No typos, no trailing slashes, exact match.

### Tunnel URL changed

If you restart your Cloudflare tunnel, the URL changes:

1. Update `PUBLIC_URL` in `.env`
2. Update `PROFILE_*_REDIRECT` for authorization code apps
3. Update callback URLs in UiPath External Applications
4. Restart the test server

### Token works but API calls fail

Check scopes! Your app needs permission for the API endpoints you're calling:

```bash
# For folder access:
PROFILE_c01_SCOPES=OR.Folders OR.Folders.Read

# For job execution:
PROFILE_c01_SCOPES=OR.Execution OR.Jobs
```

## What Each File Does

```
oauth_multi_app_v2.py   # Main test server
test_config.py          # Validates your .env file
.env                    # Your configuration (you create this)
.env.example            # Template to copy
pyproject.toml          # Dependencies (managed by uv)
```

## How to Add More Apps

Just add more `PROFILE_*` blocks to `.env`:

```bash
# App 3
PROFILE_myapp_CLIENT_ID=...
PROFILE_myapp_CLIENT_SECRET=...
PROFILE_myapp_GRANT=client_credentials
PROFILE_myapp_SCOPES=OR.Administration
```

The server auto-discovers all profiles.

## Predicting Swagger Compatibility

### Test 1: Can you get a token?

Run this test server. If you can authorize and see tokens → OAuth is configured correctly.

### Test 2: Can you call the API?

Click "Test API Call". If you get data back → Token works with Orchestrator.

### Test 3: Check CORS

Open browser console (F12) and try to call the API directly from JavaScript:

```javascript
fetch('https://cloud.uipath.com/account/tenant/orchestrator_/api/Status/Get', {
  headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
})
```

If you see CORS error → You need a proxy for Swagger.

**Result:**
- ✅ No CORS error → Direct Swagger UI will work
- ❌ CORS error → Use proxy (like `swagger_proxy.py`)

## Using With Swagger

After testing here, use your apps with Swagger:

**Option 1: Direct (if no CORS issues)**
- Configure Swagger UI with your OAuth settings
- Use your apps directly

**Option 2: Via Proxy (recommended)**
- Use `swagger_proxy.py` in the parent directory
- Proxy handles OAuth and CORS automatically
- See: `../swagger_proxy.py`

## Commands Reference

```bash
make install    # Install dependencies
make setup      # Copy .env.example to .env
make check      # Validate configuration
make run        # Run test server
make help       # Show all available commands
```

**What make actually runs:**
- `make install` → `uv sync`
- `make check` → `uv run python test_config.py`
- `make run` → `uv run python oauth_multi_app_v2.py`

## Getting Help

If tests fail:

1. Run `make check` and fix any errors
2. Check UiPath External Application settings match your `.env`
3. For authorization code apps, verify callback URLs match exactly
4. Check browser console for CORS or network errors

**Troubleshooting make:**
If `make` commands don't work on your system, you can run the underlying commands directly:
```bash
uv sync                              # Instead of: make install
uv run python test_config.py         # Instead of: make check
uv run python oauth_multi_app_v2.py  # Instead of: make run
```

## Next Steps

Once your apps work here:

1. **For automation:** Use `client_credentials` apps in your scripts
2. **For Swagger:** Use `swagger_proxy.py` in parent directory
3. **For web apps:** Use `authorization_code_pkce` apps

This tool is for **testing only**. For production, implement proper token storage and security.
