import threading
import time
from datetime import datetime
from datetime import timezone


REQUESTS_TOTAL = "requests_total"
PARSE_SUCCESS_TOTAL = "parse_success_total"
PARSE_ERROR_TOTAL = "parse_error_total"
DEGRADED_RESULT_TOTAL = "degraded_result_total"
FORCE_REFRESH_TOTAL = "force_refresh_total"

CACHE_HIT_TOTAL = "cache_hit_total"
CACHE_MISS_TOTAL = "cache_miss_total"

DISCOGS_SUCCESS_TOTAL = "discogs_success_total"
DISCOGS_NOT_FOUND_TOTAL = "discogs_not_found_total"
DISCOGS_FAILURE_TOTAL = "discogs_failure_total"

MUSICBRAINZ_SUCCESS_TOTAL = "musicbrainz_success_total"
MUSICBRAINZ_NOT_FOUND_TOTAL = "musicbrainz_not_found_total"
MUSICBRAINZ_FAILURE_TOTAL = "musicbrainz_failure_total"

METRIC_NAMES = [
    REQUESTS_TOTAL,
    PARSE_SUCCESS_TOTAL,
    PARSE_ERROR_TOTAL,
    DEGRADED_RESULT_TOTAL,
    FORCE_REFRESH_TOTAL,
    CACHE_HIT_TOTAL,
    CACHE_MISS_TOTAL,
    DISCOGS_SUCCESS_TOTAL,
    DISCOGS_NOT_FOUND_TOTAL,
    DISCOGS_FAILURE_TOTAL,
    MUSICBRAINZ_SUCCESS_TOTAL,
    MUSICBRAINZ_NOT_FOUND_TOTAL,
    MUSICBRAINZ_FAILURE_TOTAL,
]


class MetricsRegistry:
    def __init__(self, metric_names, time_provider=None, monotonic_provider=None):
        self._metric_names = list(metric_names)
        self._lock = threading.Lock()
        self._time_provider = time_provider or time.time
        self._monotonic_provider = monotonic_provider or time.monotonic
        self._started_at_epoch = self._time_provider()
        self._started_at_monotonic = self._monotonic_provider()
        self._counters = {}
        self.reset()

    def increment(self, name, value=1):
        if name not in self._counters:
            raise KeyError("Unknown metric: {}".format(name))

        with self._lock:
            self._counters[name] += value
            return self._counters[name]

    def snapshot(self):
        with self._lock:
            return dict(self._counters)

    def process_metadata(self):
        with self._lock:
            generated_at_epoch = self._time_provider()
            uptime_seconds = int(
                max(0.0, self._monotonic_provider() - self._started_at_monotonic)
            )

        return {
            "started_at": _format_utc_timestamp(self._started_at_epoch),
            "generated_at": _format_utc_timestamp(generated_at_epoch),
            "uptime_seconds": uptime_seconds,
        }

    def snapshot_with_metadata(self):
        with self._lock:
            counters = dict(self._counters)

        return {
            **self.process_metadata(),
            "summary": _build_summary(counters),
            "counters": counters,
            "metrics": dict(counters),
        }

    def reset(self):
        with self._lock:
            self._counters = {name: 0 for name in self._metric_names}


registry = MetricsRegistry(METRIC_NAMES)


def increment(name, value=1):
    return registry.increment(name, value=value)


def snapshot():
    return registry.snapshot()


def snapshot_with_metadata():
    return registry.snapshot_with_metadata()


def get_process_metadata():
    return registry.process_metadata()


def reset():
    registry.reset()


def increment_requests_total():
    increment(REQUESTS_TOTAL)


def increment_parse_success_total():
    increment(PARSE_SUCCESS_TOTAL)


def increment_parse_error_total():
    increment(PARSE_ERROR_TOTAL)


def increment_degraded_result_total():
    increment(DEGRADED_RESULT_TOTAL)


def increment_force_refresh_total():
    increment(FORCE_REFRESH_TOTAL)


def increment_cache_hit_total():
    increment(CACHE_HIT_TOTAL)


def increment_cache_miss_total():
    increment(CACHE_MISS_TOTAL)


def increment_discogs_success_total():
    increment(DISCOGS_SUCCESS_TOTAL)


def increment_discogs_not_found_total():
    increment(DISCOGS_NOT_FOUND_TOTAL)


def increment_discogs_failure_total():
    increment(DISCOGS_FAILURE_TOTAL)


def increment_musicbrainz_success_total():
    increment(MUSICBRAINZ_SUCCESS_TOTAL)


def increment_musicbrainz_not_found_total():
    increment(MUSICBRAINZ_NOT_FOUND_TOTAL)


def increment_musicbrainz_failure_total():
    increment(MUSICBRAINZ_FAILURE_TOTAL)


def record_discogs_outcome(outcome):
    if outcome == "success":
        increment_discogs_success_total()
    elif outcome == "not_found":
        increment_discogs_not_found_total()
    elif outcome == "failure":
        increment_discogs_failure_total()


def record_musicbrainz_outcome(outcome):
    if outcome == "success":
        increment_musicbrainz_success_total()
    elif outcome == "not_found":
        increment_musicbrainz_not_found_total()
    elif outcome == "failure":
        increment_musicbrainz_failure_total()


def _format_utc_timestamp(epoch_seconds):
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_ratio(numerator, denominator):
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _build_summary(counters):
    parse_success_total = counters[PARSE_SUCCESS_TOTAL]
    parse_error_total = counters[PARSE_ERROR_TOTAL]
    completed_requests_total = parse_success_total + parse_error_total
    cache_lookups_total = counters[CACHE_HIT_TOTAL] + counters[CACHE_MISS_TOTAL]

    return {
        "totals": {
            "completed_requests_total": completed_requests_total,
            "source_failure_total": (
                counters[DISCOGS_FAILURE_TOTAL]
                + counters[MUSICBRAINZ_FAILURE_TOTAL]
            ),
        },
        "ratios": {
            "cache_hit_ratio": _safe_ratio(
                counters[CACHE_HIT_TOTAL],
                cache_lookups_total,
            ),
            "degraded_result_ratio": _safe_ratio(
                counters[DEGRADED_RESULT_TOTAL],
                parse_success_total,
            ),
        },
    }
