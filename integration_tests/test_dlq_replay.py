def test_dlq_resume_replays_native_celery_message(clean_env):
    task = clean_env.api_json("POST", "/api/dev/artwork/424242")
    task_id = task["task_id"]

    clean_env.wait_for_queue_count("pixivutil-dead-letter", 1, timeout=60)
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

    clean_env.wait_worker_log_contains("Sentinel found at /tmp/pixivutil-dev-dlq-success.flag; succeeding on resumed run")
    clean_env.wait_for_queue_count("pixivutil-dead-letter", 0, timeout=60)
    assert clean_env.api_json("GET", "/api/queue/dead-letter/") == []


def test_dlq_resume_all_replays_multiple_native_celery_messages(clean_env):
    task_a = clean_env.api_json("POST", "/api/dev/artwork/111111")
    task_b = clean_env.api_json("POST", "/api/dev/artwork/222222")

    clean_env.wait_for_queue_count("pixivutil-dead-letter", 2, timeout=90)
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

    clean_env.wait_worker_log_contains("Sentinel found at /tmp/pixivutil-dev-dlq-success.flag; succeeding on resumed run")
    clean_env.wait_for_queue_count("pixivutil-queue", 0, timeout=90)
    clean_env.wait_for_queue_count("pixivutil-dead-letter", 0, timeout=90)
    assert clean_env.api_json("GET", "/api/queue/dead-letter/") == []
