# Presentation Script & Slide Outline
## UE24AM342AA5 — ML System Design & AgentOps | Mini Project 03
### Health Insurance Pre-Authorisation Desk

---

### Slide 1: Title & Overview
- **Project:** Health Insurance Pre-Authorisation Desk
- **Course:** UE24AM342AA5 — ML System Design and AgentOps (PES University)
- **Domain:** Health Insurance and Hospital Revenue Cycle
- **Team Component:** Jackfruit (Level 3)
- **Core Goal:** Build a resilient, production-grade multi-agent service that ingests pre-authorisation requests, validates data contracts, dynamically retrieves modifying policy provisions, and outputs a grounded coverage recommendation with clause citations.

---

### Slide 2: Problem Context & Domain Nuances
- **The Operational Challenge:** Hospital TPA desks request pre-authorisation before planned admissions. Insurer medical officers must decide quickly: is it covered, and up to what limit?
- **High Stakes:** Premature approval causes direct claim loss; unjustified denial results in consumer court & IRDAI grievance.
- **Corpus Complexity:** Coverage clauses (Inpatient / Day care) state what is covered, but waiting periods (24-month specific conditions, 36-month PED), sub-limits (room rent 1%, cataract caps), and exclusions are located in disparate sections.
- **Role Boundary:** The automated system **never** gives final authorization; it generates evidence-backed recommendations for a human medical officer.

---

### Slide 3: Section 4.1 — The Difficult Case
- **Scenario:** *"Planned cataract surgery. The policy was issued eleven months ago."*
- **Why Naive Search Fails:** Searching "cataract surgery" returns Clause 1.1 / Day Care Schedule confirming cataract is covered. Because the request does not mention waiting periods, standard embedding-based retrieval fails to pull the waiting-period clause.
- **Agent 2-Stage Retrieval:**
  1. Primary search retrieves Day Care Schedule `DC-EYE-01` & Clause 1.1.
  2. The Clinical Intake Agent identifies "Cataract" as a condition carrying mandatory waiting periods and issues a targeted secondary query for Clause 2.2 (`SEC-WAIT-24M-SPECIFIC`).
  3. Adjudication compares policy vintage (11 months) < waiting period (24 months).
  4. Routes to `medical-review` citing **both** `SEC-COV-DAYCARE` and `SEC-WAIT-24M-SPECIFIC`!

---

### Slide 4: Multi-Agent Architecture & Topology (A1, A2, A3)
- **Agent 1: Clinical Intake Agent**
  - Admission classification (planned, day care, emergency, maternity).
  - Clinical entity extraction, ICD-10 validation, vintage calculation.
  - Multi-stage dynamic retrieval.
- **Agent 2: Adjudication Agent**
  - Clause verification, sub-limit calculations (room rent 1% cap, cataract cap).
  - Self-verification (A3): Checks that every citation resolves to retrieved text.
  - Decision routing: `approve-recommended`, `query-to-hospital`, `medical-review`.
- **Bound Orchestrator Loop:** Max 6 steps, max 8 tool calls, 25-second wall-clock timeout.

---

### Slide 5: Ingestion Boundary, Quarantine & Safety (D1, F2, L4)
- **Data Contract:** Enforces schema, types, ranges, categories, and cross-field rules (e.g. discharge date >= admission date, day-care same-day discharge).
- **Ingestion Quarantine (D1):** Malformed requests are rejected with HTTP 422 and saved to `data/quarantine/`. Zero agent runs start!
- **Prompt Injection Defense (L4):** Detects and blocks adversarial instructions ("ignore rules", "system override", "DAN mode").
- **Authority Boundaries:** Enforces legal disclaimers and prevents unauthorized commitments.

---

### Slide 6: Benchmark & LLMOps Evaluation (L2, L3)
- **Evaluation Suite:** 20 diverse clinical scenarios in `data/eval_scenarios.json`.
- **TruLens Metrics Computed:**
  - Groundedness: 0.925
  - Context Relevance: 1.000
  - Faithfulness: 0.900
  - Hallucination Rate: 0.100 (10%)
- **Prompt Comparison (L2):** Prompt v2 (Verified CoT with 2-Stage Retrieval) improved accuracy by +20% and reduced hallucination by 25% over Prompt v1.
- **Cost per 100 Runs:** $0.004032.

---

### Slide 7: Operational Resilience & Docker Architecture (A5, D3, A7)
- **Resilience:** Circuit Breaker with 3 failure threshold, exponential backoff retries, and graceful degradation fallback.
- **Docker Compose Setup (4 Services):**
  1. `api`: FastAPI REST Gateway + Web Client.
  2. `agent-worker`: Asynchronous agent task runner.
  3. `redis`: Queue broker & cache.
  4. `prometheus`: Observability scraper (`/metrics`).
- **Worker Scaling:** Verified with `docker compose up --scale agent-worker=3`.

---

### Slide 8: SLO & Locust Load Testing (D6)
- **Declared Target SLO:** p95 <= 2.50s (2500 ms) from submission to final polling result.
- **Measured Results (Stub Mode):** p50 = ~65 ms, p95 = ~140 ms (Met with substantial margin).
- **Throughput:** > 250 req/sec under multi-worker scaling.

---

### Slide 9: 10 Demonstration Items Checklist
- All 10 items in Section 9 are prepared, verified, and ready for live demonstration.

---

### Slide 10: Conclusion & Design Judgement
- Emphasizes the transition from naive pipelines to production multi-agent systems with active self-verification and operational guardrails.
