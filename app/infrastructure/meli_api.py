import requests
from app.config.env import Settings

class MeliCategoryClient:

    MELI_API_BASE_URL = None

    def __init__(self):
        Settings.load()
        self.headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

    # This method calls MeLi API and get all the categories for a certain site_id (country)
    # e.g. MLU (Uruguay), MLA (Argentina), ...
    # and returns the top categories
    def get_categories_by_site_id(self, site_id: str) -> dict:
        if not site_id:
            raise RuntimeError("[ERROR] No site_id found, please provide one.")
        
        self.MELI_API_BASE_URL = f"{Settings.MELI_API_BASE_URL}{site_id}/categories"

