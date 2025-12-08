from app.infrastructure.repository.site_repository import SiteRepository

class SiteService:
    def __init__(self):
        self.site_repo = SiteRepository()


    def save_sites(self, sites: list[dict]):
        """
        Calls save_sites in site_repo
        """
        self.site_repo.save_sites(sites)


    def get_sites(self) -> dict | None:
        """
        Calls get_sites in site_repo
        """
        return self.site_repo.get_sites()
    

    def get_site_info_by_id(self, site_id: str) -> dict | None:
        """
        Calls get_site_info_by_id in site_repo
        """
        return self.site_repo.get_site_info_by_id(site_id)
