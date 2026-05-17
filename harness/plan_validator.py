"""
plan_validator.py — Plan JSON 格式硬校验

大脑 Agent 每轮输出 Plan 后，Harness 必须通过以下全部校验才允许取数。
任一失败 → 拒绝执行 → 返回错误列表 → 大脑 Agent 必须修正。
"""

from config import MAX_ROUNDS, ALLOWED_STEPS, MIN_IMPACT_PCT


def validate_plan(plan: dict) -> tuple[bool, list[str]]:
    """
    校验 Plan JSON 格式。

    Returns:
        (is_valid, error_list)
        is_valid=True 表示所有校验通过
    """
    errors: list[str] = []

    # ── 顶层必需字段 ──────────────────────────────────────────────────────
    required_top = ["round", "analytical_step", "question",
                    "query_spec", "expected_output",
                    "acceptance_criteria", "stop_condition"]
    for field in required_top:
        if field not in plan:
            errors.append(f"缺少顶层必需字段：{field}")

    if errors:
        return False, errors  # 顶层字段缺失，后续校验无意义

    # ── 轮次上限 ─────────────────────────────────────────────────────────
    if plan["round"] > MAX_ROUNDS:
        errors.append(f"round({plan['round']}) > MAX_ROUNDS({MAX_ROUNDS})")

    # ── 分析步骤白名单 ────────────────────────────────────────────────────
    if plan["analytical_step"] not in ALLOWED_STEPS:
        errors.append(
            f"analytical_step '{plan['analytical_step']}' 不在白名单 {ALLOWED_STEPS}"
        )

    # ── query_spec 必需字段 ───────────────────────────────────────────────
    qs = plan.get("query_spec", {})
    for field in ["metrics", "group_by", "date_range"]:
        if field not in qs:
            errors.append(f"query_spec 缺少字段：{field}")
    if "metrics" in qs and not isinstance(qs["metrics"], list):
        errors.append("query_spec.metrics 必须是列表")
    if "group_by" in qs and not isinstance(qs["group_by"], list):
        errors.append("query_spec.group_by 必须是列表")

    # ── expected_output 必需字段 ──────────────────────────────────────────
    eo = plan.get("expected_output", {})
    for field in ["format", "required_fields", "unit_sales", "unit_rate"]:
        if field not in eo:
            errors.append(f"expected_output 缺少字段：{field}")
    if "required_fields" in eo and not isinstance(eo["required_fields"], list):
        errors.append("expected_output.required_fields 必须是列表")

    # ── stop_condition 校验 ───────────────────────────────────────────────
    sc = plan.get("stop_condition", {})
    if "if_impact_below_pct" not in sc:
        errors.append("stop_condition 缺少字段：if_impact_below_pct")
    elif sc["if_impact_below_pct"] < MIN_IMPACT_PCT:
        errors.append(
            f"stop_condition.if_impact_below_pct({sc['if_impact_below_pct']}) "
            f"< MIN_IMPACT_PCT({MIN_IMPACT_PCT})，不允许设置更低的停止阈值"
        )
    if "reason" not in sc:
        errors.append("stop_condition 缺少字段：reason")

    return len(errors) == 0, errors
