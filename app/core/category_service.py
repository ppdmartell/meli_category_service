from app.infrastructure.auth_api import AuthServiceClient

class CategoryService:
    def __init__(self):
        #self.category_repo = CategoryRepository()
        self.auth_client = AuthServiceClient()

    def initialize_access_token(self):
        return self.auth_client.get_access_token()