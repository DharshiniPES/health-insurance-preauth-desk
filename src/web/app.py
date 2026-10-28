import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from src.config import settings, QUARANTINE_DIR, BASE_DIR
from src.contracts import (
    PreAuthRequest,
    PreAuthRecommendation,
    QuarantineRecord,
    quarantine_payload,
    FeedbackRequest
)
from src.queue_runner import queue_runner
from src.metrics import metrics_tracker, generate_latest, CONTENT_TYPE_LATEST
from src.llm_provider import circuit_breaker
from src.vector_store import policy_index

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start asynchronous queue worker
    queue_runner.start()
    yield
    # Shutdown: Stop queue workers
    await queue_runner.stop()


app = FastAPI(
    title="Health Insurance Pre-Authorisation Desk",
    description="Multi-Agent Coverage Adjudication & Routing Service (UE24AM342AA5)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id_and_timing(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", f"CORR-{uuid.uuid4().hex[:8].upper()}")
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000.0
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# ------------------------------------------------------------------------------
# 1. Ingestion Boundary & Pre-Auth Submission (F1, F2, D1, A4)
# ------------------------------------------------------------------------------
@app.post(
    "/api/v1/preauth",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit pre-authorisation request",
    response_description="Returns run identifier immediately for asynchronous tracking"
)
async def submit_preauth(request: Request):
    """
    Accepts pre-authorisation requests over published data contract.
    Enforces schema, type, range, categorical, and cross-field validation at ingestion boundary.
    Quarantines rejected records immediately; agent run NEVER starts on invalid payloads.
    """
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body format.")

    # Ingestion boundary validation (D1, F2)
    try:
        preauth_req = PreAuthRequest.model_validate(raw_body)
    except ValidationError as ve:
        # Quarantine rejected payload
        metrics_tracker.record_quarantine()
        err_list = [{"field": ".".join(str(l) for l in err["loc"]), "msg": err["msg"]} for err in ve.errors()]
        quarantine_rec = quarantine_payload(raw_body, err_list)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "QUARANTINED",
                "message": "Validation failed at ingestion boundary. No agent run was initiated.",
                "quarantine_id": quarantine_rec.quarantine_id,
                "errors": err_list
            }
        )

    # Valid payload: Enqueue asynchronously (A4)
    run_id = await queue_runner.submit(preauth_req)
    return {
        "status": "QUEUED",
        "run_id": run_id,
        "request_id": preauth_req.request_id,
        "poll_url": f"/api/v1/preauth/{run_id}",
        "message": "Pre-authorisation request accepted. Execution dispatched to multi-agent worker."
    }


# ------------------------------------------------------------------------------
# 2. Polling Endpoint (A4)
# ------------------------------------------------------------------------------
@app.get("/api/v1/preauth/{run_id}", summary="Poll status of pre-auth execution")
async def get_preauth_status(run_id: str):
    """Poll run execution status and retrieve final coverage recommendation with full trace."""
    run_data = queue_runner.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail=f"Run identifier '{run_id}' not found.")

    res = {
        "run_id": run_id,
        "status": run_data["status"],
        "submitted_at": run_data["submitted_at"],
    }
    if run_data["status"] == "COMPLETED":
        res["result"] = run_data["result"]
    elif run_data["status"] == "FAILED":
        res["error"] = run_data["error"]

    return res


# ------------------------------------------------------------------------------
# 3. Human Feedback Endpoint (L6)
# ------------------------------------------------------------------------------
@app.post("/api/v1/feedback", summary="Submit medical officer feedback")
async def submit_feedback(fb: FeedbackRequest):
    """Allows caller/medical officer to mark result satisfactory or not, with reasons."""
    metrics_tracker.record_feedback(fb.run_id, fb.satisfactory, fb.reason)
    return {
        "status": "RECORDED",
        "run_id": fb.run_id,
        "satisfactory": fb.satisfactory,
        "message": "Feedback successfully logged into quality analytics."
    }

@app.get("/api/v1/feedback", summary="Retrieve all persisted medical officer feedback (L6)")
async def get_feedback():
    """Returns all persisted and aggregated feedback entries for quality monitoring."""
    return {
        "total_feedback": len(metrics_tracker.feedback_list),
        "satisfaction_rate_percent": metrics_tracker.get_summary_stats().get("satisfaction_rate_percent", 100.0),
        "entries": metrics_tracker.feedback_list
    }


# ------------------------------------------------------------------------------
# 4. Quarantine Inspector (D1)
# ------------------------------------------------------------------------------
@app.get("/api/v1/quarantine", summary="List quarantined invalid requests")
async def list_quarantine():
    """Lists quarantined records rejected at the ingestion boundary."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for f in QUARANTINE_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as qf:
                records.append(json.load(qf))
        except Exception:
            pass
    return {"quarantined_count": len(records), "records": records}


# ------------------------------------------------------------------------------
# 5. Health, Circuit Breaker & Admin Controls (F8, A5, D6)
# ------------------------------------------------------------------------------
@app.get("/health", summary="Health check endpoint")
async def health_check():
    return {
        "status": "HEALTHY",
        "uptime_seconds": metrics_tracker.get_uptime_seconds(),
        "circuit_breaker": {
            "state": circuit_breaker.state,
            "consecutive_failures": circuit_breaker.consecutive_failures,
            "force_open": circuit_breaker.force_open
        },
        "llm_provider": settings.LLM_PROVIDER,
        "prompt_version": settings.ACTIVE_PROMPT_VERSION
    }


@app.post("/api/v1/admin/circuit-breaker/toggle", summary="Toggle circuit breaker force open state (Demo Item 8)")
async def toggle_circuit_breaker(force_open: bool = Query(...)):
    """Simulates upstream provider failure to demonstrate circuit breaker opening & degradation path."""
    circuit_breaker.force_open = force_open
    if force_open:
        circuit_breaker.state = "OPEN"
    else:
        circuit_breaker.state = "CLOSED"
        circuit_breaker.consecutive_failures = 0
    return {
        "message": f"Circuit breaker force_open set to {force_open}",
        "current_state": circuit_breaker.state
    }


@app.get("/api/v1/stats", summary="Per-agent and pipeline statistics (A6)")
async def get_system_stats():
    """Returns task success rate, step/tool counts, latency p50/p95, tokens, and cost."""
    return metrics_tracker.get_summary_stats()


@app.get("/metrics", summary="Prometheus metrics scrape endpoint (D5)")
async def prometheus_metrics():
    """Exposes Prometheus metrics for Grafana scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ------------------------------------------------------------------------------
# 6. Web Client UI (A8)
# ------------------------------------------------------------------------------
static_dir = BASE_DIR / "src" / "web" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_html = static_dir / "index.html"
    if index_html.exists():
        with open(index_html, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Pre-Authorisation Desk API Running</h1><p>Visit /docs for Swagger API documentation.</p>"
