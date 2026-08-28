#!/usr/bin/env python3
"""Regression checks for per-agent temperature manifests."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from harness.agent_runtime_validator import (
    EXPECTED_AGENT_MANIFESTS,
    load_and_validate_agent_manifests,
    validate_manifest_data,
)


def main() -> int:
    errors: list[str] = []
    ok, _, messages = load_and_validate_agent_manifests(SKILL_DIR)
    if not ok:
        errors.append(f"live manifests failed: {messages}")

    for role, expected in EXPECTED_AGENT_MANIFESTS.items():
        valid = {
            "name": expected["name"],
            "status": "active",
            "execution": {
                "temperature": expected["temperature"],
                "node_type": "agent",
            },
            "prompt_ref": "SKILL.md",
        }
        drift = copy.deepcopy(valid)
        drift["execution"]["temperature"] = 0.7
        drift_ok, drift_messages = validate_manifest_data(drift, role)
        if drift_ok or not any("temperature 必须为" in item for item in drift_messages):
            errors.append(f"{role} temperature drift must fail")

    if errors:
        print("AGENT_RUNTIME_CONTRACT_TESTS_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("AGENT_RUNTIME_CONTRACT_TESTS_PASS: six live manifests and temperature drift gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
