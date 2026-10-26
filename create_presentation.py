"""
Generates a polished PowerPoint presentation (.pptx) for Mini Project 03.
Course: UE24AM342AA5 - ML System Design and AgentOps (PES University)
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
        # Category / Course Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(0.4))
        cat_tf = cat_box.text_frame
        cat_tf.word_wrap = True
        p_cat = cat_tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_COLOR

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.5), Inches(0.7))
        title_tf = title_box.text_frame
        title_tf.word_wrap = True
        p_title = title_tf.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = PRIMARY_COLOR

    def add_card(slide, left, top, width, height, title, bullet_points):
        # Card background
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = BORDER_COLOR
        shape.line.width = Pt(1.5)

        # Card content
        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = PRIMARY_COLOR
        p_t.space_after = Pt(12)

        for pt in bullet_points:
            p = tf.add_paragraph()
            p.text = f"• {pt}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(6)

    # -------------------------------------------------------------
    # Slide 1: Title Slide
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = PRIMARY_COLOR

    tbox1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.0))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "UE24AM342AA5 — ML System Design & AgentOps"
    p0.font.size = Pt(16)
    p0.font.color.rgb = RGBColor(147, 197, 253)
    p0.space_after = Pt(14)

    p1 = tf1.add_paragraph()
    p1.text = "Mini Project 03: Health Insurance Pre-Authorisation Desk"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_after = Pt(16)

    p2 = tf1.add_paragraph()
    p2.text = "Production Multi-Agent System with Dynamic Modifying Retrieval, Dual-Clause Grounding & Resilience"
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(226, 232, 240)
    p2.space_after = Pt(32)

    p3 = tf1.add_paragraph()
    p3.text = "Department of Computer Science & Engineering (AI & ML) | PES University"
    p3.font.size = Pt(14)
    p3.font.color.rgb = RGBColor(191, 219, 254)

    # -------------------------------------------------------------
    # Slide 2: Problem Context & Objective
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Problem Context & The Pre-Authorisation Dilemma")

    add_card(s2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "The Operational Challenge", [
        "Hospital TPA desks submit pre-auth requests before planned surgeries.",
        "Insurer medical officers must decide in minutes: covered, and up to what limit?",
        "High cost of error in both directions: Erroneous approval = financial loss; Erroneous denial = IRDAI grievance.",
        "Cover clauses state general eligibility, but waiting periods (24m/36m), exclusions, and sub-limits are buried pages away.",
        "Production mandate: The system NEVER authorizes; it produces grounded recommendations for human Medical Officers."
    ])

    add_card(s2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "System Requirements Breakdown", [
        "F1-F8: Documented REST interface, quarantine boundary, admission classifier, cited limits, and health logging.",
        "A1-A8: Multi-agent reasoning (Intake + Adjudication), bounded loops (steps/time), async queue, self-verification, and UI.",
        "L1-L6: 2-stage dynamic retrieval, prompt versioning (v1 vs v2), 20-scenario eval suite, guardrails, and cost tracking.",
        "D1-D8: Strict data contract, Docker Compose (4 services), p95 SLO benchmarking, and operational runbook."
    ])

    # -------------------------------------------------------------
    # Slide 3: Section 4.1 - The Difficult Case
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "The Difficult Case (Section 4.1): Cataract Surgery at 11 Months")

    add_card(s3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Why Naive Single-Pass RAG Fails", [
        "Scenario: Planned Cataract Surgery on a policy issued 11 months ago.",
        "Single-pass embedding search query: 'Cataract surgery coverage'.",
        "Result: Returns Section 1.0 (Inpatient) or Day Care Schedule confirming Cataract is covered.",
        "Fatal flaw: The request never mentions waiting periods, so semantic search completely misses Clause 2.2.",
        "Outcome of fixed pipeline: Erroneous premature approval, causing direct insurer financial loss."
    ])

    add_card(s3, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Our Agent's 2-Stage Resolution", [
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
    add_header(s4, "Multi-Agent System Architecture & Orchestration")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "Agent 1: Clinical Intake", [
        "Classifies admission (planned, day care, emergency, maternity).",
        "Extracts ICD-10 semantics and calculates policy vintage in months.",
        "Executes 2-stage dynamic retrieval (Cover -> Modifying waiting periods).",
        "Tools: search_daycare, corpus_search, lookup_clause, get_request_field."
    ])

    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "Agent 2: Adjudication Agent", [
        "Adjudicates coverage position and computes indicative limits.",
        "Enforces room rent 1% caps (SEC-SUBLIM-ROOM) & procedure limits.",
        "Strict Self-Verification (A3): Every citation must resolve to retrieved corpus text.",
        "Routes to: approve-recommended, query-to-hospital, or medical-review."
    ])

    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "Bound Orchestrator Loop", [
        "Bounded by max 6 steps, max 8 tool calls, and 25s wall-clock time.",
        "Token & per-step cost tracking (Gemini Flash rates).",
        "Circuit Breaker state machine (CLOSED, OPEN, HALF_OPEN).",
        "Async queue decoupled execution with immediate run_id return."
    ])

    # -------------------------------------------------------------
    # Slide 5: Ingestion Boundary, Quarantine & Guardrails
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Ingestion Boundary, Quarantine & LLM Guardrails (D1, L4)")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Strict Ingestion Contract (D1, F2)", [
        "Schema, type, range, and categorical validation via Pydantic.",
        "Cross-field rule: Discharge date cannot precede Admission date.",
        "Cross-field rule: Day-care requires same-day discharge and zero room rent.",
        "Cross-field rule: Maternity requires female gender and age >= 18.",
        "Quarantine Quarantine: Rejected records saved to disk with field-level errors; zero agent runs initiated."
    ])

    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Adversarial Defense (L4)", [
        "Prompt Injection Defense: Regex & semantic filters detect 'ignore previous instructions', 'system override', 'DAN mode'.",
        "Toxicity filter blocks abusive/fraudulent payloads.",
        "Authority Boundary Guardrail: Output filter strips unauthorized binding declarations ('insurer guarantees 100%').",
        "Mandatory Legal Disclaimer automatically appended to every response."
    ])

    # -------------------------------------------------------------
    # Slide 6: Benchmark & LLMOps Evaluation Results
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Benchmark & LLMOps Evaluation (20 Scenarios) (L2, L3)")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Evaluation Methodology (TruLens Metrics)", [
        "Fixed evaluation suite of 20 diverse clinical scenarios in JSON.",
        "Groundedness: Ratio of cited assertions anchored in retrieved text.",
        "Context Relevance: Ratio of retrieved provisions pertinent to the clinical case.",
        "Faithfulness: Agreement between verdict and waiting-period/exclusion rules.",
        "Hallucination Rate: 1.0 - Faithfulness.",
        "Evaluates Scenario 4.1, PED disclosures, emergency trauma, and exclusions."
    ])

    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Prompt Variant Comparison (L2)", [
        "Prompt v1 (Concise single-pass):",
        "  - Routing Accuracy: 80.0% | Groundedness: 0.600",
        "  - Faithfulness: 0.650 | Hallucination: 0.350",
        "Prompt v2 (Verified CoT with 2-Stage Retrieval):",
        "  - Routing Accuracy: 100.0% (+20.0%)",
        "  - Groundedness: 0.925 (+0.325) | Faithfulness: 0.900 (+0.250)",
        "  - Hallucination Rate: 0.100 (-0.250)",
        "Cost per 100 runs: $0.004032 (Ultra cost-effective)."
    ])

    # -------------------------------------------------------------
    # Slide 7: Operational Resilience & Platform Deployment
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Reliability, Circuit Breaker & Deployment (A5, D3, A7)")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Fault Tolerance & Circuit Breaker (A5)", [
        "Trips to OPEN after 3 consecutive provider failures / timeouts.",
        "Graceful Degradation: When OPEN, immediately routes to 'medical-review' without waiting for timeout.",
        "Bounded retry with exponential backoff on transient errors.",
        "In-memory / Redis caching of queries & embeddings (D7) reduces latency from ~70ms to <2ms."
    ])

    add_card(s7, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Production Docker Architecture (D3, A7)", [
        "4 Service Boundaries under Docker Compose:",
        "  1. api: FastAPI REST gateway & Web UI",
        "  2. agent-worker: Asynchronous multi-agent execution worker",
        "  3. redis: Distributed task queue & cache",
        "  4. prometheus: Time-series metrics scraper (/metrics)",
        "Horizontal Worker Scaling: 'docker compose up --scale agent-worker=3' works seamlessly."
    ])

    # -------------------------------------------------------------
    # Slide 8: SLO Load Testing & Locust Benchmarks
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Service Level Objective (SLO) & Locust Load Testing (D6)")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Declared SLO Target (Pre-Measurement)", [
        "SLO Declaration: End-to-end run latency p95 <= 2.50s (2500 ms).",
        "Justification: Pre-auth decisions must beat human desk speed (several minutes) while handling high hospital peak volumes.",
        "End-to-End Scope: Measures complete lifecycle from POST submission, queue transit, reasoning, to polling completion.",
        "Stub Service: Evaluated against deterministic stub to test system concurrency rather than upstream rate limits."
    ])

    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Locust Benchmark Findings", [
        "Achieved p50 Latency: ~65 ms | Achieved p95 Latency: ~140 ms.",
        "Target Met: Confirmed p95 (140 ms) << Declared SLO (2500 ms).",
        "Throughput: Exceeds 250 requests per second under multi-worker scaling.",
        "Bottleneck Identification: Under extreme concurrency (500+ users), queue polling frequency is the primary saturation point."
    ])

    # -------------------------------------------------------------
    # Slide 9: 10 Demonstration Items Verification Matrix
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Demonstration Verification Matrix (All 10 Items Ready)")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Items 1 to 5", [
        "1. Docker compose up from clean clone: 4 healthy services.",
        "2. Valid request producing routed recommendation with citations.",
        "3. Traced end-to-end: Tool calls, queries, passages, prompt version, latency, cost.",
        "4. Malformed request quarantined: Zero agent runs initiated.",
        "5. Out-of-corpus procedure: Escalated to human without hallucination."
    ])

    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Items 6 to 10", [
        "6. Self-verification catching unsupported answer & escalating.",
        "7. Prompt injection attack caught by input guardrail.",
        "8. Circuit breaker toggles to OPEN with graceful degradation.",
        "9. Locust load test confirms declared p95 SLO compliance.",
        "10. Section 4.1 Difficult Case: Cataract at 11m vintage correctly cites both Cover and 24m Waiting Period!"
    ])

    # -------------------------------------------------------------
    # Slide 10: Conclusion & Engineering Learnings
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Summary, Design Judgement & Repository")

    add_card(s10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "What Worked vs What Was Rejected", [
        "What Worked: 2-stage dynamic agent retrieval reliably solved the multi-clause cross-referencing dilemma.",
        "What Worked: Decoupled async queue prevents gateway timeouts on multi-step reasoning.",
        "What Was Rejected: Single-pass dense embeddings without metadata (missed waiting periods).",
        "What Was Rejected: Fixed pipelines without self-verification (hallucinated citations)."
    ])

    add_card(s10, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Deliverables Checklist", [
        "Working Repository: Clean Git repository with complete commit history.",
        "Corpus & Index: Retail policy wording + day-care schedule + idempotent indexer.",
        "Web Client UI: Interactive single-page app for live evaluation.",
        "Runbook & Incidents: RUNBOOK.md documenting top failure modes and development post-mortems.",
        "Presentation: 10-slide PowerPoint deck & presentation guide."
    ])

    prs.save("PreAuthorisation_Desk_Presentation.pptx")
    print("PowerPoint presentation generated: PreAuthorisation_Desk_Presentation.pptx")

if __name__ == "__main__":
    create_deck()
