"""
data_validator.py — 取数结果硬校验

取数 Agent 返回 data JSON 后，Harness 立即校验：
- 结果结构合法性
- 必需字段存在性
- 数值范围合法性（防止 LLM 幻觉数据）
"""


def validate_data(data: dict, plan: dict) -> tuple[bool, list[str]]:
    """
    校验取数结果是否满足 plan 要求。

    Args:
        data: 取数 Agent 返回的 dict
        plan: 已通过 plan_validator 的 Plan JSON

    Returns:
        (is_valid, error_list)
    """
    errors: list[str] = []

    # ── 基本结构 ──────────────────────────────────────────────────────────
    for field in ["row_count", "fields", "rows"]:
        if field not in data:
            errors.append(f"data 缺少必需字段：{field}")

    if errors:
        return False, errors

    if not isinstance(data["rows"], list):
        errors.append("data.rows 必须是列表")
        return False, errors

    # ── 行数校验 ──────────────────────────────────────────────────────────
    criteria = plan.get("acceptance_criteria", {})
    if "min_rows" in criteria:
        if data["row_count"] < criteria["min_rows"]:
            errors.append(
                f"row_count({data['row_count']}) < min_rows({criteria['min_rows']})"
            )

    # ── 必需字段存在性 ────────────────────────────────────────────────────
    required_fields = plan.get("expected_output", {}).get("required_fields", [])
    actual_fields = set(data.get("fields", []))
    missing = [f for f in required_fields if f not in actual_fields]
    if missing:
        errors.append(f"data 缺少 expected_output 要求的字段：{missing}")

    # ── 数值范围校验（通用：百分比字段必须在 0-100）──────────────────────
    rate_fields = [f for f in actual_fields if "rate" in f.lower() or "pct" in f.lower()]
    for row in data.get("rows", []):
        for field in rate_fields:
            val = row.get(field)
            if val is not None and isinstance(val, (int, float)):
                # 允许负数（环比变化），但绝对率不应超出 -100 到 100
                if not (-100 <= val <= 100):
                    errors.append(
                        f"字段 {field} 的值 {val} 超出合理范围 [-100, 100]，"
                        "疑似 LLM 幻觉数据"
                    )
                    break  # 只报第一个异常行

    # ── 空结果警告（不报错，但记录）─────────────────────────────────────
    if data["row_count"] == 0:
        errors.append("WARNING: 取数结果为空（row_count=0），请检查过滤条件")

    return len(errors) == 0, errors
