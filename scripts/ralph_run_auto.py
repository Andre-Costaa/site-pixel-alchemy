#!/usr/bin/env python3
"""
Run ralph-tui with auto-close sidecar in one command.
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
from pathlib import Path


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run ralph-tui with automatic PRD done-mark sidecar."
    )
    parser.add_argument("--prd", default="prd.json", help="Path to PRD JSON.")
    parser.add_argument("--parallel", type=int, default=1, help="Ralph parallel workers.")
    parser.add_argument("--force", action="store_true", help="Forward --force to ralph-tui.")
    parser.add_argument("--state-dir", default=".ralph-tui", help="Ralph state directory.")
    parser.add_argument("--interval-seconds", type=int, default=20, help="Autoclose poll interval.")
    parser.add_argument("--retry-seconds", type=int, default=300, help="Autoclose retry seconds.")
    parser.add_argument(
        "--no-require-origin-main",
        action="store_true",
        help="Allow sidecar to skip origin/main requirement.",
    )
    parser.add_argument("--autoclose-quiet", action="store_true", help="Reduce sidecar logs.")
    return parser.parse_known_args()


def terminate_process(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main() -> int:
    args, passthrough = parse_args()
    project_root = Path.cwd()
    sidecar_script = project_root / "scripts" / "ralph_autoclose.py"
    if not sidecar_script.exists():
        print(f"Missing sidecar script: {sidecar_script}", file=sys.stderr)
        return 1

    sidecar_cmd = [
        sys.executable,
        str(sidecar_script),
        "--prd",
        args.prd,
        "--state-dir",
        args.state_dir,
        "--interval-seconds",
        str(args.interval_seconds),
        "--retry-seconds",
        str(args.retry_seconds),
    ]
    if args.no_require_origin_main:
        sidecar_cmd.append("--no-require-origin-main")
    if args.autoclose_quiet:
        sidecar_cmd.append("--quiet")

    ralph_cmd = [
        "ralph-tui",
        "run",
        "--prd",
        args.prd,
        "--parallel",
        str(args.parallel),
    ]
    if args.force:
        ralph_cmd.append("--force")
    if passthrough:
        ralph_cmd.extend(passthrough)

    print("[ralph_run_auto] starting autoclose sidecar...", flush=True)
    sidecar_proc = subprocess.Popen(sidecar_cmd, cwd=str(project_root), text=True)
    ralph_proc: subprocess.Popen[str] | None = None

    def forward_signal(sig: int, _frame: object) -> None:
        if ralph_proc is not None and ralph_proc.poll() is None:
            ralph_proc.send_signal(sig)

    signal.signal(signal.SIGINT, forward_signal)
    signal.signal(signal.SIGTERM, forward_signal)

    try:
        print(f"[ralph_run_auto] running: {' '.join(ralph_cmd)}", flush=True)
        ralph_proc = subprocess.Popen(ralph_cmd, cwd=str(project_root), text=True)
        return ralph_proc.wait()
    finally:
        print("[ralph_run_auto] stopping autoclose sidecar...", flush=True)
        terminate_process(sidecar_proc)


if __name__ == "__main__":
    raise SystemExit(main())
