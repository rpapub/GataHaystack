from typing import List, Optional, Union
from fastapi import APIRouter, Query, HTTPException, Body, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator, parse_obj_as
import httpx
from ..common import Tags
from functools import lru_cache
from typing import Annotated
from ..config import Settings
from ..models.uipathcloud import Machine

#@lru_cache
def get_settings():
    return Settings()


router = APIRouter(
    prefix="/uipathcloud",
    tags=["machines (beta)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")

# Dummy database of machines for demonstration
fake_machine_db: List[Machine] = [
    # Example machines
    Machine(machine_id_int=1, tenant_id="tenant1", name="Machine1", type="Type1", configuration={"key": "value"}),
    Machine(machine_id_int=2, tenant_id="tenant2", name="Machine2", type="Type2", configuration={"key": "value"})
]

# @router.get("/machines", response_model=List[Machine], summary="Retrieve all machines or filter by tenant", tags=["inventory"])
# async def uipathcloud_machine_retrieve_all(tenant_id: Optional[List[str]] = Query(None, description="Tenant ID(s) to filter by")):
#     """
#     Retrieves all machines or filters them by the provided tenant ID(s). 
#     Pass multiple tenant IDs as query parameters to filter by more than one tenant.
#     """
#     if tenant_id:
#         return [machine for machine in fake_machine_db if machine.tenant_id in tenant_id]
#     return fake_machine_db

# Updated function to use TemplateResponse
@router.get("/machines", summary="Retrieve all machines or filter by tenant", tags=["inventory"])
async def uipathcloud_machine_retrieve_all(request: Request, settings: Settings = Depends(get_settings)):
#async def uipathcloud_machine_retrieve_all(request: Request, settings: Settings = Depends(get_settings), tenant_id: Optional[List[str]] = Query(None, description="Tenant ID(s) to filter by")):
    """
    Retrieves all machines or filters them by the provided tenant ID(s).
    Pass multiple tenant IDs as query parameters to filter by more than one tenant.
    """

    # # Filter machines based on the tenant_id query parameter
    # filtered_machines = [machine for machine in fake_machine_db if not tenant_id or machine.tenant_id in tenant_id]
    # print(filtered_machines)
    # # Extract distinct tenant_ids from filtered machines to pass to the template
    # distinct_tenant_ids = list(set(machine.tenant_id for machine in filtered_machines))
    
    # # Return a template response, passing the filtered machines and distinct tenant IDs to the template
    # return templates.TemplateResponse("machines.html", {
    #     "request": request,
    #     "settings": settings.mask_sensitive_data(),
    #     "machines": filtered_machines,  # Pass the filtered list of machines
    #     "tenant_ids": distinct_tenant_ids  # Pass the list of distinct tenant IDs
    # })    # Assuming settings has an attribute or method to get the correct access token for the organization
    print(settings)
    return ""
    access_token = "your_access_token_here"  # You'll need to replace this with actual token retrieval logic
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
            return {"machines": machines}
    except httpx.HTTPError as e:
        # Log the actual error detail from the exception
        error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=error_detail)


# @router.post("/machines/filter", response_model=List[Machine], summary="Filter machines by tenant IDs")
# async def uipathcloud_machine_filter(tenant_query: TenantQuery):
#     """
#     Filters machines based on the specified tenant IDs. This endpoint supports specifying either multiple tenant IDs or a single tenant ID.
#     """
#     tenant_ids = tenant_query.tenant_ids
#     filtered_machines = [machine for machine in fake_machine_db if machine.tenant_id in tenant_ids]
#     return filtered_machines


# # Endpoint to retrieve a specific machine by ID
# @router.get("/machines/{machine_id_int}", response_model=Machine, summary="Retrieve a machine")
# async def uipathcloud_machine_retrieve(machine_id_int: int, tenant: str = Query(..., description="Tenant ID")):
#     """
#     Retrieves a machine by its ID for the specified tenant.
#     """
#     for machine in fake_machine_db:
#         if machine.machine_id_int == machine_id_int and machine.tenant_id == tenant:
#             return machine
#     raise HTTPException(status_code=404, detail="Machine not found")

# @router.post("/machines", summary="Create a new machine", response_model=Machine)
# async def uipathcloud_machine_create(machine_create: MachineCreate):
#     """
#     Creates a new machine within specified tenants.
#     """
#     created_machine = Machine(
#         machine_id_int="generated_machine_id",  # Adjust generation logic as needed.
#         tenant_id=machine_create.tenant_ids[0],  # Adjust based on logic for handling multiple tenants.
#         name=machine_create.name,
#         type=machine_create.type,
#         configuration=machine_create.configuration or {}
#     )
#     fake_machine_db.append(created_machine)
#     return created_machine


# # Endpoint to update a machine
# @router.put("/machines/{machine_id_int}", response_model=Machine, summary="Update a machine")
# async def uipathcloud_machine_update(machine_id_int: int, machine_update: MachineUpdate, tenant: str = Query(..., description="Tenant ID")):
#     """
#     Updates a machine's details for the specified tenant.
#     """
#     for machine in fake_machine_db:
#         if machine.machine_id_int == machine_id_int and machine.tenant_id == tenant:
#             if machine_update.name is not None:
#                 machine.name = machine_update.name
#             if machine_update.type is not None:
#                 machine.type = machine_update.type
#             if machine_update.configuration is not None:
#                 machine.configuration = machine_update.configuration
#             return machine
#     raise HTTPException(status_code=404, detail="Machine not found")

# # Endpoint to delete a machine
# @router.delete("/machines/{machine_id_int}", response_model=Machine, summary="Delete a machine")
# async def uipathcloud_machine_delete(machine_id_int: int, tenant: str = Query(..., description="Tenant ID")):
#     """
#     Deletes a machine by its ID for the specified tenant.
#     """
#     for index, machine in enumerate(fake_machine_db):
#         if machine.id == machine_id_int and machine.tenant_id == tenant:
#             return fake_machine_db.pop(index)
#     raise HTTPException(status_code=404, detail="Machine not found")
