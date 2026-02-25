import pytest

from PixivServer.config.celery import DEAD_LETTER_QUEUE_NAME, MAIN_QUEUE_NAME


def _attempt_history(state: dict) -> list[int]:
    history = state.get("attempt_history")
    if not isinstance(history, list):
        return []
    return [int(item) for item in history]


@pytest.mark.pixiv_api
def test_dlq_resume_replays_native_celery_message(clean_env):
    """
    Replaying a single native Celery DLQ message should republish it back to the main queue and remove it from DLQ.

    This validates the baseline operator workflow for manual recovery using the dev endpoint and DLQ resume endpoint.
    If this fails, administrators cannot reliably recover failed tasks from the dead letter queue.
    """
    task = clean_env.api_json("POST", "/api/dev/artwork/424242")
    task_id = task["task_id"]

    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 1, timeout=60)
    messages = clean_env.api_json("GET", "/api/queue/dead-letter/")
    assert len(messages) == 1
    message = messages[0]
    assert message["dead_letter_id"] == task_id
    assert message["task_name"] == "dev_download_artworks_by_id"
    assert message["payload"]["artwork_id"] == 424242

    clean_env.docker_exec(
        "pixivutil-worker",
        "sh",
        "-lc",
        "touch /tmp/pixivutil-dev-dlq-success.flag",
    )

    resumed = clean_env.api_json("POST", f"/api/queue/dead-letter/{task_id}/resume")
    assert resumed["requeued"] is True
    assert resumed["task_name"] == "dev_download_artworks_by_id"

    state = clean_env.wait_for_dev_task_terminal_state(task_id, "succeeded", timeout=90)
    assert _attempt_history(state) == [1, 2, 1, 2]
    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 0, timeout=60)
    assert clean_env.api_json("GET", "/api/queue/dead-letter/") == []


@pytest.mark.pixiv_api
def test_dlq_resume_resets_retry_counter_for_replayed_native_celery_message(clean_env):
    """
    Replaying a single native Celery message should reset retry state so the task starts a fresh retry lifecycle.

    DLQ replay is an operator recovery action, so the resumed task is expected to behave like a new enqueue rather than
    inheriting an exhausted retry budget from the failed message. If this fails, replayed transient failures may skip
    retry-attempt 1 and fail immediately or earlier than expected.
    """
    artwork_id = 333333
    task = clean_env.api_json("POST", f"/api/dev/artwork/{artwork_id}")
    task_id = task["task_id"]

    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 1, timeout=60)
    before_state = clean_env.wait_for_dev_task_terminal_state(task_id, "failed", timeout=60)
    assert before_state["artwork_id"] == artwork_id
    assert _attempt_history(before_state) == [1, 2]

    clean_env.docker_exec(
        "pixivutil-worker",
        "sh",
        "-lc",
        "touch /tmp/pixivutil-dev-dlq-success.flag",
    )

    resumed = clean_env.api_json("POST", f"/api/queue/dead-letter/{task_id}/resume")
    assert resumed["requeued"] is True
    assert resumed["task_name"] == "dev_download_artworks_by_id"

    after_state = clean_env.wait_for_dev_task_terminal_state(task_id, "succeeded", timeout=90)
    assert _attempt_history(after_state) == [1, 2, 1, 2]
    clean_env.wait_for_queue_count(MAIN_QUEUE_NAME, 0, timeout=90)
    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 0, timeout=90)


@pytest.mark.pixiv_api
def test_dlq_resume_all_replays_multiple_native_celery_messages(clean_env):
    """
    Bulk DLQ replay should requeue all recognized native Celery messages and empty the dead letter queue.

    This covers the "resume all" operational path used to recover multiple failed tasks at once. If this fails,
    operators may believe tasks were recovered while some messages remain stranded in DLQ or are not reprocessed.
    """
    task_a = clean_env.api_json("POST", "/api/dev/artwork/111111")
    task_b = clean_env.api_json("POST", "/api/dev/artwork/222222")

    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 2, timeout=90)
    messages = clean_env.api_json("GET", "/api/queue/dead-letter/")
    assert len(messages) == 2

    ids = {message["dead_letter_id"] for message in messages}
    assert ids == {task_a["task_id"], task_b["task_id"]}
    assert {message["payload"]["artwork_id"] for message in messages} == {111111, 222222}

    clean_env.docker_exec(
        "pixivutil-worker",
        "sh",
        "-lc",
        "touch /tmp/pixivutil-dev-dlq-success.flag",
    )

    resumed = clean_env.api_json("POST", "/api/queue/dead-letter/resume")
    assert resumed["requeued"] == 2

    clean_env.wait_for_dev_task_terminal_state(task_a["task_id"], "succeeded", timeout=90)
    clean_env.wait_for_dev_task_terminal_state(task_b["task_id"], "succeeded", timeout=90)
    clean_env.wait_for_queue_count(MAIN_QUEUE_NAME, 0, timeout=90)
    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 0, timeout=90)
    assert clean_env.api_json("GET", "/api/queue/dead-letter/") == []


@pytest.mark.pixiv_api
def test_dlq_resume_all_resets_retry_counter_for_replayed_native_celery_messages(clean_env):
    """
    Bulk replay should reset retry state for every replayed native Celery message, not only the single-item path.

    The single-message and bulk replay endpoints should have consistent replay semantics. If this fails, bulk recovery
    can silently requeue tasks with stale retry metadata, causing immediate re-failure and making DLQ recovery brittle.
    """
    artwork_ids = (444444, 555555)
    task_a = clean_env.api_json("POST", f"/api/dev/artwork/{artwork_ids[0]}")
    task_b = clean_env.api_json("POST", f"/api/dev/artwork/{artwork_ids[1]}")

    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 2, timeout=90)
    before_state_a = clean_env.wait_for_dev_task_terminal_state(task_a["task_id"], "failed", timeout=90)
    before_state_b = clean_env.wait_for_dev_task_terminal_state(task_b["task_id"], "failed", timeout=90)
    assert _attempt_history(before_state_a) == [1, 2]
    assert _attempt_history(before_state_b) == [1, 2]

    clean_env.docker_exec(
        "pixivutil-worker",
        "sh",
        "-lc",
        "touch /tmp/pixivutil-dev-dlq-success.flag",
    )

    resumed = clean_env.api_json("POST", "/api/queue/dead-letter/resume")
    assert resumed["requeued"] == 2

    after_state_a = clean_env.wait_for_dev_task_terminal_state(task_a["task_id"], "succeeded", timeout=90)
    after_state_b = clean_env.wait_for_dev_task_terminal_state(task_b["task_id"], "succeeded", timeout=90)
    assert _attempt_history(after_state_a) == [1, 2, 1, 2]
    assert _attempt_history(after_state_b) == [1, 2, 1, 2]
    clean_env.wait_for_queue_count(MAIN_QUEUE_NAME, 0, timeout=90)
    clean_env.wait_for_queue_count(DEAD_LETTER_QUEUE_NAME, 0, timeout=90)
