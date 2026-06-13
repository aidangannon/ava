from ava.crosscutting import logging
from ava.crosscutting.config import Config
import dacite
from ava.application import ports
from ava.application.states import review
from ava.application.states import pending
from ava.application.states import searching
from ava.application import states


state_machine: dict[str, states.StateRunnable] = {
    states.SEARCHING: searching.run,
    states.PENDING: pending.run,
    states.REVIEW: review.run
}

def ava_routine() -> None:
    config_dict = ports.config_repository.get_config().unwrap()

    config = dacite.from_dict(data=config_dict, data_class=Config)

    state = states.SEARCHING
    state_result = ports.config_repository.get_state()

    if not state_result.has_failed():
        state = state_result.unwrap()

    with logging.logger.contextualize(**{"STATE": state, "CONFIG": config}):
        state_machine[state](config)
