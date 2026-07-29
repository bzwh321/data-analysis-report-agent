"""
output_validator.py — final report structure validator

校验项：
1. 结论可追溯性：每条 finding 必须有 data_source 字段
2. 组织归因规则：有 org attribution 时必须有数据来源，不得纯推断
3. 禁止内部框架标注词出现在 executive_summary
4. Summary 非空且含具体数字
5. 必须诚实记录 data_gaps
"""

import re


FORBIDDEN_LABELS = ['数据事实', '运营逻辑', '组织归因', '业务结论']
MATERIAL_SUPPORT_STATUSES = {
    "verified",
    "supported",
    "partially_supported",
    "hypothesis",
    "needs_data",
    "contradicted",
}
MATERIAL_CLAIM_SCOPES = {
    "within_parent_driver",
    "contextual_support",
    "rejected_child",
}
MATERIAL_LINKAGE_TYPES = {
    "mechanism",
    "segment",
    "funnel_step",
    "temporal",
    "mix_shift",
    "supply_constraint",
    "efficiency",
}
MATERIAL_PACK_VERSION = "0.3"
MATERIAL_PACK_COMPAT_VERSION = "0.2"
ANALYSIS_BRANCH_DECISIONS = {"continue", "stop"}
FINDING_CAUSAL_STATUSES = {
    "descriptive",
    "associative",
    "causal",
    "counterevidence",
}
FINDING_RECOMMENDED_USES = {
    "intervene",
    "investigate",
    "monitor",
    "deprioritize",
    "no_action",
}
CHART_DECISION_ROLES = {
    "issue_judgement",
    "magnitude",
    "driver",
    "counterevidence",
    "boundary",
    "action",
}
CHART_VISUAL_PRIORITIES = {"dominant", "supporting", "optional"}
CLAIM_REVIEW_STATUSES = {"approved_as_written", "rewritten"}
CLAIM_REVIEW_CHECKS = (
    "factually_supported",
    "business_meaning_clear",
    "decision_direction_clear",
    "causal_strength_appropriate",
    "alternative_explanations_considered",
    "visual_evidence_sufficient",
)


def validate_final_output(final: dict) -> tuple[bool, list[str]]:
    """
    校验最终报告结构。
    警告级别错误也会返回，调用方自行决定是否中止。

    Returns:
        (is_valid, error_list)
        is_valid=False 表示存在严重错误（结构或可追溯性问题）
        is_valid=True 可能仍有 WARNING 级别信息
    """
    errors: list[str] = []
    warnings: list[str] = []

    # ── 必需顶层字段 ──────────────────────────────────────────────────────
    required = ["executive_summary", "findings"]
    for field in required:
        if field not in final:
            errors.append(f"final_insights 缺少必需字段：{field}")

    if errors:
        return False, errors

    # ── Summary 校验 ──────────────────────────────────────────────────────
    summary = final.get("executive_summary", "")
    if not summary.strip():
        errors.append("executive_summary 不得为空")
    elif not any(c.isdigit() for c in summary):
        warnings.append("WARNING: executive_summary 中未发现具体数字，建议补充")

    # ── 禁止内部框架标注词 ────────────────────────────────────────────────
    for label in FORBIDDEN_LABELS:
        if label in summary:
            errors.append(
                f"executive_summary 包含内部框架标注词 '{label}'，"
                "不得出现在面向读者的输出中"
            )

    # ── findings 校验 ────────────────────────────────────────────────────
    findings = final.get("findings", [])
    if not findings:
        errors.append("findings 列表不得为空")
    else:
        for i, finding in enumerate(findings):
            # 可追溯性
            if "data_source" not in finding:
                errors.append(f"findings[{i}] 缺少 data_source 字段（结论可追溯性要求）")
            # 组织归因规则
            if finding.get("has_org_attribution"):
                if finding.get("org_attribution_source") == "inference_only":
                    errors.append(
                        f"findings[{i}] 的组织归因来源为 inference_only，"
                        "必须有数据来源，不得纯推断"
                    )
            # finding 内容不得为空
            if not finding.get("content", "").strip():
                warnings.append(f"WARNING: findings[{i}] content 为空")

    # ── data_gaps 校验 ────────────────────────────────────────────────────
    if "data_gaps" not in final:
        warnings.append(
            "WARNING: 缺少 data_gaps 字段，建议诚实记录分析盲点"
        )
    elif not isinstance(final["data_gaps"], list):
        errors.append("data_gaps 必须是列表")

    if "analysis_material_pack" in final:
        _validate_analysis_material_pack(final["analysis_material_pack"], errors, warnings)

    # 合并 errors + warnings（errors 排前）
    all_messages = errors + warnings
    return len(errors) == 0, all_messages


