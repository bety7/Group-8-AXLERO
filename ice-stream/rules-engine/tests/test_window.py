from window import SlidingWindow


def test_rate_is_zero_when_empty():
    assert SlidingWindow(10).error_rate(now=0) == 0.0


def test_rate_counts_errors():
    w = SlidingWindow(10)
    for i in range(10):
        w.add(i < 2, now=float(i) * 0.1)   # 2 errors out of 10
    assert w.error_rate(now=1.0) == 0.2


def test_old_events_drop_out_of_the_window():
    w = SlidingWindow(10)
    w.add(True, now=0.0)
    w.add(False, now=5.0)
    assert w.count(now=5.0) == 2
    assert w.count(now=12.0) == 1          # the error at t=0 expired
    assert w.error_rate(now=12.0) == 0.0


def test_reset_clears_everything():
    w = SlidingWindow(10)
    w.add(True, now=0.0)
    w.reset()
    assert w.count(now=0.0) == 0