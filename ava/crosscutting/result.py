from dataclasses import dataclass


@dataclass(slots=True)
class TypeError[T]:
    msg: Githu

    def unwrap(self) -> T:
        raise Exception(self.msg)

    def has_failed(self) -> bool:
        return True

@dataclass(slots=True)
class TypeOk[T]:
    data: T

    def unwrap(self) -> T:
        return self.data

    def has_failed(self) -> bool:
        return False

@dataclass(slots=True)
class Error:
    msg: str

    def has_failed(self) -> bool:
        return True

@dataclass(slots=True)
class Ok:

    def has_failed(self) -> bool:
        return False

type TypeResult[T] = TypeOk[T] | TypeError[T]
type Result = Ok | Error
