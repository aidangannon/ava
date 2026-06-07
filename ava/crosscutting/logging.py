import sys
from typing import Protocol, Any, ContextManager

import loguru


__all__ = ["logger", "Logger"]


class Logger(Protocol):
    """
    non-implementation specific duck-type for the logger
    """

    def info(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def warning(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def error(self, __message: str, *args: Any, **kwargs: Any) -> None: ...

    def contextualize(self, *args: Any, **kwargs: Any) -> ContextManager[Any]: ...


loguru.logger.remove()
loguru.logger.add(sys.stdout, serialize=True)
logger: Logger = loguru.logger
