"""Validate per-agent runtime manifests used by the report workflow."""

from __future__ import annotations

from pathlib import Path

import yaml


EXPECTED_AGENT_MANIFESTS = {
    "chart": {
        "ref": "agents/chart-spec-agent/manifest.yaml",
        "name": "chart-spec-agent",
        "temperature": 0.0,
    },
    "controller": {
        "ref": "agents/report-text-controller/manifest.yaml",
        "name": "report-text-controller",
        "temperature": 0.0,
    },
    "writer": {
        "ref": "agents/report-text-editor/manifest.yaml",
        "name": "report-text-editor",
        "temperature": 0.0,
    },
    "reviewer": {
        "ref": "agents/report-text-adversarial-reviewer/manifest.yaml",
        "name": "report-text-adversarial-reviewer",
        "temperature": 0.2,
    },
    "assembler": {
        "ref": "agents/report-assembler/manifest.yaml",
        "name": "report-assembler",
        "temperature": 0.0,
    },
    "renderer": {
        "ref": "agents/html-report-renderer/manifest.yaml",
        "name": "html-report-renderer",
        "temperature": 0.0,
    },
}


def validate_manifest_data(data: object, role: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    expected = EXPECTED_AGENT_MANIFESTS[role]
    if not isinstance(data, dict):
        return False, [f"{role} manifest 必须是对象"]
    if data.get("name") != expected["name"]:
        errors.append(f"{role} manifest.name 必须为 {expected['name']}")
    if data.get("status") != "active":
        errors.append(f"{role} manifest.status 必须为 active")
    execution = data.get("execution")
    if not isinstance(execution, dict):
        errors.append(f"{role} manifest.execution 必须是对象")
    else:
        if execution.get("temperature") != expected["temperature"]:
            errors.append(
                f"{role} manifest.execution.temperature 必须为 {expected['temperature']}"
            )
        if execution.get("node_type") != "agent":
            errors.append(f"{role} manifest.execution.node_type 必须为 agent")
    if data.get("prompt_ref") != "SKILL.md":
        errors.append(f"{role} manifest.prompt_ref 必须为 SKILL.md")
    return not errors, errors


def load_and_validate_agent_manifests(
    skill_root: Path | None = None,
) -> tuple[bool, dict[str, dict], list[str]]:
    root = skill_root or Path(__file__).resolve().parent.parent
    manifests: dict[str, dict] = {}
    errors: list[str] = []
    for role, expected in EXPECTED_AGENT_MANIFESTS.items():
        path = root / expected["ref"]
        if not path.is_file():
            errors.append(f"缺少 {role} agent manifest：{expected['ref']}")
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"无法读取 {role} agent manifest：{exc}")
            continue
        ok, messages = validate_manifest_data(data, role)
        if not ok:
            errors.extend(messages)
            continue
        manifests[role] = data
    return not errors, manifests, errors


if __name__ == "__main__":
    import sys

    ok, _, messages = load_and_validate_agent_manifests()
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
