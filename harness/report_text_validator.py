"""Validate report_text_pack v0.4 before HTML or React rendering."""

from __future__ import annotations

import re

try:
    from harness.agent_runtime_validator import (
        EXPECTED_AGENT_MANIFESTS,
        load_and_validate_agent_manifests,
    )
except ModuleNotFoundError:  # Direct script execution from harness/.
    from agent_runtime_validator import (
        EXPECTED_AGENT_MANIFESTS,
        load_and_validate_agent_manifests,
    )


TEXT_PACK_VERSION = "0.4"
MATERIAL_PACK_VERSION = "0.3"
CAUSAL_STATUSES = {"descriptive", "associative", "causal", "counterevidence"}
FINAL_QUESTION_STATUSES = {"supported", "contradicted", "not_applicable", "unresolved"}
QUESTION_HISTORY_STATUSES = {"supported", "contradicted", "missing", "not_applicable"}
VERIFICATION_STATUSES = {"verified", "bounded"}
UTILITY_CONTRIBUTIONS = {"answers_research_question", "establishes_scope", "states_boundary"}
BODY_ROLES = {"claim_sentence", "context_sentence", "authorized_strategy_sentence"}
SEGMENT_ROLES = {"combined", "evidence", "conclusion", "strategy"}
REVIEW_CHECKS = {
    "expression",
    "data_evidence",
    "verification_logic",
    "business_context",
    "report_utility",
    "line_fit",
}
SUMMARY_ROLE_RANK = {
    "goal_attainment": 0,
    "core_metric": 1,
    "key_question_answer": 2,
    "solution": 3,
    "boundary": 4,
}
THIN_RESULT_ROUTES = {
    "evidence_does_not_support_conclusion": "react",
    "expression_title_or_line_fit": "writer",
    "no_report_value": "controller",
}
HYPE_PATTERNS = (
    r"全面崩塌",
    r"断崖式",
    r"史诗级",
    r"彻底失败",
    r"致命",
    r"震撼",
    r"惊人",
    r"绝对",
    r"必然",
)
RESPONSIBILITY_PATTERNS = (r"责任在", r"责任归因", r"失职", r"管理不善")
ADVICE_PATTERNS = (r"建议", r"应当", r"应该", r"必须", r"立即", r"务必", r"应优先", r"需要采取")
FILLER_PATTERNS = (r"随着.{0,12}发展", r"在当今.{0,12}时代", r"这一节最重要", r"后续需要跟进", r"需要关注")
VISIBLE_ANSWER_LABEL_PATTERN = re.compile(
    r"^\s*(?:证据|结论|边界|判断|现有证据|证据边界|总体判断|核心表现|结构解释)\s*[：:。．]"
)
META_DISCLOSURE_PATTERNS = (
    r"以下结论",
    r"通过验证链",
    r"只使用.{0,12}数据",
    r"不延伸为",
    r"不做.{0,12}判断",
    r"本文仅",
    r"本报告仅",
)
SENTENCE_END_PATTERN = re.compile(r"[。！？!?]\s*$")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require(value: object, fields: tuple[str, ...], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path} 必须是对象")
        return False
    for field in fields:
        if field not in value:
            errors.append(f"{path} 缺少必需字段：{field}")
    return True


def _strings(value: object, path: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not _text(item) for item in value):
        errors.append(f"{path} 必须是字符串列表")
        return []
    if not allow_empty and not value:
        errors.append(f"{path} 不得为空")
    return value


