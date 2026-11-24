import time
from enum import Enum
from window import SlidingWindow


class State(str, Enum):
    CLOSED = "CLOSED"        # healthy: good data goes to the main table
    OPEN = "OPEN"            # tripped: everything goes to the dead letter queue
    HALF_OPEN = "HALF_OPEN"  # testing: sample some events before resuming


class CircuitBreaker:
    def __init__(self, threshold=0.02, window_seconds=10, min_events=100,
                 cooldown_seconds=15, probe_size=100, clock=time.monotonic,
                 on_change=None):
        self.threshold = threshold
        self.min_events = min_events
        self.cooldown = cooldown_seconds
        self.probe_size = probe_size
        self.clock = clock
        self.on_change = on_change
        self.window = SlidingWindow(window_seconds)
        self.state = State.CLOSED
        self.opened_at = None
        self.probe_total = 0
        self.probe_errors = 0
        self.last_rate = 0.0

    def _to(self, new_state, now):
        old = self.state
        self.state = new_state
        if new_state == State.OPEN:
            self.opened_at = now
        elif new_state == State.HALF_OPEN:
            self.probe_total = 0
            self.probe_errors = 0
        elif new_state == State.CLOSED:
            self.window.reset()
        if self.on_change:
            self.on_change(old, new_state, self.last_rate)

    def record(self, is_error: bool):
        """Feed in the result of one event. May change the breaker state."""
        now = self.clock()

        if self.state == State.OPEN and now - self.opened_at >= self.cooldown:
            self._to(State.HALF_OPEN, now)

        if self.state == State.CLOSED:
            self.window.add(is_error, now)
            self.last_rate = self.window.error_rate(now)
            if self.window.count(now) >= self.min_events and self.last_rate > self.threshold:
                self._to(State.OPEN, now)
        elif self.state == State.HALF_OPEN:
            self.probe_total += 1
            self.probe_errors += int(is_error)
            if self.probe_total >= self.probe_size:
                self.last_rate = self.probe_errors / self.probe_total
                self._to(State.CLOSED if self.last_rate <= self.threshold else State.OPEN, now)

    def allow_main(self) -> bool:
        return self.state == State.CLOSED