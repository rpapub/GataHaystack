from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from typing import List, Optional

router = APIRouter(
    prefix="/uipathcloud",
    tags=["folders (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")

@router.get("/folders", tags=["inventory"])
async def read_folders():
    return [{"folders": "dummy"}]


@router.get("/folders/{folder_id_int}", summary="Retrieve a folder")
async def uipathcloud_folder_retrieve(folder_id_int: int):
    pass


@router.post("/folders", summary="Create a new folder")
async def uipathcloud_folder_create():
    pass

@router.put("/folders", summary="Update a folder")
async def uipathcloud_folder_update():
    pass

@router.delete("/folders", summary="Delete a folder")
async def uipathcloud_folder_delete():
    pass