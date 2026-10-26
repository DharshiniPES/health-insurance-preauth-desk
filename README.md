# Health Insurance Pre-Authorisation Desk

**Course:** UE24AM342AA5 — ML System Design & AgentOps | Dept. of CSE (AI & ML), PES University  
**Project Component:** Jackfruit (Level 3), 10 Marks | Domain: Health Insurance & Hospital Revenue Cycle  
**Author / Team:** Dharshini V (PES1UG24AM428) & Team

---

## 1. Executive Summary & Problem Context

Before a planned hospitalisation, the hospital's Third Party Administrator (TPA) desk submits a pre-authorisation request to the health insurer. An underwriting decision must be reached within minutes: **will this admission be covered, and up to what limit?**

Answering this requires evaluating multiple interdependent policy conditions:
1. Is the policy active and has the initial 30-day waiting period passed?
2. Has the specific waiting period (e.g. 24 months for Cataract, Hernia, Joint Replacement) or Pre-Existing Disease (PED) waiting period (36 months) been served?
3. Does the procedure fall under general permanent exclusions (e.g. cosmetic, experimental therapies)?
4. Are room rent sub-limits (1% of Sum Insured) or specific procedure caps (Cataract max Rs. 40,000) triggered?

> **Core Operating Principle:** The automated system **never** authorizes an admission directly. It produces an evidence-grounded coverage recommendation with clause citations for human Medical Officer adjudication.

---

## 2. The Difficult Case (Section 4.1)

```
"Planned cataract surgery. The policy was issued eleven months ago."
```

* **Why Naive Single-Pass Retrieval Fails:** A single embedding search for "cataract surgery" returns the Cover clause (Inpatient or Day Care Schedule) confirming Cataract is covered. The request does not mention waiting periods, so a single search misses the modifying waiting-period clause located pages away.
* **Our Agentic 2-Stage Retrieval Approach:**
  1. **Stage 1 (Primary Cover):** Retrieves Clause 1.1 / Day Care Schedule `DC-EYE-01`.
  2. **Stage 2 (Dynamic Modifying Search):** The Clinical Intake Agent identifies Cataract as a specific surgical condition requiring modifying provisions and queries Clause 2.2 (`SEC-WAIT-24M-SPECIFIC`).
  3. **Adjudication & Grounding:** Compares policy vintage (11 months) against the required 24 months, verifies the violation, and routes to `medical-review` with citations to **BOTH** `SEC-COV-DAYCARE` and `SEC-WAIT-24M-SPECIFIC`.

---

## 3. Architecture & Multi-Agent Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 TPA / Hospital Desk                    │
                  └──────────────────────────┬─────────────────────────────┘
                                             │ POST /api/v1/preauth
                                             ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │                           INGESTION BOUNDARY (D1, F1, F2)                        │
  │  • Pydantic Schema, Range & Cross-Field Validation                               │
  │  • Adversarial Prompt Injection & Toxicity Defense (L4)                          │
  │  • Quarantine Engine: Invalid payloads quarantined with ZERO agent runs started   │
  └──────────────────────────────────────────┬───────────────────────────────────────┘
                                             │ HTTP 202 (Immediate run_id)
                                             ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │                         ASYNCHRONOUS TASK RUNNER (A4)                            │
  │  • In-Memory / Redis Queue Broker                                                │
  │  • Scalable Worker Pool (docker compose up --scale agent-worker=3)               │
  └──────────────────────────────────────────┬───────────────────────────────────────┘
                                             │ Dispatch
                                             ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │                       MULTI-AGENT ORCHESTRATION LAYER (A1, A2)                   │
  │                                                                                  │
  │   [Agent 1: Clinical Intake Agent]                                               │
  │   ├── Admission Classifier (planned, day care, emergency, maternity)             │
  │   ├── Policy Vintage Calculator & ICD-10 Extractor                               │
  │   └── 2-Stage Dynamic Retrieval (Tools: corpus_search, lookup_clause, daycare)   │
  │                                     │ (Structured Hand-off)                      │
  │                                     ▼                                            │
  │   [Agent 2: Coverage Adjudication Agent]                                         │
  │   ├── Clause Rule Evaluation & Sub-limit / Room Rent Capping                      │
  │   ├── Strict Self-Verification against Retrieved Passages (A3)                   │
  │   └── Recommendation Routing (approve-recommended, query-to-hospital, review)   │
  └──────────────────────────────────────────┬───────────────────────────────────────┘
                                             │ Result Polling / Prometheus / Logs
                                             ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │                 OBSERVABILITY, STORAGE & PRESENTATION LAYER                      │
  │  • Prometheus Metrics (/metrics) & System KPIs (/api/v1/stats)                   │
  │  • Circuit Breaker & Resilience Degradation Fallback (A5)                        │
  │  • Single-Page Web Client UI (A8)                                                │
  └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Quickstart & Local Reproduction

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Set Up
```bash
git clone <repo-url>
cd health-insurance-preauth-desk

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Build Policy Index (Idempotent Pipeline - D2)
```bash
python -m src.indexer
```

### 3. Run the Evaluation Suite (20 Scenarios - L2, L3)
```bash
python -m src.evaluator
```

### 4. Start the Service & Web Client (A4, A8)
```bash
uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at: **`http://localhost:8000`**

