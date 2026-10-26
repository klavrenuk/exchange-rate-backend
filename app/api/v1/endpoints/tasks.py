from fastapi import APIRouter
from app.tasks import jobs

router = APIRouter()


@router.post("/run-all")
async def run_all():
    await jobs.run_all_manual()
    return {"status": "ok"}
