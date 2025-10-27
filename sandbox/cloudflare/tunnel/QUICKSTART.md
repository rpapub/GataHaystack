# Quick Start Guide

Your OAuth edge is already configured at `oauthedge.darpas.jerm.uk`. Here's how to use it:

## 1. Install Dependencies

```bash
uv sync
```

## 2. Configure Your Apps

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and fill in your UiPath External Application credentials:

```bash
# Public URL (already configured)
PUBLIC_URL=https://oauthedge.darpas.jerm.uk

# App 1 - Full RW Confidential
APP1_CLIENT_ID=your-client-id-from-uipath
APP1_CLIENT_SECRET=your-client-secret-from-uipath
APP1_CALLBACK_PATH=/cb/orch/dev/rpb/gthy/fullrw/c01

# App 2 - Non-Confidential
APP2_CLIENT_ID=your-second-client-id
APP2_CLIENT_SECRET=your-second-client-secret
APP2_CALLBACK_PATH=/cb/orch/dev/rpb/gthy/fullrw/nc02
```

## 3. Verify UiPath Configuration

Make sure both External Applications in UiPath have these callback URLs configured:

**App 1 Redirect URI:**
```
https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/c01
```

**App 2 Redirect URI:**
```
https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/nc02
```

## 4. Set Up Reverse Proxy

You need to configure your server at `oauthedge.darpas.jerm.uk` to forward requests to wherever you run this Python app.

**If using nginx:**
```nginx
location /cb/orch/dev/rpb/gthy/fullrw/ {
    proxy_pass http://localhost:8000/cb/orch/dev/rpb/gthy/fullrw/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Also proxy the main routes
location / {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**If using Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://localhost:8000
```

## 5. Start the Application

```bash
python oauth_multi_app.py
```

Or with uv:
```bash
uv run python oauth_multi_app.py
```

You should see:
```
================================================================================
Multi-App OAuth2 Handler
================================================================================

Public URL: https://oauthedge.darpas.jerm.uk

App 1 Callback: https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/c01
App 2 Callback: https://oauthedge.darpas.jerm.uk/cb/orch/dev/rpb/gthy/fullrw/nc02

Starting server on http://localhost:8000
================================================================================
```

## 6. Test It

Open your browser and go to:
```
https://oauthedge.darpas.jerm.uk
```

You should see a dashboard with both apps. Click "Authorize" for each to test the OAuth flow.

## Troubleshooting

### Can't access https://oauthedge.darpas.jerm.uk

- Verify the domain is resolving correctly: `nslookup oauthedge.darpas.jerm.uk`
- Check if there's a reverse proxy configured
- Make sure port 8000 is accessible from the proxy server

### "Invalid redirect_uri"

- Verify the callback URLs match **exactly** in UiPath External Application settings
- Check for trailing slashes or typos
- Confirm PUBLIC_URL in `.env` matches your domain

### Authentication works but API calls fail

- Check the OAuth scopes granted to each application
- Verify ACCOUNT_LOGICAL_NAME and TENANT_LOGICAL_NAME are correct
- Ensure the token hasn't expired (default: 1 hour)

## Testing Without Public Domain

If you want to test locally first without the public domain:

1. Update `.env`:
   ```bash
   PUBLIC_URL=http://localhost:8000
   APP1_CALLBACK_PATH=/callback/app1
   APP2_CALLBACK_PATH=/callback/app2
   ```

2. Update the callback decorators in `oauth_multi_app.py`:
   ```python
   @app.get("/callback/app1")
   async def callback_app1(...):

   @app.get("/callback/app2")
   async def callback_app2(...):
   ```

3. Use ngrok or Cloudflare tunnel:
   ```bash
   ngrok http 8000
   # or
   cloudflared tunnel --url http://localhost:8000
   ```

4. Update PUBLIC_URL with the tunnel URL and configure UiPath accordingly
