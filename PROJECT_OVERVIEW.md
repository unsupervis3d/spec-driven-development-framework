# PROJECT_OVERVIEW: Trade Trainer

> **Framework:** spec-driven-build v0.1.0
> **Status:** Pilot project for the framework. Both the framework and the product are being developed together; expect both to change as we learn.

---

## What this is

Trade Trainer is a **trade-defense system**. You upload a Tradovate CSV of completed trades; the system compares each trade to your declared trading strategy and flags every trade that doesn't fit. For each flagged trade, the system initiates a conversation that requires you to defend the trade. It pushes back on weak defenses. It does not let you off the hook because the trade made money.

The product's job is to **make process violations expensive even when they're profitable**. The unit of judgment is process fit, not PnL. A lucky winner — a trade that violated your strategy but happened to make money — is flagged as hard as a losing rule-break, because keeping those trades in your repertoire is unsustainable.

It is built for one user (the author).

---

## What this is NOT

Non-goals. Anything in this list that appears in a spec, ticket, or PR is auto-rejected.

- **Not a trade analyzer.** The system does not produce one-shot analyses of trades. The output is a conversation, initiated by the system, in which the user does the analyzing and the system pushes back.
- **Not a PnL-driven coach.** PnL does not drive flagging. The system flags trades for process violations, regardless of outcome. Lucky winners are flagged. In-strategy losers are not.
- **Not a multi-tenant product.** No registration, no password reset, no user-management UI. Schema is multi-tenant-shaped (see hard constraints) but the v1 surface is single-user.
- **Not a live trading tool.** No order entry, no broker connections, no live market data feeds. CSV in, conversations out.
- **Not a pre-trade discipline tool yet.** No real-time alerts, no live market reading, no integration with Atlas. That is v4 and lives in a separate planning conversation. (However, the user model the interrogator builds in v1/v2 is explicitly designed to be the substrate v4 will consume.)
- **Not a tax/accounting tool.** No commissions, no realized/unrealized PnL reporting, no broker-statement reconciliation.
- **Not a multi-broker tool.** v1 ingests Tradovate CSVs only.
- **Not Atlas-integrated.** v1 is fully standalone.

---

## Users

One user: the author. A futures day trader running ~10 trades/day (median 3-4, max ~50) across many prop accounts that all clear through a single Tradovate-routed account via a trade copier. NQ is the primary instrument; ES and others appear occasionally.

The user is technical (senior software engineer) and does not need hand-holding UX.

**The moments the product is designed for:**

1. End of trading day: upload today's CSV, get a list of flagged trades, work through the interrogations. The user expects to feel mild discomfort. That is the product working.
2. Sunday evening: review the week's flag-and-defend conversations to see which kinds of violations recurred and what defenses the user kept giving.
3. Periodically: revise the declared strategy as the user's actual practice evolves. The system should treat strategy updates as a serious event, not a quick edit — versioning, timestamp, and a "what changed and why" note.

---

## The core loop

```
   ┌─────────────────────┐
   │  CSV upload         │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐       ┌───────────────────────┐
   │  Tradovate parser   │ ────► │  Trades (Postgres)    │
   └─────────────────────┘       └──────────┬────────────┘
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │  Strategy fit check   │ ────► uses current strategy
                                 └──────────┬────────────┘       version
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │  Flagged trades       │
                                 └──────────┬────────────┘
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │  Interrogation        │ ────► Anthropic API
                                 │  conversations        │       (Claude, devil's advocate
                                 └──────────┬────────────┘        system prompt)
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │  Justification log    │ ────► tagged with violation type
                                 └───────────────────────┘       and defense category
```

The justification log is the long-game artifact. Over months it becomes the corpus that powers v3 (pattern surfacing — "you've used this defense 14 times this quarter") and eventually v4 (pre-trade nags — "this looks like the kind of trade you couldn't defend on Tuesday").

---

## Architecture

### Stack

- **Backend:** Python 3.12+, FastAPI.
- **Database:** PostgreSQL 16. Not TimescaleDB.
- **Frontend:** TBD between Nuxt 3, HTMX-on-Jinja, or plain Jinja with minimal JS. Decision deferred to the phase that needs UI.
- **LLM:** Anthropic Claude. Single provider, no abstraction layer. Model selection per call site (Sonnet for routine flagging, possibly Opus for interrogation conversations).
- **Deployment:** Deferred. Not relevant to v1 phases 1-4. Will be decided when there is something worth deploying.

