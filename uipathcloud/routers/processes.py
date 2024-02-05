from fastapi import APIRouter

router = APIRouter(
    prefix="/uipathcloud",
    tags=["processes (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

@router.get("/processes", tags=["inventory"])
async def read_processes():
    return [{"processes": "dummy"}]


@router.get("/processes/{process_id_int}", summary="Retrieve a process")
async def uipathcloud_process_retrieve(process_id_int: int):
    pass


@router.post("/processes", summary="Create a new process")
async def uipathcloud_process_create():
    pass

@router.put("/processes", summary="Update a process")
async def uipathcloud_process_update():
    pass

@router.delete("/processes", summary="Delete a process")
async def uipathcloud_process_delete():
    pass