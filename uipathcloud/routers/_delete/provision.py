from fastapi import APIRouter

router = APIRouter()


@router.get("/provision/", tags=["provision"])
async def read_provision():
    return [{"provision": "provision"}]