### Major data entities

- **Strategy** — versioned, semi-structured. A strategy is a markdown-ish document with declared sections: instruments, time windows, valid setups, invalid setups, risk rules, exit rules. Each section is free-text but must exist. Strategies are immutable once created; "editing" produces a new version. Trades are evaluated against the strategy version that was current at trade time.
- **Trade** — one Tradovate round-trip pair. Symbol, qty, buy/sell prices, buy/sell timestamps, direction (inferred), PnL, the strategy version it was evaluated against, the fit verdict (in-strategy / out-of-strategy / unknown), the violation category if out-of-strategy.
- **Flag** — a (trade, violation_reason, severity) record. Created by the fit check when a trade is judged out-of-strategy.
- **Conversation** — the interrogation about a flag. A series of messages alternating between the system (asking, pushing back) and the user (defending).
- **Defense** — a tagged user statement extracted from a conversation. Tagged with a category ("market structure read," "gut feel," "revenge," "FOMO," "size adjustment," etc. — the tag list grows as patterns emerge). The corpus of defenses is what makes v3 and v4 possible.

---

## Hard constraints

Auto-fail criteria. Grep-checked on every PR.

1. **PnL does not drive flagging.** No code path that flags trades may read the `pnl` column. The fit check sees direction, timing, instrument, size, and market context — not PnL. PnL is displayed in the UI but is not an input to the judgment. Grep target: `pnl` referenced in any module under `app/fit/` or `app/flagging/` fails review.
2. **The system never tells the user a trade was "good" or "bad."** No code path produces a verdict on the trade's outcome. The system asks; the user explains; the system pushes back. Review rejects strings like "great trade," "bad call," "you should have," "you shouldn't have" appearing in LLM prompts as instructions to *produce* such language.
3. **The system never closes an interrogation on the user's first answer.** The interrogator must ask at least one follow-up. A defense is not accepted until the user has been pushed at least once. Enforced at prompt level and verified by behavioral contract tests.
4. **Strategies are immutable; edits create new versions.** No `UPDATE strategies SET ...` outside administrative migration scripts. Schema-enforced via no-update trigger or structural design. Trades reference the strategy version at trade time, not the current one.
5. **`user_id` on every domain table.** Every trade, strategy, upload, flag, conversation, and defense has a `user_id` FK. Every query scopes by `user_id`. Schema-enforced default of 1 in v1. Grep target: `SELECT.*FROM (trades|strategies|uploads|flags|conversations|defenses)` without `WHERE user_id` fails review.
6. **Postgres, not Timescale.** No hypertables, no Timescale SQL, no `timescaledb` in requirements.
7. **Single LLM provider.** Anthropic only. Direct SDK imports. No provider abstraction. Grep target: `openai|gemini|bedrock|provider_registry` fails review.
8. **All secrets via environment variables.** Grep target: `sk-`, `api_key\s*=\s*['"]`, similar literals fail review.
9. **No external job infrastructure.** No Redis, no Celery, no message queue. Async work uses FastAPI background tasks or APScheduler in-process. Postgres is the only external service the application depends on.
10. **No live trading code paths.** No broker SDKs, no live feeds. Imports of `schwab`, `tradovate-api`, `ib_insync`, live-mode `databento` fail review. Historical Databento lookups in a designated context-fetch module are allowed.
11. **CSV parser handles quoted PnL.** `"$1,160.00"` → decimal `1160.00`. Sign preserved. Behavioral contract + unit test required.
12. **Trade direction inferred from timestamp ordering.** LONG iff `bought_timestamp < sold_timestamp`, else SHORT. Behavioral contract + unit test for both cases.
13. **One trade per round-trip.** No aggregation, no netting at write time.
14. **Uploaded CSVs are stored read-only after ingest.** The parser reads; the parser does not modify the source file.

---

## Cost contracts

