from fastapi import APIRouter
from ..common import Tags 

router = APIRouter()


@router.get("/decommission", tags=Tags.decommission.value)
async def read_decommission():
    return [{"decommission": "decommissioned"}]