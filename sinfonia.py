#!/usr/bin/env python3
"""
Sinfonia — Lightweight orchestrator for Pixel Alchemy site pipeline.

Reads pending stories from prd.json, dispatches them to an LLM agent runner
(Claude Code, Codex, Kimi CLI, or Droid), validates via done_gate, and marks
done on success. Designed for tmux-based observability.

State machine: PENDING -> CLAIMED -> RUNNING -> VALIDATING -> DONE
                                         |                      |
                                         v                      v
                                      ERRORED -> RETRY_QUEUED -> CLAIMED (retry)
                                         |
                                         v (max retries)
                                       FAILED

Features:
- Retry with failure context injection (done_gate results in retry prompt)
- Backoff delay between retries (configurable via retry.backoff_seconds)
- SIGTERM/SIGKILL timeout handling (10s grace period)
- Reconciliation on startup (orphaned processes, stale claims)
- Lockfile guard (single-instance via fcntl.flock)
- current.log symlink for live tail -f

Usage:
    python3 sinfonia.py run [--runner claude] [--once] [--story US-162] [--dry-run]
    python3 sinfonia.py status
    python3 sinfonia.py retry US-162
    python3 sinfonia.py logs US-162
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
SINFONIA_DIR = REPO_ROOT / ".sinfonia"
STATE_DIR = SINFONIA_DIR / "state"
ARCHIVE_DIR = SINFONIA_DIR / "archive"
LOGS_DIR = SINFONIA_DIR / "logs"
LOCK_FILE = SINFONIA_DIR / "sinfonia.lock"
STATUS_FILE = SINFONIA_DIR / "status.json"
PROMPTS_DIR = SINFONIA_DIR / "prompts"

# ── Colors ───────────────────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[97m"


def ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(msg: str, color: str = C.WHITE) -> None:
    print(f"{C.DIM}[{ts()}]{C.RESET} {color}{msg}{C.RESET}", flush=True)


def log_ok(msg: str) -> None:
    log(msg, C.GREEN)


def log_warn(msg: str) -> None:
    log(msg, C.YELLOW)


def log_err(msg: str) -> None:
    log(msg, C.RED)


def log_info(msg: str) -> None:
    log(msg, C.CYAN)


# ── Config ───────────────────────────────────────────────────────────────────

def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or (REPO_ROOT / "sinfonia.yaml")
    if not config_path.exists():
        log_err(f"Config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


# ── PRD ──────────────────────────────────────────────────────────────────────

def load_prd(config: dict[str, Any]) -> dict[str, Any]:
    prd_path = REPO_ROOT / config["paths"]["prd"]
    with open(prd_path) as f:
        return json.load(f)


def get_pending_stories(prd: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        s for s in prd.get("userStories", [])
        if isinstance(s, dict) and not s.get("passes", False)
    ]


# ── State Machine ────────────────────────────────────────────────────────────

STATES = ("PENDING", "CLAIMED", "RUNNING", "VALIDATING", "ERRORED", "RETRY_QUEUED", "DONE", "FAILED")


def ensure_dirs() -> None:
    for d in (SINFONIA_DIR, STATE_DIR, ARCHIVE_DIR, LOGS_DIR, PROMPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def state_path(us_id: str) -> Path:
    return STATE_DIR / f"{us_id}.json"


def read_state(us_id: str) -> dict[str, Any] | None:
    p = state_path(us_id)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def write_state(state: dict[str, Any]) -> None:
    p = state_path(state["us_id"])
    with open(p, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")


def archive_state(us_id: str) -> None:
    src = state_path(us_id)
    if src.exists():
        dst = ARCHIVE_DIR / f"{us_id}.json"
        src.rename(dst)


def new_state(us_id: str, runner: str) -> dict[str, Any]:
    return {
        "us_id": us_id,
        "state": "CLAIMED",
        "runner": runner,
        "claimed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "started_at": None,
        "finished_at": None,
        "attempt": 1,
        "max_attempts": 3,
        "pid": None,
        "last_error": None,
        "done_gate_result": None,
    }


def transition(state: dict[str, Any], new: str, **extra: Any) -> None:
    old = state["state"]
    state["state"] = new
    state.update(extra)
    write_state(state)
    colors = {
        "CLAIMED": C.CYAN, "RUNNING": C.MAGENTA, "VALIDATING": C.YELLOW,
        "DONE": C.GREEN, "FAILED": C.RED, "ERRORED": C.RED, "RETRY_QUEUED": C.YELLOW,
    }
    color = colors.get(new, C.WHITE)
    log(f"{state['us_id']}  {old} -> {color}{C.BOLD}{new}{C.RESET}", C.WHITE)


# ── Lockfile ─────────────────────────────────────────────────────────────────

_lock_fd = None


def acquire_lock() -> bool:
    global _lock_fd
    ensure_dirs()
    _lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        return True
    except OSError:
        return False


def release_lock() -> None:
    global _lock_fd
    if _lock_fd:
        fcntl.flock(_lock_fd, fcntl.LOCK_UN)
        _lock_fd.close()
        _lock_fd = None
        LOCK_FILE.unlink(missing_ok=True)


# ── Prompt Builder ───────────────────────────────────────────────────────────

def build_prompt(story: dict[str, Any], config: dict[str, Any], retry_context: str | None = None) -> str:
    workflow_path = REPO_ROOT / config["paths"]["workflow"]
    workflow_raw = workflow_path.read_text(encoding="utf-8")

    # Strip YAML front matter
    if workflow_raw.startswith("---"):
        end = workflow_raw.find("---", 3)
        if end != -1:
            workflow_raw = workflow_raw[end + 3:].lstrip("\n")

    # Extract story fields
    us_id = story["id"]
    slug = story.get("slug", "")
    nome = story.get("nome", story.get("title", "").replace(" - Site Completo", ""))
    nicho = story.get("nicho", "")
    telefone = story.get("telefone", "")
    endereco = story.get("endereco", "")
    notion_page_id = story.get("notionPageId", "")
    today = datetime.date.today().isoformat()

    # If slug not in story top-level, try extracting from acceptance criteria
    if not slug:
        for crit in story.get("acceptanceCriteria", []):
            m = re.search(r"site-demo/([^'/\s]+)", str(crit))
            if m:
                slug = m.group(1)
                break

    # Template substitution
    replacements = {
        "us_id": us_id,
        "slug": slug,
        "nome": nome,
        "nicho": nicho,
        "telefone": telefone,
        "endereco": endereco,
        "notion_page_id": notion_page_id,
        "date": today,
    }

    # Use simple string replacement ({{ }} style)
    prompt = workflow_raw
    for key, val in replacements.items():
        prompt = prompt.replace("{{" + key + "}}", str(val))

    # Prepend system preamble
    preamble = f"""You are executing Sinfonia workflow for story {us_id}.

