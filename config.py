# config.py — 所有参数硬编码于此，LLM 运行时不可覆盖
# 修改此文件即可调整整个系统行为，无需改动 Agent 代码

# ── LLM 温度 ─────────────────────────────────────────────
BRAIN_TEMP      = 0.3   # 大脑 Agent：需要推理但保持稳定
FETCHER_TEMP    = 0.0   # 取数 Agent：严格确定性
FORMATTER_TEMP  = 0.1   # 制图 Agent：轻微创意
DESIGNER_TEMP   = 0.2   # 设计 Agent：排版自由度

# ── 迭代控制 ─────────────────────────────────────────────
MAX_ROUNDS          = 5     # 最大迭代轮次，到达后强制收拢
OVERLAP_THRESHOLD   = 0.80  # 新洞察与已有 insight 重叠度 > 80% 停止
MIN_IMPACT_PCT      = 3.0   # 发现的影响 < 总量 3% 停止该分支

# ── 分析步骤白名单（取数 Agent 只接受此列表内的 step）─────
ALLOWED_STEPS = [
    'trend_analysis',   # 趋势分析
    'decomposition',    # 维度拆解
    'attribution',      # 归因分析
    'risk_mining',      # 风险挖掘
]

# ── 路径配置 ─────────────────────────────────────────────
EXPERIENCE_DIR  = 'experience/'
LOG_DIR         = 'run_logs/{run_id}/'
PLAN_SCHEMA     = 'experience/plan_schema.json'

# ── LLM 模型 ─────────────────────────────────────────────
# 默认使用 Claude；如需切换，修改此处并调整 agents/ 中的 client 初始化
LLM_MODEL = 'claude-opus-4-5'
