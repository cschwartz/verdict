from pydantic import BaseModel

from app.models.system import SystemPublic


class SystemListResponse(BaseModel):
    systems: list[SystemPublic]
    total: int
