from fastapi import APIRouter, Depends

from app.core.category_service import CategoryService
from app.dependencies.singleton_auth_service_client import get_auth_service_client, AuthServiceClient

router = APIRouter(prefix="/api/v1") # This appends /api/v1 at the beginning of every endpoint

@router.get("/sites") # Returns all the sites available (countries where MeLi is operating or related to)
def get_sites(auth_client: AuthServiceClient = Depends(get_auth_service_client)):        # Injecting the singleton for AuthServiceClient
    category_service = CategoryService(auth_client)
    return category_service.get_sites()

@router.get("/{site_id}/categories")
async def build_category_tree(site_id: str):
    """
    This endpoint builds (persist in the database) and returns the category tree with
    links to each category and other required data for each of the categories.
    """
    category_service = CategoryService()
    return category_service.build_category_tree(site_id)

@router.get("/{category_id}")
async def get_category_info(category_id: str):
    category_service = CategoryService()
    return category_service.get_category_info(category_id)