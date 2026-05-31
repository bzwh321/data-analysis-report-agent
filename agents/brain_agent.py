"""
brain_agent.py — 大脑 Agent（节点执行层）

职责：执行工作流中属于"大脑"的各个节点。
不负责调度逻辑（几轮、何时停止）——那些在 workflow.py 里。

公开接口（由 workflow.py 调用）：
  brain.design_framework(question, context)                        → Phase 1 框架
  brain.define_hypothesis(round_num, ...)                          → 单轮假设
  brain.generate_plan(round_num, define_out, question)             → 单轮取数计划（含升级阶梯）
  brain.reflect_on_data(round_num, define_out, plan, data)         → 单轮洞察
  brain.integrate_insights(question, insights, conflict_hint="")   → Phase 3 整合

异常：
  PlanEscalationNeeded — generate_plan 三级升级全失败后抛出，由 workflow.py 触发人工断点

输出约束（v2）：
  - 结论必须追溯到本轮 data JSON 的具体字段
  - 组织归因不是必须模块；无数据支撑时跳过
  - 输出为段落叙述 + 数字列表，不用分析框架子标题
  - 写到数据支撑的最后一层；结尾自然给出下一步方向
"""

import json
import os
import re
import time
from typing import Any

import anthropic

from config import (
    BRAIN_TEMP, LLM_MODEL, MAX_ROUNDS,
    MIN_IMPACT_PCT, OVERLAP_THRESHOLD,
)
from config import PLAN_SCHEMA
from harness.plan_validator import validate_plan
from harness.output_validator import validate_final_output


# ── 自定义异常 ──────────────────────────────────────────────────────────────

class PlanEscalationNeeded(Exception):
    """
    generate_plan 三级升级全部失败后抛出。
    由 workflow.py 捕获，触发人工干预断点。
    """
    def __init__(self, round_num: int, last_errors: list):
        self.round_num = round_num
        self.last_errors = last_errors
        super().__init__(f"Round {round_num} Plan 生成失败，需人工介入")


# ── 系统提示词 ─────────────────────────────────────────────────────────────

_BRAIN_SYSTEM = """你是一名资深数据分析师，负责主导本次数据分析任务。

你的工作分三个阶段：
**Phase 1 · 设计分析框架**
  输出 JSON：{{"framework": {{"dimensions": [...], "key_questions": [...], "success_criteria": "..."}}}}

**Phase 2 · 迭代取数+解读（DEFINE→PLAN→REFLECT 循环）**
  每轮分两步：
  步骤 DEFINE：在取数前，输出你的假设和判断标准
    {{"phase": "DEFINE", "hypothesis": "...", "judgment_criteria": "...", "expected_direction": "up|down|flat|unknown"}}
  步骤 REFLECT：收到数据后，解读并决策
    {{"phase": "REFLECT", "insight_text": "...", "impact_pct": 数字, "has_insight": true/false,
     "conclusion_type": "event_driven|structural|healthy|inconclusive",
     "data_source": "round_N_data.字段名", "decision": "CONTINUE|PIVOT|STOP", "stop_reason": "..."}}

**Phase 3 · 整合洞察**
  输出最终 JSON：
  {{
    "executive_summary": "2-3句话，含具体数字",
    "findings": [{{"title": "...", "content": "...", "data_source": "round_N_data.字段名", "impact_pct": 数字}}],
    "data_gaps": ["尚未验证的假设1", ...],
    "chart_instructions": [{{"chart_type": "bar|line|scatter", "title": "...", "x_field": "...", "y_field": "..."}}]
  }}

**输出规则（不可违反）**：
1. 结论必须能追溯到本轮 data JSON 的具体字段（格式：round_N_data.字段名）
2. 组织归因不是必须模块：数据没有 → 跳过，不推断
3. 禁止子标题：①数据事实 ②运营逻辑 ③组织归因 ④业务结论
4. 禁用词：需要关注 / 可能存在问题 / 后续需要跟进 / 这一现象值得重视
5. 数据边界处理：写到数据支撑的最后一层，结尾一句话给下一步建议方向（不声明"当前数据无法..."）

**停止信号**（由系统硬代码判断，你的 REFLECT 输出仅供参考）：
- impact_pct < {MIN_IMPACT_PCT}% → 系统强制停止该分支
- 与已有 insight 重叠度 > {OVERLAP_THRESHOLD:.0%} → 系统强制停止
- 轮次 ≥ {MAX_ROUNDS} → 系统强制收拢
""".format(
    MIN_IMPACT_PCT=MIN_IMPACT_PCT,
    OVERLAP_THRESHOLD=OVERLAP_THRESHOLD,
    MAX_ROUNDS=MAX_ROUNDS,
)

