from fastapi import FastAPI

from app.routes.assets import router as assets_router
from app.routes.ingestion import router as ingestion_router
from app.routes.roles import router as roles_router
from app.routes.sync import router as sync_router
from app.routes.systems import router as systems_router
from app.routes.users import router as users_router

app = FastAPI()
app.include_router(assets_router)
app.include_router(systems_router)
app.include_router(ingestion_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(sync_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
