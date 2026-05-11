# ADR-001: Second Agent Direction (D5)

**Date:** 2026-05-10
**Status:** Accepted

## Context

MVP 已完成 Day 5 working memory + Day 9 summarize。下一步需要决定第二
agent 方向,候选三条路:
- d. 单 agent + tool 化(function calling)
- e. Long-term memory(跨 session 持久化)
- f. Multi-agent orchestration(dispatcher + 专家 agents)

## Decision

**MVP 先走 d**,后续 roadmap 按 **d → f → e** 顺序扩展。

## Rationale

1. **d 是 e/f 的基础**——f 的每个专家 agent 都是 d 风格,e 是给 d 加存储层。
   先 d 是无悔投资。
2. **d → f 顺序优于 d → e**:f 直接命中 JD 关键词
   "agent-based solutions",e 是 infra 改进,resume narrative 价值更低。
3. **f 演示冲击力 > e**:"multi-agent" 一秒讲清楚,"long-term memory"
   还要解释 session 概念。
4. **e 推迟无痛**(已有 session 级 working memory),f 推迟会少 JD #1 卖点。

## Consequences

- **MVP 范围**:`agents/research.py` 单 agent + N 个 tools(get_kb / get_price 等)
- **MVP 不做**:dispatcher 路由层、跨 session 持久化
- **README 写**:"single-agent MVP, multi-agent in 0.2 milestone, long-term memory in 0.3"
- **风险**:面试官追问"为什么不一上来就多 agent" → 答:"先建对单 agent 的 tool calling 基础,
  避免 dispatcher 抽象建在不稳的根上"——这是合理工程顺序

## Future Steps

- Phase 0.2: f. Multi-agent orchestration(dispatcher + 至少 2 个专家 agent)
- Phase 0.3: e. Long-term memory(SQLite 存 session_id → messages)
