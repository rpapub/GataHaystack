from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..config import Settings
from functools import lru_cache
from typing import Annotated
import httpx

router = APIRouter()


@lru_cache
def get_settings():
    return Settings()

# Placeholder for storing tenant names
tenant_names = []

class TenantNamesInput(BaseModel):
    tenant_names: str  # Comma-separated tenant names

class TenantInfo(BaseModel):
    name: str
    tenant_id: int
    uuid: str
    display_name: str

@router.get("/setup", tags=["setup"])
async def read_setup(settings: Annotated[Settings, Depends(get_settings)]):
    tenant_names_output = tenant_names if tenant_names else None
    return [{"setup": "setup", "settings": settings.dict(), "tenant_names": tenant_names_output}]

# @router.post("/store-tenants/")
# async def store_tenant_names(tenant_input: TenantNamesInput):
#     global tenant_names
#     tenant_names = tenant_input.tenant_names.split(',')
#     return {"message": "Tenant names stored successfully", "tenant_names": tenant_names}



# async def fetch_tenant_id(settings: Settings, tenant_name: str) -> int:
#     url = f"{settings.uipath_cloud_baseurl}/{settings.uipath_cloud_orgname}/{tenant_name}/orchestrator_/odata/Settings/UiPath.Server.Configuration.OData.GetConnectionString"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         if response.status_code == 200:
#             data = response.json()
#             tenant_id_url = data["value"]
#             tenant_id = tenant_id_url.split('=')[-1]
#             return int(tenant_id)
#         else:
#             response.raise_for_status()

# @router.get("/process-tenants/")
# async def process_tenants(settings: Annotated[Settings, Depends(get_settings)]):
#     processed_tenants = []
#     for tenant_name in tenant_names:
#         try:
#             tenant_id = await fetch_tenant_id(settings, tenant_name)
#             tenant_info = TenantInfo(name=tenant_name, tenant_id=tenant_id, uuid="example-uuid", display_name="Example Display Name")
#             processed_tenants.append(tenant_info.dict())
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"Failed to process tenant {tenant_name}: {str(e)}")

#     return {"processed_tenants": processed_tenants}
    
# @router.get("/get-tenants/")
# async def get_tenant_names():
#     """
#     Retrieves the list of stored tenant names.
#     """
#     return {"tenant_names": tenant_names}