def _refs(refs: list[str], valid: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(set(refs) - valid)
    if missing:
        errors.append(f"{path} 包含未知引用：{missing}")


def _unique(value: object, seen: set[str], path: str, errors: list[str]) -> None:
    if not _text(value):
        errors.append(f"{path} 必须是非空字符串")
    elif value in seen:
        errors.append(f"{path} 重复：{value}")
    else:
        seen.add(value)


def _line_fit(value: object, path: str, errors: list[str], expected_max: int | None = None) -> None:
    if not _require(value, ("max_lines", "planned_lines"), path, errors):
        return
    max_lines = value.get("max_lines")
    planned = value.get("planned_lines")
    if not isinstance(max_lines, int) or max_lines < 1:
        errors.append(f"{path}.max_lines 必须是正整数")
    if not isinstance(planned, int) or planned < 1:
        errors.append(f"{path}.planned_lines 必须是正整数")
    if isinstance(max_lines, int) and isinstance(planned, int) and planned > max_lines:
        errors.append(f"{path}.planned_lines 不得超过 max_lines")
    if expected_max is not None and max_lines != expected_max:
        errors.append(f"{path}.max_lines 必须等于 layout_context.title_max_lines")


def _visible_sentence(value: object, path: str, errors: list[str]) -> None:
    if not _text(value):
        errors.append(f"{path} 不得为空")
        return
    text = value.strip()
    if VISIBLE_ANSWER_LABEL_PATTERN.search(text):
        errors.append(f"{path} 不得外显证据、结论或边界答题标签")
    if not SENTENCE_END_PATTERN.search(text):
        errors.append(f"{path} 必须是以句号、问号或感叹号结束的完整句子")


def validate_report_text_payload(payload: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return False, ["payload 必须是对象"]

    material = payload.get("analysis_material_pack")
    pack = payload.get("report_text_pack")
    if not isinstance(material, dict):
        errors.append("analysis_material_pack 必须是对象")
    if not isinstance(pack, dict):
        errors.append("report_text_pack 必须是对象")
    if errors:
        return False, errors

    if material.get("contract_version") != MATERIAL_PACK_VERSION:
        errors.append(f"analysis_material_pack.contract_version 必须为 {MATERIAL_PACK_VERSION}")
    if pack.get("contract_version") != TEXT_PACK_VERSION:
        errors.append(f"report_text_pack.contract_version 必须为 {TEXT_PACK_VERSION}")

    findings = material.get("validated_findings", [])
    evidence = material.get("evidence_inventory", [])
    if not isinstance(findings, list) or not findings:
        errors.append("analysis_material_pack.validated_findings 必须是非空列表")
        findings = []
    if not isinstance(evidence, list) or not evidence:
        errors.append("analysis_material_pack.evidence_inventory 必须是非空列表")
        evidence = []

    finding_map: dict[str, dict] = {}
    finding_evidence: dict[str, set[str]] = {}
    for index, finding in enumerate(findings):
        path = f"analysis_material_pack.validated_findings[{index}]"
        if not _require(finding, ("finding_id", "statement", "causal_status", "evidence_refs"), path, errors):
            continue
        finding_id = finding.get("finding_id")
        if not _text(finding_id) or finding_id in finding_map:
            errors.append(f"{path}.finding_id 缺失或重复")
            continue
        finding_map[finding_id] = finding
        refs = finding.get("evidence_refs", [])
        finding_evidence[finding_id] = set(refs) if isinstance(refs, list) else set()

    evidence_ids = {
        item.get("evidence_id")
        for item in evidence
        if isinstance(item, dict) and _text(item.get("evidence_id"))
    }
    if len(evidence_ids) != len(evidence):
        errors.append("analysis_material_pack.evidence_inventory 的 evidence_id 必须完整且唯一")
    finding_ids = set(finding_map)

    manifests_ok, manifests, manifest_errors = load_and_validate_agent_manifests()
    if not manifests_ok:
        errors.extend(f"agent runtime manifest: {item}" for item in manifest_errors)
    manifest_temperatures = {
        role: manifest.get("execution", {}).get("temperature")
        for role, manifest in manifests.items()
    }

    runtime = pack.get("runtime_policy")
    reviewer_temperature = manifest_temperatures.get("reviewer")
    if _require(
        runtime,
        ("temperature_source", "manifest_validation_status", "execution_receipts"),
        "report_text_pack.runtime_policy",
        errors,
    ):
        if runtime.get("temperature_source") != "agent_manifests":
            errors.append("runtime_policy.temperature_source 必须为 agent_manifests")
        if runtime.get("manifest_validation_status") != "pass":
            errors.append("runtime_policy.manifest_validation_status 必须为 pass")
        receipts = runtime.get("execution_receipts")
        if not isinstance(receipts, dict) or set(receipts) != set(EXPECTED_AGENT_MANIFESTS):
            errors.append("runtime_policy.execution_receipts 必须恰好包含六个 Agent")
            receipts = {}
        for role, expected in EXPECTED_AGENT_MANIFESTS.items():
            receipt = receipts.get(role)
            path = f"runtime_policy.execution_receipts.{role}"
            if not _require(
                receipt,
                ("manifest_ref", "configured_temperature", "applied_temperature", "status"),
                path,
                errors,
            ):
                continue
            if receipt.get("manifest_ref") != expected["ref"]:
                errors.append(f"{path}.manifest_ref 与 Agent manifest 不一致")
            manifest_temperature = manifest_temperatures.get(role)
            if receipt.get("configured_temperature") != manifest_temperature:
                errors.append(f"{path}.configured_temperature 与 Agent manifest 不一致")
            if receipt.get("applied_temperature") != manifest_temperature:
                errors.append(f"{path}.applied_temperature 未执行 Agent manifest 温度")
            if receipt.get("status") != "enforced":
                errors.append(f"{path}.status 必须为 enforced")

    prewrite = pack.get("prewrite_prompt")
    if _require(prewrite, ("ref", "version", "applied"), "report_text_pack.prewrite_prompt", errors):
        if prewrite.get("ref") != "references/report_writing_micro_prompt.md":
            errors.append("prewrite_prompt.ref 不正确")
        if prewrite.get("version") != "0.1" or prewrite.get("applied") is not True:
            errors.append("prewrite_prompt 必须使用 0.1 且 applied=true")

    goal = pack.get("report_goal")
    if _require(
        goal,
        ("research_question", "audience", "business_context", "decision_advice_mode", "explicit_request_ref"),
        "report_text_pack.report_goal",
        errors,
    ):
        for field in ("research_question", "audience", "business_context"):
            if not _text(goal.get(field)):
                errors.append(f"report_text_pack.report_goal.{field} 不得为空")
        advice_mode = goal.get("decision_advice_mode")
        if advice_mode not in {"forbidden", "explicitly_requested"}:
            errors.append("report_goal.decision_advice_mode 不受支持")
        if advice_mode == "explicitly_requested" and not _text(goal.get("explicit_request_ref")):
            errors.append("显式请求建议时必须提供 explicit_request_ref")
    else:
        advice_mode = None

    controller = pack.get("controller_resolution")
    if _require(
        controller,
        (
            "controller_run_id",
            "manifest_ref",
            "temperature",
            "status",
            "question_results",
            "omitted_units",
            "context_policy",
        ),
        "report_text_pack.controller_resolution",
        errors,
    ):
        if controller.get("manifest_ref") != EXPECTED_AGENT_MANIFESTS["controller"]["ref"]:
            errors.append("controller_resolution.manifest_ref 不正确")
        if controller.get("temperature") != manifest_temperatures.get("controller"):
            errors.append("controller_resolution.temperature 未使用 controller manifest")
        if controller.get("status") not in {"answered", "partially_answered", "unanswered"}:
            errors.append("controller_resolution.status 不受支持")
        context_policy = controller.get("context_policy")
        if _require(
            context_policy,
            ("unit_packets_only", "full_material_pack_sent_to_writer", "full_material_pack_sent_to_reviewer"),
            "controller_resolution.context_policy",
            errors,
        ):
            if context_policy.get("unit_packets_only") is not True:
                errors.append("context_policy.unit_packets_only 必须为 true")
            if context_policy.get("full_material_pack_sent_to_writer") is not False:
                errors.append("不得把 full material pack 发送给 writer")
            if context_policy.get("full_material_pack_sent_to_reviewer") is not False:
                errors.append("不得把 full material pack 发送给 reviewer")

    visuals = pack.get("visual_evidence", [])
    if not isinstance(visuals, list) or not visuals:
        errors.append("report_text_pack.visual_evidence 必须是非空列表")
        visuals = []
    visual_map: dict[str, dict] = {}
    for index, visual in enumerate(visuals):
        path = f"report_text_pack.visual_evidence[{index}]"
        if not _require(
            visual,
            (
                "visual_id",
                "kind",
                "status",
                "data_ref",
                "unit",
                "time_scope",
                "comparison_basis",
                "report_position",
                "evidence_refs",
                "finding_refs",
            ),
            path,
            errors,
        ):
            continue
        visual_id = visual.get("visual_id")
        if not _text(visual_id) or visual_id in visual_map:
            errors.append(f"{path}.visual_id 缺失或重复")
            continue
        visual_map[visual_id] = visual
        if visual.get("status") != "validated":
            errors.append(f"{path}.status 必须为 validated")
        for field in ("kind", "data_ref", "unit", "time_scope", "comparison_basis", "report_position"):
            if not _text(visual.get(field)):
                errors.append(f"{path}.{field} 不得为空")
        visual_evidence = _strings(visual.get("evidence_refs"), f"{path}.evidence_refs", errors)
        visual_findings = _strings(visual.get("finding_refs"), f"{path}.finding_refs", errors)
        _refs(visual_evidence, evidence_ids, f"{path}.evidence_refs", errors)
        _refs(visual_findings, finding_ids, f"{path}.finding_refs", errors)
        allowed = set().union(*(finding_evidence.get(ref, set()) for ref in visual_findings))
        if set(visual_evidence) - allowed:
            errors.append(f"{path}.evidence_refs 超出 finding_refs 的证据范围")
    visual_ids = set(visual_map)

    sections = pack.get("sections", [])
    if not isinstance(sections, list) or not sections:
        errors.append("report_text_pack.sections 必须是非空列表")
        sections = []
    section_ids: set[str] = set()
    conclusion_ids: set[str] = set()
    text_ids: set[str] = set()
    title_text_ids: set[str] = set()
    section_evidence: dict[str, set[str]] = {}
    section_verification: dict[str, str] = {}
    visible_texts: list[tuple[str, str]] = []

    for index, section in enumerate(sections):
        path = f"report_text_pack.sections[{index}]"
        if not _require(
            section,
            (
                "section_id",
                "unit_packet",
                "writer_run",
                "resolution_log",
                "verification",
                "utility",
                "logic_chain",
                "conclusion",
                "title",
                "subtitle",
                "visual_texts",
                "body_blocks",
                "adversarial_review",
            ),
            path,
            errors,
        ):
            continue
        section_id = section.get("section_id")
        _unique(section_id, section_ids, f"{path}.section_id", errors)
        if not _text(section_id):
            continue

        packet = section.get("unit_packet")
        if not _require(
            packet,
            (
                "packet_id",
                "context_scope",
                "full_report_context_included",
                "research_question",
                "business_context",
                "selected_finding_refs",
                "selected_evidence_refs",
                "selected_visual_refs",
                "layout_context",
            ),
            f"{path}.unit_packet",
            errors,
        ):
            continue
        if packet.get("context_scope") != "single_report_unit":
            errors.append(f"{path}.unit_packet.context_scope 必须为 single_report_unit")
        if packet.get("full_report_context_included") is not False:
            errors.append(f"{path}.unit_packet 不得包含 full report context")
        for field in ("packet_id", "research_question", "business_context"):
            if not _text(packet.get(field)):
                errors.append(f"{path}.unit_packet.{field} 不得为空")
        selected_findings = _strings(packet.get("selected_finding_refs"), f"{path}.unit_packet.selected_finding_refs", errors)
        selected_evidence = _strings(packet.get("selected_evidence_refs"), f"{path}.unit_packet.selected_evidence_refs", errors)
        selected_visuals = _strings(packet.get("selected_visual_refs"), f"{path}.unit_packet.selected_visual_refs", errors)
        _refs(selected_findings, finding_ids, f"{path}.unit_packet.selected_finding_refs", errors)
        _refs(selected_evidence, evidence_ids, f"{path}.unit_packet.selected_evidence_refs", errors)
        _refs(selected_visuals, visual_ids, f"{path}.unit_packet.selected_visual_refs", errors)
        layout = packet.get("layout_context")
        if _require(
            layout,
            ("report_position", "grid_span", "available_width_px", "title_max_lines", "conclusion_preferred_lines"),
            f"{path}.unit_packet.layout_context",
            errors,
        ):
            if not _text(layout.get("report_position")):
                errors.append(f"{path}.unit_packet.layout_context.report_position 不得为空")
            if not isinstance(layout.get("grid_span"), int) or not (1 <= layout.get("grid_span") <= 12):
                errors.append(f"{path}.unit_packet.layout_context.grid_span 必须在 1-12")
            if not isinstance(layout.get("available_width_px"), int) or layout.get("available_width_px") <= 0:
                errors.append(f"{path}.unit_packet.layout_context.available_width_px 必须为正整数")
            if not isinstance(layout.get("title_max_lines"), int) or layout.get("title_max_lines") < 1:
                errors.append(f"{path}.unit_packet.layout_context.title_max_lines 必须为正整数")
            if layout.get("conclusion_preferred_lines") != 1:
                errors.append(f"{path}.unit_packet.layout_context.conclusion_preferred_lines 必须为 1")

        writer_run = section.get("writer_run")
        if _require(
            writer_run,
            ("run_id", "manifest_ref", "temperature", "context_scope", "prewrite_prompt_applied"),
            f"{path}.writer_run",
            errors,
        ):
            if writer_run.get("manifest_ref") != EXPECTED_AGENT_MANIFESTS["writer"]["ref"]:
                errors.append(f"{path}.writer_run.manifest_ref 不正确")
            if writer_run.get("temperature") != manifest_temperatures.get("writer"):
                errors.append(f"{path}.writer_run.temperature 未使用 writer manifest")
            if writer_run.get("context_scope") != "unit_only":
                errors.append(f"{path}.writer_run.context_scope 必须为 unit_only")
            if writer_run.get("prewrite_prompt_applied") is not True:
                errors.append(f"{path}.writer_run 必须应用 prewrite prompt")

        resolution_log = section.get("resolution_log")
        if not isinstance(resolution_log, list):
            errors.append(f"{path}.resolution_log 必须是列表")
            resolution_log = []
        for r_index, item in enumerate(resolution_log):
            r_path = f"{path}.resolution_log[{r_index}]"
            if not _require(item, ("issue_code", "route", "status"), r_path, errors):
                continue
            issue_code = item.get("issue_code")
            if issue_code not in {
                "evidence_does_not_support_conclusion",
                "expression_title_or_line_fit",
            }:
                errors.append(f"{r_path}.issue_code 不属于允许的单薄结论处理类型")
                continue
            if item.get("route") != THIN_RESULT_ROUTES[issue_code]:
                errors.append(f"{r_path}.route 与 issue_code 不一致")
            if item.get("status") != "resolved":
                errors.append(f"{r_path}.status 必须为 resolved 才能进入 sections")

        verification = section.get("verification")
        verification_question_ids: set[str] = set()
        verification_question_roles: dict[str, str] = {}
        verified_evidence: set[str] = set()
        missing_history_questions: set[str] = set()
        final_unresolved: set[str] = set()
        if _require(
            verification,
            ("status", "questions", "backfill_requests", "unresolved_critical_question_refs"),
            f"{path}.verification",
            errors,
        ):
            verification_status = verification.get("status")
            if verification_status not in VERIFICATION_STATUSES:
                errors.append(f"{path}.verification.status 不受支持")
            elif verification_status != "verified":
                errors.append(f"{path}.verification.status 非 verified 单元必须移入 bounded_modules")
            questions = verification.get("questions")
            if not isinstance(questions, list) or len(questions) < 2:
                errors.append(f"{path}.verification.questions 至少需要两个验证问题")
                questions = []
            roles: set[str] = set()
            critical_ids: set[str] = set()
            for q_index, question in enumerate(questions):
                q_path = f"{path}.verification.questions[{q_index}]"
                if not _require(
                    question,
                    ("question_id", "question", "role", "critical", "final_status", "answer", "evidence_refs", "history"),
                    q_path,
                    errors,
                ):
                    continue
                question_id = question.get("question_id")
                _unique(question_id, verification_question_ids, f"{q_path}.question_id", errors)
                if not _text(question.get("question")) or not _text(question.get("role")):
                    errors.append(f"{q_path}.question 和 role 不得为空")
                else:
                    roles.add(question.get("role"))
                    if _text(question_id):
                        verification_question_roles[question_id] = question.get("role")
                if not isinstance(question.get("critical"), bool):
                    errors.append(f"{q_path}.critical 必须是布尔值")
                elif question.get("critical"):
                    critical_ids.add(question_id)
                final_status = question.get("final_status")
                if final_status not in FINAL_QUESTION_STATUSES:
                    errors.append(f"{q_path}.final_status 不受支持")
                if final_status == "unresolved":
                    final_unresolved.add(question_id)
                elif final_status != "not_applicable" and not _text(question.get("answer")):
                    errors.append(f"{q_path}.answer 不得为空")
                q_evidence = _strings(question.get("evidence_refs"), f"{q_path}.evidence_refs", errors, allow_empty=final_status in {"not_applicable", "unresolved"})
                _refs(q_evidence, set(selected_evidence), f"{q_path}.evidence_refs", errors)
                verified_evidence.update(q_evidence)
                history = question.get("history")
                if not isinstance(history, list) or not history:
                    errors.append(f"{q_path}.history 必须是非空列表")
                    history = []
                last_round = 0
                for h_index, item in enumerate(history):
                    h_path = f"{q_path}.history[{h_index}]"
                    if not _require(item, ("round", "status", "evidence_refs"), h_path, errors):
                        continue
                    if not isinstance(item.get("round"), int) or item.get("round") <= last_round:
                        errors.append(f"{h_path}.round 必须严格递增")
                    else:
                        last_round = item.get("round")
                    if item.get("status") not in QUESTION_HISTORY_STATUSES:
                        errors.append(f"{h_path}.status 不受支持")
                    if item.get("status") == "missing":
                        missing_history_questions.add(question_id)
                    h_evidence = _strings(item.get("evidence_refs"), f"{h_path}.evidence_refs", errors, allow_empty=item.get("status") in {"missing", "not_applicable"})
                    _refs(h_evidence, set(selected_evidence), f"{h_path}.evidence_refs", errors)
            if len(roles) < 2:
                errors.append(f"{path}.verification.questions 至少需要两个不同验证角色")

            backfills = verification.get("backfill_requests")
            if not isinstance(backfills, list):
                errors.append(f"{path}.verification.backfill_requests 必须是列表")
                backfills = []
            backfilled_questions: set[str] = set()
            for b_index, backfill in enumerate(backfills):
                b_path = f"{path}.verification.backfill_requests[{b_index}]"
                if not _require(backfill, ("request_id", "question_refs", "requested_data", "status", "returned_evidence_refs"), b_path, errors):
                    continue
                if not _text(backfill.get("request_id")) or not _text(backfill.get("requested_data")):
                    errors.append(f"{b_path}.request_id 和 requested_data 不得为空")
                q_refs = _strings(backfill.get("question_refs"), f"{b_path}.question_refs", errors)
                _refs(q_refs, verification_question_ids, f"{b_path}.question_refs", errors)
                backfilled_questions.update(q_refs)
                if backfill.get("status") not in {"resolved", "blocked"}:
                    errors.append(f"{b_path}.status 不受支持")
                returned = _strings(backfill.get("returned_evidence_refs"), f"{b_path}.returned_evidence_refs", errors, allow_empty=backfill.get("status") == "blocked")
                _refs(returned, set(selected_evidence), f"{b_path}.returned_evidence_refs", errors)
            if missing_history_questions - backfilled_questions:
                errors.append(f"{path}.verification 存在 missing 问题但没有 backfill_request")

            unresolved = _strings(
                verification.get("unresolved_critical_question_refs"),
                f"{path}.verification.unresolved_critical_question_refs",
                errors,
                allow_empty=True,
            )
            _refs(unresolved, critical_ids, f"{path}.verification.unresolved_critical_question_refs", errors)
            if set(unresolved) != (final_unresolved & critical_ids):
                errors.append(f"{path}.verification unresolved critical questions 不一致")
            if verification_status == "verified" and unresolved:
                errors.append(f"{path}.verification verified 时不得有 unresolved critical questions")
            if verification_status == "bounded" and not unresolved:
                errors.append(f"{path}.verification bounded 时必须声明 unresolved critical questions")
        else:
            verification_status = None
        section_verification[section_id] = verification_status

        utility = section.get("utility")
        if _require(utility, ("status", "contribution", "reason"), f"{path}.utility", errors):
            if utility.get("status") != "include":
                errors.append(f"{path}.utility.status 不是 include，不得进入文本包")
            if utility.get("contribution") not in UTILITY_CONTRIBUTIONS:
                errors.append(f"{path}.utility.contribution 不受支持")
            elif utility.get("contribution") == "states_boundary":
                errors.append(f"{path} states_boundary 必须移入 bounded_modules")
            if not _text(utility.get("reason")):
                errors.append(f"{path}.utility.reason 不得为空")

        chain = section.get("logic_chain")
        if not isinstance(chain, list) or not chain:
            errors.append(f"{path}.logic_chain 必须是非空列表")
            chain = []
        step_ids: set[str] = set()
        observation_count = 0
        relationship_count = 0
        conclusion_indexes: list[int] = []
        chain_evidence: set[str] = set()
        for s_index, step in enumerate(chain):
            s_path = f"{path}.logic_chain[{s_index}]"
            if not _require(step, ("step_id", "type", "text", "evidence_refs", "verification_question_refs"), s_path, errors):
                continue
            _unique(step.get("step_id"), step_ids, f"{s_path}.step_id", errors)
            if not _text(step.get("text")):
                errors.append(f"{s_path}.text 不得为空")
            step_evidence = _strings(step.get("evidence_refs"), f"{s_path}.evidence_refs", errors)
            _refs(step_evidence, set(selected_evidence), f"{s_path}.evidence_refs", errors)
            if set(step_evidence) - verified_evidence:
                errors.append(f"{s_path}.evidence_refs 未经过 verification")
            chain_evidence.update(step_evidence)
            q_refs = _strings(step.get("verification_question_refs"), f"{s_path}.verification_question_refs", errors)
            _refs(q_refs, verification_question_ids, f"{s_path}.verification_question_refs", errors)
            step_type = step.get("type")
            if step_type == "observation":
                observation_count += 1
            elif step_type == "relationship":
                relationship_count += 1
            elif step_type == "conclusion":
                conclusion_indexes.append(s_index)
            else:
                errors.append(f"{s_path}.type 不受支持")
        if observation_count < 1 or relationship_count < 1:
            errors.append(f"{path}.logic_chain 至少需要 observation 和 relationship")
        if conclusion_indexes != [len(chain) - 1]:
            errors.append(f"{path}.logic_chain 必须且只能以 conclusion 结束")

        conclusion = section.get("conclusion")
        if not _require(
            conclusion,
            (
                "conclusion_id",
                "text",
                "source_finding_refs",
                "evidence_refs",
                "verification_question_refs",
                "support_status",
                "causal_status",
                "business_value",
                "driver_claim",
                "driver_decomposition_question_refs",
                "render_plan",
            ),
            f"{path}.conclusion",
            errors,
        ):
            continue
        conclusion_id = conclusion.get("conclusion_id")
        _unique(conclusion_id, conclusion_ids, f"{path}.conclusion.conclusion_id", errors)
        conclusion_text = conclusion.get("text")
        if _text(conclusion_text):
            visible_texts.append((f"{path}.conclusion.text", conclusion_text))
        else:
            errors.append(f"{path}.conclusion.text 不得为空")
        source_findings = _strings(conclusion.get("source_finding_refs"), f"{path}.conclusion.source_finding_refs", errors)
        conclusion_evidence = _strings(conclusion.get("evidence_refs"), f"{path}.conclusion.evidence_refs", errors)
        conclusion_questions = _strings(conclusion.get("verification_question_refs"), f"{path}.conclusion.verification_question_refs", errors)
        _refs(source_findings, set(selected_findings), f"{path}.conclusion.source_finding_refs", errors)
        _refs(conclusion_evidence, set(selected_evidence), f"{path}.conclusion.evidence_refs", errors)
        _refs(conclusion_questions, verification_question_ids, f"{path}.conclusion.verification_question_refs", errors)
        source_evidence = set().union(*(finding_evidence.get(ref, set()) for ref in source_findings))
        if set(conclusion_evidence) - source_evidence:
            errors.append(f"{path}.conclusion.evidence_refs 超出 source findings")
        if set(conclusion_evidence) - verified_evidence or set(conclusion_evidence) - chain_evidence:
            errors.append(f"{path}.conclusion.evidence_refs 未完整经过 verification 和 logic_chain")
        if conclusion.get("support_status") != "sufficient":
            errors.append(f"{path}.conclusion.support_status 必须为 sufficient")
        causal_status = conclusion.get("causal_status")
        if causal_status not in CAUSAL_STATUSES:
            errors.append(f"{path}.conclusion.causal_status 不受支持")
        source_statuses = {finding_map[ref].get("causal_status") for ref in source_findings if ref in finding_map}
        if causal_status != "descriptive" and causal_status not in source_statuses:
            errors.append(f"{path}.conclusion.causal_status 强于或不同于 source findings")
        if not _text(conclusion.get("business_value")):
            errors.append(f"{path}.conclusion.business_value 不得为空")
        driver_claim = conclusion.get("driver_claim")
        if not isinstance(driver_claim, bool):
            errors.append(f"{path}.conclusion.driver_claim 必须是布尔值")
        driver_question_refs = _strings(
            conclusion.get("driver_decomposition_question_refs"),
            f"{path}.conclusion.driver_decomposition_question_refs",
            errors,
            allow_empty=driver_claim is False,
        )
        _refs(
            driver_question_refs,
            verification_question_ids,
            f"{path}.conclusion.driver_decomposition_question_refs",
            errors,
        )
        if driver_claim is True:
            invalid_driver_refs = sorted(
                ref
                for ref in driver_question_refs
                if verification_question_roles.get(ref) != "driver_decomposition"
            )
            if invalid_driver_refs:
                errors.append(
                    f"{path}.conclusion.driver_decomposition_question_refs "
                    f"必须只引用 role=driver_decomposition 的验证问题：{invalid_driver_refs}"
                )
        elif driver_question_refs:
            errors.append(
                f"{path}.conclusion.driver_claim=false 时 "
                "driver_decomposition_question_refs 必须为空"
            )
        if chain and isinstance(chain[-1], dict) and chain[-1].get("text") != conclusion_text:
            errors.append(f"{path}.logic_chain 最终结论与 conclusion.text 不一致")

        render_plan = conclusion.get("render_plan")
        if _require(render_plan, ("internal_only", "preferred_lines", "planned_lines", "split_mode", "split_reason", "segments"), f"{path}.conclusion.render_plan", errors):
            if render_plan.get("internal_only") is not True:
                errors.append(f"{path}.conclusion.render_plan.internal_only 必须为 true")
            if render_plan.get("preferred_lines") != 1:
                errors.append(f"{path}.conclusion.render_plan.preferred_lines 必须为 1")
            planned = render_plan.get("planned_lines")
            if not isinstance(planned, int) or not (1 <= planned <= 3):
                errors.append(f"{path}.conclusion.render_plan.planned_lines 必须在 1-3")
                planned = 0
            segments = render_plan.get("segments")
            if not isinstance(segments, list) or len(segments) != planned:
                errors.append(f"{path}.conclusion.render_plan.segments 数量必须等于 planned_lines")
                segments = []
            if planned == 1:
                if render_plan.get("split_mode") != "none" or render_plan.get("split_reason") is not None:
                    errors.append(f"{path}.conclusion 单行时 split_mode 必须为 none 且 split_reason=null")
            elif render_plan.get("split_mode") not in {"evidence_conclusion", "evidence_conclusion_strategy"} or not _text(render_plan.get("split_reason")):
                errors.append(f"{path}.conclusion 多行时必须声明 split_mode 和 split_reason")
            for seg_index, segment in enumerate(segments):
                seg_path = f"{path}.conclusion.render_plan.segments[{seg_index}]"
                if not _require(segment, ("role", "text"), seg_path, errors):
                    continue
                if segment.get("role") not in SEGMENT_ROLES or not _text(segment.get("text")):
                    errors.append(f"{seg_path} role 或 text 无效")
                if segment.get("role") == "strategy" and advice_mode != "explicitly_requested":
                    errors.append(f"{seg_path} strategy 未获授权")

        title_max_lines = layout.get("title_max_lines") if isinstance(layout, dict) else None
        for field in ("title", "subtitle"):
            block = section.get(field)
            b_path = f"{path}.{field}"
            required = ("text_id", "text", "source_conclusion_ref", "line_fit")
            if field == "title":
                required += ("mode", "question_alignment")
            if not _require(block, required, b_path, errors):
                continue
            _unique(block.get("text_id"), text_ids, f"{b_path}.text_id", errors)
            if _text(block.get("text")):
                visible_texts.append((f"{b_path}.text", block.get("text")))
                title_text_ids.add(block.get("text_id"))
                if field == "title" and any(mark in block.get("text") for mark in ("?", "？")):
                    errors.append(f"{b_path}.text 不得使用疑问句")
            else:
                errors.append(f"{b_path}.text 不得为空")
            if block.get("source_conclusion_ref") != conclusion_id:
                errors.append(f"{b_path}.source_conclusion_ref 必须指向本节结论")
            _line_fit(block.get("line_fit"), f"{b_path}.line_fit", errors, title_max_lines if field == "title" else None)
            if field == "title":
                mode = block.get("mode")
                expected_alignment = "direct_answer" if mode == "claim" else "descriptive_scope"
                if mode not in {"claim", "descriptive"}:
                    errors.append(f"{b_path}.mode 不受支持")
                if block.get("question_alignment") != expected_alignment:
                    errors.append(f"{b_path}.question_alignment 应为 {expected_alignment}")

        visual_texts = section.get("visual_texts")
        if not isinstance(visual_texts, list) or not visual_texts:
            errors.append(f"{path}.visual_texts 必须是非空列表")
            visual_texts = []
        covered_visuals: set[str] = set()
        for v_index, block in enumerate(visual_texts):
            v_path = f"{path}.visual_texts[{v_index}]"
            if not _require(block, ("text_id", "visual_ref", "text", "source_conclusion_ref"), v_path, errors):
                continue
            _unique(block.get("text_id"), text_ids, f"{v_path}.text_id", errors)
            if block.get("visual_ref") not in set(selected_visuals):
                errors.append(f"{v_path}.visual_ref 不属于 unit_packet")
            else:
                covered_visuals.add(block.get("visual_ref"))
            if block.get("source_conclusion_ref") != conclusion_id:
                errors.append(f"{v_path}.source_conclusion_ref 必须指向本节结论")
            if _text(block.get("text")):
                visible_texts.append((f"{v_path}.text", block.get("text")))
            else:
                errors.append(f"{v_path}.text 不得为空")
        if covered_visuals != set(selected_visuals):
            errors.append(f"{path}.visual_texts 未覆盖 selected_visual_refs")

        body = section.get("body_blocks")
        if not isinstance(body, list) or not body:
            errors.append(f"{path}.body_blocks 必须是非空列表")
            body = []
        for b_index, block in enumerate(body):
            b_path = f"{path}.body_blocks[{b_index}]"
            if not _require(block, ("text_id", "role", "display_mode", "text", "conclusion_refs", "evidence_refs", "line_fit"), b_path, errors):
                continue
            _unique(block.get("text_id"), text_ids, f"{b_path}.text_id", errors)
            if block.get("role") not in BODY_ROLES:
                errors.append(f"{b_path}.role 不受支持")
            if block.get("display_mode") not in {"line", "point"}:
                errors.append(f"{b_path}.display_mode 必须为 line 或 point")
            if block.get("role") == "authorized_strategy_sentence" and advice_mode != "explicitly_requested":
                errors.append(f"{b_path} authorized_strategy_sentence 未获授权")
            if _text(block.get("text")):
                visible_texts.append((f"{b_path}.text", block.get("text")))
            _visible_sentence(block.get("text"), f"{b_path}.text", errors)
            _line_fit(block.get("line_fit"), f"{b_path}.line_fit", errors)
            if (
                isinstance(block.get("line_fit"), dict)
                and block.get("display_mode") == "line"
                and block["line_fit"].get("planned_lines") != 1
            ):
                errors.append(f"{b_path}.display_mode=line 时 planned_lines 必须为 1；放不进一行时改用 point")
            if set(_strings(block.get("conclusion_refs"), f"{b_path}.conclusion_refs", errors)) != {conclusion_id}:
                errors.append(f"{b_path}.conclusion_refs 必须只指向本节结论")
            block_evidence = _strings(block.get("evidence_refs"), f"{b_path}.evidence_refs", errors)
            if set(block_evidence) - set(conclusion_evidence):
                errors.append(f"{b_path}.evidence_refs 超出本节结论")

        review = section.get("adversarial_review")
        if _require(
            review,
            (
                "reviewer_run_id",
                "manifest_ref",
                "temperature",
                "independent_context",
                "full_material_pack_received",
                "writer_reasoning_received",
                "verdict",
                "failure_category",
                "checks",
                "issues",
                "route_on_fail",
            ),
            f"{path}.adversarial_review",
            errors,
        ):
            if review.get("manifest_ref") != EXPECTED_AGENT_MANIFESTS["reviewer"]["ref"]:
                errors.append(f"{path}.adversarial_review.manifest_ref 不正确")
            if review.get("temperature") != reviewer_temperature:
                errors.append(f"{path}.adversarial_review.temperature 未使用 reviewer manifest")
            if review.get("independent_context") is not True:
                errors.append(f"{path}.adversarial_review 必须使用独立上下文")
            if review.get("full_material_pack_received") is not False or review.get("writer_reasoning_received") is not False:
                errors.append(f"{path}.adversarial_review 接收了禁止的上下文")
            verdict = review.get("verdict")
            if verdict != "pass":
                errors.append(f"{path}.adversarial_review 最终 verdict 必须为 pass")
            checks = review.get("checks")
            if not isinstance(checks, dict) or set(checks) != REVIEW_CHECKS:
                errors.append(f"{path}.adversarial_review.checks 必须恰好包含六项检查")
            elif any(checks.get(key) != "pass" for key in REVIEW_CHECKS):
                errors.append(f"{path}.adversarial_review 存在未通过检查")
            if verdict == "pass":
                if (
                    review.get("failure_category") is not None
                    or review.get("issues") != []
                    or review.get("route_on_fail") is not None
                ):
                    errors.append(
                        f"{path}.adversarial_review pass 时 failure_category/route 必须为空且 issues=[]"
                    )
            else:
                category = review.get("failure_category")
                if category not in THIN_RESULT_ROUTES:
                    errors.append(f"{path}.adversarial_review.failure_category 不受支持")
                elif review.get("route_on_fail") != THIN_RESULT_ROUTES[category]:
                    errors.append(f"{path}.adversarial_review.route_on_fail 与 failure_category 不一致")
                if not isinstance(review.get("issues"), list) or not review.get("issues"):
                    errors.append(f"{path}.adversarial_review fail 时 issues 不得为空")

        section_evidence[section_id] = set(conclusion_evidence)

    bounded_modules = pack.get("bounded_modules")
    if not isinstance(bounded_modules, list):
        errors.append("report_text_pack.bounded_modules 必须是列表")
        bounded_modules = []
    bounded_module_ids: set[str] = set()
    bounded_module_sources: dict[str, str] = {}
    bounded_module_gaps: dict[str, set[str]] = {}
    for index, module in enumerate(bounded_modules):
        path = f"report_text_pack.bounded_modules[{index}]"
        if not _require(
            module,
            (
                "module_id",
                "source_question_ref",
                "source_packet_ref",
                "status",
                "render_disposition",
                "summary_eligible",
                "removable",
                "report_position",
                "visual_refs",
                "evidence_refs",
                "unresolved_gap_refs",
                "title",
                "statements",
            ),
            path,
            errors,
        ):
            continue
        module_id = module.get("module_id")
        _unique(module_id, bounded_module_ids, f"{path}.module_id", errors)
        if not _text(module_id):
            continue
        source_question_ref = module.get("source_question_ref")
        if not _text(source_question_ref) or not _text(module.get("source_packet_ref")):
            errors.append(f"{path}.source_question_ref 和 source_packet_ref 不得为空")
        else:
            bounded_module_sources[module_id] = source_question_ref
        if module.get("status") != "bounded":
            errors.append(f"{path}.status 必须为 bounded")
        if module.get("render_disposition") != "detachable_boundary":
            errors.append(f"{path}.render_disposition 必须为 detachable_boundary")
        if module.get("summary_eligible") is not False:
            errors.append(f"{path}.summary_eligible 必须为 false")
        if module.get("removable") is not True:
            errors.append(f"{path}.removable 必须为 true")
        if not _text(module.get("report_position")):
            errors.append(f"{path}.report_position 不得为空")
        module_visuals = _strings(module.get("visual_refs"), f"{path}.visual_refs", errors, allow_empty=True)
        module_evidence = _strings(module.get("evidence_refs"), f"{path}.evidence_refs", errors)
        module_gaps = _strings(module.get("unresolved_gap_refs"), f"{path}.unresolved_gap_refs", errors)
        _refs(module_visuals, visual_ids, f"{path}.visual_refs", errors)
        _refs(module_evidence, evidence_ids, f"{path}.evidence_refs", errors)
        bounded_module_gaps[module_id] = set(module_gaps)

        title = module.get("title")
        if _require(title, ("text_id", "text", "mode", "line_fit"), f"{path}.title", errors):
            _unique(title.get("text_id"), text_ids, f"{path}.title.text_id", errors)
            if title.get("mode") != "descriptive":
                errors.append(f"{path}.title.mode 必须为 descriptive")
            if _text(title.get("text")):
                visible_texts.append((f"{path}.title.text", title.get("text")))
                if any(mark in title.get("text") for mark in ("?", "？")):
                    errors.append(f"{path}.title.text 不得使用疑问句")
            else:
                errors.append(f"{path}.title.text 不得为空")
            _line_fit(title.get("line_fit"), f"{path}.title.line_fit", errors)
        statements = module.get("statements")
        if not isinstance(statements, list) or not statements:
            errors.append(f"{path}.statements 必须是非空列表")
            statements = []
        for statement_index, block in enumerate(statements):
            b_path = f"{path}.statements[{statement_index}]"
            if not _require(block, ("text_id", "text", "evidence_refs", "line_fit"), b_path, errors):
                continue
            _unique(block.get("text_id"), text_ids, f"{b_path}.text_id", errors)
            if _text(block.get("text")):
                visible_texts.append((f"{b_path}.text", block.get("text")))
            _visible_sentence(block.get("text"), f"{b_path}.text", errors)
            statement_evidence = _strings(
                block.get("evidence_refs"),
                f"{b_path}.evidence_refs",
                errors,
                allow_empty=True,
            )
            if set(statement_evidence) - set(module_evidence):
                errors.append(f"{b_path}.evidence_refs 超出 bounded module")
            _line_fit(block.get("line_fit"), f"{b_path}.line_fit", errors)

    if isinstance(controller, dict):
        omitted_units = controller.get("omitted_units")
        if not isinstance(omitted_units, list):
            errors.append("controller_resolution.omitted_units 必须是列表")
            omitted_units = []
        omitted_ids: set[str] = set()
        for index, item in enumerate(omitted_units):
            path = f"controller_resolution.omitted_units[{index}]"
            if not _require(item, ("unit_id", "issue_code", "route", "render", "reason"), path, errors):
                continue
            unit_id = item.get("unit_id")
            _unique(unit_id, omitted_ids, f"{path}.unit_id", errors)
            if item.get("issue_code") != "no_report_value":
                errors.append(f"{path}.issue_code 只能为 no_report_value")
            if item.get("route") != THIN_RESULT_ROUTES["no_report_value"]:
                errors.append(f"{path}.route 必须为 controller")
            if item.get("render") is not False:
                errors.append(f"{path}.render 必须为 false")
            if not _text(item.get("reason")):
                errors.append(f"{path}.reason 不得为空")
            if unit_id in section_ids or unit_id in bounded_module_ids:
                errors.append(f"{path}.unit_id 不得同时存在于可渲染单元")

        question_results = controller.get("question_results")
        if not isinstance(question_results, list) or not question_results:
            errors.append("controller_resolution.question_results 必须是非空列表")
        else:
            result_ids: set[str] = set()
            result_statuses: list[str] = []
            result_map: dict[str, dict] = {}
            for index, result in enumerate(question_results):
                path = f"controller_resolution.question_results[{index}]"
                if not _require(
                    result,
                    (
                        "question_id",
                        "question",
                        "status",
                        "section_refs",
                        "bounded_module_refs",
                        "unresolved_gap_refs",
                    ),
                    path,
                    errors,
                ):
                    continue
                question_id = result.get("question_id")
                _unique(question_id, result_ids, f"{path}.question_id", errors)
                if _text(question_id):
                    result_map[question_id] = result
                if not _text(result.get("question")):
                    errors.append(f"{path}.question 不得为空")
                status = result.get("status")
                if status not in {"answered", "partially_answered", "unanswered"}:
                    errors.append(f"{path}.status 不受支持")
                else:
                    result_statuses.append(status)
                refs = _strings(
                    result.get("section_refs"),
                    f"{path}.section_refs",
                    errors,
                    allow_empty=status != "answered",
                )
                _refs(refs, section_ids, f"{path}.section_refs", errors)
                bounded_refs = _strings(
                    result.get("bounded_module_refs"),
                    f"{path}.bounded_module_refs",
                    errors,
                    allow_empty=True,
                )
                _refs(bounded_refs, bounded_module_ids, f"{path}.bounded_module_refs", errors)
                if status == "answered" and bounded_refs:
                    errors.append(f"{path} answered 时不得引用 bounded_modules")
                gaps = _strings(result.get("unresolved_gap_refs"), f"{path}.unresolved_gap_refs", errors, allow_empty=status == "answered")
                if status == "answered" and gaps:
                    errors.append(f"{path} answered 时不得有 unresolved gaps")
            expected_status = "answered"
            if "unanswered" in result_statuses:
                expected_status = "unanswered" if all(item == "unanswered" for item in result_statuses) else "partially_answered"
            elif "partially_answered" in result_statuses:
                expected_status = "partially_answered"
            if controller.get("status") != expected_status:
                errors.append("controller_resolution.status 与 question_results 不一致")
            for module_id, question_ref in bounded_module_sources.items():
                result = result_map.get(question_ref)
                if result is None:
                    errors.append(f"bounded_module {module_id} 的 source_question_ref 未知")
                    continue
                if module_id not in result.get("bounded_module_refs", []):
                    errors.append(f"bounded_module {module_id} 未被对应 question_result 引用")
                if bounded_module_gaps.get(module_id) != set(result.get("unresolved_gap_refs", [])):
                    errors.append(f"bounded_module {module_id} 的 unresolved gaps 与 question_result 不一致")

    summary = pack.get("summary_chain")
    if not isinstance(summary, list) or not summary:
        errors.append("report_text_pack.summary_chain 必须是非空列表")
        summary = []
    summary_ids: set[str] = set()
    summary_evidence: dict[str, set[str]] = {}
    previous_id: str | None = None
    previous_rank = -1
    for index, item in enumerate(summary):
        path = f"report_text_pack.summary_chain[{index}]"
        if not _require(
            item,
            ("summary_id", "text_id", "role", "text", "source_title_refs", "section_refs", "evidence_refs", "previous_summary_ref"),
            path,
            errors,
        ):
            continue
        summary_id = item.get("summary_id")
        _unique(summary_id, summary_ids, f"{path}.summary_id", errors)
        _unique(item.get("text_id"), text_ids, f"{path}.text_id", errors)
        role = item.get("role")
        if role not in SUMMARY_ROLE_RANK:
            errors.append(f"{path}.role 不受支持")
            rank = previous_rank
        else:
            rank = SUMMARY_ROLE_RANK[role]
            if rank < previous_rank:
                errors.append(f"{path}.role 没有保持递进顺序")
            previous_rank = rank
        if role == "solution" and advice_mode != "explicitly_requested":
            errors.append(f"{path} solution 未获授权")
        if item.get("previous_summary_ref") != previous_id:
            errors.append(f"{path}.previous_summary_ref 没有形成连续链")
        previous_id = summary_id
        if _text(item.get("text")):
            visible_texts.append((f"{path}.text", item.get("text")))
        else:
            errors.append(f"{path}.text 不得为空")
        source_titles = _strings(item.get("source_title_refs"), f"{path}.source_title_refs", errors)
        _refs(source_titles, title_text_ids, f"{path}.source_title_refs", errors)
        item_sections = _strings(item.get("section_refs"), f"{path}.section_refs", errors)
        _refs(item_sections, section_ids, f"{path}.section_refs", errors)
        item_evidence = _strings(item.get("evidence_refs"), f"{path}.evidence_refs", errors)
        allowed = set().union(*(section_evidence.get(ref, set()) for ref in item_sections))
        if set(item_evidence) - allowed:
            errors.append(f"{path}.evidence_refs 超出 source sections")
        summary_evidence[summary_id] = set(item_evidence)

    report_title = pack.get("report_title")
    if _require(report_title, ("text_id", "text", "mode", "source_summary_refs", "question_alignment", "line_fit"), "report_text_pack.report_title", errors):
        _unique(report_title.get("text_id"), text_ids, "report_title.text_id", errors)
        if _text(report_title.get("text")):
            visible_texts.append(("report_title.text", report_title.get("text")))
            if any(mark in report_title.get("text") for mark in ("?", "？")):
                errors.append("report_title.text 不得使用疑问句")
        else:
            errors.append("report_title.text 不得为空")
        title_summary_refs = _strings(report_title.get("source_summary_refs"), "report_title.source_summary_refs", errors)
        _refs(title_summary_refs, summary_ids, "report_title.source_summary_refs", errors)
        mode = report_title.get("mode")
        expected_alignment = "direct_answer" if mode == "claim" else "descriptive_scope"
        if mode not in {"claim", "descriptive"} or report_title.get("question_alignment") != expected_alignment:
            errors.append("report_title mode 与 question_alignment 不一致")
        if mode == "claim" and isinstance(controller, dict) and controller.get("status") == "unanswered":
            errors.append("研究问题 unanswered 时不得使用 claim report title")
        _line_fit(report_title.get("line_fit"), "report_title.line_fit", errors)

    report_subtitle = pack.get("report_subtitle")
    if _require(report_subtitle, ("text_id", "text", "source_summary_refs", "line_fit"), "report_text_pack.report_subtitle", errors):
        _unique(report_subtitle.get("text_id"), text_ids, "report_subtitle.text_id", errors)
        if _text(report_subtitle.get("text")):
            visible_texts.append(("report_subtitle.text", report_subtitle.get("text")))
        else:
            errors.append("report_subtitle.text 不得为空")
        subtitle_refs = _strings(report_subtitle.get("source_summary_refs"), "report_subtitle.source_summary_refs", errors)
        _refs(subtitle_refs, summary_ids, "report_subtitle.source_summary_refs", errors)
        _line_fit(report_subtitle.get("line_fit"), "report_subtitle.line_fit", errors)

    recommendations = pack.get("recommendations")
    if not isinstance(recommendations, list):
        errors.append("report_text_pack.recommendations 必须是列表")
        recommendations = []
    if advice_mode == "forbidden" and recommendations:
        errors.append("decision_advice_mode=forbidden 时 recommendations 必须为空")
    for index, item in enumerate(recommendations):
        path = f"report_text_pack.recommendations[{index}]"
        if not _require(item, ("text_id", "text", "finding_refs", "evidence_refs"), path, errors):
            continue
        _unique(item.get("text_id"), text_ids, f"{path}.text_id", errors)
        if _text(item.get("text")):
            visible_texts.append((f"{path}.text", item.get("text")))
        rec_findings = _strings(item.get("finding_refs"), f"{path}.finding_refs", errors)
        rec_evidence = _strings(item.get("evidence_refs"), f"{path}.evidence_refs", errors)
        _refs(rec_findings, finding_ids, f"{path}.finding_refs", errors)
        _refs(rec_evidence, evidence_ids, f"{path}.evidence_refs", errors)
        allowed = set().union(*(finding_evidence.get(ref, set()) for ref in rec_findings))
        if set(rec_evidence) - allowed:
            errors.append(f"{path}.evidence_refs 超出 source findings")

    for path, value in visible_texts:
        if "!" in value or "！" in value:
            errors.append(f"{path} 不得使用感叹号")
        for pattern in HYPE_PATTERNS:
            if re.search(pattern, value):
                errors.append(f"{path} 包含夸张表达：{pattern}")
        for pattern in RESPONSIBILITY_PATTERNS:
            if re.search(pattern, value):
                errors.append(f"{path} 包含未经允许的责任判断：{pattern}")
        for pattern in FILLER_PATTERNS:
            if re.search(pattern, value):
                errors.append(f"{path} 包含无信息增量表达：{pattern}")
        for pattern in META_DISCLOSURE_PATTERNS:
            if re.search(pattern, value):
                errors.append(f"{path} 不得外显验证链、写作边界或报告生成规则：{pattern}")
        if advice_mode == "forbidden":
            for pattern in ADVICE_PATTERNS:
                if re.search(pattern, value):
                    errors.append(f"{path} 包含未经授权的决策建议：{pattern}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Validate report_text_pack v0.4 before rendering.")
    parser.add_argument("payload_json", help="JSON containing analysis_material_pack and report_text_pack")
    args = parser.parse_args()
    payload = json.loads(Path(args.payload_json).read_text(encoding="utf-8-sig"))
    ok, messages = validate_report_text_payload(payload)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
