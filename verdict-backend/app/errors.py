from dataclasses import dataclass
from typing import final


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
