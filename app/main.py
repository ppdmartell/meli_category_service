from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import os
import logging
from datetime import datetime

from app.core.category_service import CategoryService
from app.infrastructure.auth_api import AuthServiceClient
from app.routes import category_routes
from app.dependencies.singleton_auth_service_client import get_auth_service_client # Singleton imported
from app.infrastructure.db_initializer import initialize_database

# 1. Create "logs" folder in a portable way
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# 2. Create timestamped log file
log_filename = f"meli_category_service_log_{datetime.now().strftime('%Y-%m-%d')}.log"
log_filepath = os.path.join(LOGS_DIR, log_filename)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_filepath, encoding="utf-8"),
        logging.StreamHandler()  # optional: also print to console
    ]
)

category_service = CategoryService(get_auth_service_client())   # Singleton injected to the constructor


# This code will try to get the access_token from meli_auth_service microservice before everything
# and if it fails, the app will fail fast.
# NOTE: Code before yield executes before and code after yield is executed after
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_database()
        print("[INFO] Database initialized successfully.")
    except Exception as e:
        print("[ERROR] Database couldn't be initialize at startup. Please check and correct.")

    try:
        category_service.get_access_token()
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