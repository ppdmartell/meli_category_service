from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "meli_category_service is running."}