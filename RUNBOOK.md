# Operational Runbook & Incident Log (D8)

## 1. Top Failure Modes

### Failure Mode 1: LLM Provider Outage or Circuit Breaker Tripped (Symptom, Confirmation, Recovery)
* **Symptom:**
  - Upstream model API calls return HTTP 429 (Rate Limit Exceeded) or 503 (Service Unavailable).
  - Web UI displays `Circuit Breaker: OPEN (Degraded)`.
  - All incoming pre-authorisation requests route directly to `medical-review` with reason *"Circuit breaker OPEN: upstream LLM provider unavailable"*.
  - Latency drops to ~2ms per run (fallback path executed without invoking LLM).
* **Confirmation:**
  - Inspect `/health` endpoint: check `"circuit_breaker.state" == "OPEN"`.
  - Inspect Prometheus metrics: `preauth_requests_total{route="medical-review"}` spikes.
  - Review application logs: look for `CircuitBreakerOpenException` and consecutive failure counter `>= 3`.
* **Recovery:**
  1. Verify upstream provider status and API key quotas.
  2. If provider has recovered, the circuit breaker automatically transitions to `HALF_OPEN` after 30 seconds (`CB_RESET_TIMEOUT_SEC`).
  3. Alternatively, force reset via administrative API endpoint:
     ```bash
     curl -X POST "http://localhost:8000/api/v1/admin/circuit-breaker/toggle?force_open=false"
     ```
  4. If upstream cloud provider remains impaired, switch configuration to offline high-fidelity local stub provider:
     ```bash
     export LLM_PROVIDER=stub
     ```

---

### Failure Mode 2: Async Worker Queue Backlog & Memory Saturation (Symptom, Confirmation, Recovery)
* **Symptom:**
  - Pre-auth submission returns HTTP 202, but run status remains stuck in `QUEUED` for > 10 seconds.
  - End-to-end run latency p95 breaches the 2.50s SLO target.
  - `preauth_queued_runs` metric climbs monotonically.
* **Confirmation:**
  - Query Prometheus: `preauth_queued_runs > 50` while `preauth_active_runs` is pegged at worker concurrency limit.
  - Execute health query:
     ```bash
     curl http://localhost:8000/api/v1/stats
     ```
* **Recovery:**
  1. Scale the asynchronous agent workers dynamically:
     ```bash
     docker compose up --scale agent-worker=3 -d
     ```
  2. If stuck tasks persist, check for unhandled deadlocks in vector index read locks.
  3. Purge orphaned runs older than TTL (3600s).

---

## 2. Development Incident Post-Mortem Log

| Incident ID | Date | Severity | Summary | Root Cause | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **INC-2026-1025-01** | 2026-10-25 | High | Ingestion worker thread hang on malformed ICD-10 codes | Unescaped catastrophic backtracking regex in ICD-10 pattern validator during batch load testing. | Replaced regex with strict anchored finite-state pattern `^[A-Z][0-9]{2}(\.[0-9]{1,2})?$` and pre-compiled regex object at module import. |
| **INC-2026-1025-02** | 2026-10-25 | Medium | Scenario 01 (Cataract 11m) single-pass retrieval failure | Cover search returned Section 1.0 (Inpatient) but missed Clause 2.2 (24m Specific Waiting Period) located 12 pages away in policy text. | Upgraded architecture to 2-stage dynamic agent retrieval (Section 5 Design Approach): Clinical Intake Agent detects specific surgical entities and issues secondary targeted search for modifying waiting periods. |
