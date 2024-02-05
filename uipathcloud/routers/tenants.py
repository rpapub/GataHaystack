from fastapi import APIRouter

router = APIRouter(
    prefix="/uipathcloud",
    tags=["tenants (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

@router.get("/tenants", tags=["inventory"])
async def read_tenants():
    return [{"tenants": "dummy"}]


@router.get("/tenants/{tenant_id_int}", summary="Retrieve a tenant")
async def uipathcloud_tenant_retrieve(tenant_id_int: int):
    pass


@router.post("/tenants", summary="Create a new tenant")
async def uipathcloud_tenant_create():
    pass

@router.put("/tenants", summary="Update a tenant")
async def uipathcloud_tenant_update():
    pass

@router.delete("/tenants", summary="Delete a tenant")
async def uipathcloud_tenant_delete():
    pass