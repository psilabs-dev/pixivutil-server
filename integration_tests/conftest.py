import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from PixivServer.config.celery import (
    DEAD_LETTER_QUEUE_NAME,
    LEGACY_MAIN_QUEUE_NAME,
    MAIN_QUEUE_NAME,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://localhost:8000"
AUTH_HEADER = ("Authorization", "Bearer pixiv")
DEV_SUCCESS_SENTINEL = "/tmp/pixivutil-dev-dlq-success.flag" # TODO: this requires a redesign.

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

    def dev_task_state(self, task_id: str) -> dict:
        state = self.api_json("GET", f"/api/dev/task/{task_id}")
        if not isinstance(state, dict):
            raise RuntimeError(f"Unexpected dev task state payload for {task_id}: {state!r}")
        return state

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

    def restart_worker(self) -> None:
        self.compose("restart", "pixivutil-worker", timeout=240)

    def wait_for_queue_absent(self, queue_name: str, timeout: int = 45) -> None:
        deadline = time.time() + timeout
        last_counts: dict[str, int] | None = None
        while time.time() < deadline:
            counts = self.rabbitmq_queue_counts()
            last_counts = counts
            if queue_name not in counts:
                return
            time.sleep(1)
        raise RuntimeError(f"Queue {queue_name!r} still exists after {timeout}s (last_counts={last_counts})")

    def seed_legacy_main_queue_message(self, body: str = "legacy-cutover-test") -> None:
        script = (
            "from kombu import Connection, Exchange, Queue; "
            f"from PixivServer.config.celery import LEGACY_MAIN_EXCHANGE_NAME, LEGACY_MAIN_QUEUE_NAME; "
            "conn = Connection('amqp://guest:guest@rabbitmq:5672'); "
            "conn.connect(); "
            "ex = Exchange(LEGACY_MAIN_EXCHANGE_NAME, type='direct', durable=True); "
            "q = Queue(LEGACY_MAIN_QUEUE_NAME, exchange=ex, routing_key=LEGACY_MAIN_QUEUE_NAME, durable=True); "
            "q = q.bind(conn); q.declare(); "
            "producer = conn.Producer(); "
            f"producer.publish({body!r}, exchange=ex, routing_key=LEGACY_MAIN_QUEUE_NAME, "
            "content_type='text/plain', content_encoding='utf-8', delivery_mode=2); "
            "conn.release()"
        )
        self.docker_exec("pixivutil-worker", "python", "-c", script, timeout=120)

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

    def wait_for_dev_task_terminal_state(self, task_id: str, terminal_state: str, timeout: int = 45) -> dict:
        deadline = time.time() + timeout
        last_state: dict | None = None
        last_error: str | None = None
        while time.time() < deadline:
            try:
                state = self.dev_task_state(task_id)
                last_state = state
                if state.get("terminal_state") == terminal_state:
                    return state
            except urllib.error.HTTPError as exc:
                last_error = str(exc)
                if exc.code != 404:
                    raise
            time.sleep(1)
        raise RuntimeError(
            f"Dev task {task_id!r} did not reach terminal_state={terminal_state!r} within {timeout}s "
            f"(last_state={last_state}, last_error={last_error})"
        )

    def dev_priority_probe_state(self) -> dict:
        state = self.api_json("GET", "/api/dev/priority")
        if not isinstance(state, dict):
            raise RuntimeError(f"Unexpected dev priority probe payload: {state!r}")
        return state

    def wait_for_priority_probe_started_count(self, expected: int, timeout: int = 90) -> dict:
        deadline = time.time() + timeout
        last_state: dict | None = None
        while time.time() < deadline:
            state = self.dev_priority_probe_state()
            last_state = state
            started = state.get("started")
            if isinstance(started, list) and len(started) >= expected:
                return state
            time.sleep(0.5)
        raise RuntimeError(
            f"Priority probe did not reach started_count>={expected} within {timeout}s (last_state={last_state})"
        )

    def clear_state(self) -> None:
        self.docker_exec(
            "pixivutil-worker",
            "sh",
            "-lc",
            (
                f"rm -f {DEV_SUCCESS_SENTINEL} "
                "/workdir/.pixivUtil2/dev-dlq-task-state.json "
                "/workdir/.pixivUtil2/dev-dlq-task-state.tmp "
                "/workdir/.pixivUtil2/dev-priority-task-state.json "
                "/workdir/.pixivUtil2/dev-priority-task-state.tmp"
            ),
            check=False,
        )
        self.docker_exec(
            "rabbitmq",
            "rabbitmqctl",
            "purge_queue",
            MAIN_QUEUE_NAME,
            check=False,
            timeout=90,
        )
        self.docker_exec(
            "rabbitmq",
            "rabbitmqctl",
            "purge_queue",
            DEAD_LETTER_QUEUE_NAME,
            check=False,
            timeout=90,
        )
        self.docker_exec(
            "rabbitmq",
            "rabbitmqctl",
            "purge_queue",
            LEGACY_MAIN_QUEUE_NAME,
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
    compose_env.wait_for_queue_count(MAIN_QUEUE_NAME, 0, timeout=30)
    compose_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 0, timeout=30)
    yield compose_env
    compose_env.clear_state()
