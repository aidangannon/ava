from typing import Protocol, Any, ContextManager

__all__ = ["logger", "Logger"]


class Logger(Protocol):
    """
    non-implementation specific duck-type for the logger
    """

    def info(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def warning(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def error(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def contextualize(self, *args: Any, **kwargs: Any) -> ContextManager[Any]: ...


logger: Logger
