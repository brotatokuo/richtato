"""Persistent per-institution run state.

Stored as a single JSON file under `local_data/automation/state.json` so the
automation container and host-side tools can both inspect it without a database.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger


@dataclass
class InstitutionState:
    last_success: str | None = None
    last_success_file: str | None = None
    last_failure: str | None = None
    last_failure_reason: str | None = None
    consecutive_failures: int = 0


@dataclass
class RunState:
    institutions: dict[str, InstitutionState] = field(default_factory=dict)

    def get(self, institution: str) -> InstitutionState:
        return self.institutions.setdefault(institution, InstitutionState())

    def record_success(self, institution: str, downloaded_path: Path) -> None:
        entry = self.get(institution)
        entry.last_success = datetime.now(timezone.utc).isoformat()
        entry.last_success_file = str(downloaded_path)
        entry.last_failure = None
        entry.last_failure_reason = None
        entry.consecutive_failures = 0

    def record_failure(self, institution: str, reason: str) -> None:
        entry = self.get(institution)
        entry.last_failure = datetime.now(timezone.utc).isoformat()
        entry.last_failure_reason = reason
        entry.consecutive_failures += 1


def load_state(path: Path) -> RunState:
    if not path.exists():
        return RunState()
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read state file {}: {}; starting fresh", path, exc)
        return RunState()

    institutions = {
        slug: InstitutionState(**data)
        for slug, data in raw.get("institutions", {}).items()
    }
    return RunState(institutions=institutions)


def save_state(state: RunState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "institutions": {
            slug: asdict(entry) for slug, entry in state.institutions.items()
        }
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
