from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .dependencies import get_query_token, get_token_header
from .routers import tenants, packages, libraries, machines, folders, processes, assets, rnd_multiplecalls, setup, oauth2_uipath, oauth2_github_rpapub, rnd_loop
from .config import Settings, get_settings
from .common import Tags

from .middleware.print_header_type import MyMiddleware
from .middleware.oauth2_uipath import OAuth2AuthCodeMiddleware
from .middleware.oauth2a import OAuth2MiddlewareA
from starlette.middleware.sessions import SessionMiddleware


tags_metadata = [
    {
        "name": "machines (alpha)",
        "description": "Operations with machines in tenants.",
    },
    {
        "name": "oauth2",
        "description": "Operations to authenticate with UiPath Cloud using OAuth2.",
        "externalDocs": {
            "description": "The OAuth 2.0 Authorization Framework",
            "url": "https://datatracker.ietf.org/doc/html/rfc6749",
        },
    },
]


app = FastAPI(
    title="Gata Haystack",
    summary="Automating the UiPath Automation Cloud Community Edition",
    version="0.0.1",
    license_info={
        "name": "Creative Commons Attribution 4.0 International License (CC-BY)",
        "url": "https://creativecommons.org/licenses/by/4.0/legalcode",
    },
    contact={
        "name": "Christian Prior-Mamulyan",
        "url": "https://github.com/rpapub",
        "email": "cprior@gmail.com",
    },
    swagger_ui_parameters = {"docExpansion":"none"},
    openapi_tags=tags_metadata,
)

templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="./static"), name="static")
favicon_path = 'favicon.ico'

#app.add_middleware(MyMiddleware, some_attribute="some_attribute_here_if_needed", settings=Settings())
#app.add_middleware(OAuth2MiddlewareA, settings=Settings())
#app.add_middleware(OAuth2AuthCodeMiddleware, settings=Settings())
# for authlib
#app.add_middleware(SessionMiddleware, secret_key="oumv9g4quxzir5Zp4ZS4qoCj8lc683Ns")




app.include_router(tenants.router)
app.include_router(packages.router)
app.include_router(libraries.router)
app.include_router(machines.router)
app.include_router(processes.router)
app.include_router(assets.router)
app.include_router(folders.router)
app.include_router(oauth2_uipath.router)
app.include_router(rnd_loop.router)
#app.include_router(oauth2_github_rpapub.router)

@app.get("/info", tags=["debug"])
async def info(settings: Annotated[Settings, Depends(get_settings)]):
    return settings


@app.get("/", response_class=HTMLResponse, tags=["frontend"])
async def read_index(request: Request, settings: Settings = Depends(get_settings)):
#async def read_index(request: Request, settings: Settings = Settings()):
    print(settings)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings.mask_sensitive_data()  # Make sure to pass the settings object here
    })


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)