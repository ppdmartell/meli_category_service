from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.infrastructure.auth_api import AuthServiceClient
from app.infrastructure.meli_api import MeliCategoryClient
from app.core.access_token_service import AccessTokenService
from app.core.site_service import SiteService


class CategoryService:
    def __init__(self, auth_service_client: AuthServiceClient = None):
        self.access_token_service = AccessTokenService()
        self.site_service = SiteService()
        self.auth_service_client = auth_service_client
        self.meli_client = MeliCategoryClient()
        self.grace_period = 24
        self.grace_unit = "hours"       # days, seconds, microseconds, milliseconds, minutes, hours, and weeks

    
    def get_access_token(self):
        token = self.access_token_service.get_access_token()
        if not token:
            self.fetch_and_save()
            token = self.access_token_service.get_access_token()
        return token


    def fetch_and_save(self):
        access_token_data = self.auth_service_client.initialize_access_token()
        print("[INFO] New access token fetched.")
        self.access_token_service.save_access_token(access_token_data)
        print("[INFO] New access token saved into database.")


    def initialize_access_token(self):
        """
        Check if a token exists. If so, checks if it's expired. If expired, fetch a new one
        from meli_auth_service and saves it in the database.
        """
        access_token = self.get_access_token()
        if access_token:
            print("[INFO] Access token found in the database. Proceeding if still valid.")
            if self.access_token_service.is_existing_access_token_expired():
                print("[INFO] Access token expired, fetching a new one and save it into database.")
                self.fetch_and_save()
        else:
            print("[INFO] No access token found, requesting a new one.")
            self.fetch_and_save()

    
    def call_api_and_save_sites(self):
        access_token = self.get_access_token()
        sites = self.meli_client.get_sites(access_token)
        self.site_service.save_sites(sites)
        print("[INFO] Sites retrieved via API and persisted in the database.")
        return sites


    def get_sites(self):
        """
        Checks for sites stored previously in the database. If found, will check for expiring
        grace period set. If expired, will call the API for refreshed info and persist them
        in the database.
        If there are no sites in the database, will directly make the API call and persist them.
        """
        sites = self.site_service.get_sites()
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
    

    def get_by_id(self, site_id: str) -> dict | None:
        """
        This method gets information from the site by using the site_id passed via parameter.
        e.g. site: {
            'default_currency_id': 'UYU',
            'id': 'MLU',
            'name': 'Uruguay',
            'updated_at': datetime.datetime(2025, 12, 4, 19, 7, 13, 956660)
        }
        """
        site = self.site_service.get_by_id(site_id)
        if site is None:
            raise HTTPException(status_code=404, detail=f"Site {site_id} was not found.")
        return site

    def build_category_tree(self, site_id: str) -> list[dict]:
        """
        This method is critical, retrieves the top-level categories, and from there
        builds the category tree by filling the gaps between the top-level categories
        and the children categories, down to the leaves categories. It also persists
        in the database this tree to be fed to the scrappers.

        Checks for the category tree stored previously in the database.
        If found, will check for expiring grace period set. If expired,
        will call the API for refreshed info and build and persist the
        category tree in the database.
        If there is no category tree in the database, will directly make the API call
        and build and persist it. Then return it. 
        """
        self.get_by_id(site_id)
        access_token = self.get_access_token()
        top_level_categories = self.meli_client.get_top_level_categories(access_token, site_id)
