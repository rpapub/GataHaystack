from fastapi import APIRouter

router = APIRouter(
    prefix="/uipathcloud",
    tags=["assets (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

@router.get("/assets", tags=["inventory"])
async def read_assets():
    return [{"assets": "dummy"}]


@router.get("/assets/{asset_id_int}", summary="Retrieve a asset")
async def uipathcloud_asset_retrieve(asset_id_int: int):
    pass


@router.post("/assets", summary="Create a new asset")
async def uipathcloud_asset_create():
    pass

@router.put("/assets", summary="Update a asset")
async def uipathcloud_asset_update():
    pass

@router.delete("/assets", summary="Delete a asset")
async def uipathcloud_asset_delete():
    pass