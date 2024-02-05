from fastapi import APIRouter

router = APIRouter(
    prefix="/uipathcloud",
    tags=["packages (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

@router.get("/packages", tags=["inventory"])
async def read_packages():
    return [{"packages": "dummy"}]


@router.get("/packages/{package_id_int}", summary="Retrieve a package")
async def uipathcloud_package_retrieve(package_id_int: int):
    pass


@router.post("/packages", summary="Create a new package")
async def uipathcloud_package_create():
    pass

@router.put("/packages", summary="Update a package")
async def uipathcloud_package_update():
    pass

@router.delete("/packages", summary="Delete a package")
async def uipathcloud_package_delete():
    pass