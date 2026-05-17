"""
brain_agent.py — 大脑 Agent（核心）

架构：DEFINE → PLAN → ACT → REFLECT 迭代循环
- DEFINE（问自己）：拿到数据前，先设立假设和判断标准
- PLAN（问数据）  ：把假设转化为结构化 Plan JSON，Harness 校验后交给取数 Agent
- ACT             ：取数 Agent 执行，返回 data JSON
- REFLECT（问自己）：对照假设解读数据，更新 insight pool，决定 CONTINUE / PIVOT / STOP

大脑 Agent 内置停止判断（硬代码，非 LLM 判断）：
  A. 达到最大轮次
  B. impact_pct < MIN_IMPACT_PCT
  C. 与已有 insight 重叠度 > OVERLAP_THRESHOLD
  D. has_insight=False → PIVOT（换方向，不停止）

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
    ALLOWED_STEPS,
)
from harness.plan_validator import validate_plan
from harness.output_validator import validate_final_output


# ── 系统提示词 ─────────────────────────────────────────────────────────────

_BRAIN_SYSTEM = """你是一名资深数据分析师，负责主导本次数据分析任务。

你的工作分三个阶段：
**Phase 1 · 设计分析框架**
  输出 JSON：{"framework": {"dimensions": [...], "key_questions": [...], "success_criteria": "..."}}

**Phase 2 · 迭代取数+解读（DEFINE→PLAN→REFLECT 循环）**
  每轮分两步：
  步骤 DEFINE：在取数前，输出你的假设和判断标准
    {"phase": "DEFINE", "hypothesis": "...", "judgment_criteria": "...", "expected_direction": "up|down|flat|unknown"}
  步骤 REFLECT：收到数据后，解读并决策
    {"phase": "REFLECT", "insight_text": "...", "impact_pct": 数字, "has_insight": true/false,
     "conclusion_type": "event_driven|structural|healthy|inconclusive",
     "data_source": "round_N_data.字段名", "decision": "CONTINUE|PIVOT|STOP", "stop_reason": "..."}

**Phase 3 · 整合洞察**
  输出最终 JSON：
  {
    "executive_summary": "2-3句话，含具体数字",
    "findings": [{"title": "...", "content": "...", "data_source": "round_N_data.字段名", "impact_pct": 数字}],
    "data_gaps": ["尚未验证的假设1", ...],
    "chart_instructions": [{"chart_type": "bar|line|scatter", "title": "...", "x_field": "...", "y_field": "..."}]
  }

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


# ── 辅助函数 ───────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """从 LLM 输出中提取第一个合法 JSON 块"""
    # 尝试直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # 从 markdown code block 中提取
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 找第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"无法从输出中提取 JSON：{text[:200]}")


def _compute_overlap(new_text: str, pool: list[str]) -> float:
    """简单词袋重叠度（生产环境可替换为嵌入相似度）"""
    if not pool:
        return 0.0
    new_words = set(new_text.split())
    if not new_words:
        return 0.0
    overlaps = [len(new_words & set(t.split())) / len(new_words) for t in pool]
    return max(overlaps)


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


# ── 停止判断（硬代码，非 LLM）──────────────────────────────────────────────

def should_stop(reflect: dict, insight_pool: list[str], round_num: int) -> tuple[bool, str]:
    """
    返回 (is_stop, reason)
    reason 可为：MAX_ROUNDS / LOW_IMPACT / OVERLAP / PIVOT / CONTINUE
    """
    if round_num >= MAX_ROUNDS:
        return True, f"达到最大轮次({MAX_ROUNDS})，强制收拢"

    impact = reflect.get('impact_pct', 0)
    if impact < MIN_IMPACT_PCT:
        return True, f"impact_pct({impact}%) < MIN_IMPACT_PCT({MIN_IMPACT_PCT}%)，边际收益消失"

    insight_text = reflect.get('insight_text', '')
    overlap = _compute_overlap(insight_text, insight_pool)
    if overlap > OVERLAP_THRESHOLD:
        return True, f"与已有洞察重叠度({overlap:.0%}) > OVERLAP_THRESHOLD({OVERLAP_THRESHOLD:.0%})"

    if not reflect.get('has_insight', True):
        return False, "PIVOT"  # 换方向，不停止

    return False, "CONTINUE"


