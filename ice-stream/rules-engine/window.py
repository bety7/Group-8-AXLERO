import time
from collections import deque


class SlidingWindow:
    """Tracks how many of the events in the last N seconds were errors."""

    def __init__(self, window_seconds: float):
        self.window = window_seconds
        self.items = deque()
        self.errors = 0

    def _evict(self, now):
        cutoff = now - self.window
        while self.items and self.items[0][0] < cutoff:
            _, was_error = self.items.popleft()
            if was_error:
                self.errors -= 1

    def add(self, is_error: bool, now=None):
        now = time.monotonic() if now is None else now
        self.items.append((now, is_error))
        if is_error:
            self.errors += 1
        self._evict(now)

    def count(self, now=None) -> int:
        self._evict(time.monotonic() if now is None else now)
        return len(self.items)

    def error_rate(self, now=None) -> float:
        n = self.count(now)
        return (self.errors / n) if n else 0.0

    def reset(self):
        self.items.clear()
        self.errors = 0