---

## 5. Running with Docker Compose (D3, A7)

The system deploys 4 containerized services:
1. `api`: FastAPI REST Gateway & Web UI (Port 8000)
2. `agent-worker`: Asynchronous agent task worker
3. `redis`: Queue broker and shared cache (Port 6379)
4. `prometheus`: Observability metrics scraper (Port 9090)

```bash
# Start all 4 services
docker compose up -d

# Demonstrate horizontal worker scaling (A7)
docker compose up --scale agent-worker=3 -d
```

---

## 6. Demonstration Verification Guide (All 10 Items)

| Item # | Requirement Description | How to Verify in this System |
| :---: | :--- | :--- |
| **1** | `docker compose up` clean clone | Run `docker compose up -d`. All 4 containers start healthy with dependencies verified. |
| **2** | Valid request producing routed recommendation | Select **Scenario 02 (Cataract 36m)** in UI -> click Submit -> routes to `approve-recommended` capped at Rs. 40,000 with citations. |
| **3** | Full trace end-to-end | Every completed run displays detailed per-step timeline: agent thoughts, tools called, prompt version, latency (ms), and cost ($). |
| **4** | Malformed request quarantined | Select **Demo Item 04 (Malformed Request)** -> immediate HTTP 422 with quarantine ID. Check `/api/v1/quarantine`; zero agent runs start. |
| **5** | Out of corpus condition | Select **Scenario 19 (Robotic Dental Veneers)** -> escalates cleanly to `medical-review` without fabricating coverage. |
| **6** | Self-verification catching unsupported answer | Agent 2 verifies every assertion against retrieved text. Uncited claims trigger immediate escalation to human review. |
| **7** | Prompt injection defense | Select **Scenario 18 (Prompt Injection Attack)** -> Input guardrail detects instruction override and quarantines request. |
| **8** | Circuit breaker opening & fallback | Click **"Simulate Outage"** in UI header -> Circuit breaker toggles to `OPEN`. Subsequent requests degrade gracefully to `medical-review`. |
| **9** | Locust load test against declared SLO | Run `locust -f locustfile.py --headless -u 20 -r 5 --run-time 30s --host http://localhost:8000`. Measured p95 (~140ms) beats declared target (2500ms). |
| **10** | Section 4.1 Cataract Difficult Case | Select **Scenario 4.1** -> routes to `medical-review` citing BOTH Cover (`SEC-COV-DAYCARE`) and Waiting Period (`SEC-WAIT-24M-SPECIFIC`). |

---

## 7. Deliverables & Artifacts

- **Presentation Slides:** `PreAuthorisation_Desk_Presentation.pptx` (and `PRESENTATION.md`)
- **Operational Runbook & Incident Log:** `RUNBOOK.md`
- **Benchmark & Scenarios:** `data/eval_scenarios.json` and `data/evaluation_results.json`
- **Environment Template:** `.env.example`