CRITICAL RULES:
- Read AGENTS.md before starting — it has all project conventions
- Follow every step in the workflow below. Do NOT skip any.
- Do NOT run mark_story_done.py — the orchestrator handles that
- If you encounter an error you cannot fix, exit with non-zero code
- All output is logged to .sinfonia/logs/{us_id}.log

Story data:
{json.dumps(story, indent=2, ensure_ascii=False)}

---

"""
    full = preamble + prompt
    if retry_context:
        full += f"\n\n---\n\n{retry_context}\n"
    return full


def save_prompt(us_id: str, prompt: str) -> Path:
    p = PROMPTS_DIR / f"{us_id}.md"
    p.write_text(prompt, encoding="utf-8")
    return p


# ── Agent Runner ─────────────────────────────────────────────────────────────

def dispatch_agent(story: dict[str, Any], state: dict[str, Any], config: dict[str, Any]) -> subprocess.Popen:
    us_id = story["id"]
    runner_name = state["runner"]
    runner_cfg = config["runners"][runner_name]
    # Build retry context from previous failure if any
    retry_context = None
    if state.get("done_gate_result") and state.get("attempt", 1) > 1:
        retry_context = (
            f"PREVIOUS ATTEMPT FAILED (attempt {state['attempt'] - 1} of {state['max_attempts']}).\n"
            f"Done gate results:\n{state['done_gate_result']}\n\n"
            f"Fix these specific issues and complete the workflow."
        )

    # Build and save prompt to file
    prompt = build_prompt(story, config, retry_context=retry_context)
    prompt_file = save_prompt(us_id, prompt)

    # Log file — create it immediately so tail -f can start
    log_path = LOGS_DIR / f"{us_id}.log"
    log_path.touch()

    # Symlink current.log for easy tail -f
    current_link = LOGS_DIR / "current.log"
    current_link.unlink(missing_ok=True)
    try:
        current_link.symlink_to(log_path.name)
    except OSError:
        pass

    log_info(f"{us_id}  Dispatching to {runner_name} (log: .sinfonia/logs/{us_id}.log)")

    # Write a wrapper shell script that executes the agent command.
    # This avoids shell quoting issues with `script -c` when the prompt
    # contains thousands of characters with special characters.
    wrapper_path = PROMPTS_DIR / f"{us_id}.sh"
    _write_wrapper_script(wrapper_path, runner_name, runner_cfg, prompt_file)

    # Use `script` to allocate a pseudo-terminal so CLIs produce their full
    # output as if running in a real terminal. Captures stdout+stderr to log.
    # Flags: -q = quiet, -f = flush after each write, -c = run command
    proc = subprocess.Popen(
        ["script", "-q", "-f", "-c", f"bash {wrapper_path}", str(log_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(REPO_ROOT),
    )

    transition(state, "RUNNING", started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=proc.pid)
    return proc


def _write_wrapper_script(wrapper_path: Path, runner_name: str, runner_cfg: dict, prompt_file: Path) -> None:
    """Write a shell script that invokes the agent CLI with the prompt."""
    cmd = runner_cfg["command"]
    args = runner_cfg["args"]

    # For runners that take the prompt inline (claude -p, codex exec, kimi --print -p),
    # we use cat to pipe the prompt file contents. For droid -f, we pass the file path.
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]

    if runner_name == "droid":
        # droid exec -f reads from file path
        parts = [cmd]
        for arg in args:
            if "{{prompt_file}}" in arg:
                parts.append(str(prompt_file))
            else:
                parts.append(arg)
        lines.append("exec " + " ".join(_shell_quote(p) for p in parts))
    elif runner_name == "claude":
        # claude -p reads prompt from positional arg; use file as arg via $()
        parts = [cmd]
        for arg in args:
            if "{{prompt_file}}" in arg:
                # Replace with $(cat prompt_file) for safe expansion
                parts.append(f'"$(cat {_shell_quote(str(prompt_file))})"')
            else:
                parts.append(_shell_quote(arg))
        lines.append("exec " + " ".join(parts))
    else:
        # codex, kimi — same pattern: prompt as inline arg via cat
        parts = [cmd]
        for arg in args:
            if "{{prompt_file}}" in arg:
                parts.append(f'"$(cat {_shell_quote(str(prompt_file))})"')
            else:
                parts.append(_shell_quote(arg))
        lines.append("exec " + " ".join(parts))

    wrapper_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    wrapper_path.chmod(0o755)


def _shell_quote(s: str) -> str:
    """Quote a string for safe shell embedding."""
    if not s:
        return "''"
    # If it's short and safe, no quoting needed
    if all(c.isalnum() or c in "-_=./,:" for c in s):
        return s
    # Otherwise single-quote it (escaping any existing single quotes)
    return "'" + s.replace("'", "'\"'\"'") + "'"




def kill_agent(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(10):
            time.sleep(1)
            if not is_process_alive(pid):
                return
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # process exists but owned by another user


# ── Done Gate ────────────────────────────────────────────────────────────────

def run_done_gate(us_id: str, config: dict[str, Any]) -> tuple[bool, str]:
    cmd = config["done_gate"]["command"].replace("{{us_id}}", us_id)
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=str(REPO_ROOT),
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, "done_gate timed out after 300s"
    output = proc.stdout + proc.stderr
    passed = "DONE GATE: PASS" in output
    return passed, output


def run_mark_done(us_id: str, config: dict[str, Any]) -> tuple[bool, str]:
    cmd = config["done_gate"]["mark_done"].replace("{{us_id}}", us_id)
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=str(REPO_ROOT),
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, "mark_story_done timed out after 300s"
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, output


# ── Status ───────────────────────────────────────────────────────────────────

def write_status(config: dict[str, Any], prd: dict[str, Any], running: dict[str, Any] | None = None) -> None:
    stories = prd.get("userStories", [])
    total = len(stories)
    done = sum(1 for s in stories if s.get("passes"))
    pending = total - done

    # Count active states
    active_running = 0
    active_failed = 0
    for f in STATE_DIR.iterdir():
        if f.suffix == ".json":
            with open(f) as fh:
                st = json.load(fh)
            if st["state"] in ("RUNNING", "CLAIMED", "VALIDATING"):
                active_running += 1
            elif st["state"] in ("FAILED", "ERRORED"):
                active_failed += 1

    status = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "runner": config.get("runner", "unknown"),
        "total_stories": total,
        "done": done,
        "pending": pending,
        "running": active_running,
        "failed": active_failed,
        "current": running,
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
        f.write("\n")


def print_status_line(us_id: str | None, state_name: str, attempt: int, max_attempts: int, done: int, total: int, failed: int, runner: str) -> None:
    pct = int(done / total * 100) if total > 0 else 0

    # Progress bar
    bar_width = 20
    filled = int(bar_width * done / total) if total > 0 else 0
    bar = f"{'█' * filled}{'░' * (bar_width - filled)}"

    current = f"{us_id} {state_name} ({attempt}/{max_attempts})" if us_id else "idle"

    # Move cursor up to overwrite previous status line, clear line, print new
    line = (
        f"{C.DIM}[Sinfonia]{C.RESET} "
        f"{C.CYAN}{bar}{C.RESET} {pct}% "
        f"{C.GREEN}{done}{C.RESET}/{total} done "
        f"{C.RED}{failed} fail{C.RESET} "
        f"| {C.MAGENTA}{current}{C.RESET} "
        f"| runner={C.BOLD}{runner}{C.RESET}"
    )
    # \033[2K clears entire line, \r returns to start
    print(f"\033[2K\r{line}", end="", flush=True)


# ── Reconciliation ───────────────────────────────────────────────────────────

def reconcile(config: dict[str, Any]) -> None:
    timeout = config.get("timeout_minutes", 30) * 60

    for f in STATE_DIR.iterdir():
        if f.suffix != ".json":
            continue
        with open(f) as fh:
            state = json.load(fh)

        if state["state"] == "RUNNING":
            pid = state.get("pid")
            if pid and not is_process_alive(pid):
                log_warn(f"{state['us_id']}  Orphaned (PID {pid} dead) -> ERRORED")
                transition(state, "ERRORED", last_error="orphaned: agent process died")
            elif state.get("started_at"):
                started = datetime.datetime.fromisoformat(state["started_at"])
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
                if elapsed > timeout:
                    log_warn(f"{state['us_id']}  Timeout ({int(elapsed)}s > {timeout}s) -> ERRORED")
                    if pid:
                        kill_agent(pid)
                    transition(state, "ERRORED", last_error="timeout")

        elif state["state"] == "CLAIMED":
            claimed = datetime.datetime.fromisoformat(state["claimed_at"])
            elapsed = (datetime.datetime.now(datetime.timezone.utc) - claimed).total_seconds()
            if elapsed > 120:  # 2 min claim without starting = stale
                log_warn(f"{state['us_id']}  Stale claim ({int(elapsed)}s) -> ERRORED")
                transition(state, "ERRORED", last_error="stale claim")


# ── Main Loop ────────────────────────────────────────────────────────────────

def run_loop(config: dict[str, Any], runner_override: str | None, once: bool, story_filter: str | None, dry_run: bool) -> int:
    runner = runner_override or config.get("runner", "claude")
    if runner not in config.get("runners", {}):
        log_err(f"Unknown runner: {runner}. Available: {list(config['runners'].keys())}")
        return 1

    max_concurrent = config.get("polling", {}).get("max_concurrent", 1)
    interval = config.get("polling", {}).get("interval_seconds", 5)
    max_attempts = config.get("retry", {}).get("max_attempts", 2) + 1  # +1 for initial attempt

    # Track active agent processes: us_id -> (Popen, state)
    active: dict[str, tuple[subprocess.Popen, dict[str, Any]]] = {}
    completed_count = 0
    failed_count = 0

    log(f"{C.BOLD}Sinfonia{C.RESET} starting | runner={C.BOLD}{runner}{C.RESET} | max_concurrent={max_concurrent}", C.CYAN)

    # Reconcile on startup
    reconcile(config)

    while True:
        prd = load_prd(config)
        pending = get_pending_stories(prd)
        total = len(prd.get("userStories", []))
        done_total = total - len(pending)

        # Filter if specific story requested
        if story_filter:
            pending = [s for s in pending if s["id"] == story_filter]
            if not pending and not active:
                state_data = read_state(story_filter)
                if state_data and state_data["state"] == "DONE":
                    log_ok(f"{story_filter} already done.")
                    return 0
                if not state_data:
                    log_err(f"Story {story_filter} not found in pending stories.")
                    return 1

        # Skip stories that already have state files (in progress / errored)
        claimable = []
        for s in pending:
            # Skip stories that already reached FAILED and were archived
            if (ARCHIVE_DIR / f"{s['id']}.json").exists():
                continue
            existing = read_state(s["id"])
            if existing is None:
                claimable.append(s)
            elif existing["state"] in ("ERRORED", "RETRY_QUEUED"):
                if existing.get("attempt", 1) < max_attempts:
                    # Eligible for retry
                    claimable.append(s)

        # Available slots
        available_slots = max_concurrent - len(active)

        if dry_run:
            log_info(f"DRY RUN: {len(pending)} pending, {len(claimable)} claimable, {available_slots} slots")
            for s in claimable[:available_slots]:
                log(f"  Would dispatch: {s['id']} - {s.get('title', '')}")
            return 0

        # Claim and dispatch
        backoff = config.get("retry", {}).get("backoff_seconds", 30)
        for story in claimable[:available_slots]:
            us_id = story["id"]
            existing = read_state(us_id)

            if existing and existing["state"] in ("ERRORED", "RETRY_QUEUED"):
                # Retry with backoff
                attempt = existing.get("attempt", 1) + 1
                log_warn(f"{us_id}  Retrying (attempt {attempt}/{max_attempts})")
                state = existing
                state["attempt"] = attempt
                transition(state, "RETRY_QUEUED")
                if backoff > 0:
                    log_info(f"{us_id}  Backoff {backoff}s before retry")
                    time.sleep(backoff)
                transition(state, "CLAIMED")
            else:
                state = new_state(us_id, runner)
                state["max_attempts"] = max_attempts
                write_state(state)
                log_info(f"{us_id}  {C.BOLD}{story.get('title', '')}{C.RESET}")

            proc = dispatch_agent(story, state, config)
            active[us_id] = (proc, state)

        # Check completed agents
        finished = []
        for us_id, (proc, state) in active.items():
            retcode = proc.poll()
            if retcode is not None:
                finished.append(us_id)
                state["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

                if retcode == 0:
                    # Agent finished — run done gate
                    transition(state, "VALIDATING")
                    log_info(f"{us_id}  Running done_gate...")

                    passed, output = run_done_gate(us_id, config)

                    if passed:
                        log_ok(f"{us_id}  Done gate PASS")
                        ok, mark_output = run_mark_done(us_id, config)
                        if ok:
                            transition(state, "DONE")
                            completed_count += 1
                            archive_state(us_id)
                        else:
                            log_err(f"{us_id}  mark_story_done failed: {mark_output[:200]}")
                            transition(state, "ERRORED", last_error="mark_done_failed", done_gate_result=output)
                    else:
                        log_err(f"{us_id}  Done gate FAIL")
                        # Write failure details to log
                        gate_log = LOGS_DIR / f"{us_id}.gate.log"
                        gate_log.write_text(output, encoding="utf-8")
                        transition(state, "ERRORED", last_error="done_gate_fail", done_gate_result=output[:2000])
                else:
                    log_err(f"{us_id}  Agent exited with code {retcode}")
                    transition(state, "ERRORED", last_error=f"exit_code_{retcode}")

        for us_id in finished:
            del active[us_id]

        # Check for timeouts in active agents
        timeout_secs = config.get("timeout_minutes", 30) * 60
        timed_out = []
        for us_id, (proc, state) in active.items():
            if state.get("started_at"):
                started = datetime.datetime.fromisoformat(state["started_at"])
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
                if elapsed > timeout_secs:
                    log_warn(f"{us_id}  Timeout ({int(elapsed)}s > {timeout_secs}s)")
                    kill_agent(proc.pid)
                    transition(state, "ERRORED", last_error="timeout")
                    timed_out.append(us_id)
        for us_id in timed_out:
            del active[us_id]

        # Handle retries for errored states
        for f in STATE_DIR.iterdir():
            if f.suffix != ".json":
                continue
            with open(f) as fh:
                st = json.load(fh)
            if st["state"] == "ERRORED" and st.get("attempt", 1) >= max_attempts:
                transition(st, "FAILED")
                failed_count += 1
                archive_state(st["us_id"])

        # Update status
        prd = load_prd(config)
        current_info = None
        if active:
            first_id = next(iter(active))
            _, st = active[first_id]
            current_info = {"us_id": first_id, "state": st["state"], "attempt": st.get("attempt", 1)}
        write_status(config, prd, current_info)

        # Print status line
        print_status_line(
            us_id=next(iter(active), None),
            state_name=list(active.values())[0][1]["state"] if active else "idle",
            attempt=list(active.values())[0][1].get("attempt", 1) if active else 0,
            max_attempts=max_attempts,
            done=done_total + completed_count,
            total=total,
            failed=failed_count,
            runner=runner,
        )

        # Exit conditions
        if once and not active:
            print()  # newline after status line
            if completed_count > 0:
                log_ok(f"Completed {completed_count} stories.")
            if failed_count > 0:
                log_err(f"Failed {failed_count} stories.")
            return 1 if failed_count > 0 else 0

        if not active and not claimable:
            if once or story_filter:
                print()
                log_ok("No more work to do.")
                return 0
            # Continuous mode: wait for new work

        time.sleep(interval)


# ── CLI Commands ─────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> int:
    config = load_config()
    ensure_dirs()

    if not acquire_lock():
        log_err("Another Sinfonia instance is running. Remove .sinfonia/sinfonia.lock if stale.")
        return 1

    try:
        return run_loop(
            config=config,
            runner_override=args.runner,
            once=args.once,
            story_filter=args.story,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        print()
        log_warn("Interrupted by user. Active agents may still be running.")
        return 130
    finally:
        release_lock()


def cmd_status(_args: argparse.Namespace) -> int:
    if not STATUS_FILE.exists():
        print("No status file found. Run 'sinfonia.py run' first.")
        return 1
    with open(STATUS_FILE) as f:
        status = json.load(f)
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # Also show active states
    if STATE_DIR.exists():
        states = sorted(STATE_DIR.glob("*.json"))
        if states:
            print(f"\nActive states ({len(states)}):")
            for p in states:
                with open(p) as f:
                    st = json.load(f)
                color = {"RUNNING": C.MAGENTA, "ERRORED": C.RED, "CLAIMED": C.CYAN}.get(st["state"], C.WHITE)
                print(f"  {st['us_id']}  {color}{st['state']}{C.RESET}  attempt={st.get('attempt', '?')}")
    return 0


def cmd_retry(args: argparse.Namespace) -> int:
    us_id = args.us_id
    ensure_dirs()

    # Check archive
    archived = ARCHIVE_DIR / f"{us_id}.json"
    if archived.exists():
        archived.unlink()
        log_info(f"Removed archived state for {us_id}")

    # Check active state
    active = state_path(us_id)
    if active.exists():
        active.unlink()
        log_info(f"Removed active state for {us_id}")

    log_ok(f"{us_id} reset. Run 'sinfonia.py run --story {us_id}' to retry.")
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    us_id = args.us_id
    log_file = LOGS_DIR / f"{us_id}.log"
    gate_file = LOGS_DIR / f"{us_id}.gate.log"

    if log_file.exists():
        print(f"=== Agent Log: {log_file} ===")
        print(log_file.read_text(encoding="utf-8", errors="replace"))

    if gate_file.exists():
        print(f"\n=== Done Gate Log: {gate_file} ===")
        print(gate_file.read_text(encoding="utf-8", errors="replace"))

    if not log_file.exists() and not gate_file.exists():
        print(f"No logs found for {us_id}")
        return 1
    return 0


# ── Entry Point ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sinfonia — Pixel Alchemy orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run       Start the orchestrator polling loop
  status    Show current orchestrator status
  retry     Reset a failed story for retry
  logs      Show logs for a story
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Start orchestrator")
    p_run.add_argument("--runner", help="Override runner (claude/codex/kimi/droid)")
    p_run.add_argument("--once", action="store_true", help="Process one batch and exit")
    p_run.add_argument("--story", help="Only process this specific story (e.g. US-162)")
    p_run.add_argument("--dry-run", action="store_true", help="Show what would happen")

    # status
    sub.add_parser("status", help="Show current status")

    # retry
    p_retry = sub.add_parser("retry", help="Reset a failed story")
    p_retry.add_argument("us_id", help="Story ID (e.g. US-162)")

    # logs
    p_logs = sub.add_parser("logs", help="Show logs for a story")
    p_logs.add_argument("us_id", help="Story ID (e.g. US-162)")

    args = parser.parse_args()

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "retry":
        return cmd_retry(args)
    elif args.command == "logs":
        return cmd_logs(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
