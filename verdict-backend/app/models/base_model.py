from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base for all table models. Provides an auto-increment integer primary key."""

    id: int | None = Field(default=None, primary_key=True)
