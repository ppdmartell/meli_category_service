from concurrent.futures import ThreadPoolExecutor, as_completed # as_completed is a function not an alias
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
    

    def get_site_info_by_id(self, site_id: str) -> dict | None:
        """
        This method gets information from the site by using the site_id passed via parameter.
        e.g. site: {
            'default_currency_id': 'UYU',
            'id': 'MLU',
            'name': 'Uruguay',
            'updated_at': datetime.datetime(2025, 12, 4, 19, 7, 13, 956660)
        }
        """
        site = self.site_service.get_site_info_by_id(site_id)
        if site is None:
            raise HTTPException(status_code=404, detail=f"Site {site_id} was not found.")
        return site


    def get_category_info(self, category_id: str):
        """
        This method calls meli client and retrieve information for a category by providing
        the category id (e.g. MLU5725)
        """
        access_token = self.get_access_token()      # Always try to get an access token to make API calls
        return self.meli_client.get_category_info(category_id, access_token)


    def get_category_info_thread_safe(self, category_id: str) -> dict:
        """
        This method is custom-made, its purpose is to return the data in a specific way to make
        it useful for the multi-threading category tree building. Just retrieve the data for
        each category here, without sharing mutability, and later aggregate the data into the
        top-level tree (which later will become in the full category tree).
        """
        try:
            category_info = self.get_category_info(category_id)  # This returns a dictionary
        except Exception as exc:
            print(f"[CRITICAL ERROR]: Failed to fetch category info for {category_id}:"
                  f" {exc}")
            # Re-raising the exception so the FastAPI route can raise a 500
            raise RuntimeError(f"Critical error building category tree, make sure a retry is"
                               f" attempted! -> {exc}")

        # Return the data in a dictionary form. Since this will be called several times using
        # threads, each time a dictionary will be returned, with the key being the category_id.
        # Threads only return this data, never modifies the shared object.
        return category_id, {
            "id": category_id,
            "name": category_info.get("name"),
            "site_id": category_id[:3],
            "url": category_info.get("permalink"),
            "total_items_in_this_category": category_info.get("total_items_in_this_category"),
            "fragile": category_info.get("settings").get("fragile", False),
            "parent_id": category_info.get("path_from_root"),
            "children": category_info.get("children_categories", [])
        }

    
    def initialize_tree_with_top_level_categories(self, top_level_categories_id_strings: list[str]) -> dict:
        """
        Mercado Libre only provides URL (permalink) for top-level categories, so this method
        initializes the tree (dictionary) and get's the permalink for the top-level categories
        via API calls, this is the first step.

        import time
        start = time.perf_counter()
        end = time.perf_counter()
        execution_time = end - start

        Profiling time without threads: 9.0332 seconds
        Profiling time with threads: 1.6221 seconds
        """
        category_tree = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            # cid is category_id, just used to save characters
            futures = {executor.submit(self.get_category_info_thread_safe, cid): cid for cid in top_level_categories_id_strings}

            for future in as_completed(futures):
                cid = futures[future]
                try:
                    category_id, data = future.result()
                except Exception as exc:
                    # If Critical failure -> abort everything
                    raise RuntimeError(f"[CRITICAL] Failed to fetch category {cid}: {exc}")
                
                category_tree[category_id] = data
            
            # Raise a RuntimeError if the lengths differ, which means one or more categories were not processed
            if len(top_level_categories_id_strings) != len(category_tree):
                raise RuntimeError(f"[CRITICAL] Resulting dictionary length for top-level categories"
                                   f" differs in size with the list of strings containing the category ids.")
            
        return category_tree


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
        access_token = self.get_access_token()      # Always try to get an access token to make API calls
        self.get_site_info_by_id(site_id)           # Fails with 404 if site_id doesn't exist (XLW instead of MLU)

        # This line gets all the categories for a certain site_id, including its names -> list[dict]
        top_level_categories_info = self.meli_client.get_top_level_categories(access_token, site_id)

        # And this line strips all the info and leaves only a list of string ["MLU5725","MLU1512","MLU1403",...]
        top_level_categories_id_strings = [category["id"] for category in top_level_categories_info]

        category_tree = self.initialize_tree_with_top_level_categories(top_level_categories_id_strings)

        return category_tree
