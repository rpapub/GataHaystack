from fastapi import APIRouter
import httpx
from starlette.responses import RedirectResponse
from functools import lru_cache
from typing import Annotated
from ..config import Settings


router = APIRouter(
    prefix="/oauth2_github_rpapub",
    tags=["oauth2"],
    responses={404: {"description": "Not found"}},
)
github_client_id = "Iv1.5471b7ee3e07daf8"
github_client_secret = "f910d671395287fe9635d93098047e7a81b62929"

@lru_cache
def get_settings():
    return Settings()

@router.get('/github_login')
async def login_github_rpapub():
    redirect_uri = f'https://github.com/login/oauth/authorize?client_id={github_client_id}'
    return RedirectResponse(url=redirect_uri, status_code=302)

@router.get('/github_code')
async def login_github_code(code: str):
    print(code)
    data={"client_id": github_client_id, "client_secret": github_client_secret, "code": code}
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url="https://github.com/login/oauth/access_token", data=data, headers=headers)
    response_json = response.json()
    print(response_json)
    access_token = response_json.get("access_token")
    async with httpx.AsyncClient() as client2:
        headers.update({'Authorization': f"Bearer {access_token}"})
        response2 = await client2.get(url="https://api.github.com/user", headers=headers)
    return response2.json()



