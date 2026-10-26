import time
import json
from locust import HttpUser, task, between

SAMPLE_PAYLOADS = [
    {
        "policy_id": "POL-987456",
        "policy_holder_name": "Ramesh Sharma",
        "policy_issue_date": "2025-11-25",
        "policy_sum_insured": 500000.0,
        "patient_name": "Ramesh Sharma",
        "patient_age": 58,
        "patient_gender": "male",
        "hospital_name": "Narayana Nethralaya",
        "hospital_id": "ROHINI-BLR-0142",
        "admission_type": "day_care",
        "admission_date": "2026-10-25",
        "discharge_date": "2026-10-25",
        "diagnosis": "Senile immature cataract right eye",
        "icd10_code": "H25.9",
        "procedure_name": "Planned cataract surgery with phacoemulsification",
        "estimated_cost": 42000.0,
        "room_category_requested": "day_care",
        "daily_room_rent": 0.0,
        "ped_declared": []
    },
    {
        "policy_id": "POL-223388",
        "policy_holder_name": "Arjun Kapoor",
        "policy_issue_date": "2026-09-01",
        "policy_sum_insured": 1000000.0,
        "patient_name": "Arjun Kapoor",
        "patient_age": 49,
        "patient_gender": "male",
        "hospital_name": "Fortis Escorts Heart Institute",
        "hospital_id": "ROHINI-DEL-0119",
        "admission_type": "emergency",
        "admission_date": "2026-10-24",
        "discharge_date": "2026-10-28",
        "diagnosis": "Acute ST-elevation myocardial infarction anterior wall",
        "icd10_code": "I21.0",
        "procedure_name": "Emergency primary angioplasty with stent",
        "estimated_cost": 280000.0,
        "room_category_requested": "icu",
        "daily_room_rent": 18000.0,
        "ped_declared": []
    }
]

class PreAuthDeskLoadTest(HttpUser):
    """
    Locust Load Test Measuring End-to-End Run Latency (D6).
    Declared SLO Target: p95 <= 2.50 seconds (2500 ms) from submission to final polling result.
    Uses LLM Stub Mode with realistic async task runner.
    """
    wait_time = between(0.1, 0.5)

    @task(3)
    def submit_and_poll_preauth(self):
        import random
        payload = random.choice(SAMPLE_PAYLOADS)
        start_ts = time.time()

        # Step 1: Submit Pre-auth (202 Accepted)
        with self.client.post("/api/v1/preauth", json=payload, catch_response=True) as resp:
            if resp.status_code != 202:
                resp.failure(f"Expected 202, got {resp.status_code}")
                return
            data = resp.json()
            run_id = data.get("run_id")

        if not run_id:
            return

        # Step 2: Poll status until COMPLETED (or timeout after 10s)
        completed = False
        timeout = 10.0
        poll_interval = 0.05

        while time.time() - start_ts < timeout:
            with self.client.get(f"/api/v1/preauth/{run_id}", name="/api/v1/preauth/[run_id]", catch_response=True) as poll_resp:
                if poll_resp.status_code == 200:
                    pdata = poll_resp.json()
                    if pdata.get("status") == "COMPLETED":
                        completed = True
                        break
                    elif pdata.get("status") == "FAILED":
                        poll_resp.failure("Run status reported FAILED")
                        break
            time.sleep(poll_interval)

        total_duration = time.time() - start_ts

        # Validate against declared SLO (p95 < 2.5s)
        if not completed:
            self.environment.events.request.fire(
                request_type="END_TO_END_RUN",
                name="preauth_submission_to_completion",
                response_time=total_duration * 1000,
                response_length=0,
                exception=Exception("Polling timed out before completion")
            )
        else:
            self.environment.events.request.fire(
                request_type="END_TO_END_RUN",
                name="preauth_submission_to_completion",
                response_time=total_duration * 1000,
                response_length=1,
                exception=None
            )

    @task(1)
    def health_check(self):
        self.client.get("/health")
