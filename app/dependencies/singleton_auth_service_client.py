# The entire purpose of this file is to have a Singleton instance of AuthServiceClient
# that can be shared across classes and methods.

from app.infrastructure.auth_api import AuthServiceClient

singleton_auth_service_client = AuthServiceClient()

def get_auth_service_client() -> AuthServiceClient:
    return singleton_auth_service_client