def _validate_analysis_material_pack(
    pack: object,
    errors: list[str],
    warnings: list[str],
) -> None:
    if isinstance(pack, dict) and pack.get("contract_version") == MATERIAL_PACK_VERSION:
        _validate_analysis_material_pack_v03(pack, errors, warnings)
        return

    if (
        isinstance(pack, dict)
        and pack.get("contract_version") == MATERIAL_PACK_COMPAT_VERSION
    ):
        warnings.append(
            "WARNING: analysis_material_pack 使用 v0.2 兼容模式；"
            "新的 dense-report/PPT 运行应输出决策就绪的 v0.3"
        )
        _validate_analysis_material_pack_v02(pack, errors, warnings)
        return

    warnings.append(
        "WARNING: analysis_material_pack 使用旧版 driver-tree 合同；"
        "新的 dense-report/PPT 工作流应输出 contract_version=0.3"
    )
    _validate_analysis_material_pack_legacy(pack, errors, warnings)


def _validate_analysis_material_pack_v03(
    pack: dict,
    errors: list[str],
    warnings: list[str],
) -> None:
    _validate_analysis_material_pack_v02(pack, errors, warnings)

    findings = pack.get("validated_findings")
    if not isinstance(findings, list):
        findings = []
    finding_map = {
        item.get("finding_id"): item
        for item in findings
        if isinstance(item, dict)
        and isinstance(item.get("finding_id"), str)
        and item.get("finding_id", "").strip()
    }
    finding_ids = set(finding_map)

    for index, finding in enumerate(findings):
        path = f"analysis_material_pack.validated_findings[{index}]"
        if not isinstance(finding, dict):
            continue
        for field in (
            "scope",
            "causal_status",
            "management_implication",
            "recommended_use",
        ):
            if not isinstance(finding.get(field), str) or not finding.get(
                field, ""
            ).strip():
                errors.append(f"{path}.{field} 不得为空")
        causal_status = finding.get("causal_status")
        if causal_status not in FINDING_CAUSAL_STATUSES:
            errors.append(
                f"{path}.causal_status 不支持：{causal_status}"
            )
        recommended_use = finding.get("recommended_use")
        if recommended_use not in FINDING_RECOMMENDED_USES:
            errors.append(
                f"{path}.recommended_use 不支持：{recommended_use}"
            )
        if "next_validation_question" not in finding:
            errors.append(f"{path}.next_validation_question 缺失")
        else:
            next_question = finding.get("next_validation_question")
            if next_question is not None and (
                not isinstance(next_question, str) or not next_question.strip()
            ):
                errors.append(
                    f"{path}.next_validation_question 必须是非空字符串或 null"
                )
            if recommended_use in {"investigate", "monitor", "deprioritize"} and (
                not isinstance(next_question, str) or not next_question.strip()
            ):
                errors.append(
                    f"{path}.next_validation_question 在 {recommended_use} 时不得为空"
                )

    charts = pack.get("chart_candidates")
    if not isinstance(charts, list):
        charts = []
    for index, chart in enumerate(charts):
        path = f"analysis_material_pack.chart_candidates[{index}]"
        if not isinstance(chart, dict):
            continue
        for field in (
            "message_to_prove",
            "decision_role",
            "visual_priority",
            "focus_target",
            "why_visual_not_text",
        ):
            if not isinstance(chart.get(field), str) or not chart.get(
                field, ""
            ).strip():
                errors.append(f"{path}.{field} 不得为空")
        if chart.get("decision_role") not in CHART_DECISION_ROLES:
            errors.append(
                f"{path}.decision_role 不支持：{chart.get('decision_role')}"
            )
        if chart.get("visual_priority") not in CHART_VISUAL_PRIORITIES:
            errors.append(
                f"{path}.visual_priority 不支持：{chart.get('visual_priority')}"
            )
        _validate_known_refs(
            chart.get("finding_refs"),
            finding_ids,
            f"{path}.finding_refs",
            errors,
        )

    review_log = pack.get("claim_review_log")
    if not isinstance(review_log, dict):
        errors.append("analysis_material_pack.claim_review_log 必须是对象")
        review_entries: list[object] = []
    else:
        review_entries = review_log.get("entries")
        if not isinstance(review_entries, list) or not review_entries:
            errors.append(
                "analysis_material_pack.claim_review_log.entries 必须是非空列表"
            )
            review_entries = []

    reviewed_ids: set[str] = set()
    for index, entry in enumerate(review_entries):
        path = f"analysis_material_pack.claim_review_log.entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path} 必须是对象")
            continue
        finding_id = entry.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id.strip():
            errors.append(f"{path}.finding_id 不得为空")
            continue
        if finding_id not in finding_ids:
            errors.append(f"{path}.finding_id 引用未知 finding：{finding_id}")
        elif finding_id in reviewed_ids:
            errors.append(f"{path}.finding_id 重复审查：{finding_id}")
        else:
            reviewed_ids.add(finding_id)
        for field in (
            "candidate_statement",
            "final_statement",
            "review_reason",
        ):
            if not isinstance(entry.get(field), str) or not entry.get(
                field, ""
            ).strip():
                errors.append(f"{path}.{field} 不得为空")
        review_status = entry.get("review_status")
        if review_status not in CLAIM_REVIEW_STATUSES:
            errors.append(
                f"{path}.review_status 不支持：{review_status}"
            )
        candidate_statement = entry.get("candidate_statement")
        final_statement = entry.get("final_statement")
        if review_status == "approved_as_written" and (
            isinstance(candidate_statement, str)
            and isinstance(final_statement, str)
            and candidate_statement != final_statement
        ):
            errors.append(
                f"{path} approved_as_written 时候选结论必须等于最终结论"
            )
        if review_status == "rewritten" and (
            isinstance(candidate_statement, str)
            and isinstance(final_statement, str)
            and candidate_statement == final_statement
        ):
            errors.append(f"{path} rewritten 时必须实际重写结论")
        finding = finding_map.get(finding_id)
        if (
            isinstance(finding, dict)
            and isinstance(final_statement, str)
            and final_statement != finding.get("statement")
        ):
            errors.append(f"{path}.final_statement 与 finding.statement 不一致")
        checks = entry.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"{path}.checks 必须是对象")
            continue
        for check in CLAIM_REVIEW_CHECKS:
            if checks.get(check) is not True:
                errors.append(f"{path}.checks.{check} 必须通过")

    missing_reviews = sorted(finding_ids - reviewed_ids)
    if missing_reviews:
        errors.append(
            "analysis_material_pack.claim_review_log 缺少 finding 审查："
            f"{missing_reviews}"
        )


