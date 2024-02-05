from fastapi import APIRouter, Depends, Request
from ..config import Settings
from functools import lru_cache
from typing import Annotated
import httpx

router = APIRouter()

@lru_cache
def get_settings():
    return Settings()

@router.get("/orchestrator/", tags=["orchestrator"])
async def read_orchestrator():
    return [{"orchestrator": "orchestrator"}]

@router.get("/orchestrator/test", tags=["orchestrator"])
async def read_orchestrator_test(request: Request, settings: Annotated[Settings, Depends(get_settings)]):
    print("UiPath Access Token URL:", settings.uipath_access_token_url)
    access_token = request.state.access_token
    #print("Access Token:", access_token)

    # Extract just the cookie value without attributes for the header
    cookie = request.state.cookie.split(';')[0] if hasattr(request.state, "cookie") else None
    print("Cookie from middleware:", cookie)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "*/*",
        "User-Agent": "PostmanRuntime/7.36.1",
    }
    if cookie:
        headers["Cookie"] = cookie

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://cloud.uipath.com/cprimadotnet/homelab23/orchestrator_/odata/Users",
                headers=headers
            )
            response.raise_for_status()
            data1 = response.json()
            print("First API call succeeded:", data1)
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        # Optionally, handle specific status codes differently
        if e.response.status_code == 403:
            print("Forbidden access. Check if the access token is valid or permissions are correct.")
        # You might choose to return an error response here or simply log the error
        data1 = {"error": "Failed to fetch data from the first API call."}

    try:
        async with httpx.AsyncClient() as client2:
            response2 = await client2.get(
                f"{settings.uipath_cloud_baseurl}/cprimadotnet/homelab23/orchestrator_/odata/Machines",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response2.raise_for_status()
            data2 = response2.json()
            print("Second API call succeeded:", data2)
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        if e.response.status_code == 403:
            print("Forbidden access on the second API call.")
        data2 = {"error": "Failed to fetch data from the second API call."}

    return {"orchestrator": "orchestrator", "app_name": settings.app_name, "openid": data1, "machines": data2}


@router.get("/orchestrator/replicate-postman")
async def replicate_postman_request():
    url = "https://cloud.uipath.com/cprimadotnet/portal_/api/filtering/leftnav/tenantsAndOrganizationInfo"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkE0RkEwMEZDNzEzRUMwRjA1NjREQTFCQzdFMEM4MDU3RDdEMUI3OEMiLCJ4NXQiOiJwUG9BX0hFLXdQQldUYUc4Zmd5QVY5ZlJ0NHciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2Nsb3VkLnVpcGF0aC5jb20vaWRlbnRpdHlfIiwibmJmIjoxNzA2OTU2MDk0LCJpYXQiOjE3MDY5NTYzOTQsImV4cCI6MTcwNjk1OTk5NCwiYXVkIjpbIlVpUGF0aC5PcmNoZXN0cmF0b3IiLCJQbGF0Zm9ybU1hbmFnZW1lbnQiXSwic2NvcGUiOlsiT1IuQWRtaW5pc3RyYXRpb24iLCJPUi5BbmFseXRpY3MiLCJPUi5Bc3NldHMiLCJPUi5BdWRpdCIsIk9SLkJhY2tncm91bmRUYXNrcyIsIk9SLkV4ZWN1dGlvbiIsIk9SLkZvbGRlcnMiLCJPUi5IeXBlcnZpc29yIiwiT1IuSm9icyIsIk9SLkxpY2Vuc2UiLCJPUi5NYWNoaW5lcyIsIk9SLk1MIiwiT1IuTW9uaXRvcmluZyIsIk9SLlF1ZXVlcyIsIk9SLlJvYm90cyIsIk9SLlNldHRpbmdzIiwiT1IuVGFza3MiLCJPUi5UZXN0RGF0YVF1ZXVlcyIsIk9SLlRlc3RTZXRFeGVjdXRpb25zIiwiT1IuVGVzdFNldHMiLCJPUi5UZXN0U2V0U2NoZWR1bGVzIiwiT1IuVXNlcnMiLCJPUi5XZWJob29rcyIsIlBNLkF1ZGl0IiwiUE0uR3JvdXAiLCJQTS5MaWNlbnNlIiwiUE0uUm9ib3RBY2NvdW50IiwiUE0uU2V0dGluZyIsIlBNLlVzZXIiLCJQTS5Vc2VyTG9naW5BdHRlbXB0Il0sInN1Yl90eXBlIjoic2VydmljZS5leHRlcm5hbCIsInBydF9pZCI6IjJkODc0N2Y5LWI4YmMtNDA4My1hZmEyLWQzZjU5OWYxODJmZSIsImNsaWVudF9pZCI6IjhlOWQwNTQzLWEzNzItNDc2Yy05MWI5LTRhYzA4NDU1NzBmMyIsImp0aSI6IkE1NjYwMzQyNzQ0NTc3Nzg5MTE4MTBBN0ZDOEU3MEQxIn0.Q7FHkb02x8cEORjTjKAEWz4ZpPsPgCYOa5pdzSMI-zpt7i8L0MmLKrSayaNVmE8QCF0uenmGo1mIAmrmFdhvRL63Ik8CTba1grvX-TKm5icR8DAQVM-tWYk4QMioc0jpAAjcCHY-uT1YhvarhyI9EvpuH5NXM-NV_3Y33w4bM9EI1QsYiTLAFLPSgdlXsIbxRbHt-n3idwLF5S4JvTk6bZsudHEEVCkZkQeu7MyijbW-xOUO7etGt9QNbe8QVFrf9xdTpkVpplOwPxz0I6gM4Ko_RpiYrfOWETE15H8cJ92o_tZVGTD2Yq2ExMQ1JwgslcF3rlVSP5mVqFgcubFEfQ",
        "User-Agent": "PostmanRuntime/7.36.1",
        "Accept": "*/*",
        "Connection": "keep-alive",
        # Assuming the cookie value you want to replicate is stored in `cookie_value`
        "Cookie": "__cf_bm=iqq9rAOdRxOSVTZOobCu0Cvhkivf1SlmCcG1gw4Xi30-1706955589-1-Aa0RGjh4F69/I0W+TGstpDWUlcTAp1jf+uiO6NpO5ZzfavFezJMo2vsrSNQhyzLP5hSh0fhN4l4pMKp/VgTNL2w=; UiPathBrowserId=95881d46-83cb-480f-b8de-c066dd467146"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.is_success:
            # Process successful response
            data = response.json()
            print(data)
            return data
        else:
            # Handle error response
            print(f"Error: {response.status_code}")
            return {"error": "Request failed", "status_code": response.status_code}

