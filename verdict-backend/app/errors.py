from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import final

from sqlalchemy.exc import OperationalError


class AppError(ABC):
    """Base for all application errors.

    ``message`` is safe to expose to clients.
    ``detail`` includes diagnostic info for internal logging only.
    ``__str__`` returns ``message`` so errors are safe by default.
    """

    @property
    @abstractmethod
    def message(self) -> str: ...

    @property
    @abstractmethod
    def detail(self) -> str: ...

    def __str__(self) -> str:
        return self.message


@final
@dataclass(frozen=True, slots=True)
class DuplicateError(AppError):
    model: str
    key: str

    @property
    def message(self) -> str:
        return f"duplicate {self.model}"

    @property
    def detail(self) -> str:
        return f"duplicate {self.model}: {self.key}"


@final
@dataclass(frozen=True, slots=True)
class DBError(AppError):
    statement: str | None
    raw: str

    @property
    def message(self) -> str:
        return "database error"

    @property
    def detail(self) -> str:
        if self.statement:
            return f"database error: {self.statement}"
        return "database error"


@final
@dataclass(frozen=True, slots=True)
class FetchError(AppError):
    url: str
    raw: str

    @property
    def message(self) -> str:
        return "upstream service error"

    @property
    def detail(self) -> str:
        return f"fetch error ({self.url}): {self.raw}"


@final
@dataclass(frozen=True, slots=True)
class ValidationError(AppError):
    raw: str

    @property
    def message(self) -> str:
        return "validation error"

    @property
    def detail(self) -> str:
        return f"validation error: {self.raw}"


type WriteError = DuplicateError | DBError
type IngestionError = FetchError | ValidationError | DBError


def db_error_from(e: OperationalError) -> DBError:
    """Create a DBError from a SQLAlchemy OperationalError.

    Captures the SQL statement template (safe, no parameter values) and the
    raw driver message (for internal logging only).
    """
    if e.orig is not None and e.orig.args:
        raw = str(e.orig.args[0])
    elif e.orig is not None:
        raw = str(e.orig)
    else:
        raw = "unknown database error"

    return DBError(statement=e.statement, raw=raw)
