import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

from app.models.workflow import WorkflowRun, WorkflowStep, WorkflowStatus, WorkflowStepStatus

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Abstract base for all FounderOS AI workflows."""

    name: str = "base_workflow"

    def __init__(self):
        self.run_id = str(uuid.uuid4())
        self.run = WorkflowRun(
            run_id=self.run_id,
            workflow_name=self.name,
            status=WorkflowStatus.PENDING,
        )

    async def execute(self, input_data: Dict[str, Any]) -> WorkflowRun:
        self.run.input_data = input_data
        self.run.status = WorkflowStatus.RUNNING
        self.run.started_at = datetime.now(timezone.utc)

        logger.info(f"[{self.name}] Starting run_id={self.run_id}")

        try:
            await self.run_steps(input_data)
            self.run.status = WorkflowStatus.COMPLETED
            logger.info(f"[{self.name}] Completed run_id={self.run_id}")
        except Exception as exc:
            self.run.status = WorkflowStatus.FAILED
            self.run.error = str(exc)
            logger.error(f"[{self.name}] Failed run_id={self.run_id}: {exc}")
            raise
        finally:
            self.run.completed_at = datetime.now(timezone.utc)

        return self.run

    @abstractmethod
    async def run_steps(self, input_data: Dict[str, Any]) -> None:
        """Subclasses implement the actual step sequence here."""
        ...

    async def run_step(self, step_id: str, step_name: str, coro) -> Any:
        """Execute a single named step and track its state."""
        step = WorkflowStep(step_id=step_id, name=step_name, status=WorkflowStepStatus.RUNNING)
        self.run.steps.append(step)

        start = datetime.now(timezone.utc)
        logger.info(f"[{self.name}] Step '{step_name}' started")

        try:
            result = await coro
            step.status = WorkflowStepStatus.COMPLETED
            step.output = result
            duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            step.duration_ms = int(duration)
            logger.info(f"[{self.name}] Step '{step_name}' completed in {step.duration_ms}ms")
            return result
        except Exception as exc:
            step.status = WorkflowStepStatus.FAILED
            step.error = str(exc)
            logger.error(f"[{self.name}] Step '{step_name}' failed: {exc}")
            raise
