from pydantic import BaseModel


class SyncResponse(BaseModel):
    roles_synced: int
    permissions_synced: int
