from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from app.core.category_service import CategoryService
from app.infrastructure.auth_api import AuthServiceClient
from app.routes import category_routes
from app.dependencies.singleton_auth_service_client import get_auth_service_client # Singleton imported


category_service = CategoryService(get_auth_service_client())   # Singleton injected to the constructor


# This code will try to get the access_token from meli_auth_service microservice before everything
# and if it fails, the app will fail fast.
# NOTE: Code before yield executes before and code after yield is executed after
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        category_service.initialize_access_token()
        print("[INFO] Access token fetched successfully at startup.")
    except Exception as e:
        print(f"[ERROR] Failed to fetch access token at startup: {e}")
        import sys
        sys.exit(1)
    yield
    # Optional: add shutdown code here if needed

app = FastAPI(lifespan=lifespan)
app.include_router(category_routes.router)

@app.get("/health")
def health():
    return {"status": "meli_category_service is running."}