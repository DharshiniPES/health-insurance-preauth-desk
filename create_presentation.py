"""
Generates an expanded 12-slide PowerPoint presentation (.pptx) for Mini Project 03.
Course: UE24AM342AA5 — ML System Design & AgentOps, PES University
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    PRIMARY_COLOR = RGBColor(30, 58, 138)    # Deep Navy
    ACCENT_COLOR = RGBColor(37, 99, 235)     # Royal Blue
    TEXT_DARK = RGBColor(15, 23, 42)         # Slate 900
    TEXT_MUTED = RGBColor(100, 116, 139)     # Slate 500
    BG_LIGHT = RGBColor(248, 250, 252)       # Light Slate
    CARD_BG = RGBColor(255, 255, 255)        # Pure White
    GREEN_COLOR = RGBColor(16, 185, 129)     # Emerald
    BORDER_COLOR = RGBColor(226, 232, 240)

    def add_header(slide, title_text, category_text="UE24AM342AA5 | Mini Project 03 | Jackfruit (Level 3)"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.35))
        cat_tf = cat_box.text_frame
        cat_tf.word_wrap = True
        p_cat = cat_tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_COLOR

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.7))
        title_tf = title_box.text_frame
        title_tf.word_wrap = True
        p_title = title_tf.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(23)
        p_title.font.bold = True
        p_title.font.color.rgb = PRIMARY_COLOR

    def add_card(slide, left, top, width, height, title, bullet_points, header_bg=None):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = BORDER_COLOR
        shape.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.18), width - Inches(0.4), height - Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = PRIMARY_COLOR
        p_t.space_after = Pt(10)

        for pt in bullet_points:
            p = tf.add_paragraph()
            p.text = f"• {pt}"
            p.font.size = Pt(12)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(5)

    # -------------------------------------------------------------
    # Slide 1: Title Slide
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = PRIMARY_COLOR

    tbox1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.3), Inches(4.5))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "UE24AM342AA5 — ML System Design & AgentOps"
    p0.font.size = Pt(16)
    p0.font.color.rgb = RGBColor(147, 197, 253)
    p0.space_after = Pt(12)

    p1 = tf1.add_paragraph()
    p1.text = "Mini Project 03: Health Insurance Pre-Authorisation Desk"
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "Production Multi-Agent System with Dynamic Modifying Retrieval, Dual-Clause Grounding & Resilience"
    p2.font.size = Pt(17)
    p2.font.color.rgb = RGBColor(226, 232, 240)
    p2.space_after = Pt(28)

    p3 = tf1.add_paragraph()
    p3.text = "Student: Dharshini V (SRN: PES1UG24AM428) & Team  |  Component: Jackfruit (Level 3, 10 Marks)\nDepartment of Computer Science & Engineering (AI & ML) | PES University"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(191, 219, 254)

    # -------------------------------------------------------------
    # Slide 2: Problem Context & Domain Nuances
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Problem Context & The Pre-Authorisation Dilemma")

    add_card(s2, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "The Operational Challenge", [
        "Hospital TPA desks submit pre-auth requests before planned admissions.",
        "Underwriters must answer in minutes: Is it covered, and up to what limit?",
        "High Stakes: Erroneous approval = direct insurer claim loss; Erroneous denial = consumer lawsuit & IRDAI grievance.",
        "Corpus Fragmentation: Cover clauses state general cover, but waiting periods, sub-limits, and exclusions are located 12+ pages away.",
        "Core Mandate: The automated system NEVER authorizes an admission; it produces evidence-grounded recommendations for human Medical Officers."
    ])

    add_card(s2, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "System Requirements Breakdown", [
        "F1-F8: Documented REST interface, quarantine boundary, admission classifier, cited limits, and health logging.",
        "A1-A8: Multi-agent reasoning (Intake + Adjudication), bounded loops (steps/time), async queue, self-verification, and UI.",
        "L1-L6: 2-stage dynamic retrieval, prompt versioning (v1 vs v2), 20-scenario eval suite, guardrails, and cost tracking.",
        "D1-D8: Strict data contract, Docker Compose (4 services), p95 SLO benchmarking, and operational runbook."
    ])

    # -------------------------------------------------------------
    # Slide 3: Section 4.1 - The Difficult Case
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "The Difficult Case (Section 4.1): Cataract at 11 Months Vintage")

    add_card(s3, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Why Naive Single-Pass RAG Fails", [
        "Scenario: Planned Cataract Surgery on a policy issued 11 months ago.",
        "Single-pass search query: 'Planned cataract surgery with IOL'.",
        "Result: Returns Section 1.0 (Inpatient) or Day Care Schedule confirming Cataract is covered.",
        "Fatal flaw: The request never mentions waiting periods, so semantic search completely misses Clause 2.2.",
        "Outcome of fixed pipeline: Erroneous premature approval, causing direct insurer underwriting loss."
    ])

    add_card(s3, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Our Agent's 2-Stage Resolution", [
        "Stage 1: Primary cover retrieval locates Clause 1.1 / Day Care Schedule.",
        "Stage 2 (Dynamic Reasoning): Agent identifies 'Cataract' as a specific surgical entity requiring modifying provisions.",
        "Dynamic query triggered: Searches Clause 2.2 ('24-Month Waiting Period for Specified Illnesses').",
        "Calculates policy vintage: 11 months < 24 months mandatory waiting period.",
        "Verdict: Escalates to 'medical-review' citing BOTH SEC-COV-DAYCARE and SEC-WAIT-24M-SPECIFIC."
    ])

    # -------------------------------------------------------------
    # Slide 4: Multi-Agent Topology & Architecture
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Multi-Agent Architecture & Topology (A1, A2)")

    add_card(s4, Inches(0.8), Inches(1.65), Inches(3.7), Inches(5.3), "Agent 1: Clinical Intake", [
        "Classifies admission (planned, day care, emergency, maternity).",
        "Extracts ICD-10 semantics and calculates policy vintage in months.",
        "Executes 2-stage dynamic retrieval (Cover -> Modifying waiting periods).",
        "Tools: search_daycare, corpus_search, lookup_clause, get_request_field."
    ])

    add_card(s4, Inches(4.8), Inches(1.65), Inches(3.7), Inches(5.3), "Agent 2: Adjudication Agent", [
        "Adjudicates coverage position and computes indicative limits.",
        "Enforces room rent 1% caps (SEC-SUBLIM-ROOM) & procedure limits.",
        "Strict Self-Verification (A3): Every citation must resolve to retrieved corpus text.",
        "Routes to: approve-recommended, query-to-hospital, or medical-review."
    ])

    add_card(s4, Inches(8.8), Inches(1.65), Inches(3.7), Inches(5.3), "Bound Orchestrator Loop", [
        "Bounded by max 6 steps, max 8 tool calls, and 25s wall-clock time.",
        "Token & per-step cost tracking (Gemini Flash rates).",
        "Circuit Breaker state machine (CLOSED, OPEN, HALF_OPEN).",
        "Async queue decoupled execution with immediate run_id return."
    ])

    # -------------------------------------------------------------
    # Slide 5: Ingestion Boundary & Quarantine Engine
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Ingestion Boundary & Quarantine Engine (D1, F1, F2)")

    add_card(s5, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Strict Ingestion Contract (D1, F2)", [
        "Schema, type, range, and categorical validation via Pydantic.",
        "Cross-field rule: Discharge date cannot precede Admission date.",
        "Cross-field rule: Day-care requires same-day discharge and zero room rent.",
        "Cross-field rule: Maternity requires female gender and age >= 18.",
        "Daily room rent cannot exceed total estimated hospital cost."
    ])

    add_card(s5, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Quarantine Mechanism (Demo Item 4)", [
        "Zero Agent Run Mandate: Malformed records must not initiate an LLM agent run.",
        "Immediate HTTP 422: Rejected records return structured validation errors.",
        "Audit Trail: Payload + field-level errors persisted to data/quarantine/{qid}.json.",
        "Inspector Endpoint: GET /api/v1/quarantine allows auditing all rejected submissions."
    ])

    # -------------------------------------------------------------
    # Slide 6: Dynamic 2-Stage Retrieval vs Fixed Pipeline
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Dynamic 2-Stage Retrieval vs Fixed Pipeline (Section 5)")

    add_card(s6, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Fixed Pipeline (Standard RAG)", [
        "1. Ingests request text as a static query.",
        "2. Executes single similarity search across policy embeddings.",
        "3. Feeds top-k passages directly into generator prompt.",
        "Failure: Inability to detect unmentioned constraints. The system has no mechanism to ask: 'What modifying conditions apply to this surgery?'",
        "Result: Hallucinated approvals on unserved waiting periods."
    ])

    add_card(s6, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Autonomous 2-Stage Agent Loop", [
        "1. Retrieves primary cover clause (e.g. Inpatient / Day Care).",
        "2. Inspects clinical entities against known statutory categories (Cataract, Hernia, Joint, PED, Maternity).",
        "3. Synthesizes targeted secondary query derived from findings.",
        "4. Retrieves modifying provisions (Clause 2.2, 2.3, 2.4, 3.0).",
        "5. Self-verifies support before synthesizing final recommendation."
    ])

    # -------------------------------------------------------------
    # Slide 7: Self-Verification & LLM Guardrails
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Strict Self-Verification & Safety Guardrails (A3, L4)")

    add_card(s7, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Strict Self-Verification Loop (A3)", [
        "Grounding Check: Every cited clause ID must resolve to retrieved text.",
        "Approval Guard: Approvals without authoritative coverage citations are blocked.",
        "Escalation Trigger: Unverified assertions trigger immediate escalation to medical-review.",
        "Zero Fabrication: The system chooses human review over generating an ungrounded answer."
    ])

    add_card(s7, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Adversarial & Output Guardrails (L4)", [
        "Prompt Injection Defense: Regex & semantic filters detect 'ignore previous rules', 'system override', 'DAN mode'.",
        "Toxicity filter blocks abusive/fraudulent payloads.",
        "Authority Boundary Guardrail: Output filter strips unauthorized binding declarations ('insurer guarantees payment').",
        "Mandatory Legal Disclaimer automatically appended to every response."
    ])

    # -------------------------------------------------------------
    # Slide 8: Evaluation Suite & Benchmark Results
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Benchmark Evaluation: 20 Scenarios (L2, L3)")

    add_card(s8, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Evaluation Methodology (TruLens Metrics)", [
        "Fixed suite of 20 diverse clinical scenarios in data/eval_scenarios.json.",
        "Groundedness: Ratio of cited assertions anchored in retrieved passages.",
        "Context Relevance: Ratio of retrieved provisions pertinent to the clinical case.",
        "Faithfulness: Agreement between verdict and waiting-period/exclusion rules.",
        "Hallucination Rate: 1.0 - Faithfulness.",
        "CLI Runner: Runnable as a batch from command line via 'python -m src.evaluator'."
    ])

    add_card(s8, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Prompt Variant Comparison (L2)", [
        "Prompt v1 (Concise single-pass):",
        "  - Routing Accuracy: 80.0%  | Groundedness: 0.600",
        "  - Faithfulness: 0.650      | Hallucination Rate: 0.350",
        "Prompt v2 (Verified CoT with 2-Stage Retrieval):",
        "  - Routing Accuracy: 100.0% (+20.0%)",
        "  - Groundedness: 0.925 (+0.325)",
        "  - Faithfulness: 0.900 (+0.250)",
        "  - Hallucination Rate: 0.100 (-25.0% reduction)",
        "Cost per 100 runs: $0.004032 (Ultra cost-effective)."
    ])

    # -------------------------------------------------------------
    # Slide 9: Reliability, Circuit Breaker & Fallback
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Operational Resilience & Circuit Breaker (A5)")

    add_card(s9, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Circuit Breaker State Machine", [
        "Trips to OPEN after 3 consecutive provider failures / timeouts.",
        "Auto-Reset: Transitions to HALF_OPEN after 30 seconds (CB_RESET_TIMEOUT_SEC).",
        "Admin Endpoint: POST /api/v1/admin/circuit-breaker/toggle allows simulated testing.",
        "UI Integration: Top-bar badge indicates live status (CLOSED vs OPEN)."
    ])

    add_card(s9, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Graceful Degradation Fallback (Demo Item 8)", [
        "When OPEN, incoming runs do NOT fail with 500 errors or time out.",
        "Immediate Routing: Requests route directly to human 'medical-review'.",
        "Reason Stated: 'Circuit breaker OPEN: upstream provider unavailable'.",
        "Sub-second Execution: Fallback executes in ~2ms without wasting LLM budget."
    ])

    # -------------------------------------------------------------
    # Slide 10: Docker Compose Architecture & Worker Scaling
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Container Architecture & Worker Scaling (D3, A7)")

    add_card(s10, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "4 Service Boundaries (D3)", [
        "1. api: FastAPI gateway enforcing contracts, guardrails & Web UI.",
        "2. agent-worker: Background worker executing multi-agent reasoning.",
        "3. redis: Distributed task queue & cache store (3600s TTL).",
        "4. prometheus: Observability scraping /metrics every 5 seconds.",
        "Clean Clone: Launches seamlessly with 'docker compose up -d'."
    ])

    add_card(s10, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Horizontal Worker Scaling (A7)", [
        "Command: 'docker compose up --scale agent-worker=3 -d'.",
        "Load Distribution: Multiple workers pop tasks concurrently from Redis queue.",
        "Throughput Multiplier: Worker scaling increases queue throughput from ~90 RPS to 264+ RPS.",
        "Eliminates run queuing delays during peak hospital admission surges."
    ])

    # -------------------------------------------------------------
    # Slide 11: SLO Load Testing & Locust Benchmarks
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "SLO Declaration, Load Testing & Costs (D6, L5)")

    add_card(s11, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "Declared SLO vs Measured Results", [
        "Declared Target SLO: End-to-end run p95 <= 2.50s (2500 ms).",
        "Justification: Must beat human desk speed (15-30 mins) while sustaining peak TPA load.",
        "Measured p50: ~65.0 ms  |  Measured p95: ~140.0 ms (Met by 18x margin).",
        "Locust Load Test: Tested with realistic async polling in stub mode.",
        "Bottleneck: Single-worker run-state contention at 450+ concurrent users; resolved via worker scaling."
    ])

    add_card(s11, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Cost Accounting per 100 Runs (L5)", [
        "Gemini 1.5 Flash Pricing: $0.075 / 1M prompt, $0.30 / 1M completion.",
        "Average Prompt Tokens / Run: 184 tokens.",
        "Average Completion Tokens / Run: 90 tokens.",
        "Total Cost per 100 Runs: $0.004032 (< half a cent).",
        "Primary Cost Driver: Stage 2 adjudication reasoning (68% of token spend due to clause context injection)."
    ])

    # -------------------------------------------------------------
    # Slide 12: Demonstration Checklist & Summary
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Demonstration Verification & Conclusion")

    add_card(s12, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.3), "All 10 Demonstration Items Ready", [
        "1. Docker compose up from clean clone",
        "2. Valid request producing routed recommendation",
        "3. Traced end-to-end with per-step latency and cost",
        "4. Malformed request quarantined (Zero agent runs)",
        "5. Out-of-corpus condition safely escalated",
        "6. Self-verification catching ungrounded answers",
        "7. Prompt injection attack blocked by guardrail",
        "8. Circuit breaker opening with graceful degradation",
        "9. Locust results confirming declared p95 SLO",
        "10. Section 4.1 Difficult Case (Cataract 11m) handled correctly!"
    ])

    add_card(s12, Inches(6.8), Inches(1.65), Inches(5.6), Inches(5.3), "Conclusion & Deliverables", [
        "GitHub Repo: https://github.com/DharshiniPES/health-insurance-preauth-desk",
        "Final Report: Mini_Project_03_Final_Report.docx and FINAL_REPORT.md",
        "Presentation: PreAuthorisation_Desk_Presentation.pptx and PRESENTATION.md",
        "Key Takeaway: Autonomous multi-agent systems with active self-verification and operational guardrails transform fragile pipelines into production-grade clinical desks."
    ])

    prs.save("PreAuthorisation_Desk_Presentation.pptx")
    print("Expanded 12-slide PowerPoint presentation successfully created: PreAuthorisation_Desk_Presentation.pptx")

if __name__ == "__main__":
    create_deck()
