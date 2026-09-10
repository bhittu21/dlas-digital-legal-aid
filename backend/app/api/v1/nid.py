from fastapi import APIRouter
from app.schemas.nid import NIDVerifyRequest, NIDVerifyResponse
from app.services.nid_service import MockNIDAdapter

router = APIRouter()


@router.post("/verify", response_model=NIDVerifyResponse)
def verify_bangladesh_nid(req: NIDVerifyRequest):
    """
    Simulated/Demo Bangladesh National Identity (NID) verification adapter.
    Validates format (10-digit Smart NID or 13/17-digit Legacy) and returns simulated demographic profile.
    Explicitly states no live government API connection exists.
    """
    return MockNIDAdapter.verify_nid(req)
