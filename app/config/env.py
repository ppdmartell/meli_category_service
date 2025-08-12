import os
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    _loaded = False

    AUTH_SERVICE_PROTOCOL = None
    AUTH_SERVICE_URL = None
    AUTH_SERVICE_PORT = None
    AUTH_SERVICE_ROUTE = None
    MELI_API_BASE_URL = None
    MELI_API_SITES_URL = None
    DB_URL = None

    @classmethod
    def load(cls):
        if cls._loaded == True:
            return
        
        # Try loading from environment variables first (injected by Docker/Kubernetes)
        cls.AUTH_SERVICE_PROTOCOL = os.getenv("AUTH_SERVICE_PROTOCOL")
        cls.AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
        cls.AUTH_SERVICE_PORT = os.getenv("AUTH_SERVICE_URL")
        cls.AUTH_SERVICE_PORT = os.getenv("AUTH_SERVICE_ROUTE")
        cls.MELI_API_BASE_URL = os.getenv("MELI_API_BASE_URL")
        cls.MELI_API_SITES_URL = os.getenv("MELI_API_SITES_URL")
        cls.DB_URL = os.getenv("DB_URL")
        
        if not all([cls.AUTH_SERVICE_PROTOCOL, cls.AUTH_SERVICE_URL, cls.AUTH_SERVICE_PORT, cls.AUTH_SERVICE_ROUTE, cls.DB_URL]):
            print("[INFO] Environment variables not fully loaded. Falling back to local .env file...")


            # Fallback to .env for local dev. This code portion must be replaced
            # after Docker secrets is implemented
            env_path = Path(__file__).resolve().parent.parent / ".env"

            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                cls.AUTH_SERVICE_PROTOCOL = os.getenv("AUTH_SERVICE_PROTOCOL")
                cls.AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
                cls.AUTH_SERVICE_PORT = os.getenv("AUTH_SERVICE_PORT")
                cls.AUTH_SERVICE_ROUTE = os.getenv("AUTH_SERVICE_ROUTE")
                cls.MELI_API_BASE_URL = os.getenv("MELI_API_BASE_URL")
                cls.MELI_API_SITES_URL = os.getenv("MELI_API_SITES_URL")
                cls.DB_URL = os.getenv("DB_URL")

                if not all([cls.AUTH_SERVICE_PROTOCOL, cls.AUTH_SERVICE_URL, cls.AUTH_SERVICE_PORT, cls.AUTH_SERVICE_ROUTE, cls.DB_URL]):
                    raise EnvironmentError("[ERROR] Missing one or more required environment variables:" \
                    " AUTH_SERVICE_PROTOCOL," \
                    " AUTH_SERVICE_URL," \
                    " AUTH_SERVICE_PORT," \
                    " AUTH_SERVICE_ROUTE" \
                    " DB_URL.")
            else:
                fallback_loaded = load_dotenv()
                if not fallback_loaded:
                    raise FileNotFoundError("[ERROR] Missing .env file in both expected and fallback paths.")

        cls._loaded = True
