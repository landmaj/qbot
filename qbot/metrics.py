from qbot.core import registry


def incr(stat, count=1, rate=1):
    if hasattr(registry, "statsd"):
        registry.statsd.incr(stat, count, rate)
        registry.statsd.gauge(f"{stat}", count, delta=True)
    else:
        pass
