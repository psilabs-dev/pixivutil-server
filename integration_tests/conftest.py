import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://localhost:8000"
AUTH_HEADER = ("Authorization", "Bearer pixiv")
DEV_SUCCESS_SENTINEL = "/tmp/pixivutil-dev-dlq-success.flag" # TODO: this requires a redesign.


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--pixiv-api",
        action="store_true",
        default=False,
        help="Run tests that make Pixiv API calls.",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        "markers",
        "pixiv_api: test performs Pixiv API calls and is skipped unless --pixiv-api is provided.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if config.getoption("--pixiv-api"):
        return
    skip_pixiv_api = pytest.mark.skip(reason="need --pixiv-api option enabled")
    for item in items:
        if "pixiv_api" in item.keywords:
            item.add_marker(skip_pixiv_api)


def _run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int = 120,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Command timed out ({timeout}s): {' '.join(args)}") from exc

    if check and proc.returncode != 0:
        stderr = proc.stderr.strip()
        stdout = proc.stdout.strip()
        detail = stderr or stdout
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(args)}\n{detail}")
    return proc


def _require_docker_tools() -> None:
    if shutil.which("docker") is None:
        pytest.exit("docker is not available in PATH", returncode=1)
    _run(["docker", "--version"], timeout=15)
    _run(["docker", "compose", "version"], timeout=15)


def _http_json(method: str, path: str) -> object:
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method)
    req.add_header(*AUTH_HEADER)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


class ComposeTestEnv:
    def compose(self, *args: str, check: bool = True, timeout: int = 240) -> subprocess.CompletedProcess[str]:
        return _run(["docker", "compose", *args], check=check, timeout=timeout)

    def docker_exec(self, container: str, *args: str, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return _run(["docker", "exec", container, *args], check=check, timeout=timeout)

    def wait_http_ready(self, timeout: int = 60) -> None:
        deadline = time.time() + timeout
        last_error: str | None = None
        while time.time() < deadline:
            try:
                req = urllib.request.Request(f"{BASE_URL}/", method="GET")
                with urllib.request.urlopen(req, timeout=2):
                    return
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                time.sleep(1)
        raise RuntimeError(f"Server did not become ready within {timeout}s: {last_error}")

    def api_json(self, method: str, path: str) -> object:
        return _http_json(method, path)

    def rabbitmq_queue_counts(self) -> dict[str, int]:
        proc = self.docker_exec("rabbitmq", "rabbitmqctl", "list_queues", "name", "messages", timeout=90)
        counts: dict[str, int] = {}
        for line in proc.stdout.splitlines():
            if "\t" not in line:
                continue
            name, count = line.split("\t", 1)
            if name == "name":
                continue
            try:
                counts[name.strip()] = int(count.strip())
            except ValueError:
                continue
        return counts

    def wait_for_queue_count(self, queue_name: str, expected: int, timeout: int = 45) -> None:
        deadline = time.time() + timeout
        last_count: int | None = None
        while time.time() < deadline:
            last_count = self.rabbitmq_queue_counts().get(queue_name)
            if last_count == expected:
                return
            time.sleep(1)
        raise RuntimeError(
            f"Queue {queue_name!r} did not reach {expected} within {timeout}s (last={last_count})"
        )

    def wait_worker_log_contains(self, needle: str, timeout: int = 45) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            logs = self.compose("logs", "--tail=400", "pixivutil-worker", timeout=90).stdout
            if needle in logs:
                return
            time.sleep(1)
        raise RuntimeError(f"Worker logs did not contain expected text within {timeout}s: {needle}")

    def clear_state(self) -> None:
        self.docker_exec(
            "pixivutil-worker",
            "sh",
            "-lc",
            f"rm -f {DEV_SUCCESS_SENTINEL}",
            check=False,
        )
        self.docker_exec(
            "rabbitmq",
            "rabbitmqctl",
            "purge_queue",
            "pixivutil-dead-letter",
            check=False,
            timeout=90,
        )


@pytest.fixture(scope="session")
def compose_env() -> ComposeTestEnv:
    _require_docker_tools()
    env = ComposeTestEnv()
    env.compose("down", "--volumes", check=False, timeout=180)
    env.compose("up", "--build", "-d", timeout=600)
    env.wait_http_ready()
    yield env
    env.compose("down", "--volumes", check=False, timeout=180)


@pytest.fixture
def clean_env(compose_env: ComposeTestEnv) -> ComposeTestEnv:
    compose_env.clear_state()
    compose_env.wait_for_queue_count("pixivutil-dead-letter", 0, timeout=30)
    yield compose_env
    compose_env.clear_state()
