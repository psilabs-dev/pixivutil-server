import json
import logging
import time
from pathlib import Path
from typing import Any

from celery import shared_task

from PixivServer.config.celery import MAIN_QUEUE_NAME
from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest

logger = logging.getLogger(__name__)

_SIMULATED_RETRY_COUNTDOWN = 1
_SIMULATED_MAX_RETRIES = 1
_SUCCESS_SENTINEL_PATH = Path("/tmp/pixivutil-dev-dlq-success.flag")
_TASK_STATE_PATH = Path("/workdir/.pixivUtil2/dev-dlq-task-state.json")
_PRIORITY_STATE_PATH = Path("/workdir/.pixivUtil2/dev-priority-task-state.json")


def _load_task_states() -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(_TASK_STATE_PATH.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.warning("(dev) Could not parse task state file; resetting")
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, dict):
            result[key] = value
    return result


def _save_task_states(states: dict[str, dict[str, Any]]) -> None:
    _TASK_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _TASK_STATE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(states, sort_keys=True))
    temp_path.replace(_TASK_STATE_PATH)


def _record_task_attempt(task_id: str, artwork_id: int, attempt: int) -> None:
    states = _load_task_states()
    state = states.get(task_id)
    if not isinstance(state, dict):
        state = {
            "task_id": task_id,
            "artwork_id": artwork_id,
            "attempt_history": [],
            "terminal_state": None,
        }
    history = state.get("attempt_history")
    if not isinstance(history, list):
        history = []
    history.append(attempt)
    state["attempt_history"] = history
    state["task_id"] = task_id
    state["artwork_id"] = artwork_id
    state["last_attempt"] = attempt
    state["terminal_state"] = None
    states[task_id] = state
    _save_task_states(states)


def _record_terminal_state(task_id: str, terminal_state: str) -> None:
    states = _load_task_states()
    state = states.get(task_id)
    if not isinstance(state, dict):
        state = {"task_id": task_id, "attempt_history": []}
    state["task_id"] = task_id
    state["terminal_state"] = terminal_state
    states[task_id] = state
    _save_task_states(states)


def get_dev_task_state(task_id: str) -> dict[str, Any] | None:
    state = _load_task_states().get(task_id)
    return state if isinstance(state, dict) else None


def _load_priority_probe_state() -> dict[str, Any]:
    try:
        data = json.loads(_PRIORITY_STATE_PATH.read_text())
    except FileNotFoundError:
        return {"started": [], "completed": [], "tasks": {}}
    except json.JSONDecodeError:
        logger.warning("(dev) Could not parse priority probe state file; resetting")
        return {"started": [], "completed": [], "tasks": {}}

    if not isinstance(data, dict):
        return {"started": [], "completed": [], "tasks": {}}

    started = data.get("started")
    completed = data.get("completed")
    tasks = data.get("tasks")
    return {
        "started": started if isinstance(started, list) else [],
        "completed": completed if isinstance(completed, list) else [],
        "tasks": tasks if isinstance(tasks, dict) else {},
    }


def _save_priority_probe_state(state: dict[str, Any]) -> None:
    _PRIORITY_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _PRIORITY_STATE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, sort_keys=True))
    temp_path.replace(_PRIORITY_STATE_PATH)


def _record_priority_probe_started(task_id: str, label: str, priority: int) -> None:
    state = _load_priority_probe_state()
    started = state.get("started")
    if not isinstance(started, list):
        started = []
    started.append(label)
    state["started"] = started

    tasks = state.get("tasks")
    if not isinstance(tasks, dict):
        tasks = {}
    tasks[task_id] = {
        "task_id": task_id,
        "label": label,
        "priority": priority,
        "started_index": len(started) - 1,
        "status": "started",
    }
    state["tasks"] = tasks
    _save_priority_probe_state(state)


def _record_priority_probe_completed(task_id: str) -> None:
    state = _load_priority_probe_state()
    completed = state.get("completed")
    if not isinstance(completed, list):
        completed = []

    tasks = state.get("tasks")
    if not isinstance(tasks, dict):
        tasks = {}
    task_state = tasks.get(task_id)
    if isinstance(task_state, dict):
        label = task_state.get("label")
        if isinstance(label, str):
            completed.append(label)
        task_state["status"] = "completed"
        task_state["completed_index"] = len(completed) - 1
        tasks[task_id] = task_state

    state["completed"] = completed
    state["tasks"] = tasks
    _save_priority_probe_state(state)


def get_priority_probe_state() -> dict[str, Any]:
    return _load_priority_probe_state()

# This endpoint exists to confirm DLQ functionality.
# Use this for any kind of DLQ-related task and make any necessary changes in logic to prove/confirm hypotheses.
# This will be commented out once DLQ is stable, so in the meantime do whatever you want with this endpoint,
# just clean it up when done and don't commit things back in.
@shared_task(bind=True, name="dev_download_artworks_by_id", queue=MAIN_QUEUE_NAME)
def dev_download_artworks_by_id(self, request_dict: dict):
    request = DownloadArtworkByIdRequest(**request_dict)
    task_id = str(self.request.id)
    attempt = self.request.retries + 1
    max_attempts = _SIMULATED_MAX_RETRIES + 1
    _record_task_attempt(task_id, request.artwork_id, attempt)
    logger.error(f"(dev) Attempt {attempt}/{max_attempts} for artwork_id={request.artwork_id}")
    if attempt < max_attempts:
        raise self.retry(
            exc=ConnectionError("Simulated network failure"),
            countdown=_SIMULATED_RETRY_COUNTDOWN,
        )
    if _SUCCESS_SENTINEL_PATH.exists():
        _record_terminal_state(task_id, "succeeded")
        logger.error(f"(dev) Sentinel found at {_SUCCESS_SENTINEL_PATH}; succeeding on resumed run")
        return True
    _record_terminal_state(task_id, "failed")
    logger.error(f"(dev) Max retries exceeded for artwork_id={request.artwork_id}, raising terminal failure for broker DLQ")
    raise ConnectionError("Simulated terminal failure after retries")


@shared_task(bind=True, name="dev_priority_probe_task", queue=MAIN_QUEUE_NAME)
def dev_priority_probe_task(self, request_dict: dict):
    task_id = str(self.request.id)
    label = str(request_dict.get("label", task_id))
    priority = int(request_dict.get("priority", 2))
    sleep_ms = int(request_dict.get("sleep_ms", 1000))

    logger.error(f"(dev-priority) starting label={label} priority={priority} task_id={task_id}")
    _record_priority_probe_started(task_id, label, priority)
    time.sleep(max(sleep_ms, 0) / 1000)
    _record_priority_probe_completed(task_id)
    logger.error(f"(dev-priority) completed label={label} priority={priority} task_id={task_id}")
    return True
