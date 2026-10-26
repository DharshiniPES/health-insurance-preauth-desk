import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from src.config import CORPUS_DIR, INDEX_DIR

def compute_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_index() -> Dict[str, Any]:
    """
    Idempotent corpus parser and index builder.
    Chunks policy wordings and daycare schedule into identifiable passages.
    """
    start_time = time.time()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    policy_file = CORPUS_DIR / "policy_wording.json"
    daycare_file = CORPUS_DIR / "daycare_procedures.json"

    if not policy_file.exists() or not daycare_file.exists():
        raise FileNotFoundError("Corpus files not found in data/corpus/.")

    policy_hash = compute_file_hash(policy_file)
    daycare_hash = compute_file_hash(daycare_file)

    chunks: List[Dict[str, Any]] = []

    # 1. Parse policy wording sections
    with open(policy_file, "r", encoding="utf-8") as f:
        policy_data = json.load(f)

    insurer = policy_data.get("policy_metadata", {}).get("insurer", "Unknown Insurer")
    policy_ver = policy_data.get("policy_metadata", {}).get("version", "1.0")

    for sec in policy_data.get("sections", []):
        chunks.append({
            "clause_id": sec["clause_id"],
            "title": sec["clause_title"],
            "category": sec["category"],
            "text": sec["text"],
            "metadata": {
                "source": "policy_wording",
                "insurer": insurer,
                "version": policy_ver
            }
        })

    # 2. Parse day care procedures schedule
    with open(daycare_file, "r", encoding="utf-8") as f:
        daycare_data = json.load(f)

    for proc in daycare_data.get("procedures", []):
        text_desc = (
            f"Day Care Procedure: {proc['name']} (Code: {proc['code']}, ICD-10: {proc['icd10']}, "
            f"Category: {proc['category']}). {proc['notes']}"
        )
        if proc.get("waiting_period_ref"):
            text_desc += f" Bound by waiting period clause: {proc['waiting_period_ref']}."
        if proc.get("sublimit_ref"):
            text_desc += f" Bound by sub-limit clause: {proc['sublimit_ref']}."

        chunks.append({
            "clause_id": proc["code"],
            "title": f"Day Care Procedure - {proc['name']}",
            "category": "daycare",
            "text": text_desc,
            "metadata": {
                "source": "daycare_procedures",
                "icd10": proc["icd10"],
                "waiting_period_ref": proc.get("waiting_period_ref"),
                "sublimit_ref": proc.get("sublimit_ref")
            }
        })

    elapsed = time.time() - start_time
    throughput_chunks_per_sec = len(chunks) / max(elapsed, 0.0001)

    index_output_path = INDEX_DIR / "corpus_index.json"
    with open(index_output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    metadata = {
        "built_at": datetime.utcnow().isoformat(),
        "total_chunks": len(chunks),
        "policy_version": policy_ver,
        "insurer": insurer,
        "file_hashes": {
            "policy_wording.json": policy_hash,
            "daycare_procedures.json": daycare_hash
        },
        "build_duration_sec": round(elapsed, 4),
        "throughput_chunks_per_sec": round(throughput_chunks_per_sec, 2),
        "chunking_strategy": "Clause-level semantic chunking with cross-referencing metadata (F4, L1)",
        "status": "FRESH"
    }

    meta_output_path = INDEX_DIR / "index_metadata.json"
    with open(meta_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == "__main__":
    meta = build_index()
    print("=" * 60)
    print("Corpus Indexing Completed Successfully (D2, L1)")
    print(f"Chunks Indexed: {meta['total_chunks']}")
    print(f"Data Freshness: {meta['built_at']}")
    print(f"Build Time:     {meta['build_duration_sec']}s")
    print(f"Throughput:     {meta['throughput_chunks_per_sec']} chunks/sec")
    print("=" * 60)
