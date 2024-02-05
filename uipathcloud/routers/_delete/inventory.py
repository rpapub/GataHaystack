from fastapi import APIRouter

router = APIRouter()


@router.get("/inventory", tags=["inventory"])
async def read_inventory():
    return [{"inventory": "inventory"}]