from dataclasses import dataclass
from typing import final

from sqlalchemy.exc import OperationalError


@final
@dataclass(frozen=True, slots=True)
class DuplicateError:
    model: str
    key: str
    detail: str

    def __str__(self) -> str:
        return f"duplicate {self.model}: {self.key} ({self.detail})"


@final
@dataclass(frozen=True, slots=True)
class DBError:
    message: str

    def __str__(self) -> str:
        return f"database error: {self.message}"


type WriteError = DuplicateError | DBError


@final
@dataclass(frozen=True, slots=True)
class FetchError:
    url: str
    message: str

    def __str__(self) -> str:
        return f"fetch error ({self.url}): {self.message}"


@final
@dataclass(frozen=True, slots=True)
class ValidationError:
    message: str

    def __str__(self) -> str:
        return f"validation error: {self.message}"


type IngestionError = FetchError | ValidationError | DBError


def db_error_from(e: OperationalError) -> DBError:
    if e.orig is not None and e.orig.args:
        return DBError(message=str(e.orig.args[0]))
    if e.orig is not None:
        return DBError(message=str(e.orig))
    return DBError(message="unknown database error")
