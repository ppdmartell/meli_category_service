from concurrent.futures import ThreadPoolExecutor, as_completed # as_completed is a function not an alias
from threading import Lock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from collections import deque
import json
import logging
import time
import os

from app.infrastructure.auth_api import AuthServiceClient
from app.infrastructure.meli_api import MeliCategoryClient
from app.core.access_token_service import AccessTokenService
from app.core.site_service import SiteService
from app.core.url_resolution_service import UrlResolutionService


class CategoryService:
    def __init__(self, auth_service_client: AuthServiceClient = None):
        self.access_token_service = AccessTokenService()
        self.site_service = SiteService()
        self.meli_client = MeliCategoryClient()
        self.url_resolution_service = UrlResolutionService()
        self.auth_service_client = auth_service_client
        self.grace_period = 24
        self.grace_unit = "hours"       # days, seconds, microseconds, milliseconds, minutes, hours, and weeks
        self.access_token = None

        # This dictionary will be an index for containing all the categories without nesting
        # (the tree flattened) which will help in infering the URLs for every category.
        # Once the index (dict) is built, access time will be O(1)
        self.category_index = {}
        # And this lock is for the index, since it will be constructed at the same time the tree
        # is built, hence the lock, to avoid threading issues.
        self._index_lock = Lock()

        self.logger = logging.getLogger(__name__)
        self.max_workers = 20           # We could consider increasing this value for faster tree-building


    def fetch_and_save(self):
        access_token_data = self.auth_service_client.get_access_token()
        self.logger.info("New access token fetched.")
        self.access_token_service.save_access_token(access_token_data)
        self.logger.info("New access token saved into database.")
        return access_token_data.get("access_token")


    def get_access_token(self):
        """
        Check if a token exists. If so, checks if it's expired. If expired, fetch a new one
        from meli_auth_service and saves it in the database, and assign it to self.access_token
        variable.
        """
        token_from_db = self.access_token_service.get_access_token()
        if not token_from_db:
            self.logger.info("No access_token found for current session, requesting a new one.")
            self.access_token = self.fetch_and_save()
            return self.access_token
        else:
            self.logger.info("Access token found in the database. Checking if still valid.")
            if self.access_token_service.is_existing_access_token_expired():
                self.logger.info("Access token expired, fetching a new one and save it into database.")
                self.access_token = self.fetch_and_save()
            else:
                self.logger.info("Access token not expired, returning it from database.")
                self.access_token = token_from_db

        return self.access_token

    
    def call_api_and_save_sites(self):
        sites = self.meli_client.get_sites(self.get_access_token())
        self.site_service.save_sites(sites)
        self.logger.info("Sites retrieved via API and persisted in the database.")
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
            self.logger.info("Sites found in the database, checking age.")
            latest_updated = max(site["updated_at"] for site in sites)
            now = datetime.now(timezone.utc)
            if latest_updated.tzinfo is None:
                latest_updated = latest_updated.replace(tzinfo=timezone.utc)
            
            kwargs = {self.grace_unit: self.grace_period}
            if now - latest_updated > timedelta(**kwargs):
                self.logger.info(
                    f"Sites in database are older than grace_period: {self.grace_period} {self.grace_unit},"
                    f" calling API and persisting refreshed sites."
                )
                return self.call_api_and_save_sites()
        if not sites:
            self.logger.info("Sites not found in database, retrieving them via API.")
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
        Not used by the category tree process, but used instead for simple calls for only
        one category info at the time. Will return the entire category info as-is from MeLi.
        """
        return self.meli_client.get_category_info(category_id, self.get_access_token())


    def get_category_info_thread_safe(self, category_id: str) -> dict:
        """
        This method is custom-made, its purpose is to return the data in a specific way to make
        it useful for the multi-threading category tree building. Just retrieve the data for
        each category here, without sharing mutability, and later aggregate the data into the
        top-level tree (which later will become in the full category tree).

        This method is made for building the category tree.
        """
        try:
            category_info = self.meli_client.get_category_info(category_id, self.access_token) # -> dict
        except Exception as exc:
            self.logger.critical(f"Failed to fetch category info for {category_id}:"
                                 f" {exc}")
            # Re-raising the exception so the FastAPI route can raise a 500
            raise RuntimeError(f"Critical error building category tree, make sure a retry is"
                               f" attempted! -> {exc}")

        # Return the data in a dictionary form. Since this will be called several times using
        # threads, each time a dictionary will be returned, with the key being the category_id.
        # Threads only return this data, never modifies the shared object.
        self.logger.debug(f"Calling: {category_id}")

        data = {
            "id": category_id,
            "name": category_info.get("name"),
            "site_id": category_id[:3],
            "permalink": category_info.get("permalink"),
            "url": category_info.get("permalink"),
            "total_items_in_this_category": category_info.get("total_items_in_this_category"),
            "fragile": category_info.get("settings").get("fragile", False),
            "path_from_root": category_info.get("path_from_root"),

            # To be filled later
            "children": {},

            # We retain only the child IDs for recursion
            "children_ids": [
                child["id"] for child in category_info.get("children_categories", [])
            ]
        }

        # Controlling the index construction with the lock.
        # And shallow copying the data info (data.copy), otherwise we would get the fully
        # constructed trees for each category as well.
        with self.index_lock:
            flat = data.copy()
            # break the shared reference to the children dict. And avoid fully trees in the index dict
            flat["children"] = {}
            # make children_ids independent (list copy), since the list is also mutable
            flat["children_ids"] = list(data["children_ids"])
            self.category_index[category_id] = flat
        
        return data
    

    def dump_tree_and_index_to_json(self, category_tree, category_index, response_status, site_id):
        # Dumping the tree and index JSON files.
        tree_json_dir = os.path.join("app", "tree")
        os.makedirs(tree_json_dir, exist_ok=True)
        file_path = os.path.join(tree_json_dir, f"meli_category_tree_{site_id}.json")
        file_path_index = os.path.join(tree_json_dir, f"meli_category_index_{site_id}.json")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(category_tree, f, indent=2, ensure_ascii=False)
            json_op_message = f"JSON file of the tree successfully created: {file_path}"
            self.logger.info(json_op_message)
            response_status.append(json_op_message)
        except Exception as exc:
            response_status.append(f"Error saving the JSON file of the tree: {exc}")
        
        # Dumping index
        try:
            with open(file_path_index, "w", encoding="utf-8") as f:
                json.dump(category_index, f, indent=2, ensure_ascii=False)
            json_op_message = (f"Index ({len(self.category_index)} items) JSON file successfully"
                               f" created: {file_path_index}")
            self.logger.info(json_op_message)
            response_status.append(json_op_message)
        except Exception as exc:
            response_status.append(f"Error saving the index JSON file: {exc}")

        return response_status


    def build_category_tree(self, site_id: str):
        """
        This one uses BFS to build the tree. And returns info about tree creation time and JSON file
        creation.
        """
        start = time.perf_counter()
        self.get_site_info_by_id(site_id)
        top_level_categories = self.meli_client.get_top_level_categories(self.get_access_token(), site_id)
        category_tree = {}
        
        queue = deque((cat["id"], category_tree) for cat in top_level_categories)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while queue:
                futures_map = {
                    executor.submit(self.get_category_info_thread_safe, cid): (cid, parent)
                    for cid, parent in list(queue)           
                }
                queue.clear()

                for fut in as_completed(futures_map):
                    cid, parent_container = futures_map[fut]
                    try:
                        data = fut.result()
                    except Exception as exc:
                        self.logger.critical(f"Failed fetching category {cid}: {exc}")
                        raise RuntimeError(f"Failed fetching category {cid}: {exc}")

                    parent_container[cid] = data

                    for child_id in data["children_ids"]:
                        queue.append((child_id, data["children"]))

        stop = time.perf_counter()
        construction_time = f"Tree built in: {(stop - start):.4f} seconds."
        self.logger.info(construction_time)
        response_status = [construction_time]

        # Infer the URL for each category
        self.url_resolution_service.resolve_url_for_categories(category_tree, self.category_index)

        # Dump JSON objects to JSON files
        response_status = self.dump_tree_and_index_to_json(
            category_tree, self.category_index, response_status, site_id)

        return response_status

    
    # Used to avoid calling the tree building process everytime.
    # This method is only to test the usage of url inferer utilities
    def stub_method(self):
        tree = "Tree object"
        index = "Index object"
        return "Working on the url inference part."
