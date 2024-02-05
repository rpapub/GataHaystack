# Gata Haystack

The project Gata Haystack is a wrapper around the UiPath Cloud Orchestrator API. The project is designed to be deployed on a server and

- provides a minimal HTML frontend, mostly to authenticate via Oath 2.0 with the browser
- can be accessed by a client application

Relevant resources:

- [UiPath Cloud Orchestrator API](https://docs.uipath.com/orchestrator/automation-cloud/latest/api-guide/accessing-uipath-resources-using-external-applications)
- [UiPath Cloud Orchestrator OpenID configuration](https://cloud.uipath.com/identity_/.well-known/openid-configuration)
- [OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749#section-1.3.1)

## Requirements

This project has been developed on a Windows 11 machine with WSL Windows Subsystem for Linux. The following software is required to run the project:

- Python 3.8 or higher
- ngrok

## Python setup

Setup and activate a virtual environment, e.g with the following command:

```bash

python -m myFastapiVenv /path/to/venv
source /path/to/venv/myFastapiVenv/bin/activate

```

See the file requirements.txt for the required packages and install them with the following command:

```bash

pip install -r requirements.txt

```

### .env file with UiPath Clout Platform external application credentials

Create a .uipathcloud.env file in the root of the project with the following content:

```bash
# .env
UIPATHCLOUD_ORGANIZATIONS=[{"name": "example_org", "applications": [{"app_name": "Example App", "grant_types":["authorization_code"], "client_id": "your_client_id_here", "client_secret": "your_client_secret_here", "scope": "your_scopes_here", "redirect_url": "your_redirect_url_here"}]}]
```

For clarification: The content of the variable UIPATHCLOUD_ORGANIZATIONS is a JSON array with the following structure:

```json
[
  {
    "name": "example_org",
    "applications": [
      {
        "app_name": "Example App",
        "grant_types": ["authorization_code"],
        "client_id": "your_client_id_here",
        "client_secret": "your_client_secret_here",
        "scope": "your_scopes_here",
        "redirect_url": "your_redirect_url_here"
      }
    ]
  }
]
```
