from dataclasses import dataclass


@dataclass(slots=True)
class Error:
    msg: str

type Result[T] = T | Error

def has_failed[T](result: Result[T]) -> bool:
    return isinstance(result, Error)

