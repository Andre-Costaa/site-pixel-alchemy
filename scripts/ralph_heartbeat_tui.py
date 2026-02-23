#!/usr/bin/env python3
"""
Terminal monitor for active ralph-tui sessions.

Features:
- Heartbeat every 5 minutes (configurable)
- Modern TUI with Rich
- JSONL heartbeat log file
- Health signals + recommendation (CONTINUE / STOP)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
ERROR_RE = re.compile(
    r"\berror\b|\bfailed\b|\bexception\b|\btraceback\b|\bfatal\b|permission denied|rate limit|\b429\b|\btimeout\b|\binterrupted\b",
    flags=re.IGNORECASE,
)


@dataclass
class MonitorSnapshot:
    session_id: str
    status: str
    agent_plugin: str
    tracker_plugin: str
    started_at: datetime | None
    updated_at: datetime | None
    current_iteration: int | None
    max_iterations: int | None
    total_tasks: int | None
    tasks_completed: int | None
    active_task_ids: list[str]
    is_paused: bool | None
    lock_pid: int | None
    lock_pid_alive: bool | None
    lock_is_current: bool
    latest_log: Path | None
    latest_log_mtime: datetime | None
    latest_log_is_current_session: bool
    latest_log_age_minutes: float | None
    latest_log_lines: list[str]
    error_hits: int
    inactivity_minutes: float | None
    health: str
    should_stop: bool
    recommendation: str
    reasons: list[str]


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def local_time_str(value: datetime | None) -> str:
    if not value:
        return "-"
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def duration_str(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, sec = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m {sec:02d}s"
    if minutes > 0:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"


def task_progress_bar(completed: int, total: int, width: int = 24) -> str:
    if total <= 0:
        total = 1
    ratio = min(1.0, max(0.0, completed / total))
    filled = int(width * ratio)
    return f"[{'█' * filled}{'·' * (width - filled)}] {completed}/{total} ({ratio*100:.1f}%)"


def bool_label(value: bool | None) -> str:
    if value is None:
        return "-"
    return "yes" if value else "no"


class RalphHeartbeatTUI:
    def __init__(
        self,
        state_dir: Path,
        heartbeat_seconds: int,
        refresh_seconds: float,
        stale_warning_minutes: float,
        stale_critical_minutes: float,
        error_threshold: int,
        log_file: Path,
        history_size: int,
    ) -> None:
        self.state_dir = state_dir
        self.heartbeat_seconds = heartbeat_seconds
        self.refresh_seconds = refresh_seconds
        self.stale_warning_minutes = stale_warning_minutes
        self.stale_critical_minutes = stale_critical_minutes
        self.error_threshold = error_threshold
        self.log_file = log_file
        self.history = deque(maxlen=history_size)
        self.last_heartbeat_at = 0.0
        self.console = Console()
        self.cached_log_path: Path | None = None
        self.cached_log_mtime: float | None = None
        self.cached_tail_lines: list[str] = []
        self.cached_error_hits: int = 0
        self._load_existing_history()

    def _load_existing_history(self) -> None:
        if not self.log_file.exists():
            return
        try:
            content = self._tail_text(self.log_file, max_bytes=24_000)
        except OSError:
            return
        for line in content.splitlines():
            parsed = self._parse_history_entry(line)
            if parsed:
                self.history.append(parsed)

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def _load_json(self, path: Path) -> dict[str, Any]:
        raw = self._read_text(path)
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return json.loads(CONTROL_RE.sub("", raw))
            except json.JSONDecodeError:
                return {}

    def _load_session_guess(self, path: Path) -> dict[str, Any]:
        parsed = self._load_json(path)
        if parsed:
            return parsed

        raw = self._read_text(path)
        if not raw:
            return {}
        clean = CONTROL_RE.sub("", raw)

        fields: dict[str, Any] = {}
        patterns = {
            "sessionId": r'"sessionId"\s*:\s*"([^"]+)"',
            "status": r'"status"\s*:\s*"([^"]+)"',
            "startedAt": r'"startedAt"\s*:\s*"([^"]+)"',
            "updatedAt": r'"updatedAt"\s*:\s*"([^"]+)"',
            "agentPlugin": r'"agentPlugin"\s*:\s*"([^"]+)"',
            "currentIteration": r'"currentIteration"\s*:\s*(\d+)',
            "maxIterations": r'"maxIterations"\s*:\s*(\d+)',
            "tasksCompleted": r'"tasksCompleted"\s*:\s*(\d+)',
            "totalTasks": r'"totalTasks"\s*:\s*(\d+)',
            "isPaused": r'"isPaused"\s*:\s*(true|false)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, clean, flags=re.DOTALL)
            if not match:
                continue
            value = match.group(1)
            if key in {"currentIteration", "maxIterations", "tasksCompleted", "totalTasks"}:
                fields[key] = int(value)
            elif key == "isPaused":
                fields[key] = value == "true"
            else:
                fields[key] = value

        active_match = re.search(r'"activeTaskIds"\s*:\s*\[(.*?)\]', clean, flags=re.DOTALL)
        if active_match:
            fields["activeTaskIds"] = re.findall(r'"([^"]+)"', active_match.group(1))

        tracker_match = re.search(r'"trackerState"\s*:\s*{', clean, flags=re.DOTALL)
        if tracker_match:
            sample = clean[tracker_match.start() : tracker_match.start() + 1500]
            plugin_match = re.search(r'"plugin"\s*:\s*"([^"]+)"', sample, flags=re.DOTALL)
            if plugin_match:
                fields["trackerPlugin"] = plugin_match.group(1)

        return fields

    def _tail_text(self, path: Path, max_bytes: int) -> str:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            if size <= 0:
                return ""
            offset = max(0, size - max_bytes)
            handle.seek(offset)
            data = handle.read()
        return data.decode("utf-8", errors="ignore")

    def _clean_line(self, line: str) -> str:
        line = ANSI_RE.sub("", line)
        line = CONTROL_RE.sub("", line)
        return line.strip()

    def _latest_log(self, session_id: str) -> tuple[Path | None, datetime | None, bool]:
        iterations_dir = self.state_dir / "iterations"
        if not iterations_dir.exists():
            return None, None, False
        logs = list(iterations_dir.glob("*.log"))
        if not logs:
            return None, None, False

        session_prefix = session_id.split("-")[0].strip() if session_id and session_id != "-" else ""
        if session_prefix:
            expected = f"{session_prefix}_"
            matching = [item for item in logs if item.name.startswith(expected)]
            if not matching:
                return None, None, False
            latest = max(matching, key=lambda item: item.stat().st_mtime)
            is_current = True
        else:
            latest = max(logs, key=lambda item: item.stat().st_mtime)
            is_current = False

        mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
        return latest, mtime, is_current

    def _analyze_latest_log(self, latest_log: Path | None, latest_mtime: datetime | None) -> tuple[list[str], int]:
        if latest_log is None or latest_mtime is None:
            return [], 0

        mtime_epoch = latest_mtime.timestamp()
        if self.cached_log_path == latest_log and self.cached_log_mtime == mtime_epoch:
            return self.cached_tail_lines, self.cached_error_hits

        try:
            content = self._tail_text(latest_log, max_bytes=80_000)
        except OSError:
            return [], 0

        lines: list[str] = []
        for raw in content.splitlines():
            clean = self._clean_line(raw)
            if clean:
                lines.append(clean)

        if "--- SUBAGENT TRACE ---" in lines:
            trace_index = lines.index("--- SUBAGENT TRACE ---")
            lines = lines[:trace_index]

        error_hits = sum(1 for line in lines[-150:] if ERROR_RE.search(line))
        tail_lines = lines[-12:]

        self.cached_log_path = latest_log
        self.cached_log_mtime = mtime_epoch
        self.cached_tail_lines = tail_lines
        self.cached_error_hits = error_hits
        return tail_lines, error_hits

    def _pid_alive(self, pid: int | None) -> bool | None:
        if pid is None:
            return None
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    def _health_decision(
        self,
        status: str,
        is_paused: bool | None,
        pid_alive: bool | None,
        lock_is_current: bool,
        inactivity_minutes: float | None,
        error_hits: int,
    ) -> tuple[str, bool, str, list[str]]:
        normalized = status.lower().strip()
        reasons: list[str] = []
        health = "ok"
        should_stop = False
        transitional = {"pausing", "stopping", "draining", "completing", "finalizing"}

        if normalized in {"completed", "done", "finished", "stopped"}:
            return "done", True, "STOP", ["Sessão já finalizada."]

        if normalized in {"error", "failed", "crashed"}:
            health = "critical"
            should_stop = True
            reasons.append(f"Status da sessão: {status}.")

        if normalized in transitional:
            if health == "ok":
                health = "warn"
            reasons.append("Sessão em transição de pausa/finalização.")

        if is_paused is True:
            if health == "ok":
                health = "warn"
            reasons.append("Sessão em pausa.")

        if normalized == "running" and lock_is_current and pid_alive is False:
            health = "critical"
            should_stop = True
            reasons.append("PID do lock não está ativo.")
        elif normalized == "running" and not lock_is_current and pid_alive is False:
            if health == "ok":
                health = "warn"
            reasons.append("Lock de sessão antiga detectado; PID ignorado.")

        if normalized == "running" and inactivity_minutes is not None:
            if inactivity_minutes >= self.stale_critical_minutes:
                health = "critical"
                should_stop = True
                reasons.append(f"Sem atividade há {inactivity_minutes:.1f} min.")
            elif inactivity_minutes >= self.stale_warning_minutes:
                if health == "ok":
                    health = "warn"
                reasons.append(f"Atividade lenta ({inactivity_minutes:.1f} min sem update).")

        if error_hits >= self.error_threshold:
            health = "critical"
            should_stop = True
            reasons.append(f"{error_hits} sinais de erro recentes no log.")
        elif error_hits > 0:
            if health == "ok":
                health = "warn"
            reasons.append(f"{error_hits} alertas no log recente.")

        if not reasons:
            reasons.append("Pipeline ativo e saudável.")

        recommendation = "STOP" if should_stop else "CONTINUE"
        return health, should_stop, recommendation, reasons

    def collect_snapshot(self) -> MonitorSnapshot:
        meta = self._load_json(self.state_dir / "session-meta.json")
        lock = self._load_json(self.state_dir / "ralph.lock")
        session = self._load_session_guess(self.state_dir / "session.json")

        meta_updated_at = parse_datetime(meta.get("updatedAt"))
        session_updated_at = parse_datetime(session.get("updatedAt"))
        prefer_session = False
        if session and session_updated_at and (not meta_updated_at or session_updated_at >= meta_updated_at):
            prefer_session = True
        elif session and not meta_updated_at:
            prefer_session = True

        def choose_value(meta_value: Any, session_value: Any) -> Any:
            if prefer_session:
                return session_value if session_value not in (None, "", []) else meta_value
            return meta_value if meta_value not in (None, "", []) else session_value

        selected_status = choose_value(meta.get("status"), session.get("status"))
        status = str(selected_status or "unknown")

        selected_session_id = choose_value(meta.get("id"), session.get("sessionId"))
        session_id = str(selected_session_id or lock.get("sessionId") or "-")

        meta_started_at = parse_datetime(meta.get("startedAt"))
        session_started_at = parse_datetime(session.get("startedAt"))
        candidates_started = [item for item in [meta_started_at, session_started_at, parse_datetime(lock.get("acquiredAt"))] if item]
        started_at = min(candidates_started) if candidates_started else None
        candidates_updated = [item for item in [meta_updated_at, session_updated_at] if item]
        updated_at = max(candidates_updated) if candidates_updated else None

        current_iteration = choose_value(meta.get("currentIteration"), session.get("currentIteration"))
        if not isinstance(current_iteration, int):
            current_iteration = None
        max_iterations = choose_value(meta.get("maxIterations"), session.get("maxIterations"))
        if not isinstance(max_iterations, int):
            max_iterations = None
        total_tasks = choose_value(meta.get("totalTasks"), session.get("totalTasks"))
        if not isinstance(total_tasks, int):
            total_tasks = None
        tasks_completed = choose_value(meta.get("tasksCompleted"), session.get("tasksCompleted"))
        if not isinstance(tasks_completed, int):
            tasks_completed = None

        active_task_ids_raw = session.get("activeTaskIds")
        if not isinstance(active_task_ids_raw, list):
            active_task_ids_raw = []
        active_task_ids = [str(task_id) for task_id in active_task_ids_raw]

        is_paused = session.get("isPaused")
        if not isinstance(is_paused, bool):
            is_paused = None

        lock_pid = lock.get("pid")
        if isinstance(lock_pid, str) and lock_pid.isdigit():
            lock_pid = int(lock_pid)
        if not isinstance(lock_pid, int):
            lock_pid = None
        lock_pid_alive = self._pid_alive(lock_pid)

        selected_agent = choose_value(meta.get("agentPlugin"), session.get("agentPlugin"))
        selected_tracker = choose_value(meta.get("trackerPlugin"), session.get("trackerPlugin"))
        agent_plugin = str(selected_agent or "-")
        tracker_plugin = str(selected_tracker or "-")

        lock_session_id = str(lock.get("sessionId") or "")
        preferred_session_id = str(session.get("sessionId") or "") if prefer_session else str(meta.get("id") or "")
        if not preferred_session_id:
            preferred_session_id = session_id if session_id != "-" else ""
        lock_is_current = bool(lock_session_id and preferred_session_id and lock_session_id == preferred_session_id)

        latest_log, latest_log_mtime, latest_log_is_current_session = self._latest_log(session_id=session_id)
        latest_log_lines, error_hits = self._analyze_latest_log(latest_log, latest_log_mtime)
        latest_log_age_minutes: float | None = None
        if latest_log_mtime is not None:
            latest_log_age_minutes = max(
                0.0, (datetime.now(tz=timezone.utc) - latest_log_mtime).total_seconds() / 60.0
            )

        activity_marks = [dt for dt in [updated_at, latest_log_mtime] if dt is not None]
        inactivity_minutes: float | None = None
        if activity_marks:
            last_activity = max(activity_marks)
            inactivity_minutes = max(0.0, (datetime.now(tz=timezone.utc) - last_activity).total_seconds() / 60.0)

        health, should_stop, recommendation, reasons = self._health_decision(
            status=status,
            is_paused=is_paused,
            pid_alive=lock_pid_alive,
            lock_is_current=lock_is_current,
            inactivity_minutes=inactivity_minutes,
            error_hits=error_hits,
        )

        return MonitorSnapshot(
            session_id=session_id,
            status=status,
            agent_plugin=agent_plugin,
            tracker_plugin=tracker_plugin,
            started_at=started_at,
            updated_at=updated_at,
            current_iteration=current_iteration,
            max_iterations=max_iterations,
            total_tasks=total_tasks,
            tasks_completed=tasks_completed,
            active_task_ids=active_task_ids,
            is_paused=is_paused,
            lock_pid=lock_pid,
            lock_pid_alive=lock_pid_alive,
            lock_is_current=lock_is_current,
            latest_log=latest_log,
            latest_log_mtime=latest_log_mtime,
            latest_log_is_current_session=latest_log_is_current_session,
            latest_log_age_minutes=latest_log_age_minutes,
            latest_log_lines=latest_log_lines,
            error_hits=error_hits,
            inactivity_minutes=inactivity_minutes,
            health=health,
            should_stop=should_stop,
            recommendation=recommendation,
            reasons=reasons,
        )

    def _build_heartbeat(self, snapshot: MonitorSnapshot) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "sessionId": snapshot.session_id,
            "status": snapshot.status,
            "activeTaskIds": snapshot.active_task_ids,
            "isPaused": snapshot.is_paused,
            "lockPid": snapshot.lock_pid,
            "lockPidAlive": snapshot.lock_pid_alive,
            "workersActive": len(snapshot.active_task_ids),
            "inactivityMinutes": snapshot.inactivity_minutes,
            "errorHits": snapshot.error_hits,
            "recommendation": snapshot.recommendation,
            "shouldStop": snapshot.should_stop,
            "reasons": snapshot.reasons,
            "latestLog": str(snapshot.latest_log) if snapshot.latest_log else None,
            "latestLogCurrentSession": snapshot.latest_log_is_current_session,
        }

    def _heartbeat_line(self, payload: dict[str, Any]) -> str:
        timestamp = parse_datetime(payload.get("timestamp"))
        clock = timestamp.astimezone().strftime("%H:%M:%S") if timestamp else "--:--:--"
        status = str(payload.get("status") or "unknown")
        recommendation = str(payload.get("recommendation") or "CONTINUE")
        stop_flag = "SIM" if payload.get("shouldStop") else "NAO"
        idle = payload.get("inactivityMinutes")
        idle_text = f"{float(idle):.1f}m" if isinstance(idle, (int, float)) else "-"
        return f"{clock} | {status:<9} | {recommendation:<8} | PARAR={stop_flag} | idle={idle_text}"

    def _parse_history_entry(self, line: str) -> str | None:
        line = line.strip()
        if not line:
            return None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        return self._heartbeat_line(payload)

    def maybe_write_heartbeat(self, snapshot: MonitorSnapshot) -> None:
        now = time.time()
        if self.last_heartbeat_at > 0 and (now - self.last_heartbeat_at) < self.heartbeat_seconds:
            return

        payload = self._build_heartbeat(snapshot)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.history.append(self._heartbeat_line(payload))
        self.last_heartbeat_at = now

    def _status_badge(self, status: str) -> Text:
        normalized = status.lower().strip()
        if normalized == "running":
            return Text(f" {status.upper()} ", style="bold black on green")
        if normalized == "paused":
            return Text(f" {status.upper()} ", style="bold black on yellow")
        if normalized in {"completed", "done", "finished", "stopped"}:
            return Text(f" {status.upper()} ", style="bold black on cyan")
        if normalized in {"error", "failed", "crashed"}:
            return Text(f" {status.upper()} ", style="bold white on red")
        return Text(f" {status.upper()} ", style="bold black on white")

    def _health_badge(self, health: str) -> Text:
        if health == "ok":
            return Text(" HEALTHY ", style="bold black on green")
        if health == "warn":
            return Text(" ATTENTION ", style="bold black on yellow")
        if health == "critical":
            return Text(" CRITICAL ", style="bold white on red")
        if health == "done":
            return Text(" FINISHED ", style="bold black on cyan")
        return Text(" UNKNOWN ", style="bold black on white")

    def _build_header(self, snapshot: MonitorSnapshot) -> Panel:
        line1 = Text("RALPH HEARTBEAT MONITOR", style="bold magenta")
        line2 = Text.assemble(
            ("Session ", "dim"),
            (snapshot.session_id, "bold"),
            ("  |  ", "dim"),
            ("Heartbeat ", "dim"),
            (f"{self.heartbeat_seconds}s", "bold cyan"),
            ("  |  ", "dim"),
            ("Refresh ", "dim"),
            (f"{self.refresh_seconds:.1f}s", "bold cyan"),
        )
        return Panel(Align.center(Group(line1, line2)), border_style="magenta")

    def _build_status(self, snapshot: MonitorSnapshot) -> Panel:
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold cyan", no_wrap=True)
        table.add_column(style="white")

        now = datetime.now(tz=timezone.utc)
        uptime_seconds = (now - snapshot.started_at).total_seconds() if snapshot.started_at else None

        if snapshot.max_iterations is not None and snapshot.current_iteration is not None:
            iteration_text = f"{snapshot.current_iteration}/{snapshot.max_iterations}"
        elif snapshot.current_iteration is not None:
            iteration_text = str(snapshot.current_iteration)
        else:
            iteration_text = "-"

        total = snapshot.total_tasks or 0
        done = snapshot.tasks_completed or 0
        if total < done:
            total = done

        table.add_row("Status", self._status_badge(snapshot.status))
        table.add_row("Health", self._health_badge(snapshot.health))
        table.add_row("Agent", snapshot.agent_plugin)
        table.add_row("Tracker", snapshot.tracker_plugin)
        table.add_row("Iteration", iteration_text)
        table.add_row("Tasks", task_progress_bar(done, total))
        table.add_row("Active", ", ".join(snapshot.active_task_ids) if snapshot.active_task_ids else "-")
        table.add_row("Workers", f"{len(snapshot.active_task_ids)} ativos")
        table.add_row("Paused", bool_label(snapshot.is_paused))
        table.add_row(
            "Lock PID",
            f"{snapshot.lock_pid or '-'} ({bool_label(snapshot.lock_pid_alive)})"
            + ("" if snapshot.lock_is_current else " (stale)"),
        )
        table.add_row("Started", local_time_str(snapshot.started_at))
        table.add_row("Updated", local_time_str(snapshot.updated_at))
        table.add_row("Uptime", duration_str(uptime_seconds))
        if snapshot.inactivity_minutes is None:
            table.add_row("Idle", "-")
        else:
            table.add_row("Idle", f"{snapshot.inactivity_minutes:.1f} min")
        table.add_row("Log File", snapshot.latest_log.name if snapshot.latest_log else "-")
        if snapshot.latest_log_age_minutes is None:
            table.add_row("Log Age", "-")
        else:
            table.add_row("Log Age", f"{snapshot.latest_log_age_minutes:.1f} min")

        return Panel(table, title="Session Status", border_style="cyan")

    def _build_decision(self, snapshot: MonitorSnapshot) -> Panel:
        color = "red" if snapshot.should_stop else "green"
        stop_word = "SIM" if snapshot.should_stop else "NAO"
        header = Text.assemble(
            ("Recommendation: ", "bold white"),
            (snapshot.recommendation, f"bold {color}"),
            ("   |   Parar agora? ", "bold white"),
            (stop_word, f"bold {color}"),
        )
        reason_lines = [Text(f"• {reason}") for reason in snapshot.reasons]
        return Panel(Group(header, *reason_lines), title="Decision", border_style=color)

    def _build_logs(self, snapshot: MonitorSnapshot) -> Panel:
        if snapshot.latest_log is None:
            return Panel(
                Text("Sem log da sessão atual ainda."),
                title="Recent Log Tail",
                border_style="yellow",
            )

        if snapshot.latest_log and not snapshot.latest_log_is_current_session:
            return Panel(
                Text("Log mais recente disponível é de outra sessão (stale)."),
                title="Recent Log Tail",
                border_style="yellow",
            )

        if (
            snapshot.status.lower().strip() == "running"
            and len(snapshot.active_task_ids) > 0
            and snapshot.latest_log_age_minutes is not None
            and snapshot.latest_log_age_minutes >= 5.0
        ):
            workers = ", ".join(snapshot.active_task_ids)
            notice = Group(
                Text(
                    f"Último log da sessão atual tem {snapshot.latest_log_age_minutes:.1f} min.",
                    style="yellow",
                ),
                Text(f"Workers ativos agora: {len(snapshot.active_task_ids)} ({workers})", style="cyan"),
                Text("Aguardando novo arquivo de iteração em .ralph-tui/iterations/.", style="white"),
            )
            return Panel(notice, title="Recent Log Tail", border_style="yellow")

        if not snapshot.latest_log_lines:
            return Panel(Text("Sem linhas recentes de log."), title="Recent Log Tail", border_style="yellow")
        lines: list[Text] = []
        for line in snapshot.latest_log_lines[-10:]:
            style = "white"
            if ERROR_RE.search(line):
                style = "bold red"
            elif "[Bash]" in line or "[Read]" in line or "[Write]" in line:
                style = "cyan"
            lines.append(Text(line[:180], style=style))
        return Panel(Group(*lines), title="Recent Log Tail", border_style="yellow")

    def _build_heartbeat_panel(self) -> Panel:
        if not self.history:
            return Panel(Text("Nenhum heartbeat registrado ainda."), title="Heartbeats", border_style="green")
        items = [Text(line) for line in list(self.history)[-8:]]
        return Panel(Group(*items), title=f"Heartbeats ({self.log_file.name})", border_style="green")

    def _build_footer(self) -> Panel:
        remaining = max(0, int(self.heartbeat_seconds - (time.time() - self.last_heartbeat_at)))
        text = Text.assemble(
            ("CTRL+C para sair", "dim"),
            ("   |   ", "dim"),
            ("Próximo heartbeat em ", "dim"),
            (f"{remaining}s", "bold cyan"),
            ("   |   ", "dim"),
            ("log: ", "dim"),
            (str(self.log_file), "cyan"),
        )
        return Panel(Align.center(text), border_style="magenta")

    def build_layout(self, snapshot: MonitorSnapshot) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=3))
        layout["right"].split_column(
            Layout(name="decision", size=9),
            Layout(name="logs"),
            Layout(name="heartbeats", size=9),
        )

        layout["header"].update(self._build_header(snapshot))
        layout["left"].update(self._build_status(snapshot))
        layout["right"]["decision"].update(self._build_decision(snapshot))
        layout["right"]["logs"].update(self._build_logs(snapshot))
        layout["right"]["heartbeats"].update(self._build_heartbeat_panel())
        layout["footer"].update(self._build_footer())
        return layout

    def run_once(self) -> None:
        snapshot = self.collect_snapshot()
        self.maybe_write_heartbeat(snapshot)
        self.console.print(self.build_layout(snapshot))

    def run_live(self) -> None:
        try:
            with Live(self.build_layout(self.collect_snapshot()), screen=True, auto_refresh=False, console=self.console) as live:
                while True:
                    snapshot = self.collect_snapshot()
                    self.maybe_write_heartbeat(snapshot)
                    live.update(self.build_layout(snapshot), refresh=True)
                    time.sleep(self.refresh_seconds)
        except KeyboardInterrupt:
            self.console.print("\n[bold cyan]Monitor encerrado.[/bold cyan]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heartbeat monitor com TUI para sessão ativa do ralph-tui.")
    parser.add_argument("--state-dir", type=Path, default=Path(".ralph-tui"), help="Diretório de estado do ralph-tui.")
    parser.add_argument("--heartbeat-seconds", type=int, default=300, help="Intervalo de heartbeat em segundos.")
    parser.add_argument("--refresh-seconds", type=float, default=1.0, help="Refresh da UI em segundos.")
    parser.add_argument("--stale-warning-minutes", type=float, default=10.0, help="Minutos de inatividade para alerta.")
    parser.add_argument("--stale-critical-minutes", type=float, default=25.0, help="Minutos de inatividade para STOP.")
    parser.add_argument("--error-threshold", type=int, default=3, help="Quantidade de erros recentes para STOP.")
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Arquivo JSONL do heartbeat (default: <state-dir>/heartbeat/heartbeat.jsonl).",
    )
    parser.add_argument("--history-size", type=int, default=60, help="Qtd. de heartbeats na UI.")
    parser.add_argument("--once", action="store_true", help="Renderiza snapshot único e sai.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_dir = args.state_dir
    if not state_dir.exists():
        print(f"Diretório não encontrado: {state_dir}")
        return 2

    heartbeat_seconds = max(10, args.heartbeat_seconds)
    refresh_seconds = max(0.2, args.refresh_seconds)
    stale_warning = max(1.0, args.stale_warning_minutes)
    stale_critical = max(stale_warning + 1.0, args.stale_critical_minutes)
    error_threshold = max(1, args.error_threshold)
    history_size = max(10, args.history_size)
    log_file = args.log_file or (state_dir / "heartbeat" / "heartbeat.jsonl")

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    monitor = RalphHeartbeatTUI(
        state_dir=state_dir,
        heartbeat_seconds=heartbeat_seconds,
        refresh_seconds=refresh_seconds,
        stale_warning_minutes=stale_warning,
        stale_critical_minutes=stale_critical,
        error_threshold=error_threshold,
        log_file=log_file,
        history_size=history_size,
    )

    if args.once:
        monitor.run_once()
        return 0

    monitor.run_live()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
