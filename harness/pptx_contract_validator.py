"""
Validate the data-analysis-to-PPTX handoff contract.

This validator checks the upstream report/deck JSON before it is handed to the
editable PPTX renderer. It does not render slides and does not call LLMs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "references" / "pptx_deck_contract_schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_schema(schema_path: str | None = None) -> dict[str, Any]:
    return _read_json(Path(schema_path) if schema_path else DEFAULT_SCHEMA)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_path(obj: dict[str, Any], dotted_path: str) -> bool:
    current: Any = obj
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    if isinstance(current, list):
        return len(current) > 0
    if isinstance(current, str):
        return bool(current.strip())
    return current is not None


def _source_ids(deck: dict[str, Any], errors: list[str]) -> set[str]:
    sources = deck.get("sources")
    ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return ids

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        source_id = source.get("id")
        if not _is_non_empty_string(source_id):
            errors.append(f"sources[{index}].id is required")
            continue
        if source_id in ids:
            errors.append(f"sources contains duplicate id: {source_id}")
        ids.add(source_id)
        if not _is_non_empty_string(source.get("label")):
            errors.append(f"sources[{index}].label is required")
    return ids


def _validate_text_lengths(
    slide: dict[str, Any],
    slide_path: str,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    limits = schema.get("quality_limits", {})
    title = slide.get("title", "")
    claim = slide.get("claim", "")
    if isinstance(title, str) and len(title) > limits.get("slide_title_max_chars", 10_000):
        warnings.append(f"{slide_path}.title is long; split subtitle or shorten for PPT fit")
    if isinstance(claim, str) and len(claim) > limits.get("claim_max_chars", 10_000):
        warnings.append(f"{slide_path}.claim is long; keep one sentence for slide execution")


def _validate_source_ref(
    source_ref: Any,
    source_ids: set[str],
    path: str,
    errors: list[str],
) -> None:
    if not _is_non_empty_string(source_ref):
        errors.append(f"{path} must be a non-empty source id")
    elif source_ref not in source_ids:
        errors.append(f"{path} references unknown source id: {source_ref}")


def _validate_chart(
    chart: Any,
    path: str,
    source_ids: set[str],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(chart, dict):
        errors.append(f"{path} must be an object")
        return

    for field in schema.get("native_chart_required_fields", []):
        if field not in chart:
            errors.append(f"{path}.{field} is required for editable chart data")

    chart_type = chart.get("type")
    if chart_type and chart_type not in schema.get("chart_types", []):
        errors.append(f"{path}.type is not supported: {chart_type}")

    labels = chart.get("labels")
    if not isinstance(labels, list) or not labels:
        errors.append(f"{path}.labels must be a non-empty list")
        labels = []
    elif not all(_is_non_empty_string(label) for label in labels):
        errors.append(f"{path}.labels must contain non-empty strings")

    series = chart.get("series")
    if not isinstance(series, list) or not series:
        errors.append(f"{path}.series must be a non-empty list")
        series = []

    label_count = len(labels)
    for s_index, item in enumerate(series):
        item_path = f"{path}.series[{s_index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        if not _is_non_empty_string(item.get("name")):
            errors.append(f"{item_path}.name is required")
        values = item.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"{item_path}.values must be a non-empty list")
            continue
        if label_count and len(values) != label_count:
            errors.append(f"{item_path}.values length must match labels length")
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            errors.append(f"{item_path}.values must contain numbers")

    if "source_ref" in chart:
        _validate_source_ref(chart.get("source_ref"), source_ids, f"{path}.source_ref", errors)

    label_set = set(labels)
    for h_index, label in enumerate(chart.get("highlight_labels") or []):
        if label not in label_set:
            errors.append(f"{path}.highlight_labels[{h_index}] is not in labels: {label}")

    for r_index, reference in enumerate(chart.get("reference_lines") or []):
        ref_path = f"{path}.reference_lines[{r_index}]"
        if not isinstance(reference, dict):
            errors.append(f"{ref_path} must be an object")
            continue
        if not isinstance(reference.get("value"), (int, float)) or isinstance(reference.get("value"), bool):
            errors.append(f"{ref_path}.value must be numeric")
        if not _is_non_empty_string(reference.get("label")):
            errors.append(f"{ref_path}.label is required")

    for a_index, annotation in enumerate(chart.get("annotations") or []):
        ann_path = f"{path}.annotations[{a_index}]"
        if not isinstance(annotation, dict):
            errors.append(f"{ann_path} must be an object")
            continue
        if not _is_non_empty_string(annotation.get("label")):
            errors.append(f"{ann_path}.label is required")
        has_target_label = _is_non_empty_string(annotation.get("target_label"))
        has_target_range = isinstance(annotation.get("target_range"), list) and len(annotation["target_range"]) == 2
        has_coords = isinstance(annotation.get("x"), (int, float)) and isinstance(annotation.get("y"), (int, float))
        if not (has_target_label or has_target_range or has_coords):
            errors.append(f"{ann_path} needs target_label, target_range, or x/y coordinates")
        if has_target_label and annotation["target_label"] not in label_set:
            errors.append(f"{ann_path}.target_label is not in labels: {annotation['target_label']}")
        if has_target_range:
            missing = [label for label in annotation["target_range"] if label not in label_set]
            if missing:
                errors.append(f"{ann_path}.target_range labels are unknown: {missing}")

    min_focus_labels = schema.get("quality_limits", {}).get("min_chart_labels_for_annotation_gate", 6)
    has_focus = bool(chart.get("annotations") or chart.get("highlight_labels") or chart.get("reference_lines"))
    if label_count >= min_focus_labels and not has_focus:
        warnings.append(f"{path} has many labels but no annotations, highlight_labels, or reference_lines")
    if label_count >= min_focus_labels and chart.get("data_label_position") is None:
        warnings.append(f"{path} has many labels but no data_label_position")
    if not _is_non_empty_string(chart.get("takeaway")):
        warnings.append(f"{path}.takeaway is recommended for consulting deck pages")


def _validate_table(
    table: Any,
    path: str,
    source_ids: set[str],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    if not isinstance(table, dict):
        errors.append(f"{path} must be an object")
        return
    for field in schema.get("table_required_fields", []):
        if field not in table:
            errors.append(f"{path}.{field} is required")
    if "source_ref" in table:
        _validate_source_ref(table.get("source_ref"), source_ids, f"{path}.source_ref", errors)
    columns = table.get("columns")
    rows = table.get("rows")
    if columns is not None and (not isinstance(columns, list) or not columns):
        errors.append(f"{path}.columns must be a non-empty list")
    if rows is not None and not isinstance(rows, list):
        errors.append(f"{path}.rows must be a list")


def _validate_dashboard(
    dashboard: Any,
    slide_path: str,
    source_ids: set[str],
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(dashboard, dict):
        errors.append(f"{slide_path}.dashboard must be an object")
        return

    kpis = dashboard.get("kpis")
    if not isinstance(kpis, list) or not kpis:
        errors.append(f"{slide_path}.dashboard.kpis must be a non-empty list")
    else:
        for index, kpi in enumerate(kpis):
            if not isinstance(kpi, dict):
                errors.append(f"{slide_path}.dashboard.kpis[{index}] must be an object")
                continue
            if not _is_non_empty_string(kpi.get("label")):
                errors.append(f"{slide_path}.dashboard.kpis[{index}].label is required")
            if not _is_non_empty_string(kpi.get("value")):
                errors.append(f"{slide_path}.dashboard.kpis[{index}].value is required")

    _validate_chart(dashboard.get("trend_chart"), f"{slide_path}.dashboard.trend_chart", source_ids, schema, errors, warnings)

    ring_metrics = dashboard.get("ring_metrics")
    if not isinstance(ring_metrics, list) or not ring_metrics:
        errors.append(f"{slide_path}.dashboard.ring_metrics must be a non-empty list")
    else:
        for index, metric in enumerate(ring_metrics):
            metric_path = f"{slide_path}.dashboard.ring_metrics[{index}]"
            if not isinstance(metric, dict):
                errors.append(f"{metric_path} must be an object")
                continue
            if not _is_non_empty_string(metric.get("label")):
                errors.append(f"{metric_path}.label is required")
            value = metric.get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"{metric_path}.value must be a number between 0 and 1")

    insights = dashboard.get("insights")
    if not isinstance(insights, list) or not insights:
        errors.append(f"{slide_path}.dashboard.insights must be a non-empty list")
    else:
        max_len = schema.get("quality_limits", {}).get("insight_max_chars", 10_000)
        for index, insight in enumerate(insights):
            if not _is_non_empty_string(insight):
                errors.append(f"{slide_path}.dashboard.insights[{index}] is empty")
            elif len(insight) > max_len:
                warnings.append(f"{slide_path}.dashboard.insights[{index}] may be too long for the standard insight container")


def _validate_reason_cards(
    cards: Any,
    path: str,
    schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if cards is None:
        return
    if not isinstance(cards, list):
        errors.append(f"{path} must be a list")
        return
    max_len = schema.get("quality_limits", {}).get("reason_card_body_max_chars", 10_000)
    for index, card in enumerate(cards):
        card_path = f"{path}[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{card_path} must be an object")
            continue
        if not _is_non_empty_string(card.get("title")):
            errors.append(f"{card_path}.title is required")
        body = card.get("body")
        if body is not None and isinstance(body, str) and len(body) > max_len:
            warnings.append(f"{card_path}.body may overflow the standard card container")


def _validate_slide(
    slide: Any,
    index: int,
    source_ids: set[str],
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
        elif field in {"id", "synthesis_ref", "layout", "slide_role", "title", "claim", "visual_mode"} and not _is_non_empty_string(slide.get(field)):
            errors.append(f"{slide_path}.{field} must be a non-empty string")

    layout = slide.get("layout")
    if layout and layout not in schema.get("allowed_layouts", []):
        errors.append(f"{slide_path}.layout is not supported: {layout}")
    visual_mode = slide.get("visual_mode")
    if visual_mode and visual_mode not in schema.get("allowed_visual_modes", []):
        errors.append(f"{slide_path}.visual_mode is not supported: {visual_mode}")

    evidence_refs = slide.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        errors.append(f"{slide_path}.evidence_refs must be a non-empty list")
    else:
        for ref_index, source_ref in enumerate(evidence_refs):
            _validate_source_ref(source_ref, source_ids, f"{slide_path}.evidence_refs[{ref_index}]", errors)

    if "source_ref" in slide:
        _validate_source_ref(slide.get("source_ref"), source_ids, f"{slide_path}.source_ref", errors)

    for blocked_key in ("full_slide_image", "screenshot", "html_snapshot"):
        if blocked_key in slide:
            errors.append(f"{slide_path}.{blocked_key} is not allowed in editable PPTX handoff")

    for required_path in schema.get("layout_requirements", {}).get(layout, []):
        if not _has_path(slide, required_path):
            errors.append(f"{slide_path}.{required_path} is required for layout {layout}")

    if "chart" in slide:
        _validate_chart(slide["chart"], f"{slide_path}.chart", source_ids, schema, errors, warnings)
    if "table" in slide:
        _validate_table(slide["table"], f"{slide_path}.table", source_ids, schema, errors)
    if layout == "dashboard_performance":
        _validate_dashboard(slide.get("dashboard"), slide_path, source_ids, schema, errors, warnings)
    if layout == "comparison_vs" and isinstance(slide.get("comparison"), dict):
        _validate_reason_cards(slide["comparison"].get("reason_cards"), f"{slide_path}.comparison.reason_cards", schema, errors, warnings)
    if layout == "problem_solution_grid" and isinstance(slide.get("problem_solution"), dict):
        for group in ("problems", "solutions"):
            _validate_reason_cards(slide["problem_solution"].get(group), f"{slide_path}.problem_solution.{group}", schema, errors, warnings)

    _validate_text_lengths(slide, slide_path, schema, warnings)


def validate_pptx_deck_contract(
    deck: dict[str, Any],
    schema_path: str | None = None,
) -> tuple[bool, list[str]]:
    """Return `(ok, messages)` for a PPTX deck handoff JSON object."""

    schema = _load_schema(schema_path)
    errors: list[str] = []
    warnings: list[str] = []

    for field in schema.get("required_top_level", []):
        if field not in deck:
            errors.append(f"{field} is required")
        elif field not in {"sources", "slides"} and not _is_non_empty_string(deck.get(field)):
            errors.append(f"{field} must be a non-empty string")

    if deck.get("contract_version") != schema.get("contract_version"):
        errors.append(f"contract_version must be {schema.get('contract_version')}")
    if deck.get("deck_goal") and deck["deck_goal"] not in schema.get("allowed_deck_goals", []):
        errors.append(f"deck_goal is not supported: {deck['deck_goal']}")
    if deck.get("audience") and deck["audience"] not in schema.get("allowed_audiences", []):
        errors.append(f"audience is not supported: {deck['audience']}")
    if deck.get("style_id") and deck["style_id"] not in schema.get("allowed_style_ids", []):
        errors.append(f"style_id is not supported: {deck['style_id']}")

    source_ids = _source_ids(deck, errors)
    slides = deck.get("slides")
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
            _validate_slide(slide, index, source_ids, schema, errors, warnings)

    messages = errors + [f"WARNING: {warning}" for warning in warnings]
    return len(errors) == 0, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a PPTX deck handoff JSON file.")
    parser.add_argument("deck_json", help="Path to a PPTX handoff/deck JSON file.")
    parser.add_argument("--schema", help="Optional contract schema/config JSON path.")
    args = parser.parse_args()

    deck = _read_json(Path(args.deck_json))
    ok, messages = validate_pptx_deck_contract(deck, args.schema)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