_PLAN_SYSTEM = """你是大脑 Agent 的 Plan 生成模块。
根据 DEFINE 阶段的假设，生成符合 plan_schema.json 格式的 JSON。
只输出 JSON，不输出任何说明文字。
"""

_ADVERSARIAL_SYSTEM = """你是一名数据分析报告的独立审查员，负责对抗性校验。
你的任务：以批判视角逐条检查报告结论的质量，找出漏洞，不放过任何问题。

校验维度（必须逐条检查）：
1. 可溯源性 — data_source 引用的字段，在对应轮次的数据中是否真实存在？
2. 逻辑一致性 — 各 findings 之间是否互相矛盾？方向是否一致？
3. 数字合理性 — impact_pct 是否有数据佐证？多条 findings 之和超过 100% 是否有说明？
4. 摘要匹配 — executive_summary 是否准确反映 findings 核心内容，无夸大无遗漏？
5. 边界诚实 — 是否存在数据不支撑但结论超出数据范围的推断？

输出规则：
- 每个问题必须有 severity（critical=影响核心结论 / warning=值得注意不阻断输出）
- 没有问题时 passed=true，issues=[]
- 只输出 JSON，不输出任何说明文字

输出格式：
{
  "passed": true/false,
  "issues": [
    {
      "severity": "critical|warning",
      "finding_ref": "对应 finding 的 title 或 executive_summary",
      "issue": "具体问题（一句话，≤50字）",
      "suggestion": "修正方向（一句话）"
    }
  ],
  "verdict": "通过" | "建议修正" | "重大问题，需人工确认"
}
"""


# ── 辅助函数 ───────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """从 LLM 输出中提取第一个合法 JSON 块"""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"无法从输出中提取 JSON：{text[:200]}")


def _load_experience(experience_dir: str) -> str:
    """加载经验库（注入大脑 Agent 上下文）"""
    parts = []
    thresholds_path = os.path.join(experience_dir, 'thresholds.json')
    if os.path.exists(thresholds_path):
        with open(thresholds_path, encoding='utf-8') as f:
            parts.append("【业务阈值】\n" + f.read())
    priority_path = os.path.join(experience_dir, 'priority_rules.md')
    if os.path.exists(priority_path):
        with open(priority_path, encoding='utf-8') as f:
            parts.append("【优先级规则】\n" + f.read())
    summaries_path = os.path.join(experience_dir, 'good_summaries.md')
    if os.path.exists(summaries_path):
        with open(summaries_path, encoding='utf-8') as f:
            parts.append("【好结论范例】\n" + f.read())
    return "\n\n".join(parts)


# ── BrainAgent 主体 ────────────────────────────────────────────────────────

