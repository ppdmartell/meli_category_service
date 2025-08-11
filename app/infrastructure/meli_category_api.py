import requests
from app.config.env import Settings

class MeliCategoryClient:

    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

    #def get_categories_for_site(self, site -> str) -> dict:
