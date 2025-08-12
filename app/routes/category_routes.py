from fastapi import APIRouter, Depends

from app.core.category_service import CategoryService
from app.dependencies.singleton_auth_service_client import get_auth_service_client, AuthServiceClient

router = APIRouter()

@router.get("/api/v1/sites")
def get_sites(auth_client: AuthServiceClient = Depends(get_auth_service_client)):        # Injecting the singleton for AuthServiceClient
    category_service = CategoryService(auth_client)
    return category_service.get_sites()