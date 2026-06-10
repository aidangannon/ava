from ava.crosscutting.config import Config
from typing import Callable


# all the states that the application can be in
SEARCHING = "SEARCHING"
PENDING = "PENDING"
REVIEW = "REVIEW"


type StateRunnable = Callable[[Config], None]
