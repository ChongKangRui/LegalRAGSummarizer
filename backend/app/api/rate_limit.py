import time

# key -> (count, window_start). key combines client + bucket so each
# route bucket gets its own independent counter per client.
requests: dict[str, tuple[int, float]] = {}

# prefix -> (bucket name, limit per window). Only prefixes listed here
# are rate-limited at all; anything else is skipped entirely.
ROUTE_LIMITS: dict[str, tuple[str, int]] = {
    "/summarize/stream": ("summarize/stream", 20),
    "/summarize/strategies": ("summarize/strategies", 100),
    "/compare": ("compare", 15),
    "/documents": ("documents", 300),
    "/inspector": ("inspector", 100),
    "/eval_dashboard": ("eval_dashboard", 300),
}

WINDOW_SECONDS = 60


def get_route_limit(path: str) -> tuple[str, int] | None:
    """Return (bucket, limit) for the first matching prefix, or None if this
    path isn't rate-limited at all."""
    for prefix, (bucket, limit) in ROUTE_LIMITS.items():
        if path.startswith(prefix):
            return bucket, limit
    return None


def check_rate_limiting(key: str, limit: int, window_seconds: int = WINDOW_SECONDS) -> bool:
    """Fixed-window limiter. `key` should already encode client + bucket
    (e.g. "1.2.3.4:summarize") so different routes don't share one counter.
    Returns True if allowed, False if this call should be blocked."""

    current = time.perf_counter()

    if key not in requests:
        requests[key] = (1, current)
        return True

    count, window_start = requests[key]

    if current - window_start > window_seconds:
        # window expired — start a fresh one
        requests[key] = (1, current)
        return True

    count += 1
    requests[key] = (count, window_start)

    if count > limit:
        print(f"[rate_limit] {key} blocked — {count} requests in current window (limit {limit})")
        return False

    return True