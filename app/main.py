from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.category_service import CategoryService

category_service = CategoryService()

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

@app.get("/health")
def health():
    return {"status": "meli_category_service is running."}