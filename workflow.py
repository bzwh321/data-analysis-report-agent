"""
workflow.py — 数据分析报告 Agent · 完整工作流定义与主入口

打开此文件即可看到完整工作流。所有节点、路由、并行结构、停止判断集中在此。

════════════════════════════════════════════════════════════════
工作流拓扑图
════════════════════════════════════════════════════════════════

  [用户问题 + 背景上下文]
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 1 · design_framework                               │
  │  大脑 Phase 1：读取经验库，设计分析维度与关键问题            │
  │  → BrainAgent.design_framework()                         │
  └───────────────────────┬──────────────────────────────────┘
                          │ framework dict
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 2 · iterative_loop（最多 MAX_ROUNDS=5 轮）          │
  │                                                          │
  │  ── 串行 ──────────────────────────────────────────────  │
  │  Round 1（建立基础，history=[]）                          │
  │    define → plan → fetch → reflect                       │
  │          ↓ 路由：_should_stop()                          │
  │                                                          │
  │  ── 并行 fan-out ──────────────────────────────────────  │
  │  Round 2 ──┐  （共享 Round 1 的 history 快照）            │
  │             ├── ThreadPoolExecutor(max_workers=2)        │
  │  Round 3 ──┘  （分析不同维度，互不依赖）                   │
  │          ↓ fan-in：合并两轮结果，路由判断                  │
  │                                                          │
  │  ── 串行（如需继续）──────────────────────────────────── │
  │  Round 4+ （依赖前三轮综合 history）                      │
  │    define → plan* → fetch → reflect                      │
  │                                                          │
  │  * plan 含三级升级阶梯：                                  │
  │    Attempt 1: 原始重试                                    │
  │    Attempt 2: 注入 plan_schema 上下文                    │
  │    Attempt 3: 注入 schema + 精简约束                     │
  │    全失败 → PlanEscalationNeeded → 人工断点              │
  │                                                          │
  │  停止路由 _should_stop()：                               │
  │  ├── STOP：达轮次 / impact<3% / 重叠>80%                │
  │  ├── PIVOT：has_insight=False，换方向继续                 │
  │  └── CONTINUE：继续下一轮                                 │
  └──────────────────────────────────────────────────────────┘
                          │ insights list
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 2.5 · supervisor_review                            │
  │  检查洞察覆盖是否充分；不足时追加 1 轮，重新整合            │
  │  触发条件：洞察数 < 2 或所有轮次只覆盖同一维度              │
  └───────────────────────┬──────────────────────────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 3 · integrate_insights                             │
  │  大脑 Phase 3：整合所有轮次洞察                           │
  │  ① _detect_conflicts() 检测冲突 → 生成 conflict_hint     │
  │  ② BrainAgent.integrate_insights(conflict_hint=...)      │
  │  → harness/output_validator.py 校验                      │
  └───────────────────────┬──────────────────────────────────┘
                          │ final_insights dict
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 3.3 · adversarial_validate  ← temperature=0        │
  │  独立审查员视角，校验 5 个维度：                           │
  │    可溯源性 / 逻辑一致性 / 数字合理性 / 摘要匹配 / 边界诚实 │
  │  发现 critical 问题时注入 correction_hint 重新整合         │
  │  → BrainAgent.adversarial_review()                       │
  └───────────────────────┬──────────────────────────────────┘
                          │ issues list 写入 final_insights
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 3.5 · human_breakpoint_insights  ← 人工断点        │
  │  展示：核心结论 + 主要发现 + 计划图表 + 对抗校验问题        │
  │  等待确认：方向是否正确，图表重点是否需调整                  │
  │  操作：Enter=确认 / m=修改图表重点 / q=取消               │
  └───────────────────────┬──────────────────────────────────┘
                          │ state.status == "running" 才继续
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 4 · format_charts                                  │
  │  将 chart_instructions 转化为 ECharts option JSON         │
  │  → FormatterAgent.format()                               │
  └───────────────────────┬──────────────────────────────────┘
                          │ charts list
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 5 · render_report                                  │
  │  将洞察 + 图表渲染为完整 HTML 报告                         │
  │  → DesignerAgent.render()                                │
  └───────────────────────┬──────────────────────────────────┘
                          │ html string
                          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Node 6 · write_output（可选）                            │
  │  将 HTML 写入本地文件（output_path 不为 None 时执行）        │
  └───────────────────────┬──────────────────────────────────┘
                          │
                          ▼
                  [返回 WorkflowState]

════════════════════════════════════════════════════════════════
配置参数（修改 config.py 即可调整行为，无需改此文件）
════════════════════════════════════════════════════════════════

  MAX_ROUNDS        = 5      迭代上限
  MIN_IMPACT_PCT    = 3.0    边际收益阈值（低于此值停止）
  OVERLAP_THRESHOLD = 0.80   洞察重叠度阈值（高于此值停止）

════════════════════════════════════════════════════════════════
"""

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from agents import BrainAgent, MockFetcher, FormatterAgent, DesignerAgent
from agents.brain_agent import PlanEscalationNeeded
from config import MAX_ROUNDS, MIN_IMPACT_PCT, OVERLAP_THRESHOLD


