# Cloudflare Tunnel Setup Guide

Complete guide for setting up a Cloudflare Tunnel from domain registration to local project integration.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Domain Registration and Cloudflare Setup](#domain-registration-and-cloudflare-setup)
4. [Creating a Cloudflare Tunnel](#creating-a-cloudflare-tunnel)
5. [Installing Cloudflared on Windows](#installing-cloudflared-on-windows)
6. [Tunnel Configuration](#tunnel-configuration)
7. [Testing and Verification](#testing-and-verification)
8. [Integration with OAuth Server](#integration-with-oauth-server)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

---

## Overview

**What is Cloudflare Tunnel?**

Cloudflare Tunnel (formerly Argo Tunnel) creates a secure, outbound-only connection from your local server to Cloudflare's network. This allows you to:

- Expose localhost to the internet without port forwarding
- No need for public IP addresses
- Built-in DDoS protection
- Free SSL/TLS certificates
- No firewall modifications needed

**What we'll accomplish:**

- Register/configure a domain with Cloudflare
- Create a Cloudflare Tunnel
- Install cloudflared on Windows
- Route a subdomain to your local OAuth server
- Configure SSL/TLS for secure connections
- Set up the tunnel as a Windows service

**Time Required:** 30-60 minutes

---

## Prerequisites

### Required

- A domain name (either register new or transfer existing to Cloudflare)
- Cloudflare account (free tier is sufficient)
- Windows 10/11 with Administrator access
- Internet connection

### Optional but Recommended

- Package manager for Windows:
  - **Scoop** (recommended): https://scoop.sh/
  - **Chocolatey**: https://chocolatey.org/
  - Manual installation also covered

### Technical Knowledge

- Basic command line usage (PowerShell or cmd)
- Understanding of DNS concepts
- Familiarity with localhost and ports

---

## Domain Registration and Cloudflare Setup

### Option 1: Register Domain Through Cloudflare (Recommended)

1. **Create Cloudflare Account**
   - Go to https://dash.cloudflare.com/sign-up
   - Verify your email address

2. **Register Domain**
   - Navigate to **Domain Registration** in Cloudflare dashboard
   - Search for available domain
   - Complete purchase (at-cost pricing, no markup)
   - Domain is automatically configured with Cloudflare DNS

### Option 2: Use Existing Domain

1. **Add Domain to Cloudflare**
   - Log in to Cloudflare dashboard
   - Click **Add a Site**
   - Enter your domain name
   - Select Free plan
   - Click **Add Site**

2. **Change Nameservers**
   - Cloudflare will provide two nameservers (e.g., `alice.ns.cloudflare.com`)
   - Log in to your domain registrar
   - Update nameservers to use Cloudflare's
   - Wait for DNS propagation (5 minutes to 48 hours)

3. **Verify Domain**
   - Return to Cloudflare dashboard
   - Click **Done, check nameservers**
   - Wait for active status

### DNS Configuration

Once domain is active in Cloudflare:

1. Navigate to **DNS** → **Records**
2. Note: Cloudflare Tunnel will automatically create DNS records
3. You can manually add an A record if needed:
   - Type: `A`
   - Name: `@` (or subdomain like `oauthedge`)
   - IPv4 address: `192.0.2.1` (placeholder, tunnel will override)
   - Proxy status: **Proxied** (orange cloud)

---

## Creating a Cloudflare Tunnel

### Access Zero Trust Dashboard

1. In Cloudflare dashboard, click **Zero Trust** in left sidebar
   - Or go directly to: https://one.dash.cloudflare.com/

2. If first time:
   - Click **Create a team**
   - Choose a team name (e.g., `mycompany`)
   - Select Free plan
   - Complete setup

### Create Tunnel

1. **Navigate to Tunnels**
   - Zero Trust → **Networks** → **Tunnels**
   - Click **Create a tunnel**

2. **Configure Tunnel**
   - **Connector type:** Cloudflared
   - **Tunnel name:** Choose descriptive name
     - Example: `dev-oauth-tunnel` or `RPB-DEV-GTHY-Orch-AuthEdge-01`
   - Click **Save tunnel**

3. **Install Connector**
   - Cloudflare will show installation instructions
   - **Copy the install command** - it contains your tunnel token
   - Example:
     ```
     cloudflared service install eyJhIjoiOGZjYzA4MWQyMzQ5YWRlOWVmMDU0OGUwNjc1ZmM3YzYiLCJ0Ijoi...
     ```
   - **IMPORTANT:** Save this token - you'll need it later

4. **Configure Public Hostname**
   - **Subdomain:** Enter subdomain (e.g., `oauthedge`)
   - **Domain:** Select your domain
   - **Path:** Leave blank (route all paths)
   - **Service:**
     - Type: `HTTP` or `HTTPS`
     - URL: `localhost:8000` (or your port)
   - Click **Save tunnel**

---

## Installing Cloudflared on Windows

### Method 1: Using Scoop (Recommended)

1. **Install Scoop** (if not installed):
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   irm get.scoop.sh | iex
   ```

2. **Install cloudflared:**
   ```powershell
   scoop install cloudflared
   ```

3. **Verify Installation:**
   ```powershell
   cloudflared --version
   ```

### Method 2: Using Chocolatey

```powershell
choco install cloudflared
```

### Method 3: Manual Installation

1. **Download cloudflared:**
   - Go to: https://github.com/cloudflare/cloudflared/releases
   - Download `cloudflared-windows-amd64.exe`

2. **Install:**
   ```powershell
   # Rename and move to Program Files
   Rename-Item cloudflared-windows-amd64.exe cloudflared.exe
   Move-Item cloudflared.exe "C:\Program Files\cloudflared\cloudflared.exe"

   # Add to PATH
   $env:Path += ";C:\Program Files\cloudflared"
   [Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)
   ```

3. **Verify:**
   ```powershell
   cloudflared --version
   ```

---

## Tunnel Configuration

Cloudflare tunnels can run in two modes:

1. **Token-based** (easier, recommended for most users)
2. **Config file-based** (more control, better for complex setups)

### Option 1: Token-Based Configuration (Recommended)

This is the simplest approach and what Cloudflare recommends.

**Install as Windows Service:**

```powershell
# Run as Administrator
cloudflared service install <YOUR_TOKEN>
```

Replace `<YOUR_TOKEN>` with the token from tunnel creation (starts with `eyJ...`).

**Start Service:**

```powershell
Start-Service cloudflared
```

**Verify Service:**

```powershell
Get-Service cloudflared
```

Should show:
```
Status   Name               DisplayName
------   ----               -----------
Running  cloudflared        Cloudflared agent
```

**Update Tunnel Configuration:**

Since token-based tunnels fetch configuration from Cloudflare's servers, you must update settings in the Zero Trust dashboard:

1. Go to **Networks** → **Tunnels**
2. Click on your tunnel
3. Click **Configure**
4. Edit **Public Hostname**:
   - Service URL (e.g., `http://localhost:8000`)
   - Path restrictions
   - Additional routes

Changes take effect within 30 seconds.

### Option 2: Config File-Based Configuration

For more control over tunnel configuration.

**1. Create Configuration Directory:**

```powershell
# Create directory accessible by all users
New-Item -ItemType Directory -Path "C:\Users\Public\.cloudflared" -Force
```

**2. Create Configuration File:**

Create `C:\Users\Public\.cloudflared\config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\Public\.cloudflared\<TUNNEL_ID>.json

ingress:
  # Route specific hostname to local service
  - hostname: oauthedge.example.com
    service: http://localhost:8000

  # Catch-all rule (required)
  - service: http_status:404
```

**3. Get Tunnel Credentials:**

```powershell
# Login to Cloudflare
cloudflared tunnel login

# List tunnels to get ID
cloudflared tunnel list

# Download credentials
cloudflared tunnel token <TUNNEL_NAME>
```

Or manually create from dashboard token.

**4. Install Service with Config:**

```powershell
cloudflared --config "C:\Users\Public\.cloudflared\config.yml" service install
```

**5. Start Service:**

```powershell
Start-Service cloudflared
```

### Advanced Configuration Examples

**Multiple Routes:**

```yaml
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\Public\.cloudflared\<TUNNEL_ID>.json

ingress:
  # OAuth server
  - hostname: oauth.example.com
    service: http://localhost:8000

  # API server
  - hostname: api.example.com
    service: http://localhost:3000

  # Static site
  - hostname: www.example.com
    service: http://localhost:8080

  # Catch-all
  - service: http_status:404
```

**Path-Based Routing:**

```yaml
ingress:
  - hostname: example.com
    path: /api/*
    service: http://localhost:3000

  - hostname: example.com
    path: /oauth/*
    service: http://localhost:8000

  - hostname: example.com
    service: http://localhost:80

  - service: http_status:404
```

**HTTPS Backend:**

```yaml
ingress:
  - hostname: secure.example.com
    service: https://localhost:3701
    originServerName: localhost
    noTLSVerify: true  # For self-signed certs

  - service: http_status:404
```

---

## Testing and Verification

### 1. Check Service Status

```powershell
Get-Service cloudflared
```

Should show `Running`.

### 2. Check Tunnel Connections

In Cloudflare Zero Trust dashboard:

1. Navigate to **Networks** → **Tunnels**
2. Click on your tunnel
3. Check **Status** section
4. Should show **Healthy** with active connections (usually 4)

### 3. Test Local Server

```powershell
# Test your local service is running
curl http://localhost:8000
```

Should return response from your application.

### 4. Test Public URL

```powershell
# Test through Cloudflare tunnel
curl https://oauthedge.example.com
```

Should return same response as localhost.

### 5. Browser Test

Open browser and navigate to your public URL:
```
https://oauthedge.example.com
```

Should see your application.

### 6. DNS Verification

```powershell
nslookup oauthedge.example.com
```

Should resolve to Cloudflare IPs (e.g., `104.21.x.x` or `172.67.x.x`).

### Troubleshooting Connection Issues

If public URL doesn't work:

1. **Check tunnel status:**
   ```powershell
   cloudflared tunnel info <TUNNEL_NAME>
   ```

2. **View tunnel logs:**
   ```powershell
   # For service:
   Get-EventLog -LogName Application -Source cloudflared -Newest 50

   # Or run manually for detailed logs:
   cloudflared tunnel run <TUNNEL_NAME>
   ```

3. **Verify routing configuration:**
   - Check Zero Trust dashboard → Tunnels → Configure
   - Ensure service URL is correct (http/https, port)
   - Ensure no path restrictions unless intended

4. **Test local service:**
   ```powershell
   curl http://localhost:8000
   ```
   If this fails, fix local service first.

---

## Integration with OAuth Server

### Project-Specific Setup

For the OAuth server in this project (`sandbox/cloudflare/tunnel`):

### 1. Configure Environment Variables

Edit `sandbox/cloudflare/tunnel/.env`:

```bash
# Your Cloudflare tunnel URL
PUBLIC_URL=https://oauthedge.example.com

# UiPath OAuth credentials remain the same
ACCOUNT_LOGICAL_NAME=rpapub
TENANT_LOGICAL_NAME=playground
# ... rest of config
```

### 2. SSL Certificate Handling

The OAuth server can run on either HTTP or HTTPS:

**Option A: HTTP Backend (Recommended)**

Cloudflare tunnel handles SSL termination:

- Local server: `http://localhost:8000`
- Tunnel config service: `http://localhost:8000`
- Public URL: `https://oauthedge.example.com` (Cloudflare provides SSL)

No certificates needed locally.

**Option B: HTTPS Backend**

If your local server needs HTTPS (e.g., tunnel expects it):

1. Generate self-signed certificate:
   ```bash
   cd sandbox/cloudflare/tunnel
   openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365 -subj "//CN=localhost"
   ```

2. OAuth server auto-detects cert files and runs on HTTPS port 3701

3. Update tunnel config:
   - Service: `https://localhost:3701`
   - Enable `noTLSVerify: true` for self-signed certs

### 3. Tunnel Configuration for OAuth

**If using path-based routing:**

```yaml
ingress:
  - hostname: oauthedge.example.com
    service: http://localhost:8000

  - service: http_status:404
```

**If tunnel is configured for specific path:**

Example: Tunnel routes `/cb` → `https://localhost:3701`

Then ensure OAuth server:
- Runs on HTTPS port 3701
- All callback URLs start with `/cb`

This is handled automatically by the OAuth server code - callbacks are already prefixed with `/cb/orch/dev/...`.

### 4. Update UiPath External Applications

For each OAuth profile, update the callback URLs in UiPath Cloud:

1. Go to UiPath Cloud → Admin → External Applications
2. For each application, update **Redirect URIs**:
   - Old: `http://localhost:8000/cb/orch/dev/rpb/gthy/fullrw/nc02`
   - New: `https://oauthedge.example.com/cb/orch/dev/rpb/gthy/fullrw/nc02`

3. Repeat for all profiles (c01, nc02, etc.)

### 5. Start OAuth Server

```bash
cd sandbox/cloudflare/tunnel
make run
```

Server will:
- Auto-detect cert files and run HTTPS on 3701 if present
- Otherwise run HTTP on 8000
- Display loaded profiles and callback URLs

### 6. Test OAuth Flow

1. Open browser to `https://oauthedge.example.com`
2. Click "Authorize c01" (client credentials)
3. Should see success message
4. Click "Authorize nc02" (authorization code + PKCE)
5. Should redirect to UiPath login
6. After login, should redirect back with success

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Server not found" or timeout on public URL

**Symptoms:**
- `curl https://oauthedge.example.com` fails
- Browser shows "can't reach site"

**Solutions:**

A. **Check tunnel service:**
```powershell
Get-Service cloudflared
```
If not running:
```powershell
Start-Service cloudflared
```

B. **Check tunnel status in dashboard:**
- Go to Networks → Tunnels
- Verify status is "Healthy"
- Should show 4 active connections

C. **Check DNS:**
```powershell
nslookup oauthedge.example.com
```
Should resolve to Cloudflare IPs. If not, wait for DNS propagation (up to 5 minutes).

D. **Verify local service is running:**
```powershell
curl http://localhost:8000
```
If this fails, start your local server first.

#### 2. SSL/TLS Certificate Errors

**Symptoms:**
- Browser shows "Your connection is not private"
- ERR_CERT_AUTHORITY_INVALID

**Solutions:**

A. **If using Cloudflare tunnel with HTTP backend:**
- This shouldn't happen
- Cloudflare provides valid SSL certificates
- Check tunnel service URL is `http://` not `https://`

B. **If using HTTPS backend with self-signed cert:**
- Expected behavior
- Click "Advanced" → "Proceed to site"
- Or add certificate to Windows trusted store

C. **For production:**
- Use HTTP backend and let Cloudflare handle SSL
- Or use proper CA-signed certificates locally

#### 3. Tunnel Config Not Taking Effect

**Symptoms:**
- Changed config in dashboard but no effect
- Old route still active

**Solutions:**

A. **For token-based tunnels:**
- Changes can take up to 60 seconds
- Restart service if needed:
  ```powershell
  Restart-Service cloudflared
  ```

B. **For config-based tunnels:**
- Must restart service after config changes:
  ```powershell
  Stop-Service cloudflared
  Start-Service cloudflared
  ```

C. **Verify config location:**
- Token tunnels fetch config from Cloudflare servers
- Check you're editing the right tunnel in dashboard

#### 4. "Invalid redirect_uri" from UiPath

**Symptoms:**
- OAuth authorization fails
- UiPath shows "Invalid redirect_uri" error

**Solutions:**

A. **Check exact URL match:**
- `.env` file: `PROFILE_nc02_REDIRECT=https://oauthedge.example.com/cb/orch/dev/rpb/gthy/fullrw/nc02`
- UiPath External App: Must match EXACTLY (including https://, no trailing slash)

B. **Verify PUBLIC_URL:**
```bash
# In .env file
PUBLIC_URL=https://oauthedge.example.com
```
Must match your actual tunnel URL.

C. **Test callback URL manually:**
```powershell
curl https://oauthedge.example.com/cb/orch/dev/rpb/gthy/fullrw/nc02
```
Should return HTML (not 404).

#### 5. Port Already in Use

**Symptoms:**
- `ERROR: [Errno 10048] error while attempting to bind on address`
- Server won't start

**Solutions:**

A. **Find process using port:**
```powershell
netstat -ano | findstr :8000
```

B. **Kill process:**
```powershell
Stop-Process -Id <PID> -Force
```

C. **Or use different port:**
- Update `.env` and tunnel config
- Restart both server and tunnel service

#### 6. Windows Service Won't Install

**Symptoms:**
- `cloudflared service install` fails
- Access denied errors

**Solutions:**

A. **Run PowerShell as Administrator:**
- Right-click PowerShell
- Select "Run as Administrator"

B. **Check if service already exists:**
```powershell
Get-Service cloudflared
```
If exists, uninstall first:
```powershell
cloudflared service uninstall
```

C. **Permissions on config directory:**
```powershell
# Use C:\Users\Public for shared access
New-Item -ItemType Directory -Path "C:\Users\Public\.cloudflared" -Force
icacls "C:\Users\Public\.cloudflared" /grant Users:F
```

#### 7. Tunnel Randomly Disconnects

**Symptoms:**
- Tunnel works then stops
- Status shows "Unhealthy" intermittently

**Solutions:**

A. **Check system resources:**
- Task Manager → Performance
- Ensure adequate RAM and CPU

B. **Check firewall:**
```powershell
# Allow cloudflared through Windows Firewall
New-NetFirewallRule -DisplayName "Cloudflared" -Direction Outbound -Program "C:\ProgramData\chocolatey\lib\cloudflared\tools\cloudflared.exe" -Action Allow
```

C. **Check internet connection:**
- Tunnel requires stable connection to Cloudflare

D. **View service logs:**
```powershell
Get-EventLog -LogName Application -Source cloudflared -Newest 50
```

#### 8. Config File Not Found

**Symptoms:**
- `Unable to find config file` error
- Service fails to start

**Solutions:**

A. **Verify file path:**
```powershell
Test-Path "C:\Users\Public\.cloudflared\config.yml"
```

B. **Check file contents:**
```powershell
Get-Content "C:\Users\Public\.cloudflared\config.yml"
```

C. **Reinstall service with correct path:**
```powershell
cloudflared service uninstall
cloudflared --config "C:\Users\Public\.cloudflared\config.yml" service install
Start-Service cloudflared
```

D. **Use absolute paths in config:**
```yaml
# Use full Windows paths
credentials-file: C:\Users\Public\.cloudflared\<TUNNEL_ID>.json
```

---

## Security Considerations

### Best Practices

1. **Use Token-Based Configuration When Possible**
   - Tokens are stored securely by Windows service
   - No credential files on disk
   - Centralized management in Cloudflare dashboard

2. **Protect Credentials Files**
   ```powershell
   # Restrict access to config directory
   icacls "C:\Users\Public\.cloudflared" /grant Administrators:F /inheritance:r
   ```

3. **Use HTTPS for Backend When Handling Sensitive Data**
   - Even though Cloudflare provides SSL, encrypt the entire path
   - Generate proper certificates for production

4. **Limit Tunnel Access**
   - Use Cloudflare Access policies to restrict who can access tunnel
   - Configure WAF rules for additional protection
   - Enable rate limiting

5. **Monitor Tunnel Activity**
   - Check tunnel logs regularly
   - Set up alerts in Cloudflare dashboard
   - Monitor for unusual traffic patterns

6. **Rotate Credentials**
   - Regenerate tunnel tokens periodically
   - Update service configuration with new tokens
   - Revoke old tunnels when no longer needed

7. **Don't Commit Secrets**
   ```bash
   # Add to .gitignore
   .cloudflared/
   *.pem
   .env
   ```

### Cloudflare Access Integration (Optional)

For additional security, integrate with Cloudflare Access:

1. **Enable Cloudflare Access:**
   - Zero Trust → Access → Applications
   - Click "Add an application"

2. **Configure Application:**
   - Application domain: `oauthedge.example.com`
   - Policy: Who can access
     - Email domain
     - Specific emails
     - IP ranges
     - Service tokens

3. **Authentication Methods:**
   - One-time PIN
   - Google SSO
   - Azure AD
   - GitHub
   - And more...

This adds an authentication layer before reaching your OAuth server.

---

## Advanced Topics

### Multiple Tunnels

You can run multiple tunnels for different services:

```powershell
# Create separate tunnels
cloudflared tunnel create dev-tunnel
cloudflared tunnel create prod-tunnel
cloudflared tunnel create staging-tunnel

# Each with own config
cloudflared --config config-dev.yml service install
```

### Load Balancing

Route traffic to multiple backends:

```yaml
ingress:
  - hostname: app.example.com
    service: http://localhost:8000
    originRequest:
      connectTimeout: 30s
      noHappyEyeballs: true
```

### Custom Headers

Add headers to requests:

```yaml
ingress:
  - hostname: api.example.com
    service: http://localhost:3000
    originRequest:
      httpHostHeader: custom.internal.host
      originServerName: internal.server
```

### Metrics and Monitoring

Enable Prometheus metrics:

```yaml
metrics: localhost:2000

ingress:
  # ... your routes
```

Access metrics at `http://localhost:2000/metrics`.

---

## Quick Reference

### Common Commands

```powershell
# Service Management
Start-Service cloudflared
Stop-Service cloudflared
Restart-Service cloudflared
Get-Service cloudflared

# Tunnel Management
cloudflared tunnel list
cloudflared tunnel info <TUNNEL_NAME>
cloudflared tunnel delete <TUNNEL_NAME>

# Testing
cloudflared tunnel run <TUNNEL_NAME>  # Run manually for debugging

# Service Install/Uninstall
cloudflared service install <TOKEN>
cloudflared service uninstall

# Logs
Get-EventLog -LogName Application -Source cloudflared -Newest 50
```

### Configuration File Template

```yaml
tunnel: <TUNNEL_ID>
credentials-file: <PATH_TO_CREDENTIALS>

# Optional: Metrics
metrics: localhost:2000

# Optional: Logging
loglevel: info

# Required: Ingress rules
ingress:
  # Your routes here
  - hostname: example.com
    service: http://localhost:8000

  # Catch-all (required)
  - service: http_status:404
```

### Environment Variables

```bash
# OAuth Server .env
PUBLIC_URL=https://oauthedge.example.com
ACCOUNT_LOGICAL_NAME=your-account
TENANT_LOGICAL_NAME=your-tenant
BASE_URL=https://cloud.uipath.com

# Profile configuration
PROFILE_c01_CLIENT_ID=...
PROFILE_c01_CLIENT_SECRET=...
PROFILE_c01_GRANT=client_credentials
PROFILE_c01_SCOPES=OR.Execution OR.Assets

PROFILE_nc02_CLIENT_ID=...
PROFILE_nc02_GRANT=authorization_code_pkce
PROFILE_nc02_SCOPES=OR.Assets.Read
PROFILE_nc02_REDIRECT=https://oauthedge.example.com/cb/orch/dev/rpb/gthy/fullrw/nc02
```

---

## Resources

- **Cloudflare Tunnel Docs:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **Cloudflared GitHub:** https://github.com/cloudflare/cloudflared
- **Cloudflare Zero Trust:** https://one.dash.cloudflare.com/
- **Cloudflare Community:** https://community.cloudflare.com/

---

## Summary

You've learned to:

1. Register/configure domain with Cloudflare
2. Create Cloudflare Tunnel using Zero Trust dashboard
3. Install cloudflared on Windows (3 methods)
4. Configure tunnel (token-based and config file approaches)
5. Route subdomain to local OAuth server
6. Handle SSL/TLS certificates
7. Integrate with OAuth project
8. Troubleshoot common issues
9. Apply security best practices

Your local development server is now securely accessible via a public HTTPS URL, with no port forwarding or firewall configuration needed!
