"""
plan_validator.py — Plan JSON 格式硬校验

这是 deterministic 校验脚本，不调用任何模型 API。
默认读取 experience/plan_schema.json 中的 step 白名单；调用方也可以传入 schema_path。
"""

import json
from pathlib import Path
from typing import Optional


DEFAULT_MAX_ROUNDS = 5
DEFAULT_MIN_IMPACT_PCT = 3.0


def _load_schema(schema_path: Optional[str]) -> dict:
    if not schema_path:
        schema_path = str(Path(__file__).resolve().parents[1] / "experience" / "plan_schema.json")
    path = Path(schema_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan(plan: dict, schema_path: Optional[str] = None) -> tuple[bool, list[str]]:
    """
    校验 Plan JSON 格式。

    Returns:
        (is_valid, error_list)
        is_valid=True 表示所有校验通过
    """
    errors: list[str] = []
    schema = _load_schema(schema_path)
    allowed_steps = schema.get("analytical_step_enum", [])

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
    if plan["round"] > DEFAULT_MAX_ROUNDS:
        errors.append(f"round({plan['round']}) > max_rounds({DEFAULT_MAX_ROUNDS})")

    # ── 分析步骤白名单 ────────────────────────────────────────────────────
    if allowed_steps and plan["analytical_step"] not in allowed_steps:
        errors.append(
            f"analytical_step '{plan['analytical_step']}' 不在白名单 {allowed_steps}"
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
    for field in ["format", "required_fields"]:
        if field not in eo:
            errors.append(f"expected_output 缺少字段：{field}")
    if "required_fields" in eo and not isinstance(eo["required_fields"], list):
        errors.append("expected_output.required_fields 必须是列表")

    # ── stop_condition 校验 ───────────────────────────────────────────────
    sc = plan.get("stop_condition", {})
    if "if_impact_below_pct" not in sc:
        errors.append("stop_condition 缺少字段：if_impact_below_pct")
    elif sc["if_impact_below_pct"] < DEFAULT_MIN_IMPACT_PCT:
        errors.append(
            f"stop_condition.if_impact_below_pct({sc['if_impact_below_pct']}) "
            f"< min_impact_pct({DEFAULT_MIN_IMPACT_PCT})，不允许设置更低的停止阈值"
        )
    if "reason" not in sc:
        errors.append("stop_condition 缺少字段：reason")

    return len(errors) == 0, errors


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate an analysis plan JSON file.")
    parser.add_argument("plan_json", help="Path to a plan JSON file.")
    parser.add_argument("--schema", default=None, help="Optional path to plan_schema.json.")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan_json).read_text(encoding="utf-8"))
    ok, messages = validate_plan(plan, schema_path=args.schema)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