# ─────────────────────────────────────────────────────────────
# WorkflowState：节点之间通过此对象传递数据
# ─────────────────────────────────────────────────────────────

@dataclass
class WorkflowState:
    question: str
    context: dict = field(default_factory=dict)
    framework: dict = None                              # Node 1 产物
    rounds: list = field(default_factory=list)          # 每轮 reflect 结果
    insight_pool: list = field(default_factory=list)    # 洞察文本列表，用于重叠度检测
    round_data: dict = field(default_factory=dict)      # round_N_data，供 Node 3 溯源
    final_insights: dict = None                         # Node 3 产物
    charts: list = field(default_factory=list)          # Node 4 产物
    report_html: str = ""                               # Node 5 产物
    report_path: str = ""                               # Node 6 产物
    status: str = "running"                             # running / done / cancelled / failed


# ─────────────────────────────────────────────────────────────
# 辅助函数：停止判断（路由）
# ─────────────────────────────────────────────────────────────

def _compute_overlap(new_text: str, pool: list) -> float:
    """词袋重叠度，生产环境可替换为嵌入相似度"""
    if not pool:
        return 0.0
    new_words = set(new_text.split())
    if not new_words:
        return 0.0
    overlaps = [len(new_words & set(t.split())) / len(new_words) for t in pool]
    return max(overlaps)


def _should_stop(reflect: dict, insight_pool: list, round_num: int) -> tuple:
    """
    路由判断：是否停止迭代循环。
    返回 (is_stop: bool, reason: str)

    STOP 触发条件（任一）：
      A. round_num >= MAX_ROUNDS
      B. reflect.impact_pct < MIN_IMPACT_PCT
      C. 新洞察与 insight_pool 重叠度 > OVERLAP_THRESHOLD
    PIVOT（不停止，换方向）：
      D. reflect.has_insight == False
    """
    if round_num >= MAX_ROUNDS:
        return True, f"达到最大轮次({MAX_ROUNDS})，强制收拢"

    impact = reflect.get("impact_pct", 0)
    if impact < MIN_IMPACT_PCT:
        return True, f"impact_pct({impact}%) < 阈值({MIN_IMPACT_PCT}%)，边际收益消失"

    overlap = _compute_overlap(reflect.get("insight_text", ""), insight_pool)
    if overlap > OVERLAP_THRESHOLD:
        return True, f"洞察重叠度({overlap:.0%}) > 阈值({OVERLAP_THRESHOLD:.0%})"

    if not reflect.get("has_insight", True):
        return False, "PIVOT"

    return False, "CONTINUE"


# ─────────────────────────────────────────────────────────────
# 辅助函数：单轮执行（线程安全，供并行调用）
# ─────────────────────────────────────────────────────────────

def _run_one_round(
    brain: BrainAgent,
    fetcher,
    round_num: int,
    question: str,
    framework: dict,
    history: list,
) -> tuple:
    """
    执行一轮完整分析：define → plan → fetch → reflect。
    纯函数，不修改共享状态，线程安全。

    Returns:
        (plan, data, reflect) 三元组；
        plan 为 None 时表示触发了 PlanEscalationNeeded（需 caller 处理）
    """
    define_out = brain.define_hypothesis(round_num, question, framework, history)
    try:
        plan = brain.generate_plan(round_num, define_out, question)
    except PlanEscalationNeeded:
        raise  # 向上传递，由 run_workflow 捕获处理

    data = fetcher.fetch(plan)
    brain.save_log(f"02_round_{round_num}_data.json", data)
    reflect = brain.reflect_on_data(round_num, define_out, plan, data)
    return plan, data, reflect


