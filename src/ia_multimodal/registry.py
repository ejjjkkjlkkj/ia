"""Safe in-process registry for explicit multimodal task handlers.

Handlers must be registered by trusted application code. This module never executes
shell commands, downloads models, opens arbitrary file paths, or accesses the network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class TaskStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_VALIDATED = "NOT_VALIDATED"


@dataclass(frozen=True)
class TaskRequest:
    request_id: str
    modality: str
    task: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    options: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            errors.append("request_id must be non-empty text")
        if not isinstance(self.modality, str) or not self.modality.strip():
            errors.append("modality must be non-empty text")
        if not isinstance(self.task, str) or not self.task.strip():
            errors.append("task must be non-empty text")
        if not isinstance(self.payload, Mapping):
            errors.append("payload must be a mapping")
        if not isinstance(self.options, Mapping):
            errors.append("options must be a mapping")
        return errors


@dataclass(frozen=True)
class TaskResult:
    request_id: str
    status: TaskStatus
    output: Any = None
    metrics: Mapping[str, float | int | str] = field(default_factory=dict)
    message: str = ""
    evidence: tuple[str, ...] = ()


Handler = Callable[[TaskRequest], TaskResult]


class CapabilityRegistry:
    """Explicit allow-list of installed task handlers."""

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], Handler] = {}

    @staticmethod
    def _key(modality: str, task: str) -> tuple[str, str]:
        return modality.strip().casefold(), task.strip().casefold()

    def register(self, modality: str, task: str, handler: Handler) -> None:
        if not isinstance(modality, str) or not modality.strip():
            raise ValueError("modality must be non-empty text")
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must be non-empty text")
        if not callable(handler):
            raise TypeError("handler must be callable")
        key = self._key(modality, task)
        if key in self._handlers:
            raise ValueError(f"handler already registered for {key[0]}/{key[1]}")
        self._handlers[key] = handler

    def capabilities(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._handlers))

    def dispatch(self, request: TaskRequest) -> TaskResult:
        if not isinstance(request, TaskRequest):
            return TaskResult(
                request_id="",
                status=TaskStatus.FAIL,
                message="request must be a TaskRequest instance",
            )
        errors = request.validate()
        if errors:
            return TaskResult(
                request_id=request.request_id if isinstance(request.request_id, str) else "",
                status=TaskStatus.FAIL,
                message="; ".join(errors),
            )
        key = self._key(request.modality, request.task)
        handler = self._handlers.get(key)
        if handler is None:
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.NOT_IMPLEMENTED,
                message=f"No handler registered for {key[0]}/{key[1]}",
            )
        try:
            result = handler(request)
        except Exception as exc:
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message=f"Handler raised {type(exc).__name__}",
            )
        if not isinstance(result, TaskResult):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler returned an invalid result type",
            )
        if result.request_id != request.request_id:
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler result request_id does not match request",
            )
        if not isinstance(result.status, TaskStatus):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler result contains an invalid status",
            )
        if not isinstance(result.metrics, Mapping):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler result metrics must be a mapping",
            )
        if not isinstance(result.message, str):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler result message must be text",
            )
        if not isinstance(result.evidence, (tuple, list)) or not all(
            isinstance(item, str) and item.strip() for item in result.evidence
        ):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.FAIL,
                message="Handler result evidence must be a sequence of non-empty strings",
            )
        return result