# ── BrainAgent 主体 ────────────────────────────────────────────────────────

class BrainAgent:
    """
    大脑 Agent 主体。

    Usage:
        from agents import BrainAgent, MockFetcher
        brain = BrainAgent(fetcher=MockFetcher(), experience_dir='experience/')
        report_html = brain.run(
            question="分析2024年各品类利润率走势，找出异常并归因",
            context={"date_range": {"start": "2024-01", "end": "2024-12"}}
        )
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

        self.client = anthropic.Anthropic(api_key=api_key)  # 读取 ANTHROPIC_API_KEY env var
        self.experience_text = _load_experience(experience_dir)
        self.insight_pool: list[str] = []
        self.all_insights: list[dict] = []
        self.round_data: dict[str, Any] = {}  # round_N_data

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

    # ── Phase 1：设计分析框架 ───────────────────────────────────────────────

    def _phase1_framework(self, question: str, context: dict) -> dict:
        print("[Brain] Phase 1: 设计分析框架...")
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
        self._save_log("01_framework.json", framework)
        return framework

    # ── Phase 2：迭代循环 ───────────────────────────────────────────────────

    def _define(self, round_num: int, question: str, framework: dict,
                history: list[dict]) -> dict:
        """DEFINE：取数前设立假设"""
        prompt = (
            f"第{round_num}轮分析。\n"
            f"整体问题：{question}\n"
            f"分析框架：{json.dumps(framework, ensure_ascii=False)}\n"
            f"已完成轮次摘要：{json.dumps(history, ensure_ascii=False)}\n\n"
            "请输出 DEFINE JSON（phase=DEFINE）。"
        )
        raw = self._call(
            [{"role": "user", "content": prompt}], _BRAIN_SYSTEM
        )
        define_out = _extract_json(raw)
        self._save_log(f"02_round_{round_num}_define.json", define_out)
        return define_out

    def _plan(self, round_num: int, define_out: dict, question: str) -> dict:
        """PLAN：把假设转化为 Plan JSON（Harness 校验）"""
        prompt = (
            f"第{round_num}轮。\n"
            f"DEFINE 阶段假设：{json.dumps(define_out, ensure_ascii=False)}\n"
            f"整体问题：{question}\n\n"
            "请输出符合 plan_schema.json 格式的 Plan JSON，只输出 JSON。"
        )
        for attempt in range(3):
            raw = self._call(
                [{"role": "user", "content": prompt}],
                _PLAN_SYSTEM,
                temperature=0.0,
            )
            try:
                plan = _extract_json(raw)
            except ValueError as e:
                print(f"  [Harness] Plan 解析失败（第{attempt+1}次）：{e}")
                continue
            plan['round'] = round_num  # 强制注入轮次
            ok, errors = validate_plan(plan)
            if ok:
                self._save_log(f"02_round_{round_num}_plan.json", plan)
                return plan
            print(f"  [Harness] Plan 校验失败（第{attempt+1}次）：{errors}")
            prompt += f"\n\n上次输出校验失败，错误：{errors}，请修正。"
        raise RuntimeError(f"第{round_num}轮 Plan 连续3次校验失败，中止运行")

    def _reflect(self, round_num: int, define_out: dict,
                 plan: dict, data: dict) -> dict:
        """REFLECT：对照假设解读数据，输出 insight + 决策"""
        prompt = (
            f"第{round_num}轮数据已返回。\n"
            f"DEFINE 假设：{json.dumps(define_out, ensure_ascii=False)}\n"
            f"Plan：{json.dumps(plan, ensure_ascii=False)}\n"
            f"Data：{json.dumps(data, ensure_ascii=False)}\n\n"
            "请输出 REFLECT JSON（phase=REFLECT）。"
        )
        raw = self._call([{"role": "user", "content": prompt}], _BRAIN_SYSTEM)
        reflect = _extract_json(raw)
        self._save_log(f"02_round_{round_num}_reflect.json", reflect)
        return reflect

    def _phase2_loop(self, question: str, framework: dict) -> list[dict]:
        """Phase 2 主循环"""
        history: list[dict] = []

        for round_num in range(1, MAX_ROUNDS + 1):
            print(f"\n[Brain] Phase 2 Round {round_num}/{MAX_ROUNDS}")

            # DEFINE
            define_out = self._define(round_num, question, framework, history)
            print(f"  假设：{define_out.get('hypothesis', '')[:80]}")

            # PLAN + Harness
            plan = self._plan(round_num, define_out, question)
            print(f"  分析步骤：{plan.get('analytical_step')} | 问题：{plan.get('question', '')[:60]}")

            # ACT（取数）
            data = self.fetcher.fetch(plan)
            self._save_log(f"02_round_{round_num}_data.json", data)
            self.round_data[f"round_{round_num}_data"] = data
            print(f"  取数完成，行数：{data.get('row_count', '?')}")

            # REFLECT
            reflect = self._reflect(round_num, define_out, plan, data)
            insight_text = reflect.get('insight_text', '')
            print(f"  洞察：{insight_text[:80]}")

            # 停止判断（硬代码）
            stop, reason = should_stop(reflect, self.insight_pool, round_num)
            print(f"  决策：{'STOP' if stop else reason} | {reason}")

            if reflect.get('has_insight') and insight_text:
                self.insight_pool.append(insight_text)
                self.all_insights.append({
                    "round": round_num,
                    "analytical_step": plan.get('analytical_step'),
                    **reflect,
                })
            history.append({
                "round": round_num,
                "step": plan.get('analytical_step'),
                "question": plan.get('question'),
                "decision": reason,
            })

            if stop:
                break

        return self.all_insights

    # ── Phase 3：洞察整合 ───────────────────────────────────────────────────

    def _phase3_integrate(self, question: str, insights: list[dict]) -> dict:
        print("\n[Brain] Phase 3: 整合洞察...")
        prompt = (
            f"整体问题：{question}\n"
            f"所有轮次洞察：{json.dumps(insights, ensure_ascii=False)}\n"
            f"数据来源：{list(self.round_data.keys())}\n\n"
            "请输出 Phase 3 最终整合 JSON。"
        )
        raw = self._call([{"role": "user", "content": prompt}], _BRAIN_SYSTEM)
        final = _extract_json(raw)
        self._save_log("03_final_insights.json", final)

        # Harness 校验
        ok, errors = validate_final_output(final)
        if not ok:
            print(f"  [Harness] 最终输出校验警告：{errors}")
        return final

    # ── 主入口 ─────────────────────────────────────────────────────────────

    def run(self, question: str, context: dict | None = None) -> dict:
        """
        运行完整分析流程，返回最终洞察 dict。
        由 runner.py 调用；runner 负责将 dict 渲染为 HTML 报告。
        """
        context = context or {}
        print(f"\n{'='*60}")
        print(f"[Brain] 开始分析：{question}")
        print(f"[Brain] run_id：{self.run_id}")
        print(f"{'='*60}")

        # 保存经验库快照
        self._save_log("00_experience_snapshot.json", {
            "experience_dir": self.experience_dir,
            "content_length": len(self.experience_text),
        })

        framework = self._phase1_framework(question, context)
        insights = self._phase2_loop(question, framework)
        final = self._phase3_integrate(question, insights)

        self._save_log("04_harness_log.json", {
            "run_id": self.run_id,
            "rounds_completed": len(insights),
            "insight_pool_size": len(self.insight_pool),
            "status": "completed",
        })

        print(f"\n[Brain] 分析完成，共{len(insights)}条洞察")
        return final

    # ── 日志工具 ───────────────────────────────────────────────────────────

    def _save_log(self, filename: str, data: dict) -> None:
        path = os.path.join(self.log_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