def _process_round_result(
    round_num: int,
    plan: dict,
    data: dict,
    reflect: dict,
    state: WorkflowState,
    history: list,
) -> tuple:
    """
    处理单轮结果：更新 state 和 history，返回 (stop, reason)。
    供串行和并行收束共用。
    """
    insight_text = reflect.get("insight_text", "")
    stop, reason = _should_stop(reflect, state.insight_pool, round_num)

    state.round_data[f"round_{round_num}_data"] = data

    if reflect.get("has_insight") and insight_text:
        state.insight_pool.append(insight_text)
        state.rounds.append({
            "round": round_num,
            "analytical_step": plan.get("analytical_step"),
            **reflect,
        })

    history.append({
        "round": round_num,
        "step": plan.get("analytical_step"),
        "question": plan.get("question"),
        "decision": reason,
    })

    print(f"  Round {round_num} | 步骤：{plan.get('analytical_step')} | 路由：{'STOP' if stop else reason}")
    return stop, reason


# ─────────────────────────────────────────────────────────────
# Node 2.5：Supervisor 覆盖检查
# ─────────────────────────────────────────────────────────────

def _supervisor_review(
    state: WorkflowState,
    brain: BrainAgent,
    fetcher,
    question: str,
    framework: dict,
    history: list,
    next_round_num: int,
) -> tuple:
    """
    检查洞察覆盖是否充分，不足时追加 1 轮补充分析。

    触发条件（任一）：
      · 洞察总数 < 2（太少）
      · 所有轮次的 analytical_step 完全相同（只分析了单一维度）

    Returns:
        (state, history, next_round_num) 更新后的三元组
    """
    steps = [r.get("analytical_step") for r in state.rounds]
    only_one_dimension = len(set(steps)) <= 1 and len(steps) > 0

    if len(state.rounds) >= 2 and not only_one_dimension:
        return state, history, next_round_num

    if len(state.rounds) < 2:
        reason = f"洞察数({len(state.rounds)}) < 2，覆盖不足"
    else:
        reason = f"所有轮次均为同一维度({steps[0]})，视角单一"

    print(f"\n[Supervisor] {reason}，追加第 {next_round_num} 轮补充分析")

    try:
        plan, data, reflect = _run_one_round(
            brain, fetcher, next_round_num, question, framework, history
        )
        _process_round_result(next_round_num, plan, data, reflect, state, history)
        next_round_num += 1
    except PlanEscalationNeeded as e:
        print(f"[Supervisor] 补充轮次 Plan 生成失败，跳过：{e.last_errors}")

    return state, history, next_round_num


# ─────────────────────────────────────────────────────────────
# Node 3 前：冲突检测
# ─────────────────────────────────────────────────────────────

def _detect_conflicts(rounds: list) -> str:
    """
    扫描各轮 conclusion_type，检测结论冲突。
    返回 conflict_hint 字符串（空字符串 = 无冲突）。

    冲突规则：
      · structural + event_driven 共存 → 根因性质冲突
      · healthy + 任意异常类型共存  → 范围性质冲突
    """
    types = {r.get("conclusion_type") for r in rounds if r.get("conclusion_type")}
    hints = []

    if "structural" in types and "event_driven" in types:
        hints.append(
            "结构性问题(structural) 与 事件性冲击(event_driven) 并存："
            "整合时需明确主因权重，不可混同。"
        )
    if "healthy" in types and types - {"healthy", "inconclusive"}:
        hints.append(
            "部分维度结论为健康(healthy)，部分维度存在异常："
            "整合时需区分问题范围，明确是局部问题还是整体问题。"
        )

    if hints:
        print(f"[Converge] 检测到 {len(hints)} 处结论冲突，注入整合提示")

    return "\n".join(hints)


# ─────────────────────────────────────────────────────────────
# Node 3.3：对抗校验
# ─────────────────────────────────────────────────────────────

