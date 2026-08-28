#!/usr/bin/env python3
"""Regression checks for report text governance contract v0.4."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from harness.report_text_validator import validate_report_text_payload


def _fixture() -> dict:
    conclusion_sentence_1 = "全年利润率同比下降2.19个百分点，收入基本持平、成本率上升，降幅主要集中在第三季度。"
    conclusion_sentence_2 = "第四季度利润率虽有回升，但年末仍未恢复至年初水平。"
    conclusion = conclusion_sentence_1 + conclusion_sentence_2
    return {
        "analysis_material_pack": {
            "contract_version": "0.3",
            "validated_findings": [
                {
                    "finding_id": "finding_margin",
                    "statement": conclusion,
                    "causal_status": "associative",
                    "evidence_refs": ["evidence_margin", "evidence_cost"],
                }
            ],
            "evidence_inventory": [
                {"evidence_id": "evidence_margin"},
                {"evidence_id": "evidence_cost"},
            ],
            "chart_candidates": [],
        },
        "report_text_pack": {
            "contract_version": "0.4",
            "runtime_policy": {
                "temperature_source": "agent_manifests",
                "manifest_validation_status": "pass",
                "execution_receipts": {
                    "chart": {
                        "manifest_ref": "agents/chart-spec-agent/manifest.yaml",
                        "configured_temperature": 0.0,
                        "applied_temperature": 0.0,
                        "status": "enforced",
                    },
                    "controller": {
                        "manifest_ref": "agents/report-text-controller/manifest.yaml",
                        "configured_temperature": 0.0,
                        "applied_temperature": 0.0,
                        "status": "enforced",
                    },
                    "writer": {
                        "manifest_ref": "agents/report-text-editor/manifest.yaml",
                        "configured_temperature": 0.0,
                        "applied_temperature": 0.0,
                        "status": "enforced",
                    },
                    "reviewer": {
                        "manifest_ref": "agents/report-text-adversarial-reviewer/manifest.yaml",
                        "configured_temperature": 0.2,
                        "applied_temperature": 0.2,
                        "status": "enforced",
                    },
                    "assembler": {
                        "manifest_ref": "agents/report-assembler/manifest.yaml",
                        "configured_temperature": 0.0,
                        "applied_temperature": 0.0,
                        "status": "enforced",
                    },
                    "renderer": {
                        "manifest_ref": "agents/html-report-renderer/manifest.yaml",
                        "configured_temperature": 0.0,
                        "applied_temperature": 0.0,
                        "status": "enforced",
                    },
                },
            },
            "prewrite_prompt": {
                "ref": "references/report_writing_micro_prompt.md",
                "version": "0.1",
                "applied": True,
            },
            "report_goal": {
                "research_question": "利润率是否下降，收入与成本如何共同表现？",
                "audience": "经营管理层",
                "business_context": "年度经营复盘",
                "decision_advice_mode": "forbidden",
                "explicit_request_ref": None,
            },
            "controller_resolution": {
                "controller_run_id": "controller_001",
                "manifest_ref": "agents/report-text-controller/manifest.yaml",
                "temperature": 0,
                "status": "partially_answered",
                "question_results": [
                    {
                        "question_id": "report_question_1",
                        "question": "利润率是否下降，收入与成本如何共同表现？",
                        "status": "answered",
                        "section_refs": ["section_margin"],
                        "bounded_module_refs": [],
                        "unresolved_gap_refs": [],
                    },
                    {
                        "question_id": "report_question_2",
                        "question": "促销活动是否形成可确认的经营回报？",
                        "status": "partially_answered",
                        "section_refs": [],
                        "bounded_module_refs": ["bounded_promotion_roi"],
                        "unresolved_gap_refs": ["gap_promotion_cost"],
                    }
                ],
                "omitted_units": [
                    {
                        "unit_id": "unit_decorative_sparkline",
                        "issue_code": "no_report_value",
                        "route": "controller",
                        "render": False,
                        "reason": "仅重复主图终点数值，没有新增报告信息。",
                    }
                ],
                "context_policy": {
                    "unit_packets_only": True,
                    "full_material_pack_sent_to_writer": False,
                    "full_material_pack_sent_to_reviewer": False,
                },
            },
            "visual_evidence": [
                {
                    "visual_id": "visual_margin",
                    "kind": "line_and_bar",
                    "status": "validated",
                    "data_ref": "analysis.margin_bridge",
                    "unit": "percentage_point",
                    "time_scope": "2024 full year and monthly trend",
                    "comparison_basis": "year over year and monthly sequence",
                    "report_position": "section_01.main_column.after_intro",
                    "evidence_refs": ["evidence_margin", "evidence_cost"],
                    "finding_refs": ["finding_margin"],
                }
            ],
            "sections": [
                {
                    "section_id": "section_margin",
                    "unit_packet": {
                        "packet_id": "packet_margin",
                        "context_scope": "single_report_unit",
                        "full_report_context_included": False,
                        "research_question": "利润率是否下降，收入与成本如何共同表现？",
                        "business_context": "年度经营复盘中的利润率解释",
                        "selected_finding_refs": ["finding_margin"],
                        "selected_evidence_refs": ["evidence_margin", "evidence_cost"],
                        "selected_visual_refs": ["visual_margin"],
                        "layout_context": {
                            "report_position": "section_01.main_column.after_intro",
                            "grid_span": 8,
                            "available_width_px": 760,
                            "title_max_lines": 2,
                            "conclusion_preferred_lines": 1,
                        },
                    },
                    "writer_run": {
                        "run_id": "writer_001",
                        "manifest_ref": "agents/report-text-editor/manifest.yaml",
                        "temperature": 0,
                        "context_scope": "unit_only",
                        "prewrite_prompt_applied": True,
                    },
                    "resolution_log": [],
                    "verification": {
                        "status": "verified",
                        "questions": [
                            {
                                "question_id": "q_margin",
                                "question": "利润率相对去年发生了什么变化？",
                                "role": "metric_level",
                                "critical": True,
                                "final_status": "supported",
                                "answer": "全年利润率同比下降2.19个百分点，降幅主要集中在第三季度。",
                                "evidence_refs": ["evidence_margin"],
                                "history": [
                                    {"round": 1, "status": "supported", "evidence_refs": ["evidence_margin"]}
                                ],
                            },
                            {
                                "question_id": "q_cost",
                                "question": "利润率下降期间，收入与成本分别如何变化？",
                                "role": "driver_decomposition",
                                "critical": True,
                                "final_status": "supported",
                                "answer": "收入基本持平，成本率上升。",
                                "evidence_refs": ["evidence_cost"],
                                "history": [
                                    {"round": 1, "status": "missing", "evidence_refs": []},
                                    {"round": 2, "status": "supported", "evidence_refs": ["evidence_cost"]},
                                ],
                            },
                        ],
                        "backfill_requests": [
                            {
                                "request_id": "backfill_001",
                                "question_refs": ["q_cost"],
                                "requested_data": "同期收入增速、成本率及口径说明",
                                "status": "resolved",
                                "returned_evidence_refs": ["evidence_cost"],
                            }
                        ],
                        "unresolved_critical_question_refs": [],
                    },
                    "utility": {
                        "status": "include",
                        "contribution": "answers_research_question",
                        "reason": "同时回答利润率变化、发生时段及收入成本表现。",
                    },
                    "logic_chain": [
                        {
                            "step_id": "step_margin",
                            "type": "observation",
                            "text": "全年利润率同比下降2.19个百分点，降幅主要集中在第三季度。",
                            "evidence_refs": ["evidence_margin"],
                            "verification_question_refs": ["q_margin"],
                        },
                        {
                            "step_id": "step_relationship",
                            "type": "relationship",
                            "text": "同期收入基本持平，成本率上升，与利润率下行同时出现。",
                            "evidence_refs": ["evidence_margin", "evidence_cost"],
                            "verification_question_refs": ["q_margin", "q_cost"],
                        },
                        {
                            "step_id": "step_conclusion",
                            "type": "conclusion",
                            "text": conclusion,
                            "evidence_refs": ["evidence_margin", "evidence_cost"],
                            "verification_question_refs": ["q_margin", "q_cost"],
                        },
                    ],
                    "conclusion": {
                        "conclusion_id": "conclusion_margin",
                        "text": conclusion,
                        "source_finding_refs": ["finding_margin"],
                        "evidence_refs": ["evidence_margin", "evidence_cost"],
                        "verification_question_refs": ["q_margin", "q_cost"],
                        "support_status": "sufficient",
                        "causal_status": "associative",
                        "business_value": "回答利润率是否下降，并说明收入与成本的同期表现。",
                        "driver_claim": True,
                        "driver_decomposition_question_refs": ["q_cost"],
                        "render_plan": {
                            "internal_only": True,
                            "preferred_lines": 1,
                            "planned_lines": 1,
                            "split_mode": "none",
                            "split_reason": None,
                            "segments": [{"role": "combined", "text": conclusion}],
                        },
                    },
                    "title": {
                        "text_id": "text_section_title",
                        "text": "利润率同比下降2.19个百分点，降幅主要集中在第三季度",
                        "mode": "claim",
                        "source_conclusion_ref": "conclusion_margin",
                        "question_alignment": "direct_answer",
                        "line_fit": {"max_lines": 2, "planned_lines": 1},
                    },
                    "subtitle": {
                        "text_id": "text_section_subtitle",
                        "text": "收入基本持平，成本率同期上升",
                        "source_conclusion_ref": "conclusion_margin",
                        "line_fit": {"max_lines": 1, "planned_lines": 1},
                    },
                    "visual_texts": [
                        {
                            "text_id": "text_visual_title",
                            "visual_ref": "visual_margin",
                            "text": "利润率降幅集中在第三季度",
                            "source_conclusion_ref": "conclusion_margin",
                        }
                    ],
                    "body_blocks": [
                        {
                            "text_id": "text_body_claim_1",
                            "role": "claim_sentence",
                            "display_mode": "line",
                            "text": conclusion_sentence_1,
                            "conclusion_refs": ["conclusion_margin"],
                            "evidence_refs": ["evidence_margin", "evidence_cost"],
                            "line_fit": {"max_lines": 2, "planned_lines": 1},
                        },
                        {
                            "text_id": "text_body_claim_2",
                            "role": "claim_sentence",
                            "display_mode": "line",
                            "text": conclusion_sentence_2,
                            "conclusion_refs": ["conclusion_margin"],
                            "evidence_refs": ["evidence_margin"],
                            "line_fit": {"max_lines": 2, "planned_lines": 1},
                        }
                    ],
                    "adversarial_review": {
                        "reviewer_run_id": "reviewer_001",
                        "manifest_ref": "agents/report-text-adversarial-reviewer/manifest.yaml",
                        "temperature": 0.2,
                        "independent_context": True,
                        "full_material_pack_received": False,
                        "writer_reasoning_received": False,
                        "verdict": "pass",
                        "failure_category": None,
                        "checks": {
                            "expression": "pass",
                            "data_evidence": "pass",
                            "verification_logic": "pass",
                            "business_context": "pass",
                            "report_utility": "pass",
                            "line_fit": "pass",
                        },
                        "issues": [],
                        "route_on_fail": None,
                    },
                }
            ],
            "bounded_modules": [
                {
                    "module_id": "bounded_promotion_roi",
                    "source_question_ref": "report_question_2",
                    "source_packet_ref": "packet_promotion_roi",
                    "status": "bounded",
                    "render_disposition": "detachable_boundary",
                    "summary_eligible": False,
                    "removable": True,
                    "report_position": "detachable.after_main_report",
                    "visual_refs": [],
                    "evidence_refs": ["evidence_cost"],
                    "unresolved_gap_refs": ["gap_promotion_cost"],
                    "title": {
                        "text_id": "text_bounded_title",
                        "text": "促销活动回报证据尚不完整",
                        "mode": "descriptive",
                        "line_fit": {"max_lines": 2, "planned_lines": 1},
                    },
                    "statements": [
                        {
                            "text_id": "text_bounded_statement_1",
                            "text": "促销期订单量和毛利率发生了同期变化。",
                            "evidence_refs": ["evidence_cost"],
                            "line_fit": {"max_lines": 2, "planned_lines": 1},
                        },
                        {
                            "text_id": "text_bounded_statement_2",
                            "text": "由于缺少活动成本与净收入，现有数据无法确认活动回报。",
                            "evidence_refs": [],
                            "line_fit": {"max_lines": 2, "planned_lines": 1},
                        },
                    ],
                }
            ],
            "summary_chain": [
                {
                    "summary_id": "summary_metric",
                    "text_id": "text_summary_metric",
                    "role": "core_metric",
                    "text": "全年利润率同比下降2.19个百分点。",
                    "source_title_refs": ["text_section_title"],
                    "section_refs": ["section_margin"],
                    "evidence_refs": ["evidence_margin"],
                    "previous_summary_ref": None,
                },
                {
                    "summary_id": "summary_answer",
                    "text_id": "text_summary_answer",
                    "role": "key_question_answer",
                    "text": "降幅主要集中在第三季度；收入基本持平，成本率同期上升。",
                    "source_title_refs": ["text_section_title", "text_section_subtitle"],
                    "section_refs": ["section_margin"],
                    "evidence_refs": ["evidence_margin", "evidence_cost"],
                    "previous_summary_ref": "summary_metric",
                },
                {
                    "summary_id": "summary_boundary",
                    "text_id": "text_summary_boundary",
                    "role": "boundary",
                    "text": "现有证据支持同期关系，不单独归因为收入或成本变化。",
                    "source_title_refs": ["text_section_subtitle"],
                    "section_refs": ["section_margin"],
                    "evidence_refs": ["evidence_margin", "evidence_cost"],
                    "previous_summary_ref": "summary_answer",
                },
            ],
            "report_title": {
                "text_id": "text_report_title",
                "text": "全年利润率下降，降幅主要集中在第三季度",
                "mode": "claim",
                "source_summary_refs": ["summary_metric", "summary_answer"],
                "question_alignment": "direct_answer",
                "line_fit": {"max_lines": 2, "planned_lines": 1},
            },
            "report_subtitle": {
                "text_id": "text_report_subtitle",
                "text": "收入基本持平，成本率同期上升",
                "source_summary_refs": ["summary_answer", "summary_boundary"],
                "line_fit": {"max_lines": 1, "planned_lines": 1},
            },
            "recommendations": [],
        },
    }


def _fails(payload: dict, needle: str) -> bool:
    ok, messages = validate_report_text_payload(payload)
    return not ok and any(needle in message for message in messages)


def main() -> int:
    errors: list[str] = []
    valid = _fixture()
    ok, messages = validate_report_text_payload(valid)
    if not ok:
        errors.append(f"valid fixture failed: {messages}")

    writer_temperature = copy.deepcopy(valid)
    writer_temperature["report_text_pack"]["sections"][0]["writer_run"]["temperature"] = 0.3
    if not _fails(writer_temperature, "writer_run.temperature 未使用 writer manifest"):
        errors.append("writer temperature drift must fail")

    renderer_temperature = copy.deepcopy(valid)
    renderer_temperature["report_text_pack"]["runtime_policy"]["execution_receipts"]["renderer"]["applied_temperature"] = 0.1
    if not _fails(renderer_temperature, "applied_temperature 未执行 Agent manifest 温度"):
        errors.append("renderer temperature drift must fail")

    reviewer_temperature = copy.deepcopy(valid)
    reviewer_temperature["report_text_pack"]["runtime_policy"]["execution_receipts"]["reviewer"]["applied_temperature"] = 0
    reviewer_temperature["report_text_pack"]["sections"][0]["adversarial_review"]["temperature"] = 0
    if not _fails(reviewer_temperature, "未执行 Agent manifest 温度"):
        errors.append("reviewer must use its manifest temperature")

    expanded_context = copy.deepcopy(valid)
    expanded_context["report_text_pack"]["controller_resolution"]["context_policy"]["full_material_pack_sent_to_writer"] = True
    if not _fails(expanded_context, "不得把 full material pack 发送给 writer"):
        errors.append("writer full-context expansion must fail")

    thin_verification = copy.deepcopy(valid)
    thin_verification["report_text_pack"]["sections"][0]["verification"]["questions"] = thin_verification["report_text_pack"]["sections"][0]["verification"]["questions"][:1]
    if not _fails(thin_verification, "至少需要两个验证问题"):
        errors.append("single-question verification must fail")

    no_backfill = copy.deepcopy(valid)
    no_backfill["report_text_pack"]["sections"][0]["verification"]["backfill_requests"] = []
    if not _fails(no_backfill, "存在 missing 问题但没有 backfill_request"):
        errors.append("missing data without ReAct backfill must fail")

    unresolved_verified = copy.deepcopy(valid)
    verification = unresolved_verified["report_text_pack"]["sections"][0]["verification"]
    verification["questions"][1].update({"final_status": "unresolved", "answer": "", "evidence_refs": []})
    verification["unresolved_critical_question_refs"] = ["q_cost"]
    if not _fails(unresolved_verified, "verified 时不得有 unresolved critical questions"):
        errors.append("verified status with a critical gap must fail")

    unverified_evidence = copy.deepcopy(valid)
    unverified_evidence["analysis_material_pack"]["evidence_inventory"].append({"evidence_id": "evidence_revenue"})
    unverified_evidence["analysis_material_pack"]["validated_findings"][0]["evidence_refs"].append("evidence_revenue")
    section = unverified_evidence["report_text_pack"]["sections"][0]
    section["unit_packet"]["selected_evidence_refs"].append("evidence_revenue")
    section["logic_chain"][1]["evidence_refs"].append("evidence_revenue")
    section["conclusion"]["evidence_refs"].append("evidence_revenue")
    if not _fails(unverified_evidence, "未经过 verification"):
        errors.append("conclusion evidence not covered by verification must fail")

    causal = copy.deepcopy(valid)
    causal["report_text_pack"]["sections"][0]["conclusion"]["causal_status"] = "causal"
    if not _fails(causal, "强于或不同于 source findings"):
        errors.append("causal escalation must fail")

    invalid_split = copy.deepcopy(valid)
    render_plan = invalid_split["report_text_pack"]["sections"][0]["conclusion"]["render_plan"]
    render_plan.update(
        {
            "planned_lines": 2,
            "split_mode": "none",
            "split_reason": None,
            "segments": [
                {"role": "evidence", "text": "全年利润率同比下降2.19个百分点。"},
                {"role": "conclusion", "text": "降幅主要集中在第三季度。"},
            ],
        }
    )
    if not _fails(invalid_split, "多行时必须声明 split_mode 和 split_reason"):
        errors.append("multi-line conclusion without an explicit split plan must fail")

    visible_answer_label = copy.deepcopy(valid)
    visible_answer_label["report_text_pack"]["sections"][0]["body_blocks"][0]["text"] = (
        "证据。全年利润率同比下降2.19个百分点。"
    )
    if not _fails(visible_answer_label, "不得外显证据、结论或边界答题标签"):
        errors.append("visible evidence/conclusion/boundary labels must fail")

    incomplete_visible_sentence = copy.deepcopy(valid)
    incomplete_visible_sentence["report_text_pack"]["sections"][0]["body_blocks"][0]["text"] = (
        "全年利润率同比下降2.19个百分点"
    )
    if not _fails(incomplete_visible_sentence, "必须是以句号、问号或感叹号结束的完整句子"):
        errors.append("visible sentence fragments must fail")

    meta_disclosure = copy.deepcopy(valid)
    meta_disclosure["report_text_pack"]["report_subtitle"]["text"] = (
        "以下结论只使用通过验证链的数据，不延伸为责任判断或经营建议。"
    )
    if not _fails(meta_disclosure, "不得外显验证链、写作边界或报告生成规则"):
        errors.append("visible validation-chain meta disclosure must fail")

    awkward_multiline = copy.deepcopy(valid)
    awkward_multiline["report_text_pack"]["sections"][0]["body_blocks"][0]["line_fit"][
        "planned_lines"
    ] = 2
    if not _fails(awkward_multiline, "display_mode=line 时 planned_lines 必须为 1"):
        errors.append("line-mode body copy that needs multiple planned lines must fail")

    missing_driver_decomposition = copy.deepcopy(valid)
    missing_driver_decomposition["report_text_pack"]["sections"][0]["conclusion"][
        "driver_decomposition_question_refs"
    ] = []
    if not _fails(missing_driver_decomposition, "driver_decomposition_question_refs 不得为空"):
        errors.append("driver claims without decomposition questions must fail")

    wrong_driver_role = copy.deepcopy(valid)
    wrong_driver_role["report_text_pack"]["sections"][0]["verification"]["questions"][1][
        "role"
    ] = "driver_check"
    if not _fails(wrong_driver_role, "必须只引用 role=driver_decomposition"):
        errors.append("driver claims must reference explicit driver decomposition")

    visible_render_plan = copy.deepcopy(valid)
    visible_render_plan["report_text_pack"]["sections"][0]["conclusion"]["render_plan"][
        "internal_only"
    ] = False
    if not _fails(visible_render_plan, "render_plan.internal_only 必须为 true"):
        errors.append("internal evidence/conclusion split plan must never render")

    title_overflow = copy.deepcopy(valid)
    title_overflow["report_text_pack"]["sections"][0]["title"]["line_fit"]["planned_lines"] = 3
    if not _fails(title_overflow, "planned_lines 不得超过 max_lines"):
        errors.append("title overflow must fail")

    coupled_review = copy.deepcopy(valid)
    coupled_review["report_text_pack"]["sections"][0]["adversarial_review"]["independent_context"] = False
    if not _fails(coupled_review, "必须使用独立上下文"):
        errors.append("non-independent adversarial review must fail")

    failed_review = copy.deepcopy(valid)
    review = failed_review["report_text_pack"]["sections"][0]["adversarial_review"]
    review["verdict"] = "fail"
    review["failure_category"] = "expression_title_or_line_fit"
    review["checks"]["line_fit"] = "fail"
    review["issues"] = ["conclusion wraps beyond the planned line"]
    review["route_on_fail"] = "writer"
    if not _fails(failed_review, "最终 verdict 必须为 pass"):
        errors.append("failed adversarial review must block rendering")

    broken_summary = copy.deepcopy(valid)
    broken_summary["report_text_pack"]["summary_chain"][1]["previous_summary_ref"] = None
    if not _fails(broken_summary, "没有形成连续链"):
        errors.append("broken progressive summary chain must fail")

    unauthorized_solution = copy.deepcopy(valid)
    unauthorized_solution["report_text_pack"]["summary_chain"][1]["role"] = "solution"
    if not _fails(unauthorized_solution, "solution 未获授权"):
        errors.append("unauthorized solution language must fail")

    controller_mismatch = copy.deepcopy(valid)
    controller_mismatch["report_text_pack"]["controller_resolution"]["status"] = "answered"
    if not _fails(controller_mismatch, "status 与 question_results 不一致"):
        errors.append("controller answer-state mismatch must fail")

    hype = copy.deepcopy(valid)
    hype["report_text_pack"]["report_title"]["text"] = "利润率出现断崖式下降"
    if not _fails(hype, "包含夸张表达"):
        errors.append("hype wording must fail")

    invalid_thin_issue = copy.deepcopy(valid)
    invalid_thin_issue["report_text_pack"]["sections"][0]["resolution_log"] = [
        {"issue_code": "generic_thin_conclusion", "route": "writer", "status": "resolved"}
    ]
    if not _fails(invalid_thin_issue, "不属于允许的单薄结论处理类型"):
        errors.append("thin-result handling must be limited to the three approved categories")

    bounded_in_summary = copy.deepcopy(valid)
    bounded_in_summary["report_text_pack"]["summary_chain"][0]["source_title_refs"] = [
        "text_bounded_title"
    ]
    if not _fails(bounded_in_summary, "包含未知引用"):
        errors.append("bounded module title must not enter summary_chain")

    bounded_not_detachable = copy.deepcopy(valid)
    bounded_not_detachable["report_text_pack"]["bounded_modules"][0]["removable"] = False
    if not _fails(bounded_not_detachable, "removable 必须为 true"):
        errors.append("bounded module must remain detachable")

    bounded_answer_label = copy.deepcopy(valid)
    bounded_answer_label["report_text_pack"]["bounded_modules"][0]["statements"][0][
        "text"
    ] = "现有证据：促销期订单量和毛利率发生了同期变化。"
    if not _fails(bounded_answer_label, "不得外显证据、结论或边界答题标签"):
        errors.append("bounded modules must also use complete unlabeled sentences")

    if errors:
        print("REPORT_TEXT_CONTRACT_TESTS_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("REPORT_TEXT_CONTRACT_TESTS_PASS: positive fixture and 27 boundary gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
