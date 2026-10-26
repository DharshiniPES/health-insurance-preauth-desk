import json
import re
import uuid
from datetime import date, datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from src.config import QUARANTINE_DIR

ICD10_REGEX = re.compile(r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$")

class PreAuthRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:8].upper()}")
    policy_id: str = Field(..., min_length=3, max_length=50, description="Unique insurance policy number")
    policy_holder_name: str = Field(..., min_length=2, max_length=100)
    policy_issue_date: date = Field(..., description="Date on which the policy was first issued")
    policy_sum_insured: float = Field(..., gt=0, le=100_000_000, description="Total sum insured in INR")
    
    patient_name: str = Field(..., min_length=2, max_length=100)
    patient_age: int = Field(..., ge=0, le=120, description="Age of the patient")
    patient_gender: Literal["male", "female", "other"] = Field(...)
    
    hospital_name: str = Field(..., min_length=3, max_length=150)
    hospital_id: str = Field(..., min_length=3, max_length=50, description="ROHINI or Hospital Registry ID")
    
    admission_type: Literal["planned_surgical", "day_care", "emergency", "maternity"] = Field(...)
    admission_date: date = Field(...)
    discharge_date: date = Field(...)
    
    diagnosis: str = Field(..., min_length=3, max_length=500)
    icd10_code: str = Field(..., description="Standard ICD-10 clinical classification code")
    procedure_name: str = Field(..., min_length=3, max_length=500)
    
    estimated_cost: float = Field(..., gt=0, le=50_000_000, description="Total estimated hospitalization cost")
    room_category_requested: Literal[
        "general_ward", "twin_sharing", "single_private_ac", "deluxe", "suite", "icu", "day_care"
    ] = Field(...)
    daily_room_rent: float = Field(default=0.0, ge=0.0)
    ped_declared: List[str] = Field(default_factory=list, description="Pre-existing diseases declared at proposal")

    @field_validator("icd10_code")
    @classmethod
    def validate_icd10(cls, v: str) -> str:
        clean_code = v.strip().upper()
        if not ICD10_REGEX.match(clean_code):
            raise ValueError(f"Invalid ICD-10 code format '{v}'. Expected format like 'H25.9' or 'K40.9'")
        return clean_code

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "PreAuthRequest":
        # Cross-field Rule 1: Discharge date cannot be before admission date
        if self.discharge_date < self.admission_date:
            raise ValueError(f"Discharge date ({self.discharge_date}) cannot be before admission date ({self.admission_date})")

        # Cross-field Rule 2: Day-care admissions must have same-day discharge
        if self.admission_type == "day_care" and self.discharge_date != self.admission_date:
            raise ValueError(f"Day-care admission requires same-day discharge (admission: {self.admission_date}, discharge: {self.discharge_date})")

        # Cross-field Rule 3: Daily room rent cannot exceed total estimated cost
        if self.daily_room_rent > self.estimated_cost:
            raise ValueError(f"Daily room rent ({self.daily_room_rent}) cannot exceed total estimated hospitalisation cost ({self.estimated_cost})")

        # Cross-field Rule 4: Maternity admission gender & age validation
        if self.admission_type == "maternity":
            if self.patient_gender != "female":
                raise ValueError("Maternity admission requires patient gender to be 'female'")
            if self.patient_age < 18:
                raise ValueError(f"Maternity admission age must be >= 18 (got {self.patient_age})")

        # Cross-field Rule 5: Day care room rent should be 0
        if self.room_category_requested == "day_care" and self.daily_room_rent > 0:
            raise ValueError("Day care admissions cannot have daily room rent charges")

        return self


class Citation(BaseModel):
    clause_id: str
    clause_title: str
    text_snippet: str
    relevance_score: Optional[float] = 1.0


class AgentStepTrace(BaseModel):
    step_number: int
    agent_name: str
    action: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    thought: str
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class PreAuthRecommendation(BaseModel):
    run_id: str
    request_id: str
    status: Literal["COMPLETED", "FAILED", "QUARANTINED", "PROCESSING", "QUEUED"]
    route: Literal["approve-recommended", "query-to-hospital", "medical-review"]
    summary: str
    indicative_limit_inr: Optional[float] = None
    reason: str
    citations: List[Citation]
    self_verification_passed: bool
    escalation_path: Optional[str] = None
    prompt_version: str
    total_tokens: int
    total_cost_usd: float
    total_latency_ms: float
    steps: List[AgentStepTrace]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class QuarantineRecord(BaseModel):
    quarantine_id: str
    timestamp: str
    raw_payload: Dict[str, Any]
    validation_errors: List[Dict[str, Any]]
    status: str = "QUARANTINED"
    message: str = "Request rejected at ingestion boundary. No agent run was initiated."


def quarantine_payload(raw_payload: Dict[str, Any], errors: List[Dict[str, Any]]) -> QuarantineRecord:
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    qid = f"Q-{uuid.uuid4().hex[:8].upper()}"
    record = QuarantineRecord(
        quarantine_id=qid,
        timestamp=datetime.utcnow().isoformat(),
        raw_payload=raw_payload,
        validation_errors=errors
    )
    target_file = QUARANTINE_DIR / f"{qid}.json"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(record.model_dump_json(indent=2))
    return record


class FeedbackRequest(BaseModel):
    run_id: str
    satisfactory: bool
    reason: str
    medical_officer_id: Optional[str] = "MO-AUTO-01"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
