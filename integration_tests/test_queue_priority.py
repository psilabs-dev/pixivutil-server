import random

import pytest


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
