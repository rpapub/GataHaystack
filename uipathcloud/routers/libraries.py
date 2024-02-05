from fastapi import APIRouter

router = APIRouter(
    prefix="/uipathcloud",
    tags=["libraries (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

@router.get("/libraries", tags=["inventory"])
async def read_libraries():
    return [{"libraries": "dummy"}]


@router.get("/libraries/{library_id_int}", summary="Retrieve a library")
async def uipathcloud_library_retrieve(library_id_int: int):
    pass


@router.post("/libraries", summary="Create a new library")
async def uipathcloud_library_create():
    pass

@router.put("/libraries", summary="Update a library")
async def uipathcloud_library_update():
    pass

@router.delete("/libraries", summary="Delete a library")
async def uipathcloud_library_delete():
    pass