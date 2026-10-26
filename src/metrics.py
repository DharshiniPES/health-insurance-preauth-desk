import time
from typing import Dict, Any, List
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from src.contracts import PreAuthRecommendation

# Prometheus Metrics (D5, A6)
PREAUTH_REQUESTS_TOTAL = Counter(
    "preauth_requests_total",
    "Total pre-authorisation requests processed",
    ["status", "route"]
)

QUARANTINED_REQUESTS_TOTAL = Counter(
    "preauth_quarantined_total",
    "Total requests quarantined at ingestion boundary"
)

PREAUTH_LATENCY_HISTOGRAM = Histogram(
    "preauth_latency_seconds",
    "End-to-end run latency from submission to completion",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0]
)

STEP_LATENCY_HISTOGRAM = Histogram(
    "preauth_step_latency_seconds",
    "Per-step latency for agents",
    ["agent_name", "action"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

TOOL_CALLS_TOTAL = Counter(
    "preauth_tool_calls_total",
    "Total tool calls invoked by agents",
    ["agent_name", "tool_name"]
)

TOKENS_TOTAL = Counter(
    "preauth_tokens_total",
    "Total tokens consumed",
    ["token_type"]
)

COST_TOTAL = Counter(
    "preauth_cost_usd_total",
    "Total cost accumulated in USD"
)

ACTIVE_RUNS_GAUGE = Gauge(
    "preauth_active_runs",
    "Number of runs currently executing"
)

QUEUED_RUNS_GAUGE = Gauge(
    "preauth_queued_runs",
    "Number of runs queued awaiting worker"
)

FEEDBACK_TOTAL = Counter(
    "preauth_feedback_total",
    "Human medical officer feedback rating",
    ["satisfactory"]
)


class MetricsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.quarantined_count = 0
        self.latencies: List[float] = []
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        self.step_counts: List[int] = []
        self.tool_counts: List[int] = []
        self.feedback_list: List[Dict[str, Any]] = []

    def get_uptime_seconds(self) -> float:
        return round(time.time() - self.start_time, 1)

    def increment_queued(self):
        QUEUED_RUNS_GAUGE.inc()

    def increment_active(self):
        QUEUED_RUNS_GAUGE.dec()
        ACTIVE_RUNS_GAUGE.inc()

    def decrement_active(self):
        ACTIVE_RUNS_GAUGE.dec()

    def record_quarantine(self):
        self.quarantined_count += 1
        QUARANTINED_REQUESTS_TOTAL.inc()

    def record_run_success(self, rec: PreAuthRecommendation):
        self.total_runs += 1
        self.successful_runs += 1
        PREAUTH_REQUESTS_TOTAL.labels(status="COMPLETED", route=rec.route).inc()
        
        latency_sec = rec.total_latency_ms / 1000.0
        PREAUTH_LATENCY_HISTOGRAM.observe(latency_sec)
        self.latencies.append(rec.total_latency_ms)

        self.total_tokens += rec.total_tokens
        TOKENS_TOTAL.labels(token_type="total").inc(rec.total_tokens)

        self.total_cost_usd += rec.total_cost_usd
        COST_TOTAL.inc(rec.total_cost_usd)

        tool_calls = sum(1 for s in rec.steps if s.tool_name)
        self.step_counts.append(len(rec.steps))
        self.tool_counts.append(tool_calls)

        for s in rec.steps:
            if s.tool_name:
                TOOL_CALLS_TOTAL.labels(agent_name=s.agent_name, tool_name=s.tool_name).inc()
            STEP_LATENCY_HISTOGRAM.labels(agent_name=s.agent_name, action=s.action).observe(s.latency_ms / 1000.0)

    def record_run_failure(self):
        self.total_runs += 1
        self.failed_runs += 1
        PREAUTH_REQUESTS_TOTAL.labels(status="FAILED", route="unknown").inc()

    def record_feedback(self, run_id: str, satisfactory: bool, reason: str):
        FEEDBACK_TOTAL.labels(satisfactory=str(satisfactory)).inc()
        self.feedback_list.append({
            "run_id": run_id,
            "satisfactory": satisfactory,
            "reason": reason,
            "timestamp": time.time()
        })

    def get_summary_stats(self) -> Dict[str, Any]:
        p50 = 0.0
        p95 = 0.0
        if self.latencies:
            sorted_lat = sorted(self.latencies)
            p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
            p95 = sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)]

        success_rate = (self.successful_runs / max(self.total_runs, 1)) * 100.0
        cost_per_100_runs = (self.total_cost_usd / max(self.total_runs, 1)) * 100.0

        avg_steps = sum(self.step_counts) / max(len(self.step_counts), 1)
        avg_tools = sum(self.tool_counts) / max(len(self.tool_counts), 1)

        sat_count = sum(1 for f in self.feedback_list if f["satisfactory"])
        sat_rate = (sat_count / max(len(self.feedback_list), 1)) * 100.0 if self.feedback_list else 100.0

        return {
            "uptime_seconds": self.get_uptime_seconds(),
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "quarantined_count": self.quarantined_count,
            "task_success_rate_percent": round(success_rate, 2),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "avg_steps_per_run": round(avg_steps, 2),
            "avg_tool_calls_per_run": round(avg_tools, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "cost_per_100_runs_usd": round(cost_per_100_runs, 6),
            "satisfaction_rate_percent": round(sat_rate, 1),
            "feedback_count": len(self.feedback_list)
        }


metrics_tracker = MetricsTracker()
