import requests
from app.config.env import Settings

class AuthServiceClient:

    URL = None

    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

    # This method will call meli_auth_service microservice and get and access token,
    # and that access token will be used to make calls to MeLi.
    def get_access_token(self) -> dict:
        Settings.load()

        if not all([Settings.AUTH_SERVICE_PROTOCOL, Settings.AUTH_SERVICE_URL, Settings.AUTH_SERVICE_PORT,
                     Settings.AUTH_SERVICE_ROUTE]):
            raise RuntimeError("[ERROR] One or more values are missing: AUTH_SERVICE_PROTOCOL, AUTH_SERVICE_URL," \
            " AUTH_SERVICE_PORT, AUTH_SERVICE_ROUTE. Can't proceed with the auth call to get the access token.")
        
        self.URL = (
            f"{Settings.AUTH_SERVICE_PROTOCOL}{Settings.AUTH_SERVICE_URL}"
            f"{Settings.AUTH_SERVICE_PORT}{Settings.AUTH_SERVICE_ROUTE}"
        )

        response = requests.post(self.URL, headers=self.headers, timeout=15)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("[WARNING] Check the auth_service microservice is up and listening.")
            print(f"[ERROR] {e}")
            raise e
        
        return response.json()