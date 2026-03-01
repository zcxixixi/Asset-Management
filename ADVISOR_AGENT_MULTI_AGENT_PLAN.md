# AdvisorAgent Multi-Agent Development Plan

## 1. Scope and Objective

Build an `AdvisorAgent` capability that:
- reads validated holdings and market/news context,
- generates personalized portfolio commentary and investment suggestions,
- always returns a stable JSON schema for Web UI consumption.

Design principle:
- `Script-first` for numeric truth (prices, balances, workbook sync).
- `Agent-first` only for interpretation and recommendation text.

## 2. Non-Goals

- No LLM in core valuation math.
- No direct write-back to `assets.xlsx` by AdvisorAgent.
- No publish to `src/data.json` / `public/data.json` without validator gate.

## 3. Runtime Architecture (Advisor Domain)

### 3.1 Agent Roles

1. `NewsCollectorAgent`
- Inputs: holdings symbols, run date.
- Outputs: normalized `portfolio_news` + `global_news`.
- Responsibility: multi-source collection, de-dup, source timestamp normalization.

2. `RelevanceAgent`
- Inputs: holdings weights + collected news.
- Outputs: ranked and filtered news list per asset + macro context tags.
- Responsibility: map macro events to portfolio exposure.

3. `BriefingAgent`
- Inputs: ranked news + holdings snapshot + recent performance.
- Outputs: structured briefing (`headline`, `macro_summary`, `verdict`, `suggestions`, `risks`).
- Responsibility: generate actionable but controlled narrative.

4. `GuardrailAgent`
- Inputs: BriefingAgent output + required schema.
- Outputs: `approved_briefing` or fallback rule-based briefing.
- Responsibility: schema validation, unsupported claim filtering, safe fallback.

### 3.2 Data Contract

Advisor output must always include:
- `generated_at`
- `source`
- `headline`
- `macro_summary`
- `verdict`
- `suggestions` (list of `{asset, action, rationale}`)
- `risks` (list)
- `news_context` (list)
- `global_context` (list)
- `disclaimer`

If validation fails:
- return deterministic rule-based output with the same schema.

## 4. Multi-Agent Development Plan (2-4 Engineering Agents)

### Option A: 4 Agents (Recommended)

1. **Dev Agent A: News Pipeline**
- Implement collector interfaces and normalization utilities.
- Add deterministic fixtures for offline tests.

2. **Dev Agent B: Relevance & Ranking**
- Implement scoring logic (asset mention, sector, macro sensitivity, recency).
- Produce ranked context package for briefing.

3. **Dev Agent C: Briefing & Prompt Layer**
- Implement LLM prompt template + strict JSON response handling.
- Implement deterministic fallback generator.

4. **Dev Agent D: Validation & Integration**
- Implement schema validator and guardrail checks.
- Integrate into existing extract flow and CI tests.

### Option B: 2 Agents (Lean Team)

1. **Dev Agent 1**
- A + B (news + relevance).

2. **Dev Agent 2**
- C + D (briefing + validation + integration).

## 5. Workstream and Milestones

### Milestone 1: Contract First (Day 1)
- Freeze output schema and create test fixtures.
- Define success/failure examples.

### Milestone 2: Core Build (Day 1-2)
- Build collector, ranking, and briefing pipeline.
- Add fallback path with zero external API dependency.

### Milestone 3: Guardrails (Day 2)
- Add JSON schema validation and safety checks.
- Block invalid advisory payload from publishing.

### Milestone 4: Integration + CI (Day 2-3)
- Wire into extraction flow.
- Add regression tests and run in GitHub Actions.

### Milestone 5: Stabilization (Day 3)
- Stress run (multiple cycles).
- Verify deterministic fallback and no schema drift.

## 6. Quality Gates (Must Pass)

1. Schema pass rate: **100%** (LLM path + fallback path).
2. No publish when advisor payload validation fails.
3. Re-run consistency: same input fixture => same fallback output.
4. CI checks green for:
- `extract_data_test.py`
- advisor contract tests
- integration regression tests.

## 7. Testing Strategy

1. Unit tests
- news normalization
- relevance scoring
- schema validation
- fallback generation

2. Integration tests
- full advisor pipeline with fixture data
- full extract pipeline with advisor enabled

3. Failure-path tests
- LLM timeout
- malformed LLM JSON
- empty news set
- partial upstream data

## 8. Risks and Mitigation

1. **Risk: Hallucinated claims**
- Mitigation: strict schema + source-grounded prompt + fallback.

2. **Risk: API instability**
- Mitigation: timeout + retry + local deterministic fallback.

3. **Risk: Output drift breaking UI**
- Mitigation: contract tests in CI and publish gate.

## 9. Definition of Done

AdvisorAgent is complete only when:
- it produces valid structured advisory output every run,
- it never blocks core numeric sync flow,
- it degrades gracefully without external APIs,
- all tests and CI checks pass.