def _validate_analysis_material_pack_v02(
    pack: dict,
    errors: list[str],
    warnings: list[str],
) -> None:
    required = (
        "contract_version",
        "analysis_goal",
        "metric_context",
        "validated_findings",
        "candidate_explanations",
        "evidence_inventory",
        "chart_candidates",
        "boundaries",
        "gaps",
        "analysis_decision_log",
    )
    for field in required:
        if field not in pack:
            errors.append(f"analysis_material_pack 缺少必需字段：{field}")

    goal = pack.get("analysis_goal")
    if not isinstance(goal, dict):
        errors.append("analysis_material_pack.analysis_goal 必须是对象")
    else:
        for field in ("question", "audience", "decision_to_support", "time_scope"):
            if not isinstance(goal.get(field), str) or not goal.get(field, "").strip():
                errors.append(f"analysis_material_pack.analysis_goal.{field} 不得为空")

    metrics = pack.get("metric_context")
    if not isinstance(metrics, list) or not metrics:
        errors.append("analysis_material_pack.metric_context 必须是非空列表")
    else:
        metric_ids: set[str] = set()
        for index, metric in enumerate(metrics):
            path = f"analysis_material_pack.metric_context[{index}]"
            if not isinstance(metric, dict):
                errors.append(f"{path} 必须是对象")
                continue
            metric_id = metric.get("metric_id")
            if not isinstance(metric_id, str) or not metric_id.strip():
                errors.append(f"{path}.metric_id 不得为空")
            elif metric_id in metric_ids:
                errors.append(f"{path}.metric_id 重复：{metric_id}")
            else:
                metric_ids.add(metric_id)
            for field in ("definition", "unit", "grain"):
                if not isinstance(metric.get(field), str) or not metric.get(field, "").strip():
                    errors.append(f"{path}.{field} 不得为空")
            if not _is_non_empty_string_list(metric.get("source_refs")):
                errors.append(f"{path}.source_refs 必须是非空字符串列表")

    evidence_items = pack.get("evidence_inventory")
    evidence_ids: set[str] = set()
    if not isinstance(evidence_items, list) or not evidence_items:
        errors.append("analysis_material_pack.evidence_inventory 必须是非空列表")
    else:
        for index, item in enumerate(evidence_items):
            path = f"analysis_material_pack.evidence_inventory[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} 必须是对象")
                continue
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                errors.append(f"{path}.evidence_id 不得为空")
            elif evidence_id in evidence_ids:
                errors.append(f"{path}.evidence_id 重复：{evidence_id}")
            else:
                evidence_ids.add(evidence_id)
            for field in ("type", "subject", "grain", "data_ref", "quality", "availability"):
                if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                    errors.append(f"{path}.{field} 不得为空")
            if not _is_non_empty_string_list(item.get("source_refs")):
                errors.append(f"{path}.source_refs 必须是非空字符串列表")

    boundaries = pack.get("boundaries")
    boundary_ids: set[str] = set()
    if not isinstance(boundaries, list):
        errors.append("analysis_material_pack.boundaries 必须是列表")
        boundaries = []
    for index, boundary in enumerate(boundaries):
        path = f"analysis_material_pack.boundaries[{index}]"
        if not isinstance(boundary, dict):
            errors.append(f"{path} 必须是对象")
            continue
        boundary_id = boundary.get("boundary_id")
        if not isinstance(boundary_id, str) or not boundary_id.strip():
            errors.append(f"{path}.boundary_id 不得为空")
        elif boundary_id in boundary_ids:
            errors.append(f"{path}.boundary_id 重复：{boundary_id}")
        else:
            boundary_ids.add(boundary_id)
        for field in ("scope", "limitation"):
            if not isinstance(boundary.get(field), str) or not boundary.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        if not isinstance(boundary.get("affected_material_refs"), list):
            errors.append(f"{path}.affected_material_refs 必须是列表")

    findings = pack.get("validated_findings")
    finding_ids: set[str] = set()
    if not isinstance(findings, list) or not findings:
        errors.append("analysis_material_pack.validated_findings 必须是非空列表")
        findings = []
    for index, finding in enumerate(findings):
        path = f"analysis_material_pack.validated_findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{path} 必须是对象")
            continue
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id.strip():
            errors.append(f"{path}.finding_id 不得为空")
        elif finding_id in finding_ids:
            errors.append(f"{path}.finding_id 重复：{finding_id}")
        else:
            finding_ids.add(finding_id)
        for field in ("statement", "importance", "confidence"):
            if not isinstance(finding.get(field), str) or not finding.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        _validate_known_refs(finding.get("evidence_refs"), evidence_ids, f"{path}.evidence_refs", errors)
        _validate_known_refs(
            finding.get("boundary_refs"),
            boundary_ids,
            f"{path}.boundary_refs",
            errors,
            allow_empty=True,
        )

    candidates = pack.get("candidate_explanations")
    candidate_ids: set[str] = set()
    if not isinstance(candidates, list):
        errors.append("analysis_material_pack.candidate_explanations 必须是列表")
        candidates = []
    for index, candidate in enumerate(candidates):
        path = f"analysis_material_pack.candidate_explanations[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{path} 必须是对象")
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            errors.append(f"{path}.candidate_id 不得为空")
        elif candidate_id in candidate_ids:
            errors.append(f"{path}.candidate_id 重复：{candidate_id}")
        else:
            candidate_ids.add(candidate_id)
        for field in ("statement", "status", "expected_value"):
            if not isinstance(candidate.get(field), str) or not candidate.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        _validate_known_refs(
            candidate.get("evidence_refs"),
            evidence_ids,
            f"{path}.evidence_refs",
            errors,
            allow_empty=True,
        )

    gaps = pack.get("gaps")
    gap_ids: set[str] = set()
    if not isinstance(gaps, list):
        errors.append("analysis_material_pack.gaps 必须是列表")
        gaps = []
    for index, gap in enumerate(gaps):
        path = f"analysis_material_pack.gaps[{index}]"
        if not isinstance(gap, dict):
            errors.append(f"{path} 必须是对象")
            continue
        gap_id = gap.get("gap_id")
        if not isinstance(gap_id, str) or not gap_id.strip():
            errors.append(f"{path}.gap_id 不得为空")
        elif gap_id in gap_ids:
            errors.append(f"{path}.gap_id 重复：{gap_id}")
        else:
            gap_ids.add(gap_id)
        for field in ("question", "importance", "expected_value", "feasibility"):
            if not isinstance(gap.get(field), str) or not gap.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        if not isinstance(gap.get("related_refs"), list):
            errors.append(f"{path}.related_refs 必须是列表")

    material_ids = finding_ids | candidate_ids | gap_ids
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        parent_id = candidate.get("parent_id")
        if parent_id is not None and parent_id not in finding_ids | candidate_ids:
            errors.append(
                f"analysis_material_pack.candidate_explanations[{index}].parent_id "
                f"引用未知材料：{parent_id}"
            )
    for index, boundary in enumerate(boundaries):
        if isinstance(boundary, dict):
            _validate_known_refs(
                boundary.get("affected_material_refs"),
                material_ids,
                f"analysis_material_pack.boundaries[{index}].affected_material_refs",
                errors,
                allow_empty=True,
            )
    for index, gap in enumerate(gaps):
        if isinstance(gap, dict):
            _validate_known_refs(
                gap.get("related_refs"),
                finding_ids | candidate_ids,
                f"analysis_material_pack.gaps[{index}].related_refs",
                errors,
                allow_empty=True,
            )

    charts = pack.get("chart_candidates")
    chart_ids: set[str] = set()
    if not isinstance(charts, list):
        errors.append("analysis_material_pack.chart_candidates 必须是列表")
        charts = []
    elif not charts:
        warnings.append("WARNING: analysis_material_pack.chart_candidates 为空；请确认该分析不适合数据图")
    for index, chart in enumerate(charts):
        path = f"analysis_material_pack.chart_candidates[{index}]"
        if not isinstance(chart, dict):
            errors.append(f"{path} 必须是对象")
            continue
        chart_id = chart.get("chart_id")
        if not isinstance(chart_id, str) or not chart_id.strip():
            errors.append(f"{path}.chart_id 不得为空")
        elif chart_id in chart_ids:
            errors.append(f"{path}.chart_id 重复：{chart_id}")
        else:
            chart_ids.add(chart_id)
        for field in ("question_answered", "recommended_form", "editability_need"):
            if not isinstance(chart.get(field), str) or not chart.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        _validate_known_refs(chart.get("evidence_refs"), evidence_ids, f"{path}.evidence_refs", errors)

    decision_log = pack.get("analysis_decision_log")
    if not isinstance(decision_log, dict):
        errors.append("analysis_material_pack.analysis_decision_log 必须是对象")
        entries: list[object] = []
    else:
        entries = decision_log.get("entries")
        if not isinstance(entries, list) or not entries:
            errors.append("analysis_material_pack.analysis_decision_log.entries 必须是非空列表")
            entries = []

    branch_ids: set[str] = set()
    for index, entry in enumerate(entries):
        path = f"analysis_material_pack.analysis_decision_log.entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path} 必须是对象")
            continue
        branch_id = entry.get("branch_id")
        if not isinstance(branch_id, str) or not branch_id.strip():
            errors.append(f"{path}.branch_id 不得为空")
        elif branch_id in branch_ids:
            errors.append(f"{path}.branch_id 重复：{branch_id}")
        else:
            branch_ids.add(branch_id)
        for field in ("question", "reason"):
            if not isinstance(entry.get(field), str) or not entry.get(field, "").strip():
                errors.append(f"{path}.{field} 不得为空")
        decision = entry.get("decision")
        if decision not in ANALYSIS_BRANCH_DECISIONS:
            errors.append(f"{path}.decision 必须是 continue 或 stop")
        next_probe = entry.get("next_probe")
        if decision == "continue" and (
            not isinstance(next_probe, str) or not next_probe.strip()
        ):
            errors.append(f"{path}.next_probe 在 continue 时不得为空")
        if next_probe is not None and not isinstance(next_probe, str):
            errors.append(f"{path}.next_probe 必须是字符串或 null")
        for field in ("impact_estimate", "confidence", "marginal_explanatory_value"):
            if field not in entry or entry.get(field) in (None, ""):
                errors.append(f"{path}.{field} 不得为空")
        if "depth" in entry and (
            not isinstance(entry.get("depth"), int) or entry.get("depth") < 0
        ):
            errors.append(f"{path}.depth 必须是大于等于 0 的整数")
        _validate_known_refs(
            entry.get("evidence_refs"),
            evidence_ids,
            f"{path}.evidence_refs",
            errors,
            allow_empty=True,
        )

    missing_candidate_decisions = sorted(candidate_ids - branch_ids)
    if missing_candidate_decisions:
        errors.append(
            "analysis_material_pack.analysis_decision_log 缺少候选解释分支："
            f"{missing_candidate_decisions}"
        )


