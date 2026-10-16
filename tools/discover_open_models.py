#!/usr/bin/env python3
"""Discover public Hugging Face model candidates by task; never downloads model weights.

Usage:
  python tools/discover_open_models.py --output reports/open-model-discovery.json --per-task 100

The report is a candidate index, not a license approval or benchmark result.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASKS = [
    "text-generation", "image-text-to-text", "image-to-text", "text-to-image",
    "image-to-image", "text-to-video", "image-to-video", "automatic-speech-recognition",
    "text-to-speech", "text-to-audio", "audio-text-to-text", "feature-extraction",
    "text-ranking", "document-question-answering", "visual-question-answering",
    "depth-estimation", "image-segmentation", "object-detection",
]
API = "https://huggingface.co/api/models"


def fetch_task(task: str, limit: int, retries: int = 3) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({
        "pipeline_tag": task,
        "sort": "downloads",
        "direction": "-1",
        "limit": str(limit),
        "full": "true",
    })
    request = urllib.request.Request(
        f"{API}?{query}",
        headers={"User-Agent": "ia-open-model-discovery/1.0", "Accept": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            if not isinstance(payload, list):
                raise ValueError(f"Unexpected Hub response for task {task}")
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt + 1 == retries:
                raise RuntimeError(f"Hub discovery failed for {task}: {exc}") from exc
            time.sleep(2 ** attempt)
    return []


def normalize(item: dict[str, Any], task: str) -> dict[str, Any] | None:
    repo_id = item.get("id")
    if not isinstance(repo_id, str) or not repo_id or item.get("private") is True:
        return None
    card = item.get("cardData") or {}
    tags = item.get("tags") or []
    return {
        "repo_id": repo_id,
        "task": task,
        "pipeline_tag": item.get("pipeline_tag"),
        "license": card.get("license") or next(
            (tag.split(":", 1)[1] for tag in tags if isinstance(tag, str) and tag.startswith("license:")),
            None,
        ),
        "downloads": item.get("downloads"),
        "likes": item.get("likes"),
        "last_modified": item.get("lastModified"),
        "gated": item.get("gated", False),
        "library_name": item.get("library_name"),
        "tags": sorted(tag for tag in tags if isinstance(tag, str))[:80],
        "url": f"https://huggingface.co/{repo_id}",
        "license_audit": "REQUIRED",
        "benchmark_status": "NOT_RUN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/open-model-discovery.json")
    parser.add_argument("--per-task", type=int, default=100)
    parser.add_argument("--pause", type=float, default=0.15)
    args = parser.parse_args()
    if not 1 <= args.per_task <= 200:
        parser.error("--per-task must be between 1 and 200")
    if args.pause < 0:
        parser.error("--pause must be >= 0")

    by_id: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for task in TASKS:
        try:
            items = fetch_task(task, args.per_task)
            for item in items:
                record = normalize(item, task)
                if record is None:
                    continue
                previous = by_id.get(record["repo_id"])
                if previous:
                    previous["tasks"].append(task)
                    previous["tasks"] = sorted(set(previous["tasks"]))
                else:
                    record["tasks"] = [task]
                    by_id[record["repo_id"]] = record
        except Exception as exc:  # keep a partial report when one task endpoint fails
            errors.append({"task": task, "error": str(exc)})
        time.sleep(args.pause)

    models = sorted(
        by_id.values(),
        key=lambda row: (row.get("downloads") or 0, row["repo_id"]),
        reverse=True,
    )
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "public Hugging Face Hub API",
        "scope": {
            "tasks": TASKS,
            "per_task_limit": args.per_task,
            "weights_downloaded": False,
            "private_models_accessed": False,
        },
        "count": len(models),
        "license_policy": "Metadata is not legal approval. Audit the exact model card, license text, gated status, dataset provenance, and intended use before downloading, training on, or redistributing any artifact.",
        "benchmark_policy": "No model quality or superiority is inferred from downloads, likes, or this discovery report.",
        "task_errors": errors,
        "models": models,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Discovered {len(models)} public model candidates across {len(TASKS)} tasks.")
    print(f"Report: {output}")
    print(f"Task errors: {len(errors)}")
    return 0 if models else 1


if __name__ == "__main__":
    raise SystemExit(main())
