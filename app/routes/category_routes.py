from fastapi import APIRouter, Depends

from app.core.category_service import CategoryService
from app.dependencies.singleton_auth_service_client import get_auth_service_client, AuthServiceClient

router = APIRouter(prefix="/api/v1") # This appends /api/v1 at the beginning of every endpoint

@router.get("/sites") # Returns all the sites available (countries where MeLi is operating or related to)
def get_sites(auth_client: AuthServiceClient = Depends(get_auth_service_client)):        # Injecting the singleton for AuthServiceClient
    category_service = CategoryService(auth_client)
    return category_service.get_sites()

@router.get("/{site_id}/categories")
async def get_top_level_categories(site_id: str):
    category_service = CategoryService()
    return category_service.get_top_level_categories(site_id)