- **Per-flag interrogation budget:** ≤ $0.15 per flagged trade conversation. (Higher than per-analysis because interrogations are multi-turn.)
- **Per-fit-check budget:** ≤ $0.02 per trade (the cheaper triage step that decides whether a trade gets flagged).
- **Expected monthly spend:** ~300 trades/month × $0.02 fit check = $6. Roughly 20% of trades flagged × $0.15 interrogation = $9. Total ~$15/month at v1 volumes.
- **Hard monthly ceiling:** $75/month. Above this, new fit checks pause and the UI surfaces an alert.
- **All API calls log cost.** Every Anthropic call records input tokens, output tokens, model, cost, and which entity (trade/flag/conversation) it was for, in a `llm_calls` table. Phase Reviewer audits at phase boundaries.
- **Model selection is explicit.** Each call site names its model. Grep target: model strings outside a declared constants module fail review.

---

## Phase plan

Five phases. v1 = phases 1-4. v2 = phase 5.

### Phase 1: Foundation

Project scaffolding, Postgres schema, simple local auth (env-var password gate sufficient for v1 development), application runs locally. Hello-world web UI confirming the auth and DB connection work. No trading logic. Exists to exercise the framework on something low-stakes and establish the project skeleton.

### Phase 2: CSV ingest and trade storage

Tradovate CSV upload, parser with behavioral contracts (quoted PnL, direction inference, one-trade-per-round-trip), trades table populated. Web UI lists trades (read-only, no judgments yet). Manual smoke tests against the sample CSV plus at least three real CSVs over different trading days.

### Phase 3: Strategy capture

Strategy intake flow (semi-structured: declared sections, free-text inside each). Strategies table with versioning. Web UI for viewing the current strategy and viewing version history. No fit checking yet — this phase is about getting the strategy into the system in a form the LLM can reason against in Phase 4.

The intake itself is a guided conversation, not a form: the system walks the user through declaring each section, asking clarifying questions when an answer is vague. ("You said 'I trade breakouts' — what's your definition of a breakout for the purposes of this system?") The output is the markdown strategy document, stored and versioned.

### Phase 4: Fit check + interrogation

The core product. Fit check runs on every new trade against the strategy version current at trade time. Flagged trades go to an inbox in the UI. User opens a flagged trade and enters an interrogation conversation with the system. System pushes back, asks follow-ups, refuses to accept weak defenses. Conversation is persisted. Defenses are tagged (initially by the LLM, with the tag list growing over time).

**End of v1.**

### Phase 5: Pattern surfacing

Now that v1 has produced a defense corpus, surface patterns: "You've justified this kind of trade four times this month with the same defense category." Day-of-week / time-of-day breakdowns of out-of-strategy trades. Strategy revision suggestions ("you keep doing X — either declare X as in-strategy or commit to stopping").

Explicitly NOT a real-time pre-trade tool. That is still v4.

---

## Open decisions (deferred to phase specs)

- Market context source for the fit check: Databento historical pull, web search, cached daily summaries, or a hybrid. The fit check needs to know what the market was doing around the trade to judge fit on setups defined in market terms ("breakouts," "failed auctions," etc.).
- Frontend stack: Nuxt 3, HTMX, or plain Jinja.
- Defense tag taxonomy: starts seeded with a small list (gut feel, FOMO, revenge, size error, time-of-day, setup misread). Phase 4 spec decides whether new tags require human approval or the LLM proposes them autonomously.
- Background job mechanism: FastAPI BackgroundTasks, APScheduler, or arq.
- Migrations tool: Alembic vs. hand-rolled SQL.
- Test runner layout: pytest is assumed.

---

## Success criteria for the pilot

These are about the framework, not the product.

- All five phases ship through the seven-agent roster as written.
- Each phase retro identifies at least one concrete framework improvement.
- At least one hard constraint catches a real violation during review.
- At least one behavioral contract test catches a real bug.
- Total framework-overhead time is tracked honestly. If it exceeds ~30% of phase time, that is a framework problem to fix in v0.2.0.

Product-side success is bonus: the author uses Trade Trainer regularly enough to revise his declared strategy at least once during the pilot.

---

## Living document policy

This file is updated when something at this layer changes. Phase-level changes go in phase specs. Framework-level changes go in the framework repo. If you want to edit this file mid-phase, stop and ask whether the change really belongs here.