def _adversarial_validate(
    state: WorkflowState,
    brain: BrainAgent,
    conflict_hint: str = "",
) -> WorkflowState:
    """
    Node 3.3：temperature=0 对抗校验。
    发现 critical 问题时注入 correction_hint，重新调用 integrate_insights。
    所有 issues 写入 state.final_insights["adversarial_issues"]，供 Node 3.5 展示。
    """
    review = brain.adversarial_review(state.final_insights, state.round_data)
    issues = review.get("issues", [])
    state.final_insights["adversarial_issues"] = issues

    critical = [i for i in issues if i.get("severity") == "critical"]
    if critical and not review.get("passed", True):
        correction = review.get("verdict", "")
        # 拼出具体问题描述，注入修正提示
        correction_hint = correction + "\n" + "\n".join(
            f"- [{i.get('finding_ref')}] {i.get('issue')} → {i.get('suggestion')}"
            for i in critical
        )
        print(f"  [对抗校验] 发现 {len(critical)} 个 critical 问题，重新整合洞察")
        state.final_insights = brain.integrate_insights(
            state.question, state.rounds,
            conflict_hint=conflict_hint,
            correction_hint=correction_hint,
        )
        # 保留校验问题，供断点展示
        state.final_insights["adversarial_issues"] = issues

    return state


# ─────────────────────────────────────────────────────────────
# Node 3.5：人工断点
# ─────────────────────────────────────────────────────────────

def _human_breakpoint_insights(state: WorkflowState) -> WorkflowState:
    """
    人工断点：integrate_insights 之后，format_charts 之前。

    展示：核心结论 + 主要发现（含 impact_pct）+ 计划图表列表
    等待操作：
      Enter → 确认，继续生成报告
      m     → 输入修改意见（写入 human_chart_note，format_charts 会读取）
      q     → 取消，state.status = "cancelled"
    """
    insights = state.final_insights or {}
    findings = insights.get("findings", [])
    charts = insights.get("chart_instructions", [])

    print(f"\n{'='*60}")
    print("[断点 3.5] 请确认分析洞察与图表方向")
    print(f"{'='*60}")

    summary = insights.get("executive_summary", "（无摘要）")
    print(f"\n核心结论：\n  {summary}\n")

    print(f"主要发现（{len(findings)} 条）：")
    for i, f in enumerate(findings, 1):
        title = f.get("title", f.get("content", "")[:40])
        impact = f.get("impact_pct", "?")
        print(f"  {i}. {title}  [影响 {impact}%]")

    print(f"\n计划图表（{len(charts)} 个）：")
    for i, c in enumerate(charts, 1):
        print(f"  {i}. [{c.get('chart_type', '?')}] {c.get('title', '')}")

    adv_issues = insights.get("adversarial_issues", [])
    if adv_issues:
        print(f"\n对抗校验问题（{len(adv_issues)} 条）：")
        for issue in adv_issues:
            sev = issue.get("severity", "?")
            ref = issue.get("finding_ref", "")
            msg = issue.get("issue", "")
            sug = issue.get("suggestion", "")
            print(f"  [{sev}] {ref}: {msg}")
            if sug:
                print(f"         建议：{sug}")

    print("\n操作选项：")
    print("  Enter → 确认，继续生成报告")
    print("  m     → 修改图表重点（输入说明）")
    print("  q     → 取消")

    choice = input("\n请选择: ").strip().lower()

    if choice == "q":
        state.status = "cancelled"
        print("[断点] 已取消，工作流终止")
    elif choice == "m":
        note = input("请说明修改意见（将注入图表生成提示词）: ").strip()
        state.final_insights["human_chart_note"] = note
        print(f"[断点] 已记录修改意见，继续生成报告")
    else:
        print("[断点] 确认，继续生成报告")

    return state


# ─────────────────────────────────────────────────────────────
# 主编排器
# ─────────────────────────────────────────────────────────────

