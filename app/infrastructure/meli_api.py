import requests
import threading
import time
import logging

from app.config.env import Settings

class MeliCategoryClient:

    MELI_API_BASE_URL = None

    # Throttler variables
    BASE_DELAY = 0.07 # ~ 14 req/sec (840 per minute)
    MAX_DELAY = 2.0   # a request per 5 seconds (cool down)

    def __init__(self):
        Settings.load()
        self.MELI_API_BASE_URL = Settings.MELI_API_BASE_URL
        self.logger = logging.getLogger(__name__)
        self.thread_local = threading.local() # throttler variable for delay to be shared among threads


    def get_sites(self, access_token):
        """
        This method calls MeLi API and get all the sites (countries) MeLi is available for.
        """
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


    def get_top_level_categories(self, access_token, site_id: str) -> list[dict]:
        """
        This method calls MeLi API and get all the categories for a certain site_id (country)
        e.g. MLU (Uruguay), MLA (Argentina), ...
        and returns the top categories
        Sample curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/sites/MLA/categories
        """
        if not site_id:
            raise RuntimeError("[ERROR] No site_id found, please provide one.")
        
        url = f"{self.MELI_API_BASE_URL}/sites/{site_id}/categories"
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
    

    def _get_thread_delay(self):
        """Initialize delay per thread if missing"""
        if not hasattr(self.thread_local, "delay"):
            self.thread_local.delay = self.BASE_DELAY
        return self.thread_local.delay
    

    def _set_thread_delay(self, value):
        """Assign per-thread delay"""
        self.thread_local.delay = value


    def _throttled_request(self, method, url, headers, max_retries=10):
        """
        We don't know what's the MeLi requests limit per app (developer), I tried initially with 845
        and no 429 (too many requests) was returned. But maybe in the future they decide to lower
        that limit (whichever is) and then get several 429 and possibly leading to get the app (access)
        blocked permanently.
        So, the idea is to implement a dynamic throttler/limiter which will adjust the parameters
        based on any 429 error code received, thus increasing or decreasing the requests per second
        dynamically.

        IMPORTANT: This works for each thread independently. For example, if one thread gets a 429,
        only that thread slows down. Avoiding all the threads to slow down. The same with speeding up.
        """
        attempt = 0

        while True:
            delay = self._get_thread_delay()

            try:
                response = requests.request(method, url, headers=headers, timeout=15)

                # 429 - Then rate limit
                if response.status_code == 429:
                    attempt += 1
                    new_delay = min(delay * 2, self.MAX_DELAY)
                    self._set_thread_delay(new_delay)
                    self.logger.warning(f"[429] Thread {threading.get_ident()} faced 429 status code,"
                                        f" slowing to {new_delay:.2f}s")
                    time.sleep(new_delay) # Sleep a bit before continuing.
                    continue

                # Success? - Then continue and attempt speed up a bit toward BASE_DELAY
                if response.status_code < 400:
                    new_delay = max(delay * 0.9, self.BASE_DELAY)
                    self._set_thread_delay(new_delay)

                    time.sleep(new_delay) # Short pause. Always pause, that's the purpose of the mechanism
                    return response.json()
                
                # other errros, escalate:
                response.raise_for_status()
            
            except Exception as exc:
                attempt += 1
                if attempt >= max_retries:
                    raise RuntimeError(f"Request failed after {max_retries} retries (max_retries): {exc}")
                
                # backoff (slow down) on network errors too just in case
                new_delay = min(delay * 2, self.MAX_DELAY)
                self._set_thread_delay(new_delay)
                self.logger.info(f"After network error, thread {threading.get_ident()} is retrying "
                                 f"in {new_delay:2f}s. Error: {exc}")
                time.sleep(new_delay)



    def get_category_info(self, category_id, access_token):
        """
        Given a certain category_id (e.g. MLU442392), an API call will be made to MeLi to retrieve
        info about that category such as URL, name, etc...
        Sample curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/categories/MLA5725
        """
        url = f"{self.MELI_API_BASE_URL}/categories/{category_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            category_info = self._throttled_request("GET", url, headers=headers)
            return category_info
        except Exception as exc:
            self.logger.critical(f"Failed to fetch category {category_id}: {exc}")
            raise
