from fastapi import FastAPI

from app.routes.assets import router as assets_router

app = FastAPI()
app.include_router(assets_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
