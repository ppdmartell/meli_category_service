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
    # and that access token will be used to make calls to MeLi. This method will be
    # executed once, at the beginning. And the rest of the methods will call get_acces_token
    # below, instead of this method
    def fetch_access_token(self) -> dict:
        """
        Fetches a new access token from meli_auth_service.
        Should be called only once at service startup.
        """
        Settings.load()
        if not all([
            Settings.AUTH_SERVICE_PROTOCOL,
            Settings.AUTH_SERVICE_URL,
            Settings.AUTH_SERVICE_PORT,
            Settings.AUTH_SERVICE_ROUTE
        ]):
            raise RuntimeError("[ERROR] One or more values are missing: AUTH_SERVICE_PROTOCOL, AUTH_SERVICE_URL," \
            " AUTH_SERVICE_PORT, AUTH_SERVICE_ROUTE. Can't proceed with the auth call to get the access token.")
        
        self.URL = (
            f"{Settings.AUTH_SERVICE_PROTOCOL}"
            f"{Settings.AUTH_SERVICE_URL}"
            f"{Settings.AUTH_SERVICE_PORT}"
            f"{Settings.AUTH_SERVICE_ROUTE}"
        )

        try:
            response = requests.post(self.URL, headers=self.headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                "[ERROR] Failed to connect to auth_service. "
                "Make sure it is running and reachable."
            ) from e
        
        data = response.json()

        if not data.get("access_token"):
            raise RuntimeError("[ERROR] No access_token found in meli_auth_service response.")
        return data
    
    
    def initialize_access_token(self):
        return self.fetch_access_token()