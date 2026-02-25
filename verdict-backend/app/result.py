from dataclasses import dataclass
from typing import NoReturn, final


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
