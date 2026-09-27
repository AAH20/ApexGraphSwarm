"""Configured, read-only Prometheus telemetry for vLLM.

This module only fetches the URL held in VLLM_METRICS_URL. It never accepts a
URL from a request payload, follows redirects, or treats missing measurements
as zero. Public serializers omit endpoint URLs and metric labels.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
import math
import os
import re
import time
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


MAX_BODY_BYTES = 2_000_000
MAX_METRIC_LINES = 100_000
MAX_LABELS_PER_SERIES = 64
MAX_LABEL_VALUE_CHARS = 4_096
MAX_ENDPOINT_CHARS = 2_048
MAX_TOKEN_CHARS = 4_096
MAX_WINDOW_SECONDS = 31_536_000.0
DEFAULT_TIMEOUT_SECONDS = 3.0
_METRIC_NAME = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
_SAMPLE_LINE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*)\})?\s+(\S+)(?:\s+(\S+))?\s*$")
_HIST_SUFFIXES = ("_bucket", "_sum", "_count")

# These names and types are documented in current vLLM Production Metrics and
# v1 Metrics docs. The aliases cover the documented v0/v1 naming transition.
GAUGE_FAMILIES = {
    "requests_running": ("vllm:num_requests_running",),
    "requests_waiting": ("vllm:num_requests_waiting",),
    "requests_waiting_by_reason": ("vllm:num_requests_waiting_by_reason",),
    "requests_swapped": ("vllm:num_requests_swapped",),
    "kv_cache_usage": ("vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"),
}
COUNTER_FAMILIES = {
    "prefix_cache_queries": ("vllm:prefix_cache_queries",),
    "prefix_cache_hits": ("vllm:prefix_cache_hits",),
    "external_prefix_cache_queries": ("vllm:external_prefix_cache_queries",),
    "external_prefix_cache_hits": ("vllm:external_prefix_cache_hits",),
    "prompt_tokens": ("vllm:prompt_tokens_total", "vllm:prompt_tokens"),
    "generation_tokens": ("vllm:generation_tokens_total", "vllm:generation_tokens"),
    "preemptions": ("vllm:num_preemptions_total", "vllm:num_preemptions"),
    "requests_finished": ("vllm:request_success_total", "vllm:request_success"),
}
HISTOGRAM_FAMILIES = {
    "ttft": "vllm:time_to_first_token_seconds",
    "request_latency": "vllm:e2e_request_latency_seconds",
    "queue_latency": "vllm:request_queue_time_seconds",
    "inter_token_latency": "vllm:inter_token_latency_seconds",
    "request_tpot": "vllm:request_time_per_output_token_seconds",
}


class TelemetryError(ValueError):
    """Malformed exposition, unsafe endpoint, or out-of-bound request."""


@dataclass(frozen=True)
class MetricSeries:
    name: str
    labels: tuple[tuple[str, str], ...]
    value: float
    metric_type: str | None

    @property
    def identity(self) -> tuple[str, tuple[tuple[str, str], ...]]:
        return self.name, self.labels

@dataclass(frozen=True)
class TelemetrySnapshot:
    series: tuple[MetricSeries, ...]
    metric_types: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PublicMetric:
    family: str
    metric: str
    series_id: str
    status: str
    value: float | None


@dataclass(frozen=True)
class DerivedMetric:
    family: str
    series_id: str
    status: str
    value: float | None


@dataclass(frozen=True)
class CounterWindow:
    family: str
    metric: str
    series_id: str
    status: str
    delta: float | None
    rate_per_second: float | None


@dataclass(frozen=True)
class HistogramWindow:
    family: str
    metric: str
    series_id: str
    status: str
    observations: float | None
    mean_seconds: float | None
    p50_upper_bound_seconds: float | None
    p95_upper_bound_seconds: float | None
    quantile_bound_explanation: str


@dataclass(frozen=True)
class TelemetryComparison:
    status: str
    window_seconds: float
    gauges: tuple[PublicMetric, ...]
    counters: tuple[CounterWindow, ...]
    histograms: tuple[HistogramWindow, ...]
    derived: tuple[DerivedMetric, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "window_seconds": self.window_seconds,
            "gauges": [_record_dict(row) for row in self.gauges],
            "counters": [_record_dict(row) for row in self.counters],
            "histograms": [_record_dict(row) for row in self.histograms],
            "derived": [_record_dict(row) for row in self.derived],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class CollectionResult:
    status: str
    endpoint_configured: bool
    fetched_at_unix_seconds: float | None
    snapshot: TelemetrySnapshot | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        """Serialize without the configured URL, token, or private labels."""
        public_series = []
        if self.snapshot is not None:
            family_indexes: dict[str, int] = {}
            for item in self.snapshot.series:
                if not _is_supported_raw_name(item.name):
                    continue
                family = _family_for_metric(item.name)
                if family is not None:
                    series_id = str(family_indexes.get(family, 0))
                    family_indexes[family] = int(series_id) + 1
                    row = {"family": family, "metric": item.name,
                           "series_id": series_id,
                           "status": "sample" if math.isfinite(item.value) else "invalid_sample",
                           "value": item.value if math.isfinite(item.value) else None}
                    if item.name.endswith("_bucket"):
                        # `le` is a public histogram schema label, not a model
                        # or tenant identity, and is needed to interpret bucket rows.
                        row["bucket_upper_bound"] = dict(item.labels).get("le")
                    public_series.append(row)
        return {
            "status": self.status,
            "endpoint_configured": self.endpoint_configured,
            "fetched_at_unix_seconds": self.fetched_at_unix_seconds,
            "metrics": public_series,
            "error": self.error,
            "limits": ["endpoint and labels are redacted", "only configured endpoint is queried"],
        }


def _record_dict(record: object) -> dict[str, object]:
    from dataclasses import asdict
    return asdict(record)


def _unescape_label(raw: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(raw):
        char = raw[i]
        if char != "\\":
            result.append(char)
            i += 1
            continue
        i += 1
        if i >= len(raw):
            raise TelemetryError("invalid escaped label value")
        escape = raw[i]
        if escape == "n":
            result.append("\n")
        elif escape in ('\\', '"'):
            result.append(escape)
        else:
            raise TelemetryError("invalid escaped label value")
        i += 1
    decoded = "".join(result)
    if len(decoded) > MAX_LABEL_VALUE_CHARS:
        raise TelemetryError("label value exceeds the size limit")
    return decoded


def _parse_labels(raw: str | None) -> tuple[tuple[str, str], ...]:
    if raw is None or raw == "":
        return ()
    labels: list[tuple[str, str]] = []
    index = 0
    while index < len(raw):
        match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\"", raw[index:])
        if not match:
            raise TelemetryError("invalid Prometheus label syntax")
        name = match.group(1)
        index += match.end()
        value_chars: list[str] = []
        while index < len(raw):
            char = raw[index]
            index += 1
            if char == '"':
                break
            if char == "\\":
                if index >= len(raw):
                    raise TelemetryError("invalid escaped label value")
                value_chars.extend(("\\", raw[index]))
                index += 1
            else:
                value_chars.append(char)
        else:
            raise TelemetryError("unterminated Prometheus label")
        labels.append((name, _unescape_label("".join(value_chars))))
        if len(labels) > MAX_LABELS_PER_SERIES:
            raise TelemetryError("series exceeds the label count limit")
        if index == len(raw):
            break
        if raw[index] != ",":
            raise TelemetryError("invalid Prometheus label separator")
        index += 1
        if index == len(raw):
            raise TelemetryError("trailing Prometheus label separator")
    if len({name for name, _ in labels}) != len(labels):
        raise TelemetryError("duplicate Prometheus label name")
    return tuple(sorted(labels))


def parse_prometheus(text: str) -> TelemetrySnapshot:
    """Parse bounded Prometheus text exposition, preserving exact series keys."""
    if not isinstance(text, str):
        raise TelemetryError("metrics body must be text")
    try:
        body_size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise TelemetryError("metrics body is not valid UTF-8 text") from None
    if body_size > MAX_BODY_BYTES:
        raise TelemetryError("metrics body exceeds the byte limit")
    lines = text.splitlines()
    if len(lines) > MAX_METRIC_LINES:
        raise TelemetryError("metrics body exceeds the line limit")
    types: dict[str, str] = {}
    series: dict[tuple[str, tuple[tuple[str, str], ...]], MetricSeries] = {}
    sampled_metrics: set[str] = set()
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped == "# EOF":
            continue
        if stripped.startswith("#"):
            if stripped.startswith("# TYPE "):
                parts = stripped.split()
                if len(parts) != 4 or not _METRIC_NAME.fullmatch(parts[2]) or parts[3] not in ("counter", "gauge", "histogram", "summary", "untyped"):
                    raise TelemetryError("invalid Prometheus TYPE declaration on line %d" % line_number)
                previous = types.get(parts[2])
                if previous is not None:
                    raise TelemetryError("duplicate Prometheus TYPE declaration")
                if parts[2] in sampled_metrics:
                    raise TelemetryError("Prometheus TYPE declaration must precede samples")
                types[parts[2]] = parts[3]
            continue
        match = _SAMPLE_LINE.fullmatch(stripped)
        if not match:
            raise TelemetryError("invalid Prometheus sample on line %d" % line_number)
        name, label_text, raw_value, timestamp = match.groups()
        if not _METRIC_NAME.fullmatch(name):
            raise TelemetryError("invalid Prometheus metric name")
        try:
            value = float(raw_value)
            if timestamp is not None:
                timestamp_value = int(timestamp, 10)
        except (ValueError, OverflowError):
            raise TelemetryError("invalid Prometheus numeric value on line %d" % line_number) from None
        if timestamp is not None and not -(2**63) <= timestamp_value <= 2**63 - 1:
            raise TelemetryError("Prometheus timestamp is outside signed 64-bit range")
        labels = _parse_labels(label_text)
        typed_name = name
        for suffix in _HIST_SUFFIXES:
            if name.endswith(suffix):
                typed_name = name[:-len(suffix)]
                break
        sampled_metrics.add(typed_name)
        metric_type = types.get(name)
        if metric_type is None:
            for suffix in _HIST_SUFFIXES:
                if name.endswith(suffix):
                    metric_type = types.get(name[:-len(suffix)])
                    break
        item = MetricSeries(name, labels, value, metric_type)
        if item.identity in series:
            raise TelemetryError("duplicate Prometheus series")
        series[item.identity] = item
    return TelemetrySnapshot(tuple(sorted(series.values(), key=lambda item: (item.name, item.labels))),
                             tuple(sorted(types.items())))


def _family_for_metric(metric: str) -> str | None:
    for family, names in GAUGE_FAMILIES.items():
        if metric in names:
            return family
    for family, names in COUNTER_FAMILIES.items():
        if metric in names:
            return family
    for family, name in HISTOGRAM_FAMILIES.items():
        if metric in (name, name + "_bucket", name + "_sum", name + "_count"):
            return family
    return None


def _is_supported_raw_name(metric: str) -> bool:
    return _family_for_metric(metric) is not None


def _histogram_groups(snapshot: TelemetrySnapshot, base_name: str) -> tuple[dict[tuple[tuple[str, str], ...], dict[str, object]], list[tuple[tuple[tuple[str, str], ...], str]]]:
    groups: dict[tuple[tuple[str, str], ...], dict[str, object]] = {}
    invalid: list[tuple[tuple[tuple[str, str], ...], str]] = []
    for item in snapshot.series:
        if not (item.name == base_name + "_bucket" or item.name in (base_name + "_sum", base_name + "_count")):
            continue
        labels = dict(item.labels)
        if item.name == base_name + "_bucket":
            raw_le = labels.pop("le", None)
            if raw_le is None:
                invalid.append((item.labels, "invalid_histogram"))
                continue
            if raw_le in ("+Inf", "Inf", "Infinity"):
                bound = math.inf
            else:
                try:
                    bound = float(raw_le)
                except ValueError:
                    invalid.append((tuple(sorted(labels.items())), "invalid_histogram"))
                    continue
                if not math.isfinite(bound):
                    invalid.append((tuple(sorted(labels.items())), "invalid_histogram"))
                    continue
                if bound < 0:
                    invalid.append((tuple(sorted(labels.items())), "invalid_histogram"))
                    continue
            key = tuple(sorted(labels.items()))
            group = groups.setdefault(key, {"buckets": {}})
            buckets = group["buckets"]
            assert isinstance(buckets, dict)
            if bound in buckets:
                invalid.append((key, "invalid_histogram"))
            buckets[bound] = item.value
        else:
            key = item.labels
            group = groups.setdefault(key, {"buckets": {}})
            field = "sum" if item.name == base_name + "_sum" else "count"
            if field in group:
                invalid.append((key, "invalid_histogram"))
            group[field] = item.value
    valid: dict[tuple[tuple[str, str], ...], dict[str, object]] = {}
    for labels, group in groups.items():
        buckets = group.get("buckets")
        if not isinstance(buckets, dict) or not buckets or math.inf not in buckets or "sum" not in group or "count" not in group:
            invalid.append((labels, "invalid_histogram"))
            continue
        ordered = sorted(buckets.items(), key=lambda row: row[0])
        counts = [value for _, value in ordered]
        if any(not math.isfinite(value) or value < 0 or not value.is_integer() for value in counts) or any(a > b for a, b in zip(counts, counts[1:])):
            invalid.append((labels, "invalid_histogram"))
            continue
        if not math.isfinite(float(group["sum"])) or float(group["sum"]) < 0 or not math.isfinite(float(group["count"])) or float(group["count"]) < 0:
            invalid.append((labels, "invalid_histogram"))
            continue
        if (not math.isfinite(float(group["count"])) or not float(group["count"]).is_integer()
                or not math.isclose(float(group["count"]), float(buckets[math.inf]), rel_tol=0.0, abs_tol=1e-9)):
            invalid.append((labels, "invalid_histogram"))
            continue
        valid[labels] = {"buckets": tuple(ordered), "sum": float(group["sum"]), "count": float(group["count"])}
    return valid, invalid


def _quantile_upper(buckets: tuple[tuple[float, float], ...], quantile: float, count: float) -> float | None:
    if count <= 0:
        return None
    rank = max(1.0, math.ceil(quantile * count))
    for upper, cumulative in buckets:
        if cumulative >= rank:
            return upper if math.isfinite(upper) else None
    return None


def compare_snapshots(previous: TelemetrySnapshot, current: TelemetrySnapshot, *, window_seconds: float) -> TelemetryComparison:
    """Compare two scrapes; reset, missing, or new series never become zero."""
    window = _finite_number(window_seconds, "window_seconds", low=0.000001, high=MAX_WINDOW_SECONDS)
    if not isinstance(previous, TelemetrySnapshot) or not isinstance(current, TelemetrySnapshot):
        raise TelemetryError("previous and current must be TelemetrySnapshot values")
    prev = {item.identity: item for item in previous.series}
    curr = {item.identity: item for item in current.series}
    gauges: list[PublicMetric] = []
    counters: list[CounterWindow] = []
    histograms: list[HistogramWindow] = []
    derived: list[DerivedMetric] = []
    metric_statuses: list[str] = []
    for family, names in GAUGE_FAMILIES.items():
        current_names = [name for name in names if any(item.name == name for item in current.series)]
        if not current_names:
            continue
        name = current_names[0]
        declared_type = dict(current.metric_types).get(name)
        gauge_rows = [item for item in current.series if item.name == name]
        for series_index, item in enumerate(gauge_rows):
            valid = math.isfinite(item.value) and item.value >= 0 and declared_type in (None, "gauge")
            if family == "kv_cache_usage":
                valid = valid and item.value <= 1
            gauges.append(PublicMetric(family, item.name, str(series_index),
                                       "matched" if valid else "invalid_gauge", item.value if valid else None))
            if not valid:
                metric_statuses.append("invalid_gauge")
    for family, names in COUNTER_FAMILIES.items():
        current_names = [name for name in names if any(item.name == name for item in current.series)]
        previous_names = [name for name in names if any(item.name == name for item in previous.series)]
        active_names = sorted(set(current_names) | set(previous_names))
        if not active_names:
            continue
        for name in active_names:
            current_rows = {item.identity[1]: item for item in current.series if item.name == name}
            previous_rows = {item.identity[1]: item for item in previous.series if item.name == name}
            wrong_type = (dict(current.metric_types).get(name) not in (None, "counter")
                          or dict(previous.metric_types).get(name) not in (None, "counter"))
            label_keys = sorted(set(current_rows) | set(previous_rows))
            for series_index, labels in enumerate(label_keys):
                before = previous_rows.get(labels)
                after = current_rows.get(labels)
                status = "matched"
                delta = rate = None
                if wrong_type:
                    status = "invalid_type"
                elif before is None or after is None:
                    status = "unmatched_series"
                elif before.value < 0 or after.value < 0:
                    status = "invalid_counter"
                elif after.value < before.value:
                    status = "counter_reset"
                else:
                    delta = after.value - before.value
                    rate = delta / window
                    if not math.isfinite(rate):
                        status, delta, rate = "invalid_rate", None, None
                metric_statuses.append(status)
                counters.append(CounterWindow(family, name, str(series_index), status, delta, rate))
    for prefix, hit_family, query_family in (
        ("prefix_cache_hit_ratio", "prefix_cache_hits", "prefix_cache_queries"),
        ("external_prefix_cache_hit_ratio", "external_prefix_cache_hits", "external_prefix_cache_queries"),
    ):
        hit_names = COUNTER_FAMILIES[hit_family]
        query_names = COUNTER_FAMILIES[query_family]
        current_hit_name = next((name for name in hit_names if any(s.name == name for s in current.series)), None)
        previous_hit_name = next((name for name in hit_names if any(s.name == name for s in previous.series)), None)
        current_query_name = next((name for name in query_names if any(s.name == name for s in current.series)), None)
        previous_query_name = next((name for name in query_names if any(s.name == name for s in previous.series)), None)
        names = (current_hit_name, previous_hit_name, current_query_name, previous_query_name)
        if not any(names):
            continue
        relevant_names = {name for name in names if name is not None}
        wrong_type = any(dict(current.metric_types).get(name) not in (None, "counter")
                         or dict(previous.metric_types).get(name) not in (None, "counter")
                         for name in relevant_names)
        if (current_hit_name != previous_hit_name or current_query_name != previous_query_name
                or wrong_type or current_hit_name is None or current_query_name is None):
            # A metric rename or declared-type change makes this pair incomparable.
            status = "invalid_type" if wrong_type else "unmatched_series"
            all_labels = sorted({item.identity[1] for item in current.series + previous.series
                                 if item.name in hit_names + query_names})
            for series_index, labels in enumerate(all_labels):
                derived.append(DerivedMetric(prefix, str(series_index), status, None))
                metric_statuses.append(status)
            continue
        hit_current = {s.identity[1]: s.value for s in current.series if s.name == current_hit_name}
        hit_previous = {s.identity[1]: s.value for s in previous.series if s.name == previous_hit_name}
        query_current = {s.identity[1]: s.value for s in current.series if s.name == current_query_name}
        query_previous = {s.identity[1]: s.value for s in previous.series if s.name == previous_query_name}
        all_labels = sorted(set(hit_current) | set(hit_previous) | set(query_current) | set(query_previous))
        for series_index, labels in enumerate(all_labels):
            values = (hit_current.get(labels), hit_previous.get(labels), query_current.get(labels), query_previous.get(labels))
            if any(value is None for value in values):
                status, ratio = "unmatched_series", None
            else:
                hit_now, hit_before, query_now, query_before = values
                assert hit_now is not None and hit_before is not None and query_now is not None and query_before is not None
                dh, dq = hit_now - hit_before, query_now - query_before
                if min(hit_now, hit_before, query_now, query_before) < 0:
                    status, ratio = "invalid_counter", None
                elif dh < 0 or dq < 0:
                    status, ratio = "counter_reset", None
                elif dq == 0:
                    status, ratio = "no_queries", None
                elif dh > dq:
                    status, ratio = "invalid_ratio", None
                else:
                    status, ratio = "matched", dh / dq
            metric_statuses.append(status)
            derived.append(DerivedMetric(prefix, str(series_index), status, ratio))
    for family, base_name in HISTOGRAM_FAMILIES.items():
        current_groups, current_invalid = _histogram_groups(current, base_name)
        previous_groups, previous_invalid = _histogram_groups(previous, base_name)
        wrong_type = (dict(current.metric_types).get(base_name) not in (None, "histogram")
                      or dict(previous.metric_types).get(base_name) not in (None, "histogram"))
        all_keys = sorted(set(current_groups) | set(previous_groups) | {key for key, _ in current_invalid} | {key for key, _ in previous_invalid})
        if not all_keys:
            continue
        invalid_current = dict(current_invalid)
        invalid_previous = dict(previous_invalid)
        for series_index, labels in enumerate(all_keys):
            before = previous_groups.get(labels)
            after = current_groups.get(labels)
            status = "matched"
            observations = mean = p50 = p95 = None
            if wrong_type or invalid_current.get(labels) or invalid_previous.get(labels):
                status = "invalid_histogram"
            elif before is None or after is None:
                status = "unmatched_series"
            else:
                before_buckets = dict(before["buckets"])
                after_buckets = dict(after["buckets"])
                if set(before_buckets) != set(after_buckets):
                    status = "unmatched_buckets"
                else:
                    bucket_deltas = tuple((bound, after_buckets[bound] - before_buckets[bound]) for bound in sorted(after_buckets))
                    sum_delta = float(after["sum"]) - float(before["sum"])
                    count_delta = float(after["count"]) - float(before["count"])
                    if count_delta < 0 or sum_delta < -1e-9 or any(delta < 0 for _, delta in bucket_deltas):
                        status = "counter_reset"
                    elif any(a[1] > b[1] for a, b in zip(bucket_deltas, bucket_deltas[1:])):
                        status = "invalid_histogram"
                    elif not math.isclose(count_delta, bucket_deltas[-1][1], rel_tol=0.0, abs_tol=1e-9):
                        status = "invalid_histogram"
                    elif count_delta == 0:
                        status = "no_observations"
                        observations = 0.0
                    else:
                        observations = count_delta
                        mean = max(0.0, sum_delta) / count_delta
                        p50 = _quantile_upper(bucket_deltas, 0.50, count_delta)
                        p95 = _quantile_upper(bucket_deltas, 0.95, count_delta)
                        if p50 is None or p95 is None:
                            status = "unbounded_quantile"
            metric_statuses.append(status)
            histograms.append(HistogramWindow(family, base_name, str(series_index), status, observations, mean, p50, p95,
                                              "first cumulative bucket reaching the requested window quantile; bucket edge is an upper bound, +Inf is unbounded"))
    if not current.series:
        status = "empty_current_snapshot"
    elif not previous.series:
        status = "no_previous_snapshot"
    elif not any(_is_supported_raw_name(item.name) for item in current.series):
        status = "no_supported_metrics"
    elif any(value in ("counter_reset", "invalid_counter", "invalid_gauge", "invalid_type", "invalid_ratio", "invalid_histogram", "invalid_rate") for value in metric_statuses):
        status = "partial_or_reset"
    elif any(value in ("unmatched_series", "unmatched_buckets") for value in metric_statuses):
        status = "partial_unmatched"
    else:
        status = "compared"
    return TelemetryComparison(status, window, tuple(gauges), tuple(counters), tuple(histograms), tuple(derived),
                               ("KV cache occupancy is not physical GPU utilization", "rates require exact matched counters over the caller-supplied window", "unmatched/reset series have null deltas/rates", "histogram quantiles are bucket upper bounds, not interpolated estimates"))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_endpoint(endpoint: str) -> str:
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > MAX_ENDPOINT_CHARS or "\r" in endpoint or "\n" in endpoint:
        raise TelemetryError("configured metrics endpoint is invalid")
    try:
        parsed = urlsplit(endpoint)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise TelemetryError("configured metrics endpoint is invalid") from None
    if parsed.scheme not in ("http", "https") or not hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise TelemetryError("configured metrics endpoint must be HTTPS or loopback HTTP without credentials/query/fragment")
    path = unquote(parsed.path)
    if not path.endswith("/metrics") or ".." in path.split("/"):
        raise TelemetryError("configured metrics endpoint path must end in /metrics")
    if parsed.scheme == "http":
        loopback = hostname.lower() == "localhost"
        if not loopback:
            try:
                loopback = ipaddress.ip_address(hostname).is_loopback
            except ValueError:
                loopback = False
        if not loopback:
            raise TelemetryError("HTTP metrics endpoints are allowed only on loopback")
    if port is not None and not 1 <= port <= 65535:
        raise TelemetryError("configured metrics endpoint port is invalid")
    return endpoint


def collect_configured_telemetry(env: Mapping[str, str] | None = None, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
                                max_bytes: int = MAX_BODY_BYTES) -> CollectionResult:
    """Fetch the configured `/metrics` URL once; all errors are safely redacted."""
    values = os.environ if env is None else env
    endpoint = values.get("VLLM_METRICS_URL")
    if not endpoint:
        return CollectionResult("unconfigured", False, None, None, None)
    try:
        _finite_number(timeout_seconds, "timeout_seconds", low=0.05, high=15.0)
        if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BODY_BYTES:
            raise TelemetryError("max_bytes must be from 1 to the configured body limit")
        _validate_endpoint(endpoint)
        token = values.get("VLLM_METRICS_TOKEN", "")
        if not isinstance(token, str) or len(token) > MAX_TOKEN_CHARS or "\r" in token or "\n" in token:
            raise TelemetryError("configured metrics token is invalid")
        headers = {"Accept": "text/plain; version=0.0.4, application/openmetrics-text; version=1.0.0", "User-Agent": "ApexGraphSwarm-telemetry/1"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(endpoint, headers=headers, method="GET")
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=float(timeout_seconds)) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise TelemetryError("metrics endpoint returned a non-success status")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type and content_type not in ("text/plain", "application/openmetrics-text"):
                raise TelemetryError("metrics endpoint returned an unsupported content type")
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > max_bytes:
                        raise TelemetryError("metrics response exceeds the byte limit")
                except ValueError:
                    raise TelemetryError("metrics response has invalid length metadata") from None
            raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise TelemetryError("metrics response exceeds the byte limit")
        body = raw.decode("utf-8", errors="strict")
        snapshot = parse_prometheus(body)
        return CollectionResult("collected", True, time.time(), snapshot, None)
    except HTTPError as error:
        # Do not include the URL, response body, token, or server-provided text.
        message = "metrics endpoint redirected" if 300 <= error.code < 400 else "metrics endpoint request failed"
        error.close()
    except (URLError, TimeoutError, OSError):
        message = "metrics endpoint request failed"
    except (TelemetryError, UnicodeError, ValueError):
        message = "configured metrics collection failed validation"
    return CollectionResult("error", True, None, None, message)


def _finite_number(value: object, name: str, *, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TelemetryError("%s must be finite and within bounds" % name)
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise TelemetryError("%s must be finite and within bounds" % name) from None
    if not math.isfinite(number) or number < low or number > high:
        raise TelemetryError("%s must be finite and within bounds" % name)
    return number


def main() -> int:
    """Print a single redacted JSON collection result from server config."""
    result = collect_configured_telemetry()
    print(json.dumps(result.to_dict(), ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.status in ("collected", "unconfigured") else 1


if __name__ == "__main__":
    raise SystemExit(main())