def run_workflow(
    question: str,
    context: dict = None,
    fetcher=None,
    experience_dir: str = "experience/",
    log_dir: str = "run_logs/",
    output_path: str = None,
    api_key: str = None,
    human_review: bool = True,
) -> WorkflowState:
    """
    执行完整工作流，返回 WorkflowState。

    Args:
        question:       分析问题
        context:        背景上下文（公司、时间范围等）
        fetcher:        取数 Agent 实例（默认使用 MockFetcher）
        experience_dir: 经验库目录（默认 experience/）
        log_dir:        运行日志根目录（默认 run_logs/）
        output_path:    HTML 报告写入路径（None 则只返回不写文件）
        api_key:        Anthropic API Key（不传则读取 ANTHROPIC_API_KEY 环境变量）
        human_review:   是否启用 Node 3.5 人工断点（默认 True；自动化场景可设 False）
    """
    run_id = f"run_{int(time.time())}"
    context = context or {}
    fetcher = fetcher or MockFetcher()
    state = WorkflowState(question=question, context=context)

    print(f"\n{'='*60}")
    print(f"工作流启动 | run_id: {run_id}")
    print(f"问题: {question}")
    print(f"{'='*60}")

    brain = BrainAgent(
        fetcher=fetcher,
        experience_dir=experience_dir,
        log_dir=log_dir,
        run_id=run_id,
        api_key=api_key,
    )

    # ── Node 1: design_framework ──────────────────────────────
    print("\n[Node 1] 设计分析框架")
    state.framework = brain.design_framework(question, context)

    # ── Node 2: iterative_loop ────────────────────────────────
    print(f"\n[Node 2] 迭代分析（最多 {MAX_ROUNDS} 轮）")
    history = []
    next_round = 1
    global_stop = False

    # ── Round 1：串行（建立基础假设）──────────────────────────
    print("\n  ── Round 1（串行，建立基础）──")
    try:
        plan, data, reflect = _run_one_round(
            brain, fetcher, next_round, question, state.framework, history
        )
        stop, reason = _process_round_result(next_round, plan, data, reflect, state, history)
        next_round += 1
        global_stop = stop
    except PlanEscalationNeeded as e:
        print(f"\n[升级] Round {e.round_num} Plan 失败，触发人工干预")
        hint = input("请提供补充上下文（或 Enter 跳过）: ").strip()
        if not hint:
            global_stop = True
        else:
            # 人工补充后重试（修改 define 输出再试一次）
            define_retry = brain.define_hypothesis(e.round_num, {}, question)
            define_retry["human_supplement"] = hint
            plan = brain.generate_plan(e.round_num, define_retry, question)
            data = fetcher.fetch(plan)
            brain.save_log(f"02_round_{e.round_num}_data.json", data)
            reflect = brain.reflect_on_data(e.round_num, define_retry, plan, data)
            stop, _ = _process_round_result(e.round_num, plan, data, reflect, state, history)
            next_round += 1
            global_stop = stop

    # ── Round 2 & 3：并行 fan-out（共享 Round 1 的 history 快照）──
    if not global_stop and next_round <= MAX_ROUNDS:
        print(f"\n  ── Round 2 & 3（并行 fan-out）──")
        history_snapshot = list(history)  # 快照，两个并行轮共享同一视角
        fan_out_rounds = [next_round, next_round + 1]
        fan_out_results = {}

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    _run_one_round, brain, fetcher, rn,
                    question, state.framework, history_snapshot
                ): rn
                for rn in fan_out_rounds if rn <= MAX_ROUNDS
            }
            for future in as_completed(futures):
                rn = futures[future]
                try:
                    fan_out_results[rn] = future.result()
                except PlanEscalationNeeded as e:
                    print(f"  [升级] Round {rn} Plan 失败，跳过此轮")
                    fan_out_results[rn] = None

        # fan-in：按轮次顺序处理并行结果
        print(f"\n  ── fan-in：合并并行结果 ──")
        for rn in sorted(fan_out_results):
            result = fan_out_results[rn]
            if result is None:
                next_round += 1
                continue
            plan, data, reflect = result
            stop, reason = _process_round_result(rn, plan, data, reflect, state, history)
            next_round += 1
            if stop:
                global_stop = True
                break

    # ── Round 4+：恢复串行（依赖综合 history）──────────────────
    while not global_stop and next_round <= MAX_ROUNDS:
        print(f"\n  ── Round {next_round}（串行）──")
        try:
            plan, data, reflect = _run_one_round(
                brain, fetcher, next_round, question, state.framework, history
            )
            stop, _ = _process_round_result(next_round, plan, data, reflect, state, history)
            next_round += 1
            global_stop = stop
        except PlanEscalationNeeded as e:
            print(f"\n[升级] Round {e.round_num} Plan 失败（错误：{e.last_errors}）")
            hint = input("请提供补充上下文（或 Enter 跳过此轮）: ").strip()
            if not hint:
                next_round += 1
                continue
            define_retry = brain.define_hypothesis(e.round_num, {}, question)
            define_retry["human_supplement"] = hint
            plan = brain.generate_plan(e.round_num, define_retry, question)
            data = fetcher.fetch(plan)
            brain.save_log(f"02_round_{e.round_num}_data.json", data)
            reflect = brain.reflect_on_data(e.round_num, define_retry, plan, data)
            stop, _ = _process_round_result(e.round_num, plan, data, reflect, state, history)
            next_round += 1
            global_stop = stop

    # ── Node 2.5: supervisor_review ──────────────────────────
    print(f"\n[Node 2.5] Supervisor 覆盖检查")
    state, history, next_round = _supervisor_review(
        state, brain, fetcher, question, state.framework, history, next_round
    )

    # ── Node 3: integrate_insights ────────────────────────────
    print(f"\n[Node 3] 整合 {len(state.rounds)} 条洞察")
    conflict_hint = _detect_conflicts(state.rounds)
    brain.round_data = state.round_data
    state.final_insights = brain.integrate_insights(
        question, state.rounds, conflict_hint=conflict_hint
    )
    brain.save_log("04_harness_log.json", {
        "run_id": run_id,
        "rounds_completed": len(state.rounds),
        "conflict_hint": conflict_hint,
        "status": "integrated",
    })

    # ── Node 3.3: adversarial_validate ───────────────────────
    print("\n[Node 3.3] 对抗校验（temperature=0）")
    state = _adversarial_validate(state, brain, conflict_hint=conflict_hint)

    # ── Node 3.5: human_breakpoint_insights ───────────────────
    if human_review:
        state = _human_breakpoint_insights(state)
        if state.status == "cancelled":
            print(f"\n工作流已取消 | run_id: {run_id}")
            return state

    # ── Node 4: format_charts ─────────────────────────────────
    print("\n[Node 4] 生成图表配置")
    formatter = FormatterAgent(api_key=api_key)
    chart_instructions = state.final_insights.get("chart_instructions", [])
    # 若人工断点注入了修改意见，附加到图表生成提示中
    human_note = state.final_insights.get("human_chart_note", "")
    state.charts = formatter.format(chart_instructions, state.round_data, human_note=human_note)

    # ── Node 5: render_report ─────────────────────────────────
    print("\n[Node 5] 渲染 HTML 报告")
    designer = DesignerAgent()
    state.report_html = designer.render(
        final_insights=state.final_insights,
        charts=state.charts,
        run_id=run_id,
        question=question,
    )

    # ── Node 6: write_output（可选） ──────────────────────────
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(state.report_html)
        state.report_path = output_path
        print(f"\n[Node 6] 报告已写入：{output_path}")

    state.status = "done"
    print(f"\n{'='*60}")
    print(f"工作流完成 | 轮次：{len(state.rounds)} | 状态：{state.status}")
    print(f"{'='*60}")
    return state


# ─────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据分析报告 Agent")
    parser.add_argument("--question", "-q", type=str, help="分析问题（留空则运行演示）")
    parser.add_argument("--output", "-o", type=str, default="report.html", help="输出文件路径")
    parser.add_argument("--experience", "-e", type=str, default="experience/", help="经验库目录")
    parser.add_argument("--no-review", action="store_true", help="跳过人工断点（自动化模式）")
    parser.add_argument("--demo", action="store_true", help="运行演示模式（MockFetcher）")
    args = parser.parse_args()

    if args.demo or not args.question:
        print("运行演示模式...")
        run_workflow(
            question="分析2024年各品类利润率走势，找出年度下滑的根因并给出行动建议",
            context={
                "company": "示例零售公司",
                "date_range": {"start": "2024-01", "end": "2024-12"},
                "categories": ["家具", "技术", "办公用品"],
            },
            output_path="run_logs/demo_output/report.html",
            experience_dir=args.experience,
            human_review=not args.no_review,
        )
    else:
        run_workflow(
            question=args.question,
            output_path=args.output,
            experience_dir=args.experience,
            human_review=not args.no_review,
        )
