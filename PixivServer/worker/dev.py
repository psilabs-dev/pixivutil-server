import json
import logging
from pathlib import Path
from typing import Any

from celery import shared_task

from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest

logger = logging.getLogger(__name__)

_SIMULATED_RETRY_COUNTDOWN = 1
_SIMULATED_MAX_RETRIES = 1
_SUCCESS_SENTINEL_PATH = Path("/tmp/pixivutil-dev-dlq-success.flag")
_TASK_STATE_PATH = Path("/workdir/.pixivUtil2/dev-dlq-task-state.json")


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

# This endpoint exists to confirm DLQ functionality.
# Use this for any kind of DLQ-related task and make any necessary changes in logic to prove/confirm hypotheses.
# This will be commented out once DLQ is stable, so in the meantime do whatever you want with this endpoint,
# just clean it up when done and don't commit things back in.
@shared_task(bind=True, name="dev_download_artworks_by_id", queue='pixivutil-queue')
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
