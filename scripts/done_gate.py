#!/usr/bin/env python3
"""
Done gate validator for PRD user stories.

This script enforces objective completion checks before marking `passes=true`.
It validates:
1) Site artifact and minimum content checks
2) Git commit existence
3) Remote push presence on origin/main (optional)
4) Notion evidence for stories that require Notion update
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


SITE_RE = re.compile(r"site-demo/([^'/\s]+)")
INFO_RE = re.compile(r"^Informa..es(?: da cl.nica)?:\s*(.+)$", re.IGNORECASE)
PHONE_RE = re.compile(r"^Telefone:\s*(.+)$", re.IGNORECASE)
US_RE = re.compile(r"^US-\d{3}$")


def normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value)
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    ascii_text = re.sub(r"\s+", " ", ascii_text).strip()
    return ascii_text


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def load_prd(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("userStories"), list):
        raise ValueError("Invalid prd.json shape")
    return data


def extract_story(prd: dict[str, Any], us_id: str) -> dict[str, Any] | None:
    for story in prd["userStories"]:
        if isinstance(story, dict) and story.get("id") == us_id:
            return story
    return None


def extract_slug(criteria: list[str]) -> str | None:
    for item in criteria:
        if not isinstance(item, str):
            continue
        m = SITE_RE.search(item)
        if m:
            return m.group(1)
    return None


def extract_address(criteria: list[str]) -> str | None:
    for item in criteria:
        if not isinstance(item, str):
            continue
        m = INFO_RE.match(item)
        if m:
            return m.group(1).strip()
    return None


def extract_phone(criteria: list[str]) -> str | None:
    for item in criteria:
        if not isinstance(item, str):
            continue
        m = PHONE_RE.match(item)
        if m:
            return m.group(1).strip()
    return None


def requires_notion(criteria: list[str]) -> bool:
    return any(
        isinstance(item, str) and "Atualizar Notion" in item for item in criteria
    )


def check_site(story: dict[str, Any], cwd: Path) -> list[dict[str, str | bool]]:
    results: list[dict[str, str | bool]] = []
    criteria = story.get("acceptanceCriteria") or []
    if not isinstance(criteria, list):
        criteria = []

    slug = extract_slug(criteria)
    if not slug:
        results.append(
            {
                "name": "site.slug",
                "passed": False,
                "detail": "Could not extract slug from acceptanceCriteria",
            }
        )
        return results

    site_file = cwd / "site-demo" / slug / "index.html"
    if not site_file.exists():
        results.append(
            {
                "name": "site.file",
                "passed": False,
                "detail": f"Missing file: {site_file}",
            }
        )
        return results

    results.append(
        {"name": "site.file", "passed": True, "detail": f"Found {site_file}"}
    )

    html_raw = site_file.read_text(encoding="utf-8", errors="ignore")
    html = normalize_text(html_raw)

    section_checks = [
        ("site.section.hero", "hero" in html),
        (
            "site.section.problem_solution",
            any(token in html for token in ["problema", "problem", "desafio"])
            and any(token in html for token in ["solucao", "solution", "solu"]),
        ),
        ("site.section.services", any(token in html for token in ["servicos", "services", "servic"])),
        ("site.section.testimonials", any(token in html for token in ["depoimentos", "testimonial"])),
        (
            "site.section.differentials",
            any(token in html for token in ["diferenciais", "differential", "features"]),
        ),
        ("site.section.contact", any(token in html for token in ["contato", "contact"])),
        ("site.section.footer", "<footer" in html_raw.lower()),
        ("site.form", "<form" in html_raw.lower()),
    ]
    for name, ok in section_checks:
        results.append(
            {
                "name": name,
                "passed": bool(ok),
                "detail": "ok" if ok else "Missing section/content marker",
            }
        )

    phone = extract_phone(criteria)
    if phone:
        phone_ok = digits_only(phone) in digits_only(html_raw)
        results.append(
            {
                "name": "site.phone",
                "passed": phone_ok,
                "detail": phone if phone_ok else f"Phone not found: {phone}",
            }
        )

    address = extract_address(criteria)
    if address:
        address_norm = normalize_text(address)
        # Use first two significant tokens for resilient match.
        tokens = [t for t in address_norm.split(" ") if len(t) >= 4]
        required_tokens = tokens[:2]
        address_ok = bool(required_tokens) and all(tok in html for tok in required_tokens)
        results.append(
            {
                "name": "site.address",
                "passed": address_ok,
                "detail": "ok" if address_ok else f"Address tokens missing: {required_tokens}",
            }
        )

    return results


def check_git(us_id: str, cwd: Path, require_origin_main: bool) -> list[dict[str, str | bool]]:
    results: list[dict[str, str | bool]] = []

    code, out, _ = run_git(["log", "--grep", us_id, "--format=%H", "-n", "1"], cwd)
    has_local = code == 0 and bool(out.strip())
    commit = out.splitlines()[0].strip() if has_local else ""
    results.append(
        {
            "name": "git.commit.local",
            "passed": has_local,
            "detail": commit if has_local else f"No local commit found for {us_id}",
        }
    )

    if not require_origin_main:
        return results

    if not has_local:
        results.append(
            {
                "name": "git.commit.origin_main",
                "passed": False,
                "detail": "Cannot verify remote without local commit",
            }
        )
        return results

    code, branches, _ = run_git(["branch", "-r", "--contains", commit], cwd)
    contains_main = code == 0 and any(
        line.strip().endswith("origin/main") for line in branches.splitlines()
    )
    results.append(
        {
            "name": "git.commit.origin_main",
            "passed": contains_main,
            "detail": "Commit reachable from origin/main"
            if contains_main
            else "Commit not found on origin/main (push pending)",
        }
    )
    return results


def check_notion(us_id: str, story: dict[str, Any], cwd: Path) -> list[dict[str, str | bool]]:
    results: list[dict[str, str | bool]] = []
    criteria = story.get("acceptanceCriteria") or []
    if not isinstance(criteria, list) or not requires_notion(criteria):
        results.append(
            {
                "name": "notion.required",
                "passed": True,
                "detail": "Not required by this story",
            }
        )
        return results

    logs = sorted((cwd / ".ralph-tui" / "iterations").glob(f"*_{us_id}.log"))
    if not logs:
        results.append(
            {
                "name": "notion.logs",
                "passed": False,
                "detail": f"No iteration log found for {us_id}",
            }
        )
        return results

    content = "\n".join(
        log.read_text(encoding="utf-8", errors="ignore") for log in logs
    ).lower()
    update_evidence = any(
        token in content
        for token in [
            "mcp__plugin_notion_notion__notion-update-page",
            "mcp__plugin_notion_notion__notion-create-pages",
            "build_site_ready_update",
        ]
    )
    status_evidence = "mensagem pronta" in content
    manual_fallback = "cannot directly call the mcp tools" in content
    api_error = "api error" in content and "notion" in content
    api_error_blocking = api_error and not update_evidence

    results.append(
        {
            "name": "notion.update_evidence",
            "passed": update_evidence,
            "detail": "Found Notion tool/update evidence"
            if update_evidence
            else "No Notion update/create call found in logs",
        }
    )
    results.append(
        {
            "name": "notion.status_mensagem_pronta",
            "passed": status_evidence,
            "detail": "Found 'Mensagem Pronta' evidence"
            if status_evidence
            else "Missing 'Mensagem Pronta' evidence",
        }
    )
    results.append(
        {
            "name": "notion.no_manual_fallback",
            "passed": not manual_fallback,
            "detail": "No manual fallback detected"
            if not manual_fallback
            else "Manual fallback detected (MCP not executed)",
        }
    )
    results.append(
        {
            "name": "notion.no_api_error",
            "passed": not api_error_blocking,
            "detail": "No blocking Notion API error in logs"
            if not api_error_blocking
            else "Notion API error detected with no successful update evidence",
        }
    )
    return results


def evaluate_story(
    prd: dict[str, Any],
    us_id: str,
    cwd: Path,
    require_origin_main: bool = True,
) -> dict[str, Any]:
    story = extract_story(prd, us_id)
    if story is None:
        return {
            "us_id": us_id,
            "passed": False,
            "checks": [
                {
                    "name": "story.exists",
                    "passed": False,
                    "detail": f"Story {us_id} not found in PRD",
                }
            ],
        }

    checks: list[dict[str, Any]] = []
    checks.extend(check_site(story, cwd))
    checks.extend(check_git(us_id, cwd, require_origin_main=require_origin_main))
    checks.extend(check_notion(us_id, story, cwd))

    passed = all(bool(check["passed"]) for check in checks)
    return {"us_id": us_id, "passed": passed, "checks": checks}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate objective done-gate checks for one or more user stories."
    )
    parser.add_argument(
        "--us-id",
        action="append",
        required=True,
        help="User story id (repeatable), e.g. --us-id US-090 --us-id US-091",
    )
    parser.add_argument(
        "--prd",
        default="prd.json",
        help="Path to prd.json (default: prd.json)",
    )
    parser.add_argument(
        "--no-require-origin-main",
        action="store_true",
        help="Do not require commit to be present on origin/main",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()
    prd_path = (cwd / args.prd).resolve()
    prd = load_prd(prd_path)

    invalid_ids = [us for us in args.us_id if not US_RE.match(us)]
    if invalid_ids:
        print(f"Invalid US IDs: {invalid_ids}", file=sys.stderr)
        return 2

    results = [
        evaluate_story(
            prd=prd,
            us_id=us_id,
            cwd=cwd,
            require_origin_main=not args.no_require_origin_main,
        )
        for us_id in args.us_id
    ]
    overall_pass = all(item["passed"] for item in results)

    if args.json:
        print(json.dumps({"passed": overall_pass, "results": results}, indent=2))
        return 0 if overall_pass else 1

    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"[{status}] {item['us_id']}")
        for check in item["checks"]:
            check_status = "ok" if check["passed"] else "x"
            print(f"  - [{check_status}] {check['name']}: {check['detail']}")
        print()

    print("DONE GATE: PASS" if overall_pass else "DONE GATE: FAIL")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
