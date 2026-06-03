from dataclasses import dataclass


@dataclass(slots=True)
class Error:
    msg: str

type TypeResult[T] = T | Error
type Result = None | Error

def has_failed(result) -> bool:
    return isinstance(result, Error)

