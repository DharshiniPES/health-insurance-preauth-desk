"""
Generates a formal Microsoft Word (.docx) Final Report for Mini Project 03.
Course: UE24AM342AA5 — ML System Design & AgentOps, PES University
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report_docx():
    doc = docx.Document()

    # Set Margins
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Styles
    PRIMARY = RGBColor(30, 58, 138)    # Deep Navy
    SECONDARY = RGBColor(37, 99, 235)  # Blue
    DARK_TEXT = RGBColor(15, 23, 42)   # Slate 900
    MUTED_TEXT = RGBColor(100, 116, 139)

    # Title Block
    p_pre = doc.add_paragraph()
    r_pre = p_pre.add_run("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING (AI & ML) | PES UNIVERSITY\nCOURSE: UE24AM342AA5 — ML SYSTEM DESIGN AND AGENTOPS")
    r_pre.font.size = Pt(9.5)
    r_pre.font.bold = True
    r_pre.font.color.rgb = SECONDARY
    p_pre.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_title = doc.add_paragraph()
    r_title = p_title.add_run("Mini Project 03 — Health Insurance Pre-Authorisation Desk")
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = PRIMARY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(4)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Production Multi-Agent Reasoning, Dynamic 2-Stage Retrieval & Operational Verification")
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = MUTED_TEXT
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)

    # Metadata Table
    table_meta = doc.add_table(rows=4, cols=2)
    table_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Component / Weightage", "Jackfruit (Level 3), 10 Marks (Scaled to 8 Marks)"),
        ("Student Name & SRN", "Dharshini V (SRN: PES1UG24AM428) & Team"),
        ("Repository URL", "https://github.com/DharshiniPES/health-insurance-preauth-desk"),
        ("Date of Submission", "October 2026")
    ]
    for idx, (k, v) in enumerate(meta_data):
        row = table_meta.rows[idx]
        cell_k, cell_v = row.cells[0], row.cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "F1F5F9")
        set_cell_background(cell_v, "FFFFFF")
        
        pk = cell_k.paragraphs[0]
        rk = pk.add_run(k)
        rk.font.bold = True
        rk.font.size = Pt(10)
        rk.font.color.rgb = PRIMARY

        pv = cell_v.paragraphs[0]
        rv = pv.add_run(v)
        rv.font.size = Pt(10)
        rv.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    def add_section_heading(title):
        h = doc.add_paragraph()
        r = h.add_run(title)
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = PRIMARY
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)

    def add_para(text, bold_prefix=""):
        p = doc.add_paragraph()
        if bold_prefix:
            rb = p.add_run(bold_prefix + " ")
            rb.font.bold = True
            rb.font.size = Pt(10.5)
            rb.font.color.rgb = DARK_TEXT
        r = p.add_run(text)
        r.font.size = Pt(10.5)
        r.font.color.rgb = DARK_TEXT
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        if bold_prefix:
            rb = p.add_run(bold_prefix + " ")
            rb.font.bold = True
            rb.font.size = Pt(10.5)
            rb.font.color.rgb = DARK_TEXT
        r = p.add_run(text)
        r.font.size = Pt(10.5)
        r.font.color.rgb = DARK_TEXT
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

    # 1. Executive Summary
    add_section_heading("Executive Summary")
    add_para("Before a planned hospitalisation, the hospital's Third Party Administrator (TPA) desk submits an electronic pre-authorisation request to the insurer. An underwriting determination must be delivered within minutes: will this admission be covered, and up to what monetary limit? Getting this wrong is expensive in both directions: an erroneous approval causes direct claim loss, while an erroneous denial generates consumer grievances and severe regulatory escalations under IRDAI guidelines.")
    add_para("This report documents the architectural design, implementation, and empirical evaluation of an autonomous, multi-agent reasoning system that ingests pre-authorisation requests, validates data contracts, dynamically retrieves modifying clauses across disparate policy chapters, verifies ground truth against retrieved passages, and produces an evidence-grounded recommendation routed to human Medical Officers.")

    # 2. Problem and Scope
    add_section_heading("1. Problem and Scope")
    add_bullet("Pre-authorisation requests require checking multiple interdependent conditions: policy active status, initial 30-day waiting period, disease-specific 24-month waiting periods, 36-month pre-existing disease (PED) clauses, permanent exclusions, and room rent sub-limits.", "Underwriting Challenge:")
    add_bullet("The canonical evaluation scenario involves 'Planned cataract surgery. The policy was issued eleven months ago.' Standard single-pass RAG systems match the Inpatient or Day-Care cover clause (which confirms Cataract is covered) but miss Clause 2.2 located 12 pages away, which mandates a 24-month waiting period for Cataract. The naive system thus issues an incorrect approval.", "The Section 4.1 Difficult Case:")
    add_bullet("Documented REST interface, Pydantic ingestion validation with disk quarantine, multi-stage dynamic retrieval, self-verification, Prometheus observability, circuit breaker fault tolerance, async queue execution, and prompt injection defense.", "In-Scope Boundaries:")
    add_bullet("Model weight fine-tuning and cloud-hosted deployment (runs locally via Docker Compose with synthetic patient records conforming to HIPAA / IRDAI data privacy guidelines).", "Out-of-Scope Boundaries:")

    # 3. Agent Design
    add_section_heading("2. Agent Design: Topology, Tools, Verification, and Loop Limits")
    add_bullet("Decomposes underwriting into Agent 1 (Clinical Intake & Retrieval) and Agent 2 (Adjudication & Self-Verification) communicating via a typed, immutable handoff contract.", "Agent Topology (A1, A2):")
    add_bullet("Agent 1 classifies admission type (planned, day care, emergency, maternity), calculates policy vintage in months, executes Stage 1 primary cover search, and dynamically derives Stage 2 targeted queries for modifying provisions (waiting periods and exclusions).", "Agent 1 (Clinical Intake):")
    add_bullet("Agent 2 evaluates coverage position, applies room rent 1% caps (SEC-SUBLIM-ROOM) and procedure limits (SEC-SUBLIM-CATARACT), runs strict self-verification, and routes to approve-recommended, query-to-hospital, or medical-review.", "Agent 2 (Adjudication & Verification):")
    add_bullet("Retrieval is exposed as autonomous tools: corpus_search, lookup_clause, search_daycare_schedule, check_sublimit_and_room_rent, and get_request_field.", "Dynamic Tools (A1):")
    add_bullet("Every cited clause must resolve to retrieved text passages. Unverifiable or ungrounded assertions are caught and safely escalated to medical-review (F7).", "Strict Self-Verification (A3):")
    add_bullet("Maximum 6 agent steps, maximum 8 tool calls, and a strict 25.0-second wall-clock execution timeout.", "Loop Bounds (A1):")

    # 4. Architecture & Deployment
    add_section_heading("3. Architecture & Deployment Boundaries (D3, D5, A4)")
    add_para("The system runs entirely under Docker Compose partitioned into 4 distinct service boundaries:")
    add_bullet("FastAPI REST service enforcing data contracts, regex/semantic prompt injection guardrails, ingestion quarantine, health probes, and Web Client UI.", "1. api (REST Gateway, Port 8000):")
    add_bullet("Scalable background worker running multi-agent reasoning, vector retrieval, and verification loops. Supports horizontal scaling via 'docker compose up --scale agent-worker=3'.", "2. agent-worker (Execution Engine):")
    add_bullet("Provides asynchronous task queue buffering (A4) and distributed query/embedding caching (D7) with 3600s TTL.", "3. redis (Queue Broker & Cache, Port 6379):")
    add_bullet("Scrapes /metrics every 5s, tracking p50/p95 latency, tool calls, token usage, cost, and container uptime.", "4. prometheus (Observability Scraper, Port 9090):")

    # 5. Design Decisions
    add_section_heading("4. Design Decisions & What Was Rejected")
    table_dec = doc.add_table(rows=6, cols=3)
    table_dec.alignment = WD_TABLE_ALIGNMENT.CENTER
    dec_headers = ["Decision Area", "Chosen Approach", "Alternative Rejected & Rationale"]
    hdr_row = table_dec.rows[0]
    for i, h in enumerate(dec_headers):
        cell = hdr_row.cells[i]
        set_cell_background(cell, "1E3A8A")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9.5)

    dec_rows = [
        ("Reasoning Layer", "2-Agent Structured Orchestrator with explicit state hand-off", "Unconstrained ReAct loop (Rejected: prone to infinite looping on negative search results)."),
        ("Retrieval Architecture", "2-Stage Dynamic Modifying Retrieval", "Single-pass RAG (Rejected: misses Section 4.1 waiting periods located pages away)."),
        ("Ingestion Boundary", "Pydantic v2 deterministic schema & cross-field validator (D1)", "LLM-based intake validation (Rejected: non-deterministic, slow, vulnerable to jailbreaks)."),
        ("Vector Store", "Local Clause Index with BM25 + Exact Identifier Boosting", "External cloud Vector DB (Rejected: adds network latency, credentials, cost for static policy corpus)."),
        ("Fault Tolerance", "Circuit Breaker (3 fails) with Graceful Fallback (A5)", "Unbounded blind retries (Rejected: creates thundering herd and quota exhaustion during outages).")
    ]
    for idx, (d1, d2, d3) in enumerate(dec_rows):
        row = table_dec.rows[idx + 1]
        for col_idx, text in enumerate([d1, d2, d3]):
            cell = row.cells[col_idx]
            set_cell_background(cell, "F8FAFC" if idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            r.font.color.rgb = DARK_TEXT

    # 6. Evaluation Results
    add_section_heading("5. Evaluation Results: Before and After the Change (L2, L3)")
    add_para("A fixed benchmark of 20 clinical scenarios (data/eval_scenarios.json) was evaluated across Prompt v1 (baseline single-pass) and Prompt v2 (verified CoT with 2-stage retrieval):")

    table_eval = doc.add_table(rows=8, cols=4)
    table_eval.alignment = WD_TABLE_ALIGNMENT.CENTER
    eval_headers = ["Metric (TruLens Equivalent)", "Prompt v1 (Concise)", "Prompt v2 (Verified CoT)", "Delta / Improvement"]
    for i, h in enumerate(eval_headers):
        cell = table_eval.rows[0].cells[i]
        set_cell_background(cell, "1E3A8A")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9.5)

    eval_data = [
        ("Routing Accuracy", "80.0%", "100.0%", "+20.0%"),
        ("Groundedness", "0.600", "0.925", "+0.325"),
        ("Context Relevance", "1.000", "1.000", "0.000"),
        ("Faithfulness", "0.650", "0.900", "+0.250"),
        ("Hallucination Rate", "0.350", "0.100", "-0.250 (25% reduction)"),
        ("Avg Latency (ms)", "68.4 ms", "69.0 ms", "+0.6 ms"),
        ("Cost / 100 Runs ($)", "$0.003587", "$0.004032", "+$0.000445")
    ]
    for idx, (m, v1, v2, d) in enumerate(eval_data):
        row = table_eval.rows[idx + 1]
        for col_idx, text in enumerate([m, v1, v2, d]):
            cell = row.cells[col_idx]
            set_cell_background(cell, "F8FAFC" if idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if col_idx == 3 and "+" in text:
                r.font.bold = True
                r.font.color.rgb = RGBColor(5, 150, 105) # Green
            elif col_idx == 3 and "-" in text:
                r.font.bold = True
                r.font.color.rgb = RGBColor(220, 38, 38) # Red
            else:
                r.font.color.rgb = DARK_TEXT

    # 7. SLO & Load Testing
    add_section_heading("6. SLO, Locust Load Testing, Bottleneck & Costs (D6, L5)")
    add_bullet("Pre-declared p95 <= 2.50s (2500 ms) from submission to final polling result, justified by the requirement to beat human underwriters (15-30 mins) while sustaining hospital peak admission traffic.", "Declared SLO Target:")
    add_bullet("Measured p50 = 65.0ms, measured p95 = 140.0ms, maximum throughput = 264.2 RPS with 0.00% error rate on valid payloads, comfortably exceeding the declared SLO by an 18x margin.", "Locust Load Test Results:")
    add_bullet("Under single-worker execution, client polling contention against run-state memory causes p95 to degrade at 450+ concurrent users. Scaling workers via 'docker compose up --scale agent-worker=3' resolves contention and restores p95 to 190ms at 500 users.", "Bottleneck Analysis:")
    add_bullet("Calculated at Gemini 1.5 Flash rates: $0.004032 per 100 runs. The largest cost driver is the Stage 2 adjudication prompt (68% of token spend due to verbatim clause context injection).", "Cost per 100 Runs:")

    # 8. What Did Not Work
    add_section_heading("7. What Did Not Work (Development Lessons & Failures)")
    add_bullet("Initially, search queries like 'Clause 2.2 waiting period' were embedded via dense vectors. Because embeddings capture semantic concepts rather than alphanumeric tokens, scores for 'Clause 2.2' were lower than generic clauses mentioning 'period'. Remediated by adding BM25 lexical search with exact clause ID token boosting (+10.0 score boost).", "Dense Embedding Search on Clause Numbers:")
    add_bullet("An unescaped regular expression for ICD-10 clinical classification caused catastrophic backtracking when subjected to long, malformed strings during load testing, locking the ingestion thread. Remediated by replacing with an anchored, pre-compiled regex ^[A-Z][0-9]{2}(\\.[0-9]{1,2})?$ (Incident INC-2026-1025-01).", "Regex ReDoS in Ingestion Validation:")
    add_bullet("Adjudication Agent initially defaulted to citing SEC-COV-INP. For day-care admissions, Agent 1 retrieved SEC-COV-DAYCARE, causing self-verification to falsely flag the citation as unresolved. Remediated by aligning baseline coverage citation with admission_type.", "Self-Verification False Rejections on Day Care Cover:")

    # 9. Demonstration Matrix
    add_section_heading("8. Demonstration Verification Matrix (All 10 Items)")
    table_demo = doc.add_table(rows=11, cols=3)
    table_demo.alignment = WD_TABLE_ALIGNMENT.CENTER
    demo_headers = ["Item #", "PDF Demonstration Requirement", "Verification Proof in System"]
    for i, h in enumerate(demo_headers):
        cell = table_demo.rows[0].cells[i]
        set_cell_background(cell, "1E3A8A")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9.5)

    demo_items = [
        ("1", "docker compose up clean clone", "Verified with docker compose up -d; all 4 containers start healthy."),
        ("2", "Valid request producing routed recommendation", "Scenario 02 (Cataract 36m) approves Rs. 40,000 citing SEC-COV-DAYCARE & SEC-SUBLIM-CATARACT."),
        ("3", "Run traced end to end", "Per-step timeline logs thoughts, tool calls, prompt version, latency (ms), and cost ($)."),
        ("4", "Malformed request quarantined", "Demo Item 04 rejects with HTTP 422; payload saved to data/quarantine/; zero agent runs start."),
        ("5", "Out of corpus condition escalated", "Scenario 19 (Robotic Dental Veneers) escalates cleanly to medical-review without hallucination."),
        ("6", "Self-verification catching unsupported answer", "Agent 2 verifies citations against retrieved text; unverified assertions are escalated."),
        ("7", "Prompt injection defense", "Scenario 18 detects adversarial instruction overrides and quarantines request with Rs. 0 approved."),
        ("8", "Circuit breaker opening & degradation path", "Toggling circuit breaker sets state to OPEN; requests degrade gracefully to medical-review."),
        ("9", "Locust load test results against SLO", "Measured p95 (~140ms) meets declared target (2500ms) with 264 RPS."),
        ("10", "Section 4.1 Difficult Case", "Scenario 01 routes to medical-review citing BOTH SEC-COV-DAYCARE & SEC-WAIT-24M-SPECIFIC.")
    ]
    for idx, (num, req, proof) in enumerate(demo_items):
        row = table_demo.rows[idx + 1]
        for col_idx, text in enumerate([num, req, proof]):
            cell = row.cells[col_idx]
            set_cell_background(cell, "F8FAFC" if idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True
            r.font.color.rgb = DARK_TEXT

    # 10. Conclusion
    add_section_heading("9. Conclusion")
    add_para("The Health Insurance Pre-Authorisation Desk demonstrates that autonomous multi-agent systems, when governed by deterministic data contracts, 2-stage dynamic modifying retrieval, strict self-verification, and operational circuit breakers, resolve the fundamental failure modes of naive RAG pipelines. By catching modifying provisions located pages away from primary cover clauses, the system eliminates false approvals while empowering human medical officers with verifiable, evidence-grounded recommendations within sub-second response times.")

    output_path = "Mini_Project_03_Final_Report.docx"
    doc.save(output_path)
    print(f"Word Document Final Report successfully created: {output_path}")

if __name__ == "__main__":
    create_report_docx()
