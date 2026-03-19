from pydantic import BaseModel


class IAMUserIndexItem(BaseModel):
    id: str
    username: str
    email: str


class IAMUserDetail(BaseModel):
    id: str
    username: str
    email: str
    groups: list[str]
