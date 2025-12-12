import re
import threading
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from bs4 import BeautifulSoup

from app.infrastructure.meli_api import MeliCategoryClient



class UrlResolutionService:

    def __init__(self):
        self.meli_client = MeliCategoryClient()
        self.max_workers = 20
        self._index_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()   # Reused for performance
        self._catid_href_regex = re.compile(r'href=["\']([^"\']*#CATEGORY_ID=(MLU\d+)[^"\']*)["\']',
                                         flags=re.IGNORECASE)

    def resolve_url_for_categories(self, category_tree: dict[str, dict], category_index: dict[str, dict]):
        if not category_tree and category_index:
            raise RuntimeError(f"Objects category_tree and category_index are empty!"
                               f" Can't continue with the process")
        
        # queue starts with top-level categories
        queue = deque(category_tree.values())
        # The top-level categories are already resolved (they come with permalink)
        resolved_url_count = len(category_tree.values())
        futures = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            
            while queue:
                batch = list(queue)
                queue.clear()

                for node in batch:
                    # If already resolved, then enqueue children and move to next (continue).
                    # This current one won't be processed again, avoiding reiteration and
                    # leading to O(n).
                    if node["url"]:
                        for child in node["children"].values():
                            queue.append(child)
                        continue

                    parent_id = self._get_parent_id(node)
                    # If not parent_id that means is a top-level category.
                    if not parent_id:
                        continue

                    # Preferred over category_index.get(parent_id), because it will fail with error
                    # and that's a sign something is wrong. Otherwise, get() will return None.
                    parent_node = category_index[parent_id]
                    parent_url = parent_node.get("url")

                    # Can't resolve until parent's URL is resolved, so enqueues for later.
                    if not parent_url:
                        queue.append(node)
                        continue

                    # Determine level in which the node is located in the tree
                    # 0 - top-level
                    # 1+ - children
                    level = len(node["path_from_root"]) - 1

                    # Level 1 categories have a particular way of resolving the URL, because their
                    # id is present in the parent's webpage in the form of:
                    # https://listado.mercadolibre.com.uy/accesorios-vehiculos/acc-motos-cuatriciclos/#CATEGORY_ID=MLU1772
                    if level == 1:
                        futures.append(
                            executor.submit(self._resolve_level1, node, parent_node)
                        )



    def _get_parent_id(self, node):
        """
        Docstring for _get_parent_id:

        MeLi provides the path from category to the root. A simple way to get the parent
        id of a category is checking the second to the last entry in path_from_root,
        which is the parent id, the last entry is the category itself.
        
        :param node: is a category (simple, undeveloped)
        """
        pfr = node.get("path_from_root", [])
        if len(pfr) < 2:
            return None
        return pfr[-2]["id"]
    

    def _fetch_html(self, url):
        html_code = self.meli_client.get_html_scrape_code(url)

        if not html_code:



    def _resolve_level1(self, node, parent_node):
         """Parent HTML contains CATEGORY_ID=... for level 1."""
         parent_url = parent_node["url"]
         html = self._fetch_html(parent_url)
         if not html:
             return None
        