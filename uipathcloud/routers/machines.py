from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import parse_obj_as
import httpx
from ..config import Settings, get_settings
from ..models.uipathcloud import Machine


router = APIRouter(
    prefix="/uipathcloud",
    tags=["machines (beta)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/machines", summary="Retrieve all machines or filter by tenant", tags=["inventory"])
async def uipathcloud_machines_retrieve_all(request: Request, settings: Settings = Depends(get_settings)):

    accept_header = request.headers.get("accept", "")
    access_token = settings.uipathcloud_organizations[0].applications[0].access_tokens[0].access_token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "*/*",
        "User-Agent": "httpx",
    }

    # Construct the machines API URL using settings
    machines_url = f"{settings.uipathcloud_baseurl}/cprimadotnet/homelab23/orchestrator_/odata/Machines"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(machines_url, headers=headers)
            response.raise_for_status()
            machines_data = response.json().get("value", [])
            machines = parse_obj_as(List[Machine], machines_data)
            if "application/json" in accept_header:
                #machines = parse_obj_as(List[Machine], machines_data)  # Assuming machines_data can be parsed into List[Machine]
                #return JSONResponse(content={"machines": [machine.dict() for machine in machines]})
                machine_data_modified = [{**machine, "LicenseKey": str(machine["LicenseKey"]), "Key": str(machine["Key"])} for machine in machines_data]
                return JSONResponse(content={"machines": machine_data_modified})
            else:
                return templates.TemplateResponse("machines.html", {"request": request, "machines": machines_data, "app_name": settings.app_name, "settings": settings.mask_sensitive_data()})
    except httpx.HTTPError as e:
        # Log the actual error detail from the exception
        error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=error_detail) #pylint: disable=no-member


@router.get("/machines/{machine_id_int}", summary="Retrieve a machine")
async def uipathcloud_machines_retrieve(machine_id_int: int):
    pass

@router.post("/machines", summary="Create a new machine")
async def uipathcloud_machines_create():
    pass

@router.put("/machines", summary="Update a machine")
async def uipathcloud_machines_update():
    pass

@router.delete("/machines", summary="Delete a machine")
async def uipathcloud_machines_delete():
    pass