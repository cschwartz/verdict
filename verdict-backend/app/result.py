from dataclasses import dataclass
from typing import NoReturn, final

from fastapi import HTTPException


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

    def unwrap(self) -> T:
        return self.value

    def unwrap_or[D](self, default: D) -> T:  # pyright: ignore[reportInvalidTypeVarUse]  # D unused in return but keeps signature consistent with Err.unwrap_or
        return self.value


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    value: E

    def unwrap(self) -> NoReturn:
        raise RuntimeError(f"Called unwrap on Err: {self.value}")

    def unwrap_or[D](self, default: D) -> D:
        return default

    def __str__(self) -> str:
        return str(self.value)


type Result[T, E] = Ok[T] | Err[E]


@final
@dataclass(frozen=True, slots=True)
class Some[T]:
    value: T

    def unwrap(self) -> T:
        return self.value

    def unwrap_or[D](self, default: D) -> T:  # pyright: ignore[reportInvalidTypeVarUse]  # D unused in return but keeps signature consistent with Nothing.unwrap_or
        return self.value


@final
@dataclass(frozen=True, slots=True)
class Nothing:
    def unwrap(self) -> NoReturn:
        raise RuntimeError("Called unwrap on Nothing")

    def unwrap_or[D](self, default: D) -> D:
        return default

    def __str__(self) -> str:
        return "nothing"


type Option[T] = Some[T] | Nothing


def unwrap_or_raise[T, E](
    result: Result[Option[T], E],
    *,
    err_status: int = 503,
    not_found_status: int = 404,
    not_found_detail: str = "Not found",
) -> T:
    """Unwrap a ``Result[Option[T], E]`` or raise an ``HTTPException``.

    Raises *err_status* for ``Err`` and *not_found_status* for ``Nothing``.
    """
    if isinstance(result, Err):
        raise HTTPException(status_code=err_status, detail=str(result))
    match result.value:
        case Some(value):
            return value
        case _:
            raise HTTPException(status_code=not_found_status, detail=not_found_detail)