class BrainAgent:
    """
    大脑 Agent：负责执行工作流中"大脑"相关的各个节点。
    调度逻辑（迭代几轮、何时停止）由 workflow.py 负责。

    Usage（通过 workflow.py 调用）：
        from workflow import run_workflow
        state = run_workflow("分析2024年各品类利润率走势", fetcher=MockFetcher())

    直接使用（仅测试单个节点时）：
        brain = BrainAgent(fetcher=MockFetcher(), experience_dir='experience/')
        framework = brain.design_framework("分析问题", {})
    """

    def __init__(
        self,
        fetcher,
        experience_dir: str = 'experience/',
        log_dir: str = 'run_logs/',
        run_id: str | None = None,
        api_key: str | None = None,
    ):
        self.fetcher = fetcher
        self.experience_dir = experience_dir
        self.run_id = run_id or f"run_{int(time.time())}"
        self.log_dir = os.path.join(log_dir, self.run_id)
        os.makedirs(self.log_dir, exist_ok=True)

        self.client = anthropic.Anthropic(api_key=api_key)
        self.experience_text = _load_experience(experience_dir)
        self.round_data: dict[str, Any] = {}  # 由 workflow.py 在 Node 3 前同步

    # ── 内部 LLM 调用 ──────────────────────────────────────────────────────

    def _call(self, messages: list[dict], system: str, temperature: float = BRAIN_TEMP) -> str:
        resp = self.client.messages.create(
            model=LLM_MODEL,
            max_tokens=4096,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        return resp.content[0].text

    # ── 日志工具（供 workflow.py 和各节点调用）────────────────────────────

    def save_log(self, filename: str, data: dict) -> None:
        path = os.path.join(self.log_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── Node 1：设计分析框架（Phase 1）────────────────────────────────────

    def design_framework(self, question: str, context: dict) -> dict:
        """
        Phase 1：读取经验库，设计分析维度、关键问题和成功标准。
        返回 framework dict，交给 workflow.py 存入 WorkflowState。
        """
        print("[Brain] Phase 1: 设计分析框架...")
        self.save_log("00_experience_snapshot.json", {
            "experience_dir": self.experience_dir,
            "content_length": len(self.experience_text),
        })
        messages = [
            {
                "role": "user",
                "content": (
                    f"分析问题：{question}\n"
                    f"背景：{json.dumps(context, ensure_ascii=False)}\n\n"
                    f"经验库：\n{self.experience_text}\n\n"
                    "请输出 Phase 1 的分析框架 JSON。"
                ),
            }
        ]
        raw = self._call(messages, _BRAIN_SYSTEM)
        framework = _extract_json(raw)
        self.save_log("01_framework.json", framework)
        return framework

    # ── Node 2a：设立假设（每轮 DEFINE）───────────────────────────────────

    def define_hypothesis(
        self,
        round_num: int,
        question: str,
        framework: dict,
        history: list[dict],
    ) -> dict:
        """
        取数前设立假设和判断标准。
        history 为已完成轮次的摘要列表，由 workflow.py 维护并传入。
        """
        prompt = (
            f"第{round_num}轮分析。\n"
            f"整体问题：{question}\n"
            f"分析框架：{json.dumps(framework, ensure_ascii=False)}\n"
            f"已完成轮次摘要：{json.dumps(history, ensure_ascii=False)}\n\n"
            "请输出 DEFINE JSON（phase=DEFINE）。"
        )
        raw = self._call([{"role": "user", "content": prompt}], _BRAIN_SYSTEM)
        define_out = _extract_json(raw)
        self.save_log(f"02_round_{round_num}_define.json", define_out)
        return define_out

    # ── Node 2b：生成取数计划（每轮 PLAN，含 Harness 校验）────────────────

    def generate_plan(self, round_num: int, define_out: dict, question: str) -> dict:
        """
        把假设转化为结构化 Plan JSON。

        升级阶梯（三级，失败后逐级增强上下文）：
          Attempt 1：原始提示词，直接重试
          Attempt 2：注入 plan_schema.json 完整格式（上下文增强）
          Attempt 3：注入 schema + 精简约束（只要求最少必填字段）
          全部失败 → raise PlanEscalationNeeded（由 workflow.py 触发人工断点）
        """
        base_prompt = (
            f"第{round_num}轮。\n"
            f"DEFINE 阶段假设：{json.dumps(define_out, ensure_ascii=False)}\n"
            f"整体问题：{question}\n\n"
            "请输出符合 plan_schema.json 格式的 Plan JSON，只输出 JSON。"
        )

        # 预加载 plan_schema（用于 Attempt 2/3 上下文增强）
        schema_text = ""
        if os.path.exists(PLAN_SCHEMA):
            with open(PLAN_SCHEMA, encoding="utf-8") as f:
                schema_text = f.read()

        last_errors = []
        for attempt in range(3):
            prompt = base_prompt

            # Attempt 2：注入完整 schema
            if attempt >= 1 and schema_text:
                prompt += f"\n\n[上下文增强] Plan Schema 格式要求：\n{schema_text}"

            # Attempt 3：额外精简提示
            if attempt >= 2:
                prompt += (
                    "\n\n[精简提示] 如果字段复杂，优先保证以下必填字段正确："
                    " round, analytical_step, question, query_spec(metrics/group_by/date_range),"
                    " expected_output(format/required_fields), stop_condition(if_impact_below_pct/reason)。"
                )
            if last_errors:
                prompt += f"\n\n上次校验失败，错误：{last_errors}，请修正。"

            raw = self._call(
                [{"role": "user", "content": prompt}],
                _PLAN_SYSTEM,
                temperature=0.0,
            )
            try:
                plan = _extract_json(raw)
            except ValueError as e:
                last_errors = [str(e)]
                print(f"  [升级 {attempt+1}/3] Plan 解析失败：{e}")
                continue

            plan['round'] = round_num
            ok, errors = validate_plan(plan)
            if ok:
                self.save_log(f"02_round_{round_num}_plan.json", plan)
                return plan

            last_errors = errors
            print(f"  [升级 {attempt+1}/3] Plan 校验失败：{errors}")

        # 三级全失败 → 抛出，由 workflow.py 触发人工断点
        raise PlanEscalationNeeded(round_num, last_errors)

    # ── Node 2d：解读数据（每轮 REFLECT）──────────────────────────────────

    def reflect_on_data(
        self,
        round_num: int,
        define_out: dict,
        plan: dict,
        data: dict,
    ) -> dict:
        """
        对照假设解读数据，输出洞察文本和决策信号。
        停止判断由 workflow.py 的 _should_stop() 执行，此处只输出原始信号。
        """
        prompt = (
            f"第{round_num}轮数据已返回。\n"
            f"DEFINE 假设：{json.dumps(define_out, ensure_ascii=False)}\n"
            f"Plan：{json.dumps(plan, ensure_ascii=False)}\n"
            f"Data：{json.dumps(data, ensure_ascii=False)}\n\n"
            "请输出 REFLECT JSON（phase=REFLECT）。"
        )
        raw = self._call([{"role": "user", "content": prompt}], _BRAIN_SYSTEM)
        reflect = _extract_json(raw)
        self.save_log(f"02_round_{round_num}_reflect.json", reflect)
        return reflect

    # ── Node 3：整合洞察（Phase 3）────────────────────────────────────────

    def integrate_insights(
        self,
        question: str,
        insights: list[dict],
        conflict_hint: str = "",
        correction_hint: str = "",
    ) -> dict:
        """
        整合所有轮次洞察，输出 final_insights dict。
        调用前需由 workflow.py 设置 self.round_data，供溯源使用。

        Args:
            conflict_hint:   由 _detect_conflicts() 生成的冲突提示。
            correction_hint: 由对抗校验发现的问题，触发修正时注入。
        """
        print("\n[Brain] Phase 3: 整合洞察...")
        prompt = (
            f"整体问题：{question}\n"
            f"所有轮次洞察：{json.dumps(insights, ensure_ascii=False)}\n"
            f"数据来源：{list(self.round_data.keys())}\n\n"
            "请输出 Phase 3 最终整合 JSON。"
        )
        if conflict_hint:
            prompt += (
                f"\n\n[整合提示] 各轮结论存在以下冲突，整合时必须显式说明如何裁决：\n{conflict_hint}"
            )
        if correction_hint:
            prompt += (
                f"\n\n[修正提示] 上次输出被对抗校验发现以下问题，本次必须修正：\n{correction_hint}"
            )
        raw = self._call([{"role": "user", "content": prompt}], _BRAIN_SYSTEM)
        final = _extract_json(raw)
        self.save_log("03_final_insights.json", final)

        ok, errors = validate_final_output(final)
        if not ok:
            print(f"  [Harness] 最终输出校验警告：{errors}")
        return final

    # ── Node 3.3：对抗校验（温度 0，独立审查）────────────────────────────

    def adversarial_review(
        self,
        final_insights: dict,
        round_data: dict,
    ) -> dict:
        """
        用独立审查视角对 final_insights 进行对抗性校验。

        特点：
          · temperature=0，结果确定性强，不受随机性影响
          · 使用独立系统提示（_ADVERSARIAL_SYSTEM），与生成提示分离
          · 校验 5 个维度：可溯源性、逻辑一致性、数字合理性、摘要匹配、边界诚实

        Returns:
            dict: {"passed": bool, "issues": list, "verdict": str}
        """
        print("\n[Brain] Node 3.3: 对抗校验（temperature=0）...")
        prompt = (
            f"待校验报告：\n{json.dumps(final_insights, ensure_ascii=False)}\n\n"
            f"本次取数结果摘要（用于核实 data_source）：\n"
            + json.dumps(
                {k: {"row_count": v.get("row_count"), "fields": v.get("fields", [])}
                 for k, v in round_data.items()},
                ensure_ascii=False,
            )
            + "\n\n请输出校验结果 JSON，只输出 JSON。"
        )
        raw = self._call(
            [{"role": "user", "content": prompt}],
            _ADVERSARIAL_SYSTEM,
            temperature=0.0,
        )
        try:
            result = _extract_json(raw)
        except ValueError:
            # 解析失败视为通过，避免误阻断流程
            result = {"passed": True, "issues": [], "verdict": "解析失败，视为通过"}

        passed = result.get("passed", True)
        verdict = result.get("verdict", "")
        issues = result.get("issues", [])
        critical_count = sum(1 for i in issues if i.get("severity") == "critical")
        warning_count = sum(1 for i in issues if i.get("severity") == "warning")

        if passed:
            print(f"  [对抗校验] 通过 — {verdict}")
        else:
            print(f"  [对抗校验] {verdict} | critical={critical_count} warning={warning_count}")
            for issue in issues:
                sev = issue.get("severity", "?")
                ref = issue.get("finding_ref", "?")
                msg = issue.get("issue", "")
                print(f"    [{sev}] {ref}: {msg}")

        self.save_log("03b_adversarial_review.json", result)
        return result
