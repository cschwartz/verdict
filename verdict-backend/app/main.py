from fastapi import FastAPI

from app.routes.assets import router as assets_router
from app.routes.ingestion import router as ingestion_router
from app.routes.systems import router as systems_router

app = FastAPI()
app.include_router(assets_router)
app.include_router(systems_router)
app.include_router(ingestion_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
