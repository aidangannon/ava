import time
from ava.application import service
from ava.application import ports
import sys
import loguru
from ava.crosscutting import logging
from ava import claude
from ava import file_config
from ava import _github

def setup_ports() -> None:
    ports.issue_inbox = _github.github_issue_inbox
    ports.clone_repo = _github.clone_github_repo
    ports.config_repository = file_config.file_config_repository
    ports.run_agent = claude.run_claude

def setup_logging() -> None:
    logging.logger = loguru.logger
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, serialize=True)

def run_task() -> None:
    logging.logger.info("Starting schedule")

    try:
        service.ava_routine() 
    except Exception as e:
        logging.logger.error(f"Exception occurred in schdule '{str(e)}'")

    logging.logger.info("Ending schedule")

setup_ports()
setup_logging()

while True:
    run_task()

    time.sleep(300)