def _validate_known_refs(
    value: object,
    known_ids: set[str],
    path: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} 必须是列表")
        return
    if not allow_empty and not value:
        errors.append(f"{path} 不得为空")
    for index, ref in enumerate(value):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{path}[{index}] 必须是非空字符串")
        elif ref not in known_ids:
            errors.append(f"{path}[{index}] 引用未知 id：{ref}")


def _validate_analysis_material_pack_legacy(
    pack: object,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(pack, dict):
        errors.append("analysis_material_pack 必须是对象")
        return

    required = [
        "material_goal",
        "diagnosis_frame",
        "driver_tree",
        "chart_inventory",
        "react_context_projection",
        "ppt_usage_notes",
    ]
    for field in required:
        if field not in pack:
            errors.append(f"analysis_material_pack 缺少必需字段：{field}")

    if not isinstance(pack.get("material_goal"), str) or not pack.get("material_goal", "").strip():
        errors.append("analysis_material_pack.material_goal 不得为空")

    diagnosis = pack.get("diagnosis_frame")
    if not isinstance(diagnosis, dict):
        errors.append("analysis_material_pack.diagnosis_frame 必须是对象")
    else:
        for field in ("target_metric", "movement_claim", "time_window", "judgement"):
            if not isinstance(diagnosis.get(field), str) or not diagnosis.get(field, "").strip():
                errors.append(f"analysis_material_pack.diagnosis_frame.{field} 不得为空")

    drivers = pack.get("driver_tree")
    subdriver_contexts: dict[str, dict[str, object]] = {}
    if not isinstance(drivers, list) or not drivers:
        errors.append("analysis_material_pack.driver_tree 必须是非空列表")
    else:
        if len(drivers) < 2:
            warnings.append("WARNING: analysis_material_pack.driver_tree 少于 2 个主因，PPT 素材可能偏薄")
        for i, driver in enumerate(drivers):
            _validate_material_driver(driver, f"analysis_material_pack.driver_tree[{i}]", errors, warnings)
        subdriver_contexts = _collect_subdriver_contexts(drivers, errors)

    charts = pack.get("chart_inventory")
    if not isinstance(charts, list):
        errors.append("analysis_material_pack.chart_inventory 必须是列表")
    elif not charts:
        warnings.append("WARNING: analysis_material_pack.chart_inventory 为空，PPT/React 可视化素材不足")

    notes = pack.get("ppt_usage_notes")
    if not isinstance(notes, list):
        errors.append("analysis_material_pack.ppt_usage_notes 必须是列表")

    _validate_react_context_projection(
        pack.get("react_context_projection"),
        subdriver_contexts,
        errors,
    )


def _validate_material_driver(
    driver: object,
    path: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(driver, dict):
        errors.append(f"{path} 必须是对象")
        return

    for field in (
        "id",
        "driver",
        "rank",
        "claim",
        "contribution",
        "evidence_refs",
        "context_inheritance",
        "subdrivers",
        "chart_candidates",
    ):
        if field not in driver:
            errors.append(f"{path}.{field} 缺失")

    for field in ("id", "driver", "claim"):
        if field in driver and (not isinstance(driver.get(field), str) or not driver.get(field, "").strip()):
            errors.append(f"{path}.{field} 不得为空")

    if "rank" in driver and not isinstance(driver.get("rank"), int):
        errors.append(f"{path}.rank 必须是整数")

    contribution = driver.get("contribution")
    if not isinstance(contribution, dict):
        errors.append(f"{path}.contribution 必须是对象")
    else:
        if not isinstance(contribution.get("value"), (int, float)):
            errors.append(f"{path}.contribution.value 必须是数字")
        if not isinstance(contribution.get("unit"), str) or not contribution.get("unit", "").strip():
            errors.append(f"{path}.contribution.unit 不得为空")

    if "evidence_refs" in driver and not _is_non_empty_string_list(driver.get("evidence_refs")):
        errors.append(f"{path}.evidence_refs 必须是非空字符串列表")

    context = driver.get("context_inheritance")
    if not isinstance(context, dict):
        errors.append(f"{path}.context_inheritance 必须是对象")
    else:
        for field in ("inherits_from", "metric", "time_window", "parent_claim_ref", "analysis_scope"):
            if not isinstance(context.get(field), str) or not context.get(field, "").strip():
                errors.append(f"{path}.context_inheritance.{field} 不得为空")
        if context.get("inherits_from") != "diagnosis_frame":
            errors.append(f"{path}.context_inheritance.inherits_from 必须是 diagnosis_frame")

    if "chart_candidates" in driver and not _is_non_empty_string_list(driver.get("chart_candidates")):
        errors.append(f"{path}.chart_candidates 必须是非空字符串列表")

    subdrivers = driver.get("subdrivers")
    if not isinstance(subdrivers, list) or not subdrivers:
        errors.append(f"{path}.subdrivers 必须是非空列表")
        return
    if len(subdrivers) < 2:
        warnings.append(f"WARNING: {path}.subdrivers 少于 2 个，子分析素材可能偏薄")
    for i, subdriver in enumerate(subdrivers):
        _validate_material_subdriver(
            subdriver,
            f"{path}.subdrivers[{i}]",
            driver.get("id"),
            driver.get("contribution"),
            errors,
        )


def _validate_material_subdriver(
    subdriver: object,
    path: str,
    parent_driver_id: object,
    parent_contribution: object,
    errors: list[str],
) -> None:
    if not isinstance(subdriver, dict):
        errors.append(f"{path} 必须是对象")
        return

    for field in (
        "id",
        "parent_driver_id",
        "hypothesis",
        "claim_scope",
        "linkage_type",
        "inheritance_statement",
        "support_status",
        "evidence_refs",
        "possible_analysis",
        "chart_candidates",
    ):
        if field not in subdriver:
            errors.append(f"{path}.{field} 缺失")

    for field in ("id", "parent_driver_id", "hypothesis", "inheritance_statement", "possible_analysis"):
        if field in subdriver and (not isinstance(subdriver.get(field), str) or not subdriver.get(field, "").strip()):
            errors.append(f"{path}.{field} 不得为空")

    if (
        isinstance(parent_driver_id, str)
        and isinstance(subdriver.get("parent_driver_id"), str)
        and subdriver["parent_driver_id"] != parent_driver_id
    ):
        errors.append(f"{path}.parent_driver_id 必须等于父主因 id：{parent_driver_id}")

    claim_scope = subdriver.get("claim_scope")
    if claim_scope not in MATERIAL_CLAIM_SCOPES:
        errors.append(f"{path}.claim_scope 不支持：{claim_scope}")

    linkage_type = subdriver.get("linkage_type")
    if linkage_type not in MATERIAL_LINKAGE_TYPES:
        errors.append(f"{path}.linkage_type 不支持：{linkage_type}")

    status = subdriver.get("support_status")
    if status not in MATERIAL_SUPPORT_STATUSES:
        errors.append(f"{path}.support_status 不支持：{status}")

    if "evidence_refs" in subdriver and not isinstance(subdriver.get("evidence_refs"), list):
        errors.append(f"{path}.evidence_refs 必须是列表")
    if "chart_candidates" in subdriver and not _is_non_empty_string_list(subdriver.get("chart_candidates")):
        errors.append(f"{path}.chart_candidates 必须是非空字符串列表")
    if isinstance(subdriver.get("contribution"), dict):
        _validate_child_contribution_scope(
            subdriver["contribution"],
            parent_contribution,
            path,
            errors,
        )


def _collect_subdriver_contexts(
    drivers: list[object],
    errors: list[str],
) -> dict[str, dict[str, object]]:
    contexts: dict[str, dict[str, object]] = {}
    for driver in drivers:
        if not isinstance(driver, dict):
            continue
        parent_id = driver.get("id")
        if not isinstance(parent_id, str):
            continue
        for subdriver in driver.get("subdrivers", []):
            if not isinstance(subdriver, dict):
                continue
            subdriver_id = subdriver.get("id")
            if not isinstance(subdriver_id, str):
                continue
            if subdriver_id in contexts:
                errors.append(f"analysis_material_pack.driver_tree 子观点 id 重复：{subdriver_id}")
                continue
            context = driver.get("context_inheritance")
            if not isinstance(context, dict):
                context = {}
            contexts[subdriver_id] = {
                "parent_driver_id": parent_id,
                "parent_claim": driver.get("claim"),
                "parent_contribution": driver.get("contribution"),
                "parent_analysis_scope": context.get("analysis_scope"),
                "inherited_metric": context.get("metric"),
                "inherited_time_window": context.get("time_window"),
                "claim_scope": subdriver.get("claim_scope"),
                "linkage_type": subdriver.get("linkage_type"),
                "inheritance_statement": subdriver.get("inheritance_statement"),
            }
    return contexts


def _validate_react_context_projection(
    projection: object,
    subdriver_contexts: dict[str, dict[str, object]],
    errors: list[str],
) -> None:
    if not isinstance(projection, dict):
        errors.append("analysis_material_pack.react_context_projection 必须是对象")
        return

    for field in ("context_id", "provider", "inheritance_index", "display_rules"):
        if field not in projection:
            errors.append(f"analysis_material_pack.react_context_projection.{field} 缺失")

    for field in ("context_id", "provider"):
        if field in projection and (not isinstance(projection.get(field), str) or not projection.get(field, "").strip()):
            errors.append(f"analysis_material_pack.react_context_projection.{field} 不得为空")

    if projection.get("provider") != "AnalysisMaterialContext":
        errors.append("analysis_material_pack.react_context_projection.provider 必须是 AnalysisMaterialContext")

    inheritance_index = projection.get("inheritance_index")
    if not isinstance(inheritance_index, dict):
        errors.append("analysis_material_pack.react_context_projection.inheritance_index 必须是对象")
        return

    missing = sorted(set(subdriver_contexts) - set(inheritance_index))
    extra = sorted(set(inheritance_index) - set(subdriver_contexts))
    if missing:
        errors.append(f"react_context_projection.inheritance_index 缺少子观点：{missing}")
    if extra:
        errors.append(f"react_context_projection.inheritance_index 包含未知子观点：{extra}")

    for subdriver_id, expected in subdriver_contexts.items():
        item = inheritance_index.get(subdriver_id)
        item_path = f"analysis_material_pack.react_context_projection.inheritance_index.{subdriver_id}"
        if not isinstance(item, dict):
            errors.append(f"{item_path} 必须是对象")
            continue
        for field in (
            "parent_driver_id",
            "parent_claim",
            "parent_contribution",
            "parent_analysis_scope",
            "inherited_metric",
            "inherited_time_window",
            "claim_scope",
            "linkage_type",
            "inheritance_statement",
        ):
            if field not in item:
                errors.append(f"{item_path}.{field} 缺失")
        for field in ("parent_driver_id", "parent_claim", "parent_analysis_scope", "inherited_metric", "inherited_time_window", "claim_scope", "linkage_type", "inheritance_statement"):
            if field in item and (not isinstance(item.get(field), str) or not item.get(field, "").strip()):
                errors.append(f"{item_path}.{field} 不得为空")
        if "parent_contribution" in item and not isinstance(item.get("parent_contribution"), dict):
            errors.append(f"{item_path}.parent_contribution 必须是对象")
        if item.get("parent_driver_id") != expected.get("parent_driver_id"):
            errors.append(f"{item_path}.parent_driver_id 与 driver_tree 不一致")
        if item.get("parent_claim") != expected.get("parent_claim"):
            errors.append(f"{item_path}.parent_claim 与父主因 claim 不一致")
        if item.get("parent_contribution") != expected.get("parent_contribution"):
            errors.append(f"{item_path}.parent_contribution 与父主因 contribution 不一致")
        if item.get("parent_analysis_scope") != expected.get("parent_analysis_scope"):
            errors.append(f"{item_path}.parent_analysis_scope 与父主因 analysis_scope 不一致")
        if item.get("inherited_metric") != expected.get("inherited_metric"):
            errors.append(f"{item_path}.inherited_metric 与父主因 metric 不一致")
        if item.get("inherited_time_window") != expected.get("inherited_time_window"):
            errors.append(f"{item_path}.inherited_time_window 与父主因 time_window 不一致")
        if item.get("claim_scope") != expected.get("claim_scope"):
            errors.append(f"{item_path}.claim_scope 与子观点不一致")
        if item.get("linkage_type") != expected.get("linkage_type"):
            errors.append(f"{item_path}.linkage_type 与子观点不一致")
        if item.get("inheritance_statement") != expected.get("inheritance_statement"):
            errors.append(f"{item_path}.inheritance_statement 与子观点不一致")

    if "display_rules" in projection and not _is_non_empty_string_list(projection.get("display_rules")):
        errors.append("analysis_material_pack.react_context_projection.display_rules 必须是非空字符串列表")


def _validate_child_contribution_scope(
    child_contribution: dict,
    parent_contribution: object,
    path: str,
    errors: list[str],
) -> None:
    if not isinstance(parent_contribution, dict):
        return
    child_value = child_contribution.get("value")
    parent_value = parent_contribution.get("value")
    if isinstance(child_value, (int, float)) and isinstance(parent_value, (int, float)):
        if abs(child_value) > abs(parent_value):
            errors.append(f"{path}.contribution.value 不得超过父主因贡献绝对值")


def _is_non_empty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Validate a final report JSON file.")
    parser.add_argument("final_json", help="Path to a final report JSON file.")
    args = parser.parse_args()

    final = json.loads(Path(args.final_json).read_text(encoding="utf-8"))
    ok, messages = validate_final_output(final)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
