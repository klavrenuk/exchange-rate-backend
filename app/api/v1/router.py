from fastapi import APIRouter
from app.api.v1.endpoints import status, nbrb, iea, tasks

api_router = APIRouter()
api_router.include_router(status.router, tags=["status"])
api_router.include_router(nbrb.router, prefix="/nbrb", tags=["nbrb"])
api_router.include_router(iea.router, prefix="/iea", tags=["iea"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
