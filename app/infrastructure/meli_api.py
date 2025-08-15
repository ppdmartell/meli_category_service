import requests
from app.config.env import Settings

class MeliCategoryClient:

    MELI_API_BASE_URL = None

    def __init__(self):
        Settings.load()
        self.MELI_API_BASE_URL = Settings.MELI_API_BASE_URL


    # This method calls MeLi API and get all the sites (countries) MeLi is in.
    def get_sites(self, access_token):
        if not access_token:
            raise RuntimeError("[ERROR] No access_token was provided, unable to continue with request.")
        
        url = f"{self.MELI_API_BASE_URL}/sites"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("[ERROR] Status code: ", response.status_code)
            print("[ERROR] Response text: ", response.text)
            raise e
    
        return response.json()


    # This method calls MeLi API and get all the categories for a certain site_id (country)
    # e.g. MLU (Uruguay), MLA (Argentina), ...
    # and returns the top categories
    # Sample curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN'   https://api.mercadolibre.com/sites/MLA/categories
    def get_top_level_categories(self, access_token, site_id: str) -> list[dict]:
        if not site_id:
            raise RuntimeError("[ERROR] No site_id found, please provide one.")
        
        self.MELI_API_BASE_URL = f"{Settings.MELI_API_BASE_URL}/sites/{site_id}/categories"
        url = self.MELI_API_BASE_URL
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("[ERROR] Status code: ", response.status_code)
            print("[ERROR] Response text: ", response.text)
            raise e

        return response.json()
