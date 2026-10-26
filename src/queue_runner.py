import asyncio
import time
import uuid
from typing import Dict, Any, Optional
from src.contracts import PreAuthRequest, PreAuthRecommendation
from src.agents.orchestrator import orchestrator
from src.metrics import metrics_tracker

class AsyncQueueRunner:
    """
    Asynchronous Queue and Task Runner (A4).
    Places a decouple queue between submission and execution to handle long-running agent reasoning.
    Provides immediate run_id with polling support.
    """
    def __init__(self, concurrency: int = 4):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.runs: Dict[str, Dict[str, Any]] = {}
        self.concurrency = concurrency
        self.workers: list = []
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            for i in range(self.concurrency):
                task = asyncio.create_task(self._worker_loop(i))
                self.workers.append(task)

    async def stop(self):
        self._running = False
        for task in self.workers:
            task.cancel()
        self.workers.clear()

    async def submit(self, request: PreAuthRequest) -> str:
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        self.runs[run_id] = {
            "run_id": run_id,
            "request_id": request.request_id,
            "status": "QUEUED",
            "submitted_at": time.time(),
            "request": request,
            "result": None,
            "error": None
        }
        await self.queue.put(run_id)
        metrics_tracker.increment_queued()
        return run_id

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.runs.get(run_id)

    async def _worker_loop(self, worker_id: int):
        while self._running:
            try:
                run_id = await self.queue.get()
                if run_id not in self.runs:
                    self.queue.task_done()
                    continue

                item = self.runs[run_id]
                item["status"] = "PROCESSING"
                item["started_at"] = time.time()
                metrics_tracker.increment_active()

                req: PreAuthRequest = item["request"]
                try:
                    recommendation = await orchestrator.run(req, run_id=run_id)
                    item["result"] = recommendation.model_dump()
                    item["status"] = "COMPLETED"
                    item["completed_at"] = time.time()
                    metrics_tracker.record_run_success(recommendation)
                except Exception as ex:
                    item["status"] = "FAILED"
                    item["error"] = str(ex)
                    metrics_tracker.record_run_failure()
                finally:
                    metrics_tracker.decrement_active()
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.1)


queue_runner = AsyncQueueRunner()
