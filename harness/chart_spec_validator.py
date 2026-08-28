#!/usr/bin/env python3
"""Validate chart_spec_pack v0.3 before report assembly."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


VERSION = "0.3"
STATUSES = {"pass", "needs_analysis_backfill", "needs_chart_revision", "drop_or_bounded"}
ROUTES = {"analysis", "chart_agent", "drop_or_bounded", None}
RELATIONS = {"same_claim", "supporting", "complementary", "boundary"}
PROMPT_STATUSES = {"resolved", "fallback_used"}
VISUAL_STATUSES = {"pass", "fail"}
ANNOTATION_TYPES = {
    "point_label",
    "endpoint_label",
    "range_band",
    "reference_line",
    "short_callout",
    "icon_callout",
    "detail_column",
    "in_chart_note",
}
PLACEMENT_CHANNELS = {
    "near_data_point",
    "near_bar_end",
    "inside_plot_reserved",
    "outside_plot_left",
    "outside_plot_right",
    "above_plot",
    "below_plot",
    "detail_column",
}
AVOID_REGIONS = {
    "axis_ticks",
    "axis_labels",
    "legend",
    "data_marks",
    "data_mark_bboxes",
    "value_labels",
    "callout_boxes",
    "plot_edges",
    "x_axis_tick_band",
    "other_annotations",
}
ICON_IDS = {
    "icon-signal-down",
    "icon-signal-up",
    "icon-warning-triangle",
    "icon-check-circle",
    "icon-evidence-dot",
    "icon-pin",
    "icon-note",
    "icon-question",
    "icon-point-ring",
    "icon-range-band",
    "icon-benchmark-line",
    "icon-mini-sparkline",
    "icon-compare-bars",
    "icon-bridge",
    "icon-no-overlap",
    "icon-inside-plot",
    "icon-avoid-axis",
}
COLLISION_ROLES = {
    "data_mark",
    "axis_or_legend",
    "annotation_text",
    "annotation_container",
    "reference_region",
}
CHECKED_ITEMS = {
    "text_overlap",
    "annotation_collision",
    "annotation_mark_collision",
    "label_legibility",
    "conclusion_visibility",
    "information_density",
    "gridline_and_ink",
    "palette_compliance",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def validate_chart_spec_pack(payload: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    pack = payload.get("chart_spec_pack") if "chart_spec_pack" in payload else payload
    if not isinstance(pack, dict):
        return False, ["chart_spec_pack must be an object"]
    if pack.get("contract_version") != VERSION:
        errors.append(f"chart_spec_pack.contract_version must be {VERSION}")
    runtime = pack.get("runtime_policy")
    if not isinstance(runtime, dict):
        errors.append("runtime_policy must be an object")
    else:
        if runtime.get("manifest_ref") != "agents/chart-spec-agent/manifest.yaml":
            errors.append("runtime_policy.manifest_ref must point to chart-spec-agent")
        if runtime.get("configured_temperature") != 0.0 or runtime.get("applied_temperature") != 0.0:
            errors.append("chart-spec-agent temperature must be configured and applied as 0.0")

    charts = pack.get("charts")
    if not isinstance(charts, list) or not charts:
        errors.append("charts must be a non-empty list")
        charts = []
    chart_ids: set[str] = set()
    for index, chart in enumerate(charts):
        path = f"charts[{index}]"
        if not isinstance(chart, dict):
            errors.append(f"{path} must be an object")
            continue
        required = (
            "chart_id",
            "source_chart_candidate_ref",
            "section_ref",
            "claim_to_prove",
            "relationship_intent",
            "chart_type",
            "prompt_resources",
            "required_series",
            "series_completeness",
            "focus_metric",
            "comparison_basis",
            "required_annotations",
            "emphasis_plan",
            "annotation_plan",
            "fail_if_missing",
            "style_constraints",
            "visual_check",
        )
        for field in required:
            if field not in chart:
                errors.append(f"{path}.{field} is required")
        chart_id = chart.get("chart_id")
        if not _text(chart_id):
            errors.append(f"{path}.chart_id must be non-empty")
        elif chart_id in chart_ids:
            errors.append(f"{path}.chart_id is duplicated: {chart_id}")
        else:
            chart_ids.add(chart_id)
        for field in ("source_chart_candidate_ref", "section_ref", "claim_to_prove", "chart_type", "focus_metric", "comparison_basis"):
            if field in chart and not _text(chart.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if chart.get("relationship_intent") not in RELATIONS:
            errors.append(f"{path}.relationship_intent is unsupported")
        prompt_resources = chart.get("prompt_resources")
        if not isinstance(prompt_resources, dict):
            errors.append(f"{path}.prompt_resources must be an object")
        else:
            for field in ("index_ref", "lookup_key", "status"):
                if not _text(prompt_resources.get(field)):
                    errors.append(f"{path}.prompt_resources.{field} must be non-empty")
            if prompt_resources.get("index_ref") != "references/chart_prompt_resource_index.md":
                errors.append(f"{path}.prompt_resources.index_ref is unsupported")
            if prompt_resources.get("status") not in PROMPT_STATUSES:
                errors.append(f"{path}.prompt_resources.status is unsupported")
            if prompt_resources.get("status") == "resolved" and not _text(prompt_resources.get("resource_ref")):
                errors.append(f"{path}.prompt_resources.resource_ref is required when status=resolved")
            if prompt_resources.get("status") == "fallback_used" and not _text(prompt_resources.get("fallback_reason")):
                errors.append(f"{path}.prompt_resources.fallback_reason is required when status=fallback_used")
        series = chart.get("required_series")
        if not _list(series):
            errors.append(f"{path}.required_series must be non-empty")
            series = []
        focus_metric = chart.get("focus_metric")
        series_metrics: set[str] = set()
        for s_index, item in enumerate(series):
            s_path = f"{path}.required_series[{s_index}]"
            if not isinstance(item, dict):
                errors.append(f"{s_path} must be an object")
                continue
            for field in ("metric", "values", "unit", "role", "evidence_refs"):
                if field not in item:
                    errors.append(f"{s_path}.{field} is required")
            if _text(item.get("metric")):
                series_metrics.add(item["metric"])
            if not _list(item.get("values")):
                errors.append(f"{s_path}.values must be non-empty")
            if not _list(item.get("evidence_refs")):
                errors.append(f"{s_path}.evidence_refs must be non-empty")
        if _text(focus_metric) and focus_metric not in series_metrics:
            errors.append(f"{path}.focus_metric must exist in required_series")
        completeness = chart.get("series_completeness")
        if not isinstance(completeness, dict):
            errors.append(f"{path}.series_completeness must be an object")
        else:
            domain_values = completeness.get("domain_values")
            if not _list(domain_values):
                errors.append(f"{path}.series_completeness.domain_values must be non-empty")
                domain_len = None
            else:
                domain_len = len(domain_values)
            if completeness.get("complete_base_series_required") is not True:
                errors.append(f"{path}.series_completeness.complete_base_series_required must be true")
            if not _text(completeness.get("rendering_rule")):
                errors.append(f"{path}.series_completeness.rendering_rule must be non-empty")
            annotation_only = completeness.get("annotation_only_series", [])
            if not isinstance(annotation_only, list) or any(not _text(item) for item in annotation_only):
                errors.append(f"{path}.series_completeness.annotation_only_series must be a string list")
                annotation_only = []
            if domain_len is not None:
                for s_index, item in enumerate(series):
                    if not isinstance(item, dict):
                        continue
                    metric = item.get("metric")
                    values = item.get("values")
                    if metric in annotation_only:
                        continue
                    if isinstance(values, list) and len(values) != domain_len:
                        errors.append(
                            f"{path}.required_series[{s_index}].values length must match series_completeness.domain_values"
                        )
        for field in ("required_annotations", "fail_if_missing"):
            if not _list(chart.get(field)) or any(not _text(item) for item in chart.get(field, [])):
                errors.append(f"{path}.{field} must be a non-empty string list")
        emphasis_plan = chart.get("emphasis_plan")
        if not isinstance(emphasis_plan, dict):
            errors.append(f"{path}.emphasis_plan must be an object")
        else:
            if not _list(emphasis_plan.get("methods")) or any(not _text(item) for item in emphasis_plan.get("methods", [])):
                errors.append(f"{path}.emphasis_plan.methods must be a non-empty string list")
            if not _text(emphasis_plan.get("reader_should_notice")):
                errors.append(f"{path}.emphasis_plan.reader_should_notice must be non-empty")
            if not _text(emphasis_plan.get("base_series_visibility")):
                errors.append(f"{path}.emphasis_plan.base_series_visibility must be non-empty")
        annotation_plan = chart.get("annotation_plan")
        if not isinstance(annotation_plan, list):
            errors.append(f"{path}.annotation_plan must be a list")
        else:
            for a_index, annotation in enumerate(annotation_plan):
                a_path = f"{path}.annotation_plan[{a_index}]"
                if not isinstance(annotation, dict):
                    errors.append(f"{a_path} must be an object")
                    continue
                for field in ("type", "anchor", "text", "placement_channel", "avoid_regions", "max_chars", "min_gap_px"):
                    if field not in annotation:
                        errors.append(f"{a_path}.{field} is required")
                if annotation.get("type") not in ANNOTATION_TYPES:
                    errors.append(f"{a_path}.type is unsupported")
                if not _text(annotation.get("anchor")):
                    errors.append(f"{a_path}.anchor must be non-empty")
                text = annotation.get("text")
                if not isinstance(text, str):
                    errors.append(f"{a_path}.text must be a string")
                    text = ""
                max_chars = annotation.get("max_chars")
                if not isinstance(max_chars, int) or max_chars < 0 or max_chars > 36:
                    errors.append(f"{a_path}.max_chars must be an integer from 0 to 36")
                elif len(text.strip()) > max_chars:
                    errors.append(f"{a_path}.text length must not exceed max_chars")
                min_gap_px = annotation.get("min_gap_px")
                if not isinstance(min_gap_px, int) or min_gap_px < 8:
                    errors.append(f"{a_path}.min_gap_px must be an integer >= 8")
                if annotation.get("placement_channel") not in PLACEMENT_CHANNELS:
                    errors.append(f"{a_path}.placement_channel is unsupported")
                avoid_regions = annotation.get("avoid_regions")
                if not isinstance(avoid_regions, list) or not avoid_regions:
                    errors.append(f"{a_path}.avoid_regions must be a non-empty list")
                else:
                    unsupported = set(avoid_regions) - AVOID_REGIONS
                    if unsupported:
                        errors.append(f"{a_path}.avoid_regions contains unsupported regions: {sorted(unsupported)}")
                icon_id = annotation.get("icon_id")
                if icon_id is not None and icon_id not in ICON_IDS:
                    errors.append(f"{a_path}.icon_id is unsupported")
                if annotation.get("type") == "icon_callout" and icon_id not in ICON_IDS:
                    errors.append(f"{a_path}.icon_id is required for icon_callout")
                forbidden = ("decline segment", "下降段", "large_red_box", "diagonal_arrow", "bracket")
                joined = " ".join(str(annotation.get(field, "")) for field in ("type", "text", "placement_channel", "anchor"))
                if any(item in joined for item in forbidden):
                    errors.append(f"{a_path} uses a forbidden decorative annotation pattern")
        if not isinstance(chart.get("style_constraints"), dict):
            errors.append(f"{path}.style_constraints must be an object")
        else:
            style_constraints = chart["style_constraints"]
            if style_constraints.get("color_authority") != "styles/color-system/color_system.yaml":
                errors.append(f"{path}.style_constraints.color_authority must be the shared color system")
        visual_check = chart.get("visual_check")
        if not isinstance(visual_check, dict):
            errors.append(f"{path}.visual_check must be an object")
        else:
            if visual_check.get("first_pass_status") not in VISUAL_STATUSES:
                errors.append(f"{path}.visual_check.first_pass_status is unsupported")
            checked_items = visual_check.get("checked_items")
            if (
                not isinstance(checked_items, list)
                or set(checked_items) != CHECKED_ITEMS
                or len(checked_items) != len(CHECKED_ITEMS)
            ):
                errors.append(f"{path}.visual_check.checked_items must include the required visual checks exactly once")
            revision_count = visual_check.get("revision_count")
            if not isinstance(revision_count, int) or revision_count < 0 or revision_count > 2:
                errors.append(f"{path}.visual_check.revision_count must be an integer from 0 to 2")
            if not isinstance(visual_check.get("judge_mode_used"), bool):
                errors.append(f"{path}.visual_check.judge_mode_used must be boolean")
            if visual_check.get("first_pass_status") == "pass":
                if visual_check.get("revision_count") != 0:
                    errors.append(f"{path}.visual_check.revision_count must be 0 when first pass passes")
                if visual_check.get("judge_mode_used") is not False:
                    errors.append(f"{path}.visual_check.judge_mode_used must be false when first pass passes")
            if visual_check.get("first_pass_status") == "fail" and visual_check.get("judge_mode_used") is not True:
                errors.append(f"{path}.visual_check.judge_mode_used must be true after a failed visual check")
            collision_model = visual_check.get("collision_model")
            if not isinstance(collision_model, dict):
                errors.append(f"{path}.visual_check.collision_model must be an object")
            else:
                roles = collision_model.get("checked_geometry_roles")
                if not isinstance(roles, list) or set(roles) != COLLISION_ROLES:
                    errors.append(f"{path}.visual_check.collision_model.checked_geometry_roles must include all collision roles exactly once")
                if collision_model.get("text_only_check_allowed") is not False:
                    errors.append(f"{path}.visual_check.collision_model.text_only_check_allowed must be false")
                if collision_model.get("min_gap_enforced") is not True:
                    errors.append(f"{path}.visual_check.collision_model.min_gap_enforced must be true")

    opinions = pack.get("chart_opinions")
    if not isinstance(opinions, list) or len(opinions) != len(charts):
        errors.append("chart_opinions must exist once per chart")
        opinions = []
    opinion_ids: set[str] = set()
    for index, opinion in enumerate(opinions):
        path = f"chart_opinions[{index}]"
        if not isinstance(opinion, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("chart_id", "status", "concerns", "required_backfill", "route"):
            if field not in opinion:
                errors.append(f"{path}.{field} is required")
        chart_id = opinion.get("chart_id")
        if _text(chart_id):
            opinion_ids.add(chart_id)
        if opinion.get("status") not in STATUSES:
            errors.append(f"{path}.status is unsupported")
        if opinion.get("route") not in ROUTES:
            errors.append(f"{path}.route is unsupported")
        if opinion.get("status") == "pass" and opinion.get("route") is not None:
            errors.append(f"{path}.route must be null when status=pass")
        if opinion.get("status") != "pass" and not _list(opinion.get("concerns")):
            errors.append(f"{path}.concerns must be non-empty when status is not pass")
        if not isinstance(opinion.get("required_backfill"), list):
            errors.append(f"{path}.required_backfill must be a list")
    if opinion_ids != chart_ids:
        errors.append("chart_opinions chart_id set must match charts")
    return not errors, errors


if __name__ == "__main__":
    target = Path(sys.argv[1])
    data = json.loads(target.read_text(encoding="utf-8"))
    ok, messages = validate_chart_spec_pack(data)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
