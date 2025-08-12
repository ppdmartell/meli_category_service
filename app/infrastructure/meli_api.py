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
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("[ERROR] Status code: ", response.status_code)
            print("[ERROR] Response text: ", response.text)
            raise e
    
        return response.json()


    # This method calls MeLi API and get all the categories for a certain site_id (country)
    # e.g. MLU (Uruguay), MLA (Argentina), ...
    # and returns the top categories
    def get_categories_by_site_id(self, access_token, site_id: str) -> dict:
        if not site_id:
            raise RuntimeError("[ERROR] No site_id found, please provide one.")
        
        self.MELI_API_BASE_URL = f"{Settings.MELI_API_BASE_URL}{site_id}/categories"
        headers = {"Authorization": f"Bearer {access_token}"}

