from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:  # pragma: no cover - optional dependency fallback
    class _NoopMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return self

        def observe(self, *args, **kwargs):
            return self

        def set(self, *args, **kwargs):
            return self

    Counter = Gauge = Histogram = _NoopMetric

rewarded_ads_prepare_total = Counter(
    "rewarded_ads_prepare_total",
    "Total number of /ads/prepare attempts",
    ["status"],
)
rewarded_ads_ssv_total = Counter(
    "rewarded_ads_ssv_total",
    "Total number of SSV callbacks processed",
    ["status"],
)
rewarded_ads_reward_amount = Counter(
    "rewarded_ads_reward_amount",
    "Total amount of coins granted via rewarded ads",
    ["network", "placement"],
)
rewarded_ads_duration_seconds = Histogram(
    "rewarded_ads_duration_seconds",
    "Duration reported for rewarded ad completions",
    buckets=(0, 10, 20, 25, 30, 40, 60, 90, 120, 180),
)
rewarded_ads_daily_cap = Gauge(
    "rewarded_ads_effective_daily_cap",
    "Effective DAILY_CAP_USER cap after adaptive adjustments",
)
rewarded_ads_failure_ratio = Gauge(
    "rewarded_ads_failure_ratio",
    "Rolling failure ratio for rewarded ads SSV validation",
)

__all__ = [
    "rewarded_ads_prepare_total",
    "rewarded_ads_ssv_total",
    "rewarded_ads_reward_amount",
    "rewarded_ads_duration_seconds",
    "rewarded_ads_daily_cap",
    "rewarded_ads_failure_ratio",
]
