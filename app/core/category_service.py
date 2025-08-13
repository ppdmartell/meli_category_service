from app.infrastructure.auth_api import AuthServiceClient
from app.infrastructure.meli_api import MeliCategoryClient
from app.infrastructure.access_token_repository import AccessTokenRepository

class CategoryService:
    def __init__(self, auth_service_client: AuthServiceClient):
        self.access_token_repo = AccessTokenRepository()
        self.auth_service_client = auth_service_client
        self.meli_client = MeliCategoryClient()

    def fetch_and_save(self):
        access_token_data = self.auth_service_client.initialize_access_token()
        print("[INFO] New access token fetched.")
        self.access_token_repo.save_access_token(access_token_data)
        print("[INFO] New access token saved into database.")

    def initialize_access_token(self):
        """
        Check if a token exists. If so, checks if it's expired. If expired, fetch a new one
        and save it in the database.
        """
        access_token = self.access_token_repo.get_access_token()
        if access_token:
            if self.access_token_repo.is_existing_access_token_expired():
                print("[INFO] Access token expired, fetching a new one and save it into database.")
                self.fetch_and_save()
        else:
            print("[INFO] No access token found, requesting a new one.")
            self.fetch_and_save()
    
    def get_sites(self):
        access_token = self.auth_service_client.get_access_token()
        print(f"[DEBUG] access_token: {access_token}")
        return self.meli_client.get_sites(access_token)