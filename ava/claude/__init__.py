from ava.crosscutting import logging
import pwd
import subprocess
import os
from ava.application import ports
from ava.crosscutting.result import TypeError, TypeOk, TypeResult


def run_claude(skill: str, prompt: str, history: str | None = None) -> TypeResult[str | None]:
    config = ports.config_repository.get_config()
    if config.has_failed():
        return TypeError[str | None]("Failed to load config")

    ava_user = pwd.getpwnam("ava")
    env = {**os.environ, "ANTHROPIC_API_KEY": config.unwrap()["anthropic_token"], "SHELL": ava_user.pw_shell}
    stdin = f"{prompt}\n\n{history}" if history else prompt

    logging.logger.info(f"stdin is '{stdin}'")
    
    result = subprocess.run(
        ["claude", "-p", f"/{skill}", "--dangerously-skip-permissions"],
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        user=ava_user.pw_uid
    )

    if result.returncode != 0:
        return TypeError[str | None](result.stderr)

    stdout = result.stdout.strip() or None

    logging.logger.info(f"stdout is '{stdout}'")

    return TypeOk[str | None](stdout)
