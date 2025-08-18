from app.infrastructure.repository.access_token_repository import AccessTokenRepository

class AccessTokenService:
    def __init__(self):
        self.access_token_repo = AccessTokenRepository()


    def get_access_token(self) -> str | None:
        """
        Calls the method in access_token_repo.
        """
        return self.access_token_repo.get_access_token()
    
    def save_access_token(self, token_data: dict) -> bool:
        """
        Calls the method in access_token_repo.
        """
        return self.access_token_repo.save_access_token(token_data)
    

    def is_existing_access_token_expired(self) -> bool:
        """
        Calls the method in access_token_repo
        """
        return self.access_token_repo.is_existing_access_token_expired()