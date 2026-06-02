import time
import tomllib
from pathlib import Path

from loguru import logger

from .github_client import GithubError, get_assigned_issues, get_user_reply_after_bot, issue_accessible
from .runner import run_claude

CONFIG_DIR = Path.home() / ".config" / "ava"
REPOS_FILE = CONFIG_DIR / "repos"
SKILLS_DIR = CONFIG_DIR / "skills"
HISTORY_DIR = CONFIG_DIR / "history"
STATUS_FILE_NAME = ".status"  # sits inside each HISTORY_DIR/owner/repo/issue/ dir


def load_config() -> dict:
    cfg = CONFIG_DIR / "config.toml"
    if cfg.exists():
        with open(cfg, "rb") as f:
            return tomllib.load(f)
    return {}


def load_skill() -> str:
    skill = SKILLS_DIR / "ava.md"
    return skill.read_text() if skill.exists() else ""


def load_repos() -> list[str]:
    if not REPOS_FILE.exists():
        return []
    return [l.strip() for l in REPOS_FILE.read_text().splitlines() if l.strip() and not l.startswith("#")]


def status_path(owner: str, repo: str, number: int) -> Path:
    return HISTORY_DIR / owner / repo / f"{number}.status"


def history_path(owner: str, repo: str, number: int) -> Path:
    return HISTORY_DIR / owner / repo / f"{number}.md"


def read_status(owner: str, repo: str, number: int) -> str | None:
    p = status_path(owner, repo, number)
    return p.read_text().strip() if p.exists() else None


def write_status(owner: str, repo: str, number: int, status: str):
    p = status_path(owner, repo, number)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(status)


def poll_once(config: dict, skill: str, repos: list[str]) -> bool:
    """Return True if we did work this cycle (so caller knows to skip new-issue scan)."""
    github_user = config["github_user"]

    # 1. Resume any issue waiting on user reply
    for status_file in HISTORY_DIR.glob("*/*/*.status"):
        if status_file.read_text().strip() != "waiting":
            continue
        number = int(status_file.stem)
        repo_name = status_file.parent.name
        owner = status_file.parent.parent.name

        try:
            if not issue_accessible(owner, repo_name, number):
                logger.error(f"{owner}/{repo_name}#{number}: issue gone, cleaning up")
                status_file.unlink(missing_ok=True)
                history_path(owner, repo_name, number).unlink(missing_ok=True)
                continue

            reply = get_user_reply_after_bot(owner, repo_name, number, github_user)
            if not reply:
                continue

            logger.info(f"User replied on {owner}/{repo_name}#{number}, resuming")
            hist = history_path(owner, repo_name, number)
            ctx = hist.read_text() if hist.exists() else None
            status, _ = run_claude(owner, repo_name, number, skill, config, reply=reply, history=ctx)
            write_status(owner, repo_name, number, status)
            if status == "done":
                logger.info(f"Finished {owner}/{repo_name}#{number}")
            return True

        except GithubError as e:
            logger.error(f"{owner}/{repo_name}#{number}: {e}")

    # 2. Pick up the first new assigned issue across repos
    for repo_spec in repos:
        if "/" not in repo_spec:
            logger.error(f"Bad repo format (expected owner/repo): {repo_spec}")
            continue
        owner, repo_name = repo_spec.split("/", 1)

        try:
            issues = get_assigned_issues(owner, repo_name, github_user)
        except GithubError as e:
            logger.error(f"{owner}/{repo_name}: {e}")
            continue

        for issue in issues:
            existing = read_status(owner, repo_name, issue.number)
            if existing in ("waiting", "done"):
                continue  # already tracked

            logger.info(f"Starting {owner}/{repo_name}#{issue.number}: {issue.title}")
            write_status(owner, repo_name, issue.number, "working")
            status, _ = run_claude(owner, repo_name, issue.number, skill, config)
            write_status(owner, repo_name, issue.number, status)
            if status == "done":
                logger.info(f"Finished {owner}/{repo_name}#{issue.number}")
            return True

    return False


def main():
    config = load_config()

    if not config.get("github_user"):
        logger.error("Set github_user in ~/.config/ava/config.toml")
        return

    repos = load_repos()
    if not repos:
        logger.warning("No repos listed in ~/.config/ava/repos")
        return

    skill = load_skill()
    poll_interval = config.get("poll_interval", 300)

    logger.info(f"Ava started, polling every {poll_interval}s")

    while True:
        poll_once(config, skill, repos)
        logger.info(f"Sleeping {poll_interval}s")
        time.sleep(poll_interval)
