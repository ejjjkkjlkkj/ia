"""Local, dependency-free multimodal task routing primitives.

This package is infrastructure only. It does not provide image/audio/video models;
unregistered capabilities return NOT_IMPLEMENTED instead of simulating success.
"""
from .registry import CapabilityRegistry, TaskRequest, TaskResult, TaskStatus

__all__ = ["CapabilityRegistry", "TaskRequest", "TaskResult", "TaskStatus"]
