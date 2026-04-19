import threading


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
    def __init__(self, metric_names):
        self._metric_names = list(metric_names)
        self._lock = threading.Lock()
        self._counters = {name: 0 for name in self._metric_names}

    def increment(self, name, value=1):
        if name not in self._counters:
            raise KeyError("Unknown metric: {}".format(name))

        with self._lock:
            self._counters[name] += value
            return self._counters[name]

    def snapshot(self):
        with self._lock:
            return dict(self._counters)

    def reset(self):
        with self._lock:
            self._counters = {name: 0 for name in self._metric_names}


registry = MetricsRegistry(METRIC_NAMES)


def increment(name, value=1):
    return registry.increment(name, value=value)


def snapshot():
    return registry.snapshot()


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
