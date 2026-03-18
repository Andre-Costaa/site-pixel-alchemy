# SPEC.md — Sinfonia Orchestrator Specification

**Version**: 1.0.0
**Status**: Draft
**Inspired by**: [OpenAI Symphony SPEC.md](https://github.com/openai/symphony/blob/main/SPEC.md)

---

## 1. Problem Statement

Pixel Alchemy produces 150+ single-page promotional websites for Brazilian small businesses. Each site follows a repeatable pipeline: read story, research business, create site, generate outreach message, update CRM, commit, validate. This pipeline is executed by LLM agents (Claude Code, Codex, Kimi CLI, Droid/Factory AI) but lacks a formal orchestration contract, leading to incomplete updates, skipped steps, and CRM inconsistencies.

Sinfonia is a lightweight orchestrator that:

1. Reads pending work from `prd.json` (the issue tracker)
2. Dispatches each unit of work to an agent runner
3. Validates completion via `done_gate.py`
4. Marks work as done only after all checks pass

---

## 2. Goals

| Goal | Description |
|------|-------------|
| **Agent-agnostic** | Must work with Claude Code, Codex, Kimi CLI, and Droid/Factory AI without modification |
| **Single source of truth** | `prd.json` is the tracker. Notion is the CRM. Neither is optional. |
| **Fail-safe by default** | Incomplete work is never marked done. The done_gate is the enforcement point. |
| **No over-engineering** | No databases, no Docker, no external services beyond Notion API. Pure Python + shell. |
| **Resumable** | Interrupted runs can be resumed without re-doing completed work |
| **Observable** | Every action produces logs. Failures are loud and specific. |

### Non-Goals

- Real-time collaboration between agents
- GUI or web dashboard
- Support for non-Pixel-Alchemy workflows
- Replacing `prd.json` with a database

---

## 3. System Overview

```
┌─────────────────────────────────────────────────────┐
│                    Sinfonia                          │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Workflow  │  │  Config   │  │   Orchestrator    │ │
│  │  Loader   │  │  Layer    │  │   (polling loop)  │ │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘ │
│       │              │                 │             │
│       ▼              ▼                 ▼             │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ prd.json │  │ sinfonia  │  │   Agent Runner    │ │
│  │ (tracker)│  │  .yaml    │  │ (claude/codex/    │ │
│  │          │  │ (config)  │  │  kimi/droid)      │ │
│  └──────────┘  └──────────┘  └────────┬──────────┘ │
│                                        │             │
│                                        ▼             │
│                               ┌───────────────────┐ │
│                               │   Done Gate       │ │
│                               │   (validation)    │ │
│                               └───────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 4. Core Domain Model

### 4.1 User Story (unit of work)

A user story in `prd.json` is the atomic unit of work. It represents one client site to create.

```json
{
  "id": "US-162",
  "title": "Hemocentro Herois Vet",
  "slug": "hemocentro-herois-vet",
  "nicho": "Veterinaria",
  "nome": "Hemocentro Herois Vet",
  "telefone": "(11) 99999-0000",
  "endereco": "Rua Example, 123 - Sao Paulo, SP",
  "notionPageId": "abc123-def456-...",
  "status": "pending",
  "passes": false,
  "acceptanceCriteria": [...]
}
```

`notionPageId` is mandatory for stories that update Notion. Legacy stories missing this field must be reconciled before execution.

**Story states:**

```
pending ──► in_progress ──► done
                │
                ▼
            failed (retry)
```

| State | Meaning |
|-------|---------|
| `pending` | Story exists, not yet claimed by an agent |
| `in_progress` | Agent is actively working on it (set by orchestrator) |
| `done` | `passes: true` — done_gate passed, all checks green |
| `failed` | Agent encountered an error; eligible for retry |

### 4.2 Workflow

A workflow is the sequence of steps an agent must execute for each story. Defined in `WORKFLOW.md` (see Section 5).

### 4.3 Agent Runner

The component that invokes the actual LLM agent. Each runner type maps to a specific CLI tool:

| Runner | Command | Notes |
|--------|---------|-------|
| `claude` | `claude -p "..." --allowedTools ...` | Claude Code CLI |
| `codex` | `codex --model o4-mini --full-auto -q "..."` | OpenAI Codex CLI |
| `kimi` | `kimi -p "..."` | Kimi CLI |
| `droid` | `droid run --prompt "..."` | Factory AI Droid |

### 4.4 Done Gate

The validation checkpoint that must pass before a story is marked done. Implemented in `scripts/done_gate.py`.

**Checks performed:**

| Check | What it validates |
|-------|-------------------|
| `site.exists` | `site-demo/<slug>/index.html` exists on disk |
| `site.sections` | HTML contains hero, services, testimonials, contact, footer, form |
| `notion.receipt` | Outbox receipt exists in `.notion-outbox/receipts/` |
| `notion.field.Status` | Receipt contains Status = "Mensagem Pronta" |
| `notion.field.Mensagem` | Receipt contains outreach message |
| `notion.field.Slug` | Receipt contains slug |
| `notion.field.URL Demo` | Receipt contains demo URL |
| `notion.field.US ID` | Receipt contains user story ID |
| `git.committed` | Git log contains commit with `site-demo/<slug>/` |

---

## 5. Workflow Specification

The workflow is defined in `WORKFLOW.md` with YAML front matter for runtime configuration.

### 5.1 WORKFLOW.md format

```markdown
---
name: pixel-alchemy-site-pipeline
version: 1
max_retries: 2
timeout_minutes: 30
requires:
  - prd.json
  - template-mensagem-outreach.md
  - scripts/done_gate.py
  - scripts/notion_outbox_enqueue.py
  - scripts/notion_outbox_worker.py
---

# Site Creation Pipeline

You are an agent executing user story {{us_id}} for Pixel Alchemy.

## Context Files
- Read `AGENTS.md` for complete project conventions
- Read `template-mensagem-outreach.md` for outreach message rules

## Steps

### Step 1: Read the user story
[exact instructions...]

### Step 2: Research the business
[exact instructions...]

[...through Step 7]
```

### 5.2 Template variables

The orchestrator substitutes these variables before passing the workflow to an agent:

| Variable | Source | Example |
|----------|--------|---------|
| `{{us_id}}` | story.id | `US-162` |
| `{{slug}}` | story.slug | `hemocentro-herois-vet` |
| `{{nome}}` | story.nome | `Hemocentro Herois Vet` |
| `{{nicho}}` | story.nicho | `Veterinaria` |
| `{{telefone}}` | story.telefone | `(11) 99999-0000` |
| `{{endereco}}` | story.endereco | `Rua Example, 123` |
| `{{notion_page_id}}` | story.notionPageId | `abc123-def456` |
| `{{date}}` | current date | `2026-03-12` |

If `{{notion_page_id}}` is missing, the agent must stop and run `scripts/reconcile_prd_notion_links.py` before continuing.

---

## 6. Configuration

### 6.1 sinfonia.yaml

```yaml
# sinfonia.yaml — Orchestrator configuration

# Which agent runner to use
runner: claude  # claude | codex | kimi | droid

# Runner-specific settings
runners:
  claude:
    command: "claude"
    args: ["-p", "{{prompt}}", "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Agent"]
    model: null  # uses default
  codex:
    command: "codex"
    args: ["--model", "o4-mini", "--full-auto", "-q", "{{prompt}}"]
  kimi:
    command: "kimi"
    args: ["-p", "{{prompt}}"]
  droid:
    command: "droid"
    args: ["run", "--prompt", "{{prompt}}"]

# Polling settings
polling:
  interval_seconds: 5
  max_concurrent: 1  # how many stories to process in parallel

# Retry settings
retry:
  max_attempts: 2
  backoff_seconds: 30

# Paths (relative to repo root)
paths:
  prd: "prd.json"
  workflow: "WORKFLOW.md"
  agents_md: "AGENTS.md"
  outbox: ".notion-outbox"
  logs: ".sinfonia/logs"
  state: ".sinfonia/state"

# Done gate
done_gate:
  command: "cd scripts && python3 done_gate.py --us-id {{us_id}}"
  mark_done: "cd scripts && python3 mark_story_done.py --us-id {{us_id}}"
```

### 6.2 Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_TOKEN` | Yes | Notion integration token (for outbox worker) |
| `SINFONIA_RUNNER` | No | Override runner from config (e.g., `codex`) |
| `SINFONIA_DRY_RUN` | No | If `1`, log actions without executing |
| `SINFONIA_LOG_LEVEL` | No | `debug`, `info` (default), `warn`, `error` |

---

## 7. Orchestration State Machine

```
                    ┌──────────┐
                    │ PENDING  │ ◄── story in prd.json with passes=false
                    └────┬─────┘
                         │ orchestrator claims story
                         ▼
                    ┌──────────┐
                    │ CLAIMED  │ ◄── written to .sinfonia/state/<us_id>.json
                    └────┬─────┘
                         │ agent runner starts
                         ▼
                    ┌──────────┐
                    │ RUNNING  │ ◄── agent is executing workflow
                    └────┬─────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
             ┌──────────┐  ┌──────────────┐
             │ VALIDATING│  │   ERRORED    │
             └────┬─────┘  └──────┬───────┘
                  │               │ retry < max?
                  │               ▼
                  │         ┌──────────────┐
                  │         │ RETRY_QUEUED │──► back to CLAIMED
                  │         └──────────────┘
                  │
             ┌────┴────┐
             │         │
             ▼         ▼
       ┌──────────┐  ┌──────────┐
       │   DONE   │  │  FAILED  │ ◄── max retries exhausted or
       └──────────┘  └──────────┘     done_gate FAIL after retries
```

### 7.1 State file

Each in-progress story gets a state file at `.sinfonia/state/<us_id>.json`:

```json
{
  "us_id": "US-162",
  "state": "RUNNING",
  "runner": "claude",
  "claimed_at": "2026-03-12T14:30:00Z",
  "started_at": "2026-03-12T14:30:02Z",
  "attempt": 1,
  "max_attempts": 3,
  "last_error": null,
  "done_gate_result": null
}
```

### 7.2 State transitions

| From | To | Trigger |
|------|----|---------|
| PENDING | CLAIMED | Orchestrator selects story from prd.json |
| CLAIMED | RUNNING | Agent runner process starts |
| RUNNING | VALIDATING | Agent runner process exits 0 |
| RUNNING | ERRORED | Agent runner process exits non-zero |
| VALIDATING | DONE | `done_gate.py` returns PASS |
| VALIDATING | ERRORED | `done_gate.py` returns FAIL |
| ERRORED | RETRY_QUEUED | attempt < max_attempts |
| ERRORED | FAILED | attempt >= max_attempts |
| RETRY_QUEUED | CLAIMED | After backoff delay |

---

## 8. Polling Loop

The orchestrator runs a continuous polling loop:

```python
while True:
    # 1. Load prd.json
    stories = load_pending_stories("prd.json")

    # 2. Filter: only stories with passes=false and no active state file
    claimable = [s for s in stories if not is_claimed_or_running(s)]

    # 3. Respect concurrency limit
    running_count = count_running_agents()
    available_slots = config.max_concurrent - running_count

    # 4. Claim and dispatch
    for story in claimable[:available_slots]:
        claim(story)
        dispatch_agent(story)

    # 5. Check completed agents
    for state in get_running_states():
        if agent_process_finished(state):
            if agent_exit_code(state) == 0:
                transition(state, "VALIDATING")
                run_done_gate(state)
            else:
                transition(state, "ERRORED")
                maybe_retry(state)

    # 6. Sleep
    sleep(config.polling.interval_seconds)
```

### 8.1 Leader election (single-instance guard)

Only one Sinfonia instance should run at a time. Use a lockfile at `.sinfonia/sinfonia.lock` with PID. If the PID is stale (process dead), reclaim the lock.

### 8.2 Reconciliation

On startup, Sinfonia reconciles state:

1. Read all `.sinfonia/state/*.json` files
2. For any in RUNNING state: check if agent process is still alive
3. If process dead: transition to ERRORED (orphaned run)
4. For any in CLAIMED state older than `timeout_minutes`: transition to ERRORED (timeout)

---

## 9. Workspace Management

### 9.1 Isolation model

Each agent works directly in the repository root. There is no workspace isolation (unlike Symphony's sandbox model) because:

- Sites are independent (no shared state between `site-demo/<slug-a>/` and `site-demo/<slug-b>/`)
- With `max_concurrent: 1`, there are no file conflicts
- Git commits are per-story with specific file paths (`git add site-demo/<slug>/`)

If `max_concurrent > 1` is needed in the future, use git worktrees:

```bash
git worktree add .sinfonia/worktrees/<us_id> -b sinfonia/<us_id>
```

### 9.2 Cleanup

After a story reaches DONE or FAILED:
- State file is moved to `.sinfonia/archive/<us_id>.json`
- Worktree (if any) is removed
- Log file is preserved at `.sinfonia/logs/<us_id>.log`

---

## 10. Agent Runner

### 10.1 Prompt construction

The orchestrator builds the agent prompt by:

1. Loading `WORKFLOW.md`
2. Substituting template variables (`{{us_id}}`, `{{slug}}`, etc.)
3. Prepending a system preamble:

```
You are executing Sinfonia workflow "pixel-alchemy-site-pipeline" for story {{us_id}}.

CRITICAL RULES:
- Follow AGENTS.md for all project conventions
- Do NOT skip any step in the workflow
- Do NOT mark the story as done — the orchestrator handles that
- If you encounter an error, exit with a non-zero code and describe the error
- Your output will be logged to .sinfonia/logs/{{us_id}}.log

Story data:
{{story_json}}
```

4. Appending the workflow body

### 10.2 Runner execution

```python
def dispatch_agent(story, config):
    prompt = build_prompt(story)
    runner = config.runners[config.runner]

    # Replace {{prompt}} in args
    args = [a.replace("{{prompt}}", prompt) for a in runner.args]
    cmd = [runner.command] + args

    # Start process, capture output to log
    log_path = f".sinfonia/logs/{story.id}.log"
    with open(log_path, "w") as log:
        process = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=repo_root
        )

    # Store PID in state
    update_state(story.id, pid=process.pid, state="RUNNING")
    return process
```

### 10.3 Timeout handling

If an agent exceeds `timeout_minutes`:
1. Send SIGTERM to the process
2. Wait 10 seconds
3. Send SIGKILL if still alive
4. Transition to ERRORED with `last_error: "timeout"`

---

## 11. Done Gate Integration

After an agent exits successfully, the orchestrator runs the done gate:

```bash
cd scripts && python3 done_gate.py --us-id {{us_id}}
```

**If PASS:**
1. Run `python3 scripts/mark_story_done.py --us-id {{us_id}}` (sets `passes: true` in prd.json)
2. Transition state to DONE
3. Log success

**If FAIL:**
1. Parse the failure reasons from done_gate output
2. Store in `state.done_gate_result`
3. Transition to ERRORED
4. If retries remain, the next attempt gets the failure context appended to its prompt:

```
PREVIOUS ATTEMPT FAILED. Done gate results:
- site.sections: FAIL — missing "testimonials" section
- notion.field.Mensagem: FAIL — Mensagem MISSING from outbox receipt

Fix these issues and complete the workflow.
```

---

## 12. Observability

### 12.1 Log files

Each story produces a log at `.sinfonia/logs/<us_id>.log` containing:
- Full agent stdout/stderr
- State transitions with timestamps
- Done gate results

### 12.2 Summary report

After each polling cycle, Sinfonia writes a summary to `.sinfonia/status.json`:

```json
{
  "updated_at": "2026-03-12T15:00:00Z",
  "runner": "claude",
  "total_stories": 12,
  "pending": 8,
  "running": 1,
  "done": 2,
  "failed": 1,
  "current": {
    "us_id": "US-164",
    "state": "RUNNING",
    "started_at": "2026-03-12T14:55:00Z",
    "attempt": 1
  }
}
```

### 12.3 Terminal output

While running, Sinfonia prints a status line:

```
[Sinfonia] 14:55:02 | US-164 RUNNING (attempt 1/3) | 2/12 done | 1 failed | runner=claude
```

---

## 13. Error Taxonomy

| Error Type | Cause | Recovery |
|------------|-------|----------|
| `agent_crash` | Agent process exited non-zero | Retry with same prompt |
| `agent_timeout` | Agent exceeded timeout_minutes | Retry with reduced scope hint |
| `done_gate_fail` | Validation checks failed | Retry with failure context in prompt |
| `notion_error` | Outbox worker failed (API error) | Retry; check NOTION_TOKEN |
| `git_conflict` | Merge conflict during commit | FAILED; requires human intervention |
| `lockfile_stale` | Previous Sinfonia crashed | Auto-recover on startup |

---

## 14. File Structure

```
.sinfonia/
├── sinfonia.lock          # PID lockfile (single instance guard)
├── status.json            # Current run summary
├── state/
│   ├── US-162.json        # Active story state
│   └── US-163.json
├── archive/
│   ├── US-160.json        # Completed/failed story states
│   └── US-161.json
└── logs/
    ├── US-162.log         # Agent output log
    └── US-163.log

sinfonia.yaml              # Orchestrator configuration
WORKFLOW.md                # Agent workflow template
SPEC.md                    # This file
AGENTS.md                  # Agent-agnostic project guide
prd.json                   # Issue tracker (source of truth)
```

---

## 15. Implementation Phases

### Phase 1: MVP (minimum viable orchestrator)

- [ ] `sinfonia.py` — single-file orchestrator with polling loop
- [ ] `sinfonia.yaml` — configuration file
- [ ] `WORKFLOW.md` — workflow template with variable substitution
- [ ] State machine (PENDING → CLAIMED → RUNNING → DONE/FAILED)
- [ ] Single runner support (start with `claude`)
- [ ] Done gate integration
- [ ] Log capture
- [ ] Lockfile guard

### Phase 2: Multi-runner + Retry

- [ ] Add `codex`, `kimi`, `droid` runners
- [ ] Retry logic with backoff
- [ ] Failure context injection (previous done_gate results in retry prompt)
- [ ] `status.json` summary
- [ ] Reconciliation on startup

### Phase 3: Concurrency + Polish

- [ ] `max_concurrent > 1` with git worktree isolation
- [ ] Terminal status line (live updates)
- [ ] `sinfonia report` command (summary of completed/failed stories)
- [ ] `sinfonia retry US-XXX` command (manual retry)
- [ ] `sinfonia status` command (show current state)

---

## 16. CLI Interface

```bash
# Start the orchestrator (foreground, polling loop)
python3 sinfonia.py run

# Process a single story and exit
python3 sinfonia.py run --once --story US-162

# Dry run: show what would be dispatched
python3 sinfonia.py run --dry-run

# Show current status
python3 sinfonia.py status

# Retry a failed story
python3 sinfonia.py retry US-162

# Use a different runner
python3 sinfonia.py run --runner codex

# Show logs for a story
python3 sinfonia.py logs US-162
```

---

## 17. Differences from Symphony

| Aspect | Symphony | Sinfonia |
|--------|----------|----------|
| **Tracker** | Linear (API) | `prd.json` (local file) |
| **Agent** | Codex only | Claude Code, Codex, Kimi CLI, Droid |
| **Workspace** | Git worktree per issue | Shared repo (single concurrent) |
| **Deployment** | Cloud/CI | Local machine |
| **Complexity** | Multi-service architecture | Single Python file |
| **Validation** | PR-based review | `done_gate.py` automated checks |
| **CRM** | None | Notion via outbox pattern |
| **Language** | TypeScript | Python |

---

## Appendix A: Quick Start

```bash
# 1. Ensure prd.json has pending stories
python3 -c "import json; d=json.load(open('prd.json')); print(f'{sum(1 for s in d[\"userStories\"] if not s.get(\"passes\"))} pending stories')"

# 2. Ensure NOTION_TOKEN is set
source .env

# 3. Start Sinfonia
python3 sinfonia.py run --runner claude
```

## Appendix B: Adding a New Runner

1. Add entry to `sinfonia.yaml` under `runners:`
2. Ensure the CLI tool is installed and on PATH
3. Test with: `python3 sinfonia.py run --once --story US-XXX --runner new_runner`
4. The runner must accept a prompt string and exit 0 on success, non-zero on failure
