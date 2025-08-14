from datetime import datetime, timezone, timedelta

from app.infrastructure.auth_api import AuthServiceClient
from app.infrastructure.meli_api import MeliCategoryClient
from app.infrastructure.repository.access_token_repository import AccessTokenRepository
from app.infrastructure.repository.site_repository import SiteRepository

class CategoryService:
    def __init__(self, auth_service_client: AuthServiceClient):
        self.access_token_repo = AccessTokenRepository()
        self.site_repo = SiteRepository()
        self.auth_service_client = auth_service_client
        self.meli_client = MeliCategoryClient()
        self.grace_period = 24
        self.grace_unit = "hours"       # days, seconds, microseconds, milliseconds, minutes, hours, and weeks

    
    def get_access_token(self):
        token = self.access_token_repo.get_access_token()
        if not token:
            self.fetch_and_save()
            token = self.access_token_repo.get_access_token()
        return token


    def fetch_and_save(self):
        access_token_data = self.auth_service_client.initialize_access_token()
        print("[INFO] New access token fetched.")
        self.access_token_repo.save_access_token(access_token_data)
        print("[INFO] New access token saved into database.")


    def initialize_access_token(self):
        """
        Check if a token exists. If so, checks if it's expired. If expired, fetch a new one
        from meli_auth_service and saves it in the database.
        """
        access_token = self.get_access_token()
        if access_token:
            print("[INFO] Access token found in the database. Proceeding if still valid.")
            if self.access_token_repo.is_existing_access_token_expired():
                print("[INFO] Access token expired, fetching a new one and save it into database.")
                self.fetch_and_save()
        else:
            print("[INFO] No access token found, requesting a new one.")
            self.fetch_and_save()

    
    def call_api_and_save_sites(self):
        access_token = self.get_access_token()
        sites = self.meli_client.get_sites(access_token)
        self.site_repo.save_sites(sites)
        print("[INFO] Sites retrieved via API and persisted in the database.")
        return sites


    def get_sites(self):
        """
        Checks for sites stored previously in the database. If found, will check for expiring
        grace period set. If expired, will call the API for refreshed info and persist them
        in the database.
        If there are no sites in the database, will directly make the API call and persist them.
        """
        sites = self.site_repo.get_sites()
        if sites:
            print("[INFO] Sites found in the database, checking age.")
            latest_updated = max(site["updated_at"] for site in sites)
            now = datetime.now(timezone.utc)
            if latest_updated.tzinfo is None:
                latest_updated = latest_updated.replace(tzinfo=timezone.utc)
            
            kwargs = {self.grace_unit: self.grace_period}
            if now - latest_updated > timedelta(**kwargs):
                print(
                    f"[INFO] Sites in database are older than grace_period: {self.grace_period} {self.grace_unit},"
                    f" calling API and persisting refreshed sites."
                )
                return self.call_api_and_save_sites()
        if not sites:
            print("[INFO] Sites not found in database, retrieving them via API.")
            return self.call_api_and_save_sites()
        return sites