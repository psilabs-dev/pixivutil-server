import random

import pytest

from PixivServer.config.celery import (
    LEGACY_MAIN_QUEUE_NAME,
    MAIN_QUEUE_NAME,
    QUEUE_MAX_PRIORITY,
)


@pytest.mark.pixiv_api
def test_high_priority_tasks_are_consecutive_and_preceded_by_at_most_one_low(clean_env):
    """
    A later-published pair of high-priority tasks should jump ahead of queued low-priority tasks.

    In live-worker mode (concurrency=1), one low-priority task may already be running or reserved. We accept that,
    but the next queued work should prioritize highs. This test proves the operational guarantee that high-priority
    tasks are delayed by at most one low task and are not interleaved with queued lows.
    """
    sleep_ms = 1200
    low_labels = [f"L{i}" for i in range(1, 6)]
    high_labels = ["H1", "H2"]

    for label in low_labels:
        clean_env.api_json("POST", f"/api/dev/priority/{label}?priority=1&sleep_ms={sleep_ms}")
    for label in high_labels:
        clean_env.api_json("POST", f"/api/dev/priority/{label}?priority=3&sleep_ms={sleep_ms}")

    state = clean_env.wait_for_priority_probe_started_count(len(low_labels) + len(high_labels), timeout=120)
    started = state.get("started")
    assert isinstance(started, list)

    h1_index = started.index("H1")
    h2_index = started.index("H2")
    assert h2_index == h1_index + 1
    assert h1_index <= 1, f"Expected at most one low before highs, got order={started}"


@pytest.mark.pixiv_api
def test_three_tier_priority_orders_h_then_n_then_l_with_at_most_one_leading_low(clean_env):
    """
    In live-worker mode, at most one low task may execute before queued priorities take effect.

    After that, queued work should drain by priority order: high -> normal -> low. We randomize submission order
    (deterministically) to avoid accidentally testing only a sorted enqueue path.
    """
    sleep_ms = 1000
    rng = random.Random(20260224)

    labels = [f"L{i}" for i in range(1, 11)]
    labels += [f"N{i}" for i in range(1, 6)]
    labels += [f"H{i}" for i in range(1, 6)]
    rng.shuffle(labels)

    # Preserve the live-worker edge case we want to allow: one low can start before later priorities arrive.
    first_low_index = next(i for i, label in enumerate(labels) if label.startswith("L"))
    labels[0], labels[first_low_index] = labels[first_low_index], labels[0]

    for label in labels:
        priority = 1 if label.startswith("L") else 2 if label.startswith("N") else 3
        clean_env.api_json("POST", f"/api/dev/priority/{label}?priority={priority}&sleep_ms={sleep_ms}")

    state = clean_env.wait_for_priority_probe_started_count(len(labels), timeout=180)
    started = state.get("started")
    assert isinstance(started, list)
    assert len(started) == len(labels)

    leading_low_count = 1 if started and started[0].startswith("L") else 0
    body = started[leading_low_count:]

    h_block = [label for label in body if label.startswith("H")]
    n_block = [label for label in body if label.startswith("N")]
    l_block = [label for label in body if label.startswith("L")]

    expected = h_block + n_block + l_block
    assert body == expected, f"Expected H* then N* then L* after optional leading L, got order={started}"

    assert len(h_block) == 5, f"Expected 5 high tasks, got {len(h_block)} in order={started}"
    assert len(n_block) == 5, f"Expected 5 normal tasks, got {len(n_block)} in order={started}"
    assert len(l_block) == 10 - leading_low_count, (
        f"Expected remaining low tasks to be {10 - leading_low_count}, got {len(l_block)} in order={started}"
    )


@pytest.mark.pixiv_api
def test_priority_values_above_queue_max_are_not_a_higher_tier_than_max(clean_env):
    """
    RabbitMQ x-max-priority should clamp >max values so they behave like max priority, not a new tier.
    """
    over_limit = QUEUE_MAX_PRIORITY + 1
    clean_env.api_json("POST", "/api/dev/priority/L1?priority=1&sleep_ms=1800")
    clean_env.api_json("POST", "/api/dev/priority/H3?priority=3&sleep_ms=200")
    clean_env.api_json("POST", f"/api/dev/priority/HOver?priority={over_limit}&sleep_ms=200")
    clean_env.api_json("POST", "/api/dev/priority/N1?priority=2&sleep_ms=200")

    state = clean_env.wait_for_priority_probe_started_count(4, timeout=90)
    started = state.get("started")
    assert isinstance(started, list)
    assert started[0] == "L1"
    assert started[1:] == ["H3", "HOver", "N1"], f"Expected over-limit priority to be clamped to max-priority tier, got {started}"


@pytest.mark.pixiv_api
def test_worker_startup_deletes_legacy_main_queue(clean_env):
    """
    Hard-cutover behavior: worker init should purge/delete the legacy main queue if it exists.
    """
    clean_env.seed_legacy_main_queue_message()
    clean_env.wait_for_queue_count(LEGACY_MAIN_QUEUE_NAME, 1, timeout=30)

    clean_env.restart_worker()
    clean_env.wait_for_queue_absent(LEGACY_MAIN_QUEUE_NAME, timeout=60)


@pytest.mark.pixiv_api
def test_worker_restart_keeps_v1_queues_usable_when_they_already_exist(clean_env):
    """
    Restarting the worker with pre-existing v1 queues should remain healthy and continue processing tasks.
    """
    clean_env.api_json("POST", "/api/dev/priority/BeforeRestart?priority=2&sleep_ms=200")
    clean_env.wait_for_priority_probe_started_count(1, timeout=60)

    clean_env.restart_worker()

    clean_env.api_json("POST", "/api/dev/priority/AfterRestart?priority=2&sleep_ms=200")
    state = clean_env.wait_for_priority_probe_started_count(2, timeout=90)
    started = state.get("started")
    assert isinstance(started, list)
    assert started[:2] == ["BeforeRestart", "AfterRestart"]
    assert MAIN_QUEUE_NAME in clean_env.rabbitmq_queue_counts()
