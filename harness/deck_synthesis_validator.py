"""
Validate deck synthesis output before converting it to a PPTX handoff.

The synthesis output is the understanding layer between analytical findings and
slide rendering. It decides which findings become one slide and why.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "references" / "deck_synthesis_contract_schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_schema(schema_path: str | None = None) -> dict[str, Any]:
    return _read_json(Path(schema_path) if schema_path else DEFAULT_SCHEMA)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_source_ref(source_ref: Any, source_ids: set[str], path: str, errors: list[str]) -> None:
    if not _is_non_empty_string(source_ref):
        errors.append(f"{path} must be a non-empty source id")
    elif source_ref not in source_ids:
        errors.append(f"{path} references unknown source id: {source_ref}")


def _validate_list_of_strings(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty list")
        return []
    strings: list[str] = []
    for index, item in enumerate(value):
        if not _is_non_empty_string(item):
            errors.append(f"{path}[{index}] must be a non-empty string")
        else:
            strings.append(item)
    return strings


def _collect_sources(synthesis: dict[str, Any], errors: list[str]) -> set[str]:
    sources = synthesis.get("sources")
    ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return ids
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{path} must be an object")
            continue
        source_id = source.get("id")
        if not _is_non_empty_string(source_id):
            errors.append(f"{path}.id is required")
            continue
        if source_id in ids:
            errors.append(f"sources contains duplicate id: {source_id}")
        ids.add(source_id)
        if not _is_non_empty_string(source.get("label")):
            errors.append(f"{path}.label is required")
    return ids


def _collect_findings(
    synthesis: dict[str, Any],
    source_ids: set[str],
    schema: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    findings = synthesis.get("findings")
    by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(findings, list) or not findings:
        errors.append("findings must be a non-empty list")
        return by_id

    for index, finding in enumerate(findings):
        path = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in schema.get("required_finding_fields", []):
            if field not in finding:
                errors.append(f"{path}.{field} is required")
        finding_id = finding.get("id")
        if not _is_non_empty_string(finding_id):
            errors.append(f"{path}.id must be a non-empty string")
            continue
        if finding_id in by_id:
            errors.append(f"findings contains duplicate id: {finding_id}")
        by_id[finding_id] = finding
        if not _is_non_empty_string(finding.get("claim")):
            errors.append(f"{path}.claim must be a non-empty string")
        refs = finding.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{path}.evidence_refs must be a non-empty list")
        else:
            for ref_index, source_ref in enumerate(refs):
                _validate_source_ref(source_ref, source_ids, f"{path}.evidence_refs[{ref_index}]", errors)
    return by_id


def _validate_composition(
    composition: Any,
    slide_path: str,
    archetype: str,
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(composition, dict):
        errors.append(f"{slide_path}.composition must be an object")
        return
    sections = composition.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append(f"{slide_path}.composition.sections must be a non-empty list")
        return

    role_counts: dict[str, int] = {}
    max_len = schema.get("quality_limits", {}).get("section_content_max_chars", 10_000)
    for index, section in enumerate(sections):
        path = f"{slide_path}.composition.sections[{index}]"
        if not isinstance(section, dict):
            errors.append(f"{path} must be an object")
            continue
        role = section.get("role")
        if not _is_non_empty_string(role):
            errors.append(f"{path}.role is required")
            continue
        role_counts[role] = role_counts.get(role, 0) + 1
        if not _is_non_empty_string(section.get("title")):
            errors.append(f"{path}.title is required")
        content = section.get("content")
        if content is not None and isinstance(content, str) and len(content) > max_len:
            warnings.append(f"{path}.content may be too long for a PPT container")

    archetype_rule = schema.get("archetype_rules", {}).get(archetype, {})
    min_driver_cards = archetype_rule.get("min_driver_cards")
    if min_driver_cards is not None and role_counts.get("driver_card", 0) < min_driver_cards:
        errors.append(f"{slide_path}.composition needs at least {min_driver_cards} driver_card sections")


def _validate_interpretation_packet(
    packet: Any,
    slide: dict[str, Any],
    slide_path: str,
    findings_by_id: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(packet, dict):
        errors.append(f"{slide_path}.interpretation_packet must be an object")
        return

    for field in schema.get("required_interpretation_packet_fields", []):
        if field not in packet:
            errors.append(f"{slide_path}.interpretation_packet.{field} is required")

    for field in ("page_question", "audience_decision", "story_pattern"):
        if field in packet and not _is_non_empty_string(packet.get(field)):
            errors.append(f"{slide_path}.interpretation_packet.{field} must be a non-empty string")

    story_pattern = packet.get("story_pattern")
    if story_pattern and story_pattern not in schema.get("allowed_story_patterns", []):
        errors.append(f"{slide_path}.interpretation_packet.story_pattern is unsupported: {story_pattern}")

    included_findings = set(slide.get("included_findings") or [])
    allowed_roles = set(schema.get("allowed_finding_roles", []))
    role_refs: set[str] = set()
    finding_roles = packet.get("finding_roles")
    if not isinstance(finding_roles, list) or not finding_roles:
        errors.append(f"{slide_path}.interpretation_packet.finding_roles must be a non-empty list")
    else:
        for index, role_item in enumerate(finding_roles):
            item_path = f"{slide_path}.interpretation_packet.finding_roles[{index}]"
            if not isinstance(role_item, dict):
                errors.append(f"{item_path} must be an object")
                continue
            finding_ref = role_item.get("finding_ref")
            role = role_item.get("role")
            if not _is_non_empty_string(finding_ref):
                errors.append(f"{item_path}.finding_ref must be a non-empty finding id")
            elif finding_ref not in findings_by_id:
                errors.append(f"{item_path}.finding_ref references unknown finding id: {finding_ref}")
            elif finding_ref not in included_findings:
                errors.append(f"{item_path}.finding_ref must be included in the slide")
            else:
                role_refs.add(finding_ref)
            if not _is_non_empty_string(role):
                errors.append(f"{item_path}.role must be a non-empty string")
            elif allowed_roles and role not in allowed_roles:
                errors.append(f"{item_path}.role is unsupported: {role}")

    missing_role_refs = sorted(included_findings - role_refs)
    if missing_role_refs:
        errors.append(f"{slide_path}.interpretation_packet.finding_roles must cover included findings: {missing_role_refs}")

    _validate_list_of_strings(
        packet.get("required_evidence"),
        f"{slide_path}.interpretation_packet.required_evidence",
        errors,
    )

    missing_requests = packet.get("missing_evidence_requests")
    if not isinstance(missing_requests, list):
        errors.append(f"{slide_path}.interpretation_packet.missing_evidence_requests must be a list")
        missing_requests = []
    else:
        for index, request in enumerate(missing_requests):
            request_path = f"{slide_path}.interpretation_packet.missing_evidence_requests[{index}]"
            _validate_missing_evidence_request(request, request_path, schema, errors)

    analysis_request = packet.get("analysis_agent_request")
    if not isinstance(analysis_request, dict):
        errors.append(f"{slide_path}.interpretation_packet.analysis_agent_request must be an object")
        return

    status = analysis_request.get("status")
    if status not in schema.get("allowed_analysis_agent_request_statuses", []):
        errors.append(f"{slide_path}.interpretation_packet.analysis_agent_request.status is unsupported: {status}")
    if analysis_request.get("request_mode") != "single_batch":
        errors.append(f"{slide_path}.interpretation_packet.analysis_agent_request.request_mode must be single_batch")
    if analysis_request.get("owner") != "data-analysis-report-agent":
        errors.append(f"{slide_path}.interpretation_packet.analysis_agent_request.owner must be data-analysis-report-agent")

    requests = analysis_request.get("requests")
    if not isinstance(requests, list):
        errors.append(f"{slide_path}.interpretation_packet.analysis_agent_request.requests must be a list")
        requests = []
    else:
        for index, request in enumerate(requests):
            request_path = f"{slide_path}.interpretation_packet.analysis_agent_request.requests[{index}]"
            _validate_missing_evidence_request(request, request_path, schema, errors)

    if missing_requests:
        if status != "needs_analysis_refresh":
            errors.append(
                f"{slide_path}.interpretation_packet.analysis_agent_request.status "
                "must be needs_analysis_refresh when missing evidence exists"
            )
        if not requests:
            errors.append(
                f"{slide_path}.interpretation_packet.analysis_agent_request.requests "
                "must include the consolidated evidence request"
            )
        if len(requests) < len(missing_requests):
            warnings.append(
                f"{slide_path}.interpretation_packet.analysis_agent_request.requests "
                "may not cover every missing evidence item"
            )
        review_checks = (slide.get("review_packet") or {}).get("review_checks")
        if isinstance(review_checks, list):
            statuses = {check.get("status") for check in review_checks if isinstance(check, dict)}
            if not statuses.intersection({"blocked", "needs_review"}):
                errors.append(
                    f"{slide_path}.review_packet.review_checks must include blocked or needs_review "
                    "when missing evidence exists"
                )
        errors.append(
            f"{slide_path} contains missing evidence requests; return to data-analysis-report-agent "
            "before PPTX handoff"
        )
    else:
        if status != "not_needed":
            errors.append(
                f"{slide_path}.interpretation_packet.analysis_agent_request.status "
                "must be not_needed when there is no missing evidence"
            )
        if requests:
            errors.append(
                f"{slide_path}.interpretation_packet.analysis_agent_request.requests "
                "must be empty when there is no missing evidence"
            )


def _validate_missing_evidence_request(
    request: Any,
    request_path: str,
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    if not isinstance(request, dict):
        errors.append(f"{request_path} must be an object")
        return
    for field in schema.get("required_missing_evidence_request_fields", []):
        if field not in request:
            errors.append(f"{request_path}.{field} is required")
    for field in ("need", "why_needed", "suggested_analysis_question", "expected_finding_role"):
        if field in request and not _is_non_empty_string(request.get(field)):
            errors.append(f"{request_path}.{field} must be a non-empty string")
    if request.get("expected_finding_role") and request["expected_finding_role"] not in schema.get("allowed_finding_roles", []):
        errors.append(f"{request_path}.expected_finding_role is unsupported: {request['expected_finding_role']}")
    if "required_fields" in request:
        _validate_list_of_strings(request.get("required_fields"), f"{request_path}.required_fields", errors)


def _validate_review_packet(
    review_packet: Any,
    slide: dict[str, Any],
    slide_path: str,
    archetype: str,
    source_ids: set[str],
    findings_by_id: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(review_packet, dict):
        errors.append(f"{slide_path}.review_packet must be an object")
        return

    for field in schema.get("required_review_packet_fields", []):
        if field not in review_packet:
            errors.append(f"{slide_path}.review_packet.{field} is required")

    max_summary_len = schema.get("quality_limits", {}).get("review_summary_max_chars", 10_000)
    for index, summary in enumerate(_validate_list_of_strings(review_packet.get("review_summary"), f"{slide_path}.review_packet.review_summary", errors)):
        if len(summary) > max_summary_len:
            warnings.append(f"{slide_path}.review_packet.review_summary[{index}] may be too long for human review")

    included_findings = set(slide.get("included_findings") or [])
    evidence_rows = review_packet.get("evidence_table")
    evidence_finding_refs: set[str] = set()
    if not isinstance(evidence_rows, list) or not evidence_rows:
        errors.append(f"{slide_path}.review_packet.evidence_table must be a non-empty list")
    else:
        for index, row in enumerate(evidence_rows):
            row_path = f"{slide_path}.review_packet.evidence_table[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{row_path} must be an object")
                continue
            for field in schema.get("required_evidence_row_fields", []):
                if field not in row:
                    errors.append(f"{row_path}.{field} is required")
            finding_ref = row.get("finding_ref")
            if not _is_non_empty_string(finding_ref):
                errors.append(f"{row_path}.finding_ref must be a non-empty finding id")
            elif finding_ref not in findings_by_id:
                errors.append(f"{row_path}.finding_ref references unknown finding id: {finding_ref}")
            else:
                evidence_finding_refs.add(finding_ref)
            _validate_source_ref(row.get("source_ref"), source_ids, f"{row_path}.source_ref", errors)
            for field in ("label", "value", "unit", "interpretation"):
                if field in row and not _is_non_empty_string(str(row.get(field))):
                    errors.append(f"{row_path}.{field} must be non-empty")

    missing_evidence = sorted(included_findings - evidence_finding_refs)
    if missing_evidence:
        errors.append(f"{slide_path}.review_packet.evidence_table must cover included findings: {missing_evidence}")

    cause_cards = review_packet.get("cause_cards")
    cause_finding_refs: set[str] = set()
    if not isinstance(cause_cards, list) or not cause_cards:
        errors.append(f"{slide_path}.review_packet.cause_cards must be a non-empty list")
    else:
        for index, card in enumerate(cause_cards):
            card_path = f"{slide_path}.review_packet.cause_cards[{index}]"
            if not isinstance(card, dict):
                errors.append(f"{card_path} must be an object")
                continue
            for field in schema.get("required_cause_card_fields", []):
                if field not in card:
                    errors.append(f"{card_path}.{field} is required")
            finding_ref = card.get("finding_ref")
            if not _is_non_empty_string(finding_ref):
                errors.append(f"{card_path}.finding_ref must be a non-empty finding id")
            elif finding_ref not in findings_by_id:
                errors.append(f"{card_path}.finding_ref references unknown finding id: {finding_ref}")
            else:
                cause_finding_refs.add(finding_ref)
            _validate_source_ref(card.get("evidence_ref"), source_ids, f"{card_path}.evidence_ref", errors)
            for field in ("cause", "data_point", "mechanism"):
                if field in card and not _is_non_empty_string(card.get(field)):
                    errors.append(f"{card_path}.{field} must be non-empty")
            chart_binding = card.get("chart_binding")
            if not isinstance(chart_binding, dict) or not _is_non_empty_string(chart_binding.get("chart_id")):
                errors.append(f"{card_path}.chart_binding.chart_id is required")

    archetype_rule = schema.get("archetype_rules", {}).get(archetype, {})
    min_cards = archetype_rule.get("min_driver_cards")
    if min_cards is not None and len(cause_cards or []) < min_cards:
        errors.append(f"{slide_path}.review_packet.cause_cards needs at least {min_cards} cards for {archetype}")

    chart_plans = review_packet.get("chart_plan")
    chart_ids: set[str] = set()
    if not isinstance(chart_plans, list) or not chart_plans:
        errors.append(f"{slide_path}.review_packet.chart_plan must be a non-empty list")
    else:
        for index, chart in enumerate(chart_plans):
            chart_path = f"{slide_path}.review_packet.chart_plan[{index}]"
            if not isinstance(chart, dict):
                errors.append(f"{chart_path} must be an object")
                continue
            for field in schema.get("required_chart_plan_fields", []):
                if field not in chart:
                    errors.append(f"{chart_path}.{field} is required")
            chart_id = chart.get("chart_id")
            if not _is_non_empty_string(chart_id):
                errors.append(f"{chart_path}.chart_id must be non-empty")
            else:
                chart_ids.add(chart_id)
            chart_type = chart.get("type")
            if chart_type and chart_type not in schema.get("allowed_chart_types", []):
                errors.append(f"{chart_path}.type is unsupported: {chart_type}")
            _validate_source_ref(chart.get("source_ref"), source_ids, f"{chart_path}.source_ref", errors)
            if "data_fields" in chart:
                _validate_list_of_strings(chart.get("data_fields"), f"{chart_path}.data_fields", errors)
            if "annotations" in chart and not isinstance(chart.get("annotations"), list):
                errors.append(f"{chart_path}.annotations must be a list")
            if not _is_non_empty_string(chart.get("message")):
                errors.append(f"{chart_path}.message must be non-empty")

    if isinstance(cause_cards, list):
        for index, card in enumerate(cause_cards):
            if isinstance(card, dict) and isinstance(card.get("chart_binding"), dict):
                chart_id = card["chart_binding"].get("chart_id")
                if _is_non_empty_string(chart_id) and chart_id not in chart_ids:
                    errors.append(f"{slide_path}.review_packet.cause_cards[{index}].chart_binding references unknown chart_id: {chart_id}")

    min_evidence = archetype_rule.get("min_evidence_rows")
    if min_evidence is not None and len(evidence_rows or []) < min_evidence:
        errors.append(f"{slide_path}.review_packet.evidence_table needs at least {min_evidence} rows for {archetype}")
    min_charts = archetype_rule.get("min_chart_plans")
    if min_charts is not None and len(chart_plans or []) < min_charts:
        errors.append(f"{slide_path}.review_packet.chart_plan needs at least {min_charts} chart plans for {archetype}")

    layout = review_packet.get("layout_blueprint")
    if not isinstance(layout, dict):
        errors.append(f"{slide_path}.review_packet.layout_blueprint must be an object")
    else:
        density = layout.get("density_level")
        if density not in schema.get("allowed_density_levels", []):
            errors.append(f"{slide_path}.review_packet.layout_blueprint.density_level is unsupported: {density}")
        zones = layout.get("zones")
        if not isinstance(zones, list) or not zones:
            errors.append(f"{slide_path}.review_packet.layout_blueprint.zones must be a non-empty list")
        else:
            for index, zone in enumerate(zones):
                zone_path = f"{slide_path}.review_packet.layout_blueprint.zones[{index}]"
                if not isinstance(zone, dict):
                    errors.append(f"{zone_path} must be an object")
                    continue
                for field in ("zone_id", "role", "content_refs"):
                    if field not in zone:
                        errors.append(f"{zone_path}.{field} is required")
                if "content_refs" in zone:
                    _validate_list_of_strings(zone.get("content_refs"), f"{zone_path}.content_refs", errors)

    checks = review_packet.get("review_checks")
    if not isinstance(checks, list) or not checks:
        errors.append(f"{slide_path}.review_packet.review_checks must be a non-empty list")
    else:
        for index, check in enumerate(checks):
            check_path = f"{slide_path}.review_packet.review_checks[{index}]"
            if not isinstance(check, dict):
                errors.append(f"{check_path} must be an object")
                continue
            if not _is_non_empty_string(check.get("question")):
                errors.append(f"{check_path}.question is required")
            if check.get("status") not in {"pass", "needs_review", "blocked"}:
                errors.append(f"{check_path}.status must be pass, needs_review, or blocked")


def _validate_output_slide_contract(
    contract: Any,
    slide: dict[str, Any],
    slide_path: str,
    source_ids: set[str],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(contract, dict):
        errors.append(f"{slide_path}.output_slide_contract must be an object")
        return

    for field in schema.get("required_output_slide_contract_fields", []):
        if field not in contract:
            errors.append(f"{slide_path}.output_slide_contract.{field} is required")
        elif field not in {"evidence_refs"} and not _is_non_empty_string(contract.get(field)):
            errors.append(f"{slide_path}.output_slide_contract.{field} must be a non-empty string")

    if contract.get("synthesis_ref") != slide.get("id"):
        errors.append(f"{slide_path}.output_slide_contract.synthesis_ref must equal the synthesis slide id")

    layout = contract.get("layout")
    if layout and layout not in schema.get("allowed_output_layouts", []):
        errors.append(f"{slide_path}.output_slide_contract.layout is unsupported: {layout}")
    visual_mode = contract.get("visual_mode")
    if visual_mode and visual_mode not in schema.get("allowed_visual_modes", []):
        errors.append(f"{slide_path}.output_slide_contract.visual_mode is unsupported: {visual_mode}")

    archetype = slide.get("layout_archetype")
    recommended = schema.get("archetype_rules", {}).get(archetype, {}).get("recommended_output_layouts", [])
    if recommended and layout not in recommended:
        warnings.append(f"{slide_path}.output_slide_contract.layout is not a recommended layout for {archetype}")

    refs = contract.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        errors.append(f"{slide_path}.output_slide_contract.evidence_refs must be a non-empty list")
    else:
        for index, source_ref in enumerate(refs):
            _validate_source_ref(source_ref, source_ids, f"{slide_path}.output_slide_contract.evidence_refs[{index}]", errors)


def _validate_slide(
    slide: Any,
    index: int,
    source_ids: set[str],
    findings_by_id: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    slide_path = f"slides[{index}]"
    if not isinstance(slide, dict):
        errors.append(f"{slide_path} must be an object")
        return

    for field in schema.get("required_slide_fields", []):
        if field not in slide:
            errors.append(f"{slide_path}.{field} is required")

    for field in ("id", "slide_goal", "primary_claim", "layout_archetype", "merge_logic"):
        if field in slide and not _is_non_empty_string(slide.get(field)):
            errors.append(f"{slide_path}.{field} must be a non-empty string")

    archetype = slide.get("layout_archetype")
    if archetype and archetype not in schema.get("allowed_layout_archetypes", []):
        errors.append(f"{slide_path}.layout_archetype is unsupported: {archetype}")

    included = slide.get("included_findings")
    if not isinstance(included, list) or not included:
        errors.append(f"{slide_path}.included_findings must be a non-empty list")
        included = []
    else:
        max_findings = schema.get("quality_limits", {}).get("max_findings_per_slide", 99)
        if len(included) > max_findings:
            warnings.append(f"{slide_path}.included_findings has many findings; consider splitting the slide")
        for finding_index, finding_id in enumerate(included):
            if finding_id not in findings_by_id:
                errors.append(f"{slide_path}.included_findings[{finding_index}] references unknown finding id: {finding_id}")

    archetype_rule = schema.get("archetype_rules", {}).get(archetype, {})
    min_findings = archetype_rule.get("min_included_findings")
    if min_findings is not None and len(included) < min_findings:
        errors.append(f"{slide_path}.included_findings needs at least {min_findings} findings for {archetype}")
    if len(included) > 1 and not _is_non_empty_string(slide.get("merge_logic")):
        errors.append(f"{slide_path}.merge_logic is required when merging multiple findings")

    refs = slide.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        errors.append(f"{slide_path}.evidence_refs must be a non-empty list")
        refs = []
    else:
        for ref_index, source_ref in enumerate(refs):
            _validate_source_ref(source_ref, source_ids, f"{slide_path}.evidence_refs[{ref_index}]", errors)

    for finding_id in included:
        finding = findings_by_id.get(finding_id)
        if not finding:
            continue
        missing = [ref for ref in finding.get("evidence_refs", []) if ref not in refs]
        if missing:
            errors.append(f"{slide_path}.evidence_refs must include evidence from {finding_id}: {missing}")

    max_claim = schema.get("quality_limits", {}).get("primary_claim_max_chars", 10_000)
    claim = slide.get("primary_claim")
    if isinstance(claim, str) and len(claim) > max_claim:
        warnings.append(f"{slide_path}.primary_claim may be too long for a PPT headline")

    _validate_interpretation_packet(
        slide.get("interpretation_packet"),
        slide,
        slide_path,
        findings_by_id,
        schema,
        errors,
        warnings,
    )
    _validate_review_packet(
        slide.get("review_packet"),
        slide,
        slide_path,
        archetype,
        source_ids,
        findings_by_id,
        schema,
        errors,
        warnings,
    )
    _validate_composition(slide.get("composition"), slide_path, archetype, schema, errors, warnings)
    _validate_output_slide_contract(
        slide.get("output_slide_contract"),
        slide,
        slide_path,
        source_ids,
        schema,
        errors,
        warnings,
    )


def validate_deck_synthesis(
    synthesis: dict[str, Any],
    schema_path: str | None = None,
) -> tuple[bool, list[str]]:
    """Return `(ok, messages)` for a deck synthesis JSON object."""

    schema = _load_schema(schema_path)
    errors: list[str] = []
    warnings: list[str] = []

    for field in schema.get("required_top_level", []):
        if field not in synthesis:
            errors.append(f"{field} is required")
        elif field not in {"sources", "findings", "slides"} and not _is_non_empty_string(synthesis.get(field)):
            errors.append(f"{field} must be a non-empty string")

    if synthesis.get("synthesis_version") != schema.get("synthesis_version"):
        errors.append(f"synthesis_version must be {schema.get('synthesis_version')}")
    if synthesis.get("deck_goal") and synthesis["deck_goal"] not in schema.get("allowed_deck_goals", []):
        errors.append(f"deck_goal is unsupported: {synthesis['deck_goal']}")
    if synthesis.get("audience") and synthesis["audience"] not in schema.get("allowed_audiences", []):
        errors.append(f"audience is unsupported: {synthesis['audience']}")

    source_ids = _collect_sources(synthesis, errors)
    findings_by_id = _collect_findings(synthesis, source_ids, schema, errors)

    slides = synthesis.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("slides must be a non-empty list")
    else:
        slide_ids: set[str] = set()
        for index, slide in enumerate(slides):
            if isinstance(slide, dict):
                slide_id = slide.get("id")
                if _is_non_empty_string(slide_id):
                    if slide_id in slide_ids:
                        errors.append(f"slides contains duplicate id: {slide_id}")
                    slide_ids.add(slide_id)
            _validate_slide(slide, index, source_ids, findings_by_id, schema, errors, warnings)

    messages = errors + [f"WARNING: {warning}" for warning in warnings]
    return len(errors) == 0, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a deck synthesis JSON file.")
    parser.add_argument("synthesis_json", help="Path to a deck synthesis JSON file.")
    parser.add_argument("--schema", help="Optional contract schema/config JSON path.")
    args = parser.parse_args()

    synthesis = _read_json(Path(args.synthesis_json))
    ok, messages = validate_deck_synthesis(synthesis, args.schema)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
