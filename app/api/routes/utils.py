from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/utils", tags=["utils"])

class TestRequest(BaseModel):
    message: str

@router.get("/health-check/")
async def health_check() -> bool:
    return True
