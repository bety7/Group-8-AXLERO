from breaker import CircuitBreaker, State


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make(clock):
    return CircuitBreaker(threshold=0.02, window_seconds=10, min_events=100,
                          cooldown_seconds=15, probe_size=100, clock=clock)


def feed(b, good, bad):
    for _ in range(good):
        b.record(False)
    for _ in range(bad):
        b.record(True)


def test_stays_closed_at_or_below_threshold():
    b = make(FakeClock())
    feed(b, 99, 1)          # 1% errors
    assert b.state == State.CLOSED


def test_opens_above_threshold():
    b = make(FakeClock())
    feed(b, 95, 5)          # 5% errors
    assert b.state == State.OPEN
    assert not b.allow_main()


def test_does_not_trip_before_min_events():
    b = make(FakeClock())
    feed(b, 0, 50)          # 100% errors but only 50 events
    assert b.state == State.CLOSED


def test_goes_half_open_after_cooldown():
    clock = FakeClock()
    b = make(clock)
    feed(b, 95, 5)
    clock.t += 16
    b.record(False)
    assert b.state == State.HALF_OPEN


def test_closes_again_when_probe_is_healthy():
    clock = FakeClock()
    b = make(clock)
    feed(b, 95, 5)
    clock.t += 16
    feed(b, 100, 0)
    assert b.state == State.CLOSED


def test_reopens_when_probe_is_unhealthy():
    clock = FakeClock()
    b = make(clock)
    feed(b, 95, 5)
    clock.t += 16
    feed(b, 90, 10)
    assert b.state == State.OPEN


def test_on_change_callback_fires():
    seen = []
    b = CircuitBreaker(min_events=10, clock=FakeClock(),
                       on_change=lambda old, new, rate: seen.append((old, new)))
    feed(b, 5, 5)
    assert seen == [(State.CLOSED, State.OPEN)]