from app.infrastructure.auth_api import AuthServiceClient
from app.infrastructure.meli_api import MeliCategoryClient

class CategoryService:
    def __init__(self, auth_service_client: AuthServiceClient):
        #self.category_repo = CategoryRepository()
        self.auth_service_client = auth_service_client
        self.meli_client = MeliCategoryClient()

    def initialize_access_token(self):
        return self.auth_service_client.initialize_access_token()
    
    def get_sites(self):
        access_token = self.auth_service_client.get_access_token()
        print(f"[DEBUG] access_token: {access_token}")
        return self.meli_client.get_sites(access_token)