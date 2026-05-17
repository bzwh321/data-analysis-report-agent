"""
output_validator.py — Phase 3 最终输出硬校验（第5层专属）

校验项：
1. 结论可追溯性：每条 finding 必须有 data_source 字段
2. 组织归因规则：有 org attribution 时必须有数据来源，不得纯推断
3. 禁止内部框架标注词出现在 executive_summary
4. Summary 非空且含具体数字
5. 必须诚实记录 data_gaps
"""

import re


FORBIDDEN_LABELS = ['数据事实', '运营逻辑', '组织归因', '业务结论']


def validate_final_output(final: dict) -> tuple[bool, list[str]]:
    """
    校验 Phase 3 最终输出。
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

    # 合并 errors + warnings（errors 排前）
    all_messages = errors + warnings
    return len(errors) == 0, all_messages
