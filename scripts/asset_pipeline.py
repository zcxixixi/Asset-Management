from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys

from advisor_contract import generate_fallback
from briefing_agent import generate_briefing
from extract_data import extract_data
from pipeline_state import REPO_ROOT, load_analysis_context, load_dashboard_payload, update_advisor_briefing
from telegram_bot import format_message, send_alert, send_broadcast

DATA_FILES = ["assets.xlsx", "src/data.json", "public/data.json"]
DEFAULT_TARGET_BRANCH = "main"
DEFAULT_REMOTE_NAME = "origin"
DEFAULT_COMMIT_PREFIX = "chore(data): sync portfolio data"


def load_pipeline_env() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def update_data(*, mock_date_str: str | None = None) -> dict:
    return extract_data(mock_date_str=mock_date_str)


def analyze_portfolio(*, time_of_day: str) -> dict:
    context = load_analysis_context()
    briefing = generate_briefing(
        holdings=context.get("holdings", []),
        news_context=context.get("news_context", []),
        global_context=context.get("global_context", []),
        time_of_day=time_of_day,
    )
    update_advisor_briefing(briefing)
    return briefing


def apply_fallback_briefing() -> dict:
    briefing = generate_fallback()
    update_advisor_briefing(briefing)
    return briefing


def send_briefing(*, time_of_day: str) -> None:
    payload = load_dashboard_payload()
    message = format_message(time_of_day, payload)
    asyncio.run(send_broadcast(message))


def _run_git(args: list[str], *, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=capture_output,
        check=False,
    )


def _has_non_data_changes() -> bool:
    result = _run_git(
        ["status", "--porcelain", "--", ".", ":(exclude)assets.xlsx", ":(exclude)src/data.json", ":(exclude)public/data.json"]
    )
    return bool(result.stdout.strip())


def prepare_publish_branch(
    *,
    target_branch: str = DEFAULT_TARGET_BRANCH,
    remote_name: str = DEFAULT_REMOTE_NAME,
) -> None:
    if _has_non_data_changes():
        raise RuntimeError("repository has local non-data changes; refusing publish")

    current_branch = _run_git(["branch", "--show-current"]).stdout.strip()
    if current_branch != target_branch:
        dirty = _run_git(["status", "--porcelain"]).stdout.strip()
        if dirty:
            raise RuntimeError(f"cannot switch from {current_branch} to {target_branch} with a dirty working tree")
        for args in (["checkout", target_branch], ["fetch", remote_name, target_branch], ["pull", "--rebase", remote_name, target_branch]):
            result = _run_git(args)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
        return

    for args in (["fetch", remote_name, target_branch], ["pull", "--rebase", remote_name, target_branch]):
        result = _run_git(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")


def publish_data(
    *,
    target_branch: str = DEFAULT_TARGET_BRANCH,
    remote_name: str = DEFAULT_REMOTE_NAME,
    commit_prefix: str = DEFAULT_COMMIT_PREFIX,
) -> bool:
    if _has_non_data_changes():
        raise RuntimeError("pipeline produced non-data changes; refusing publish")

    prepare_publish_branch(target_branch=target_branch, remote_name=remote_name)

    add_result = _run_git(["add", *DATA_FILES])
    if add_result.returncode != 0:
        raise RuntimeError(add_result.stderr.strip() or add_result.stdout.strip() or "git add failed")

    diff_result = _run_git(["diff", "--cached", "--quiet"], capture_output=False)
    if diff_result.returncode == 0:
        print("No data changes to publish.")
        return False
    if diff_result.returncode not in {0, 1}:
        raise RuntimeError("git diff --cached --quiet failed")

    timestamp = subprocess.run(["date", "+%Y-%m-%d %H:%M:%S %Z"], text=True, capture_output=True, check=False).stdout.strip()
    commit_result = _run_git(["commit", "-m", f"{commit_prefix} {timestamp}"])
    if commit_result.returncode != 0:
        raise RuntimeError(commit_result.stderr.strip() or commit_result.stdout.strip() or "git commit failed")

    push_result = _run_git(["push", remote_name, target_branch])
    if push_result.returncode != 0:
        raise RuntimeError(push_result.stderr.strip() or push_result.stdout.strip() or "git push failed")

    print(f"Published data files to {remote_name}/{target_branch}.")
    return True


def _notify_failure(stage: str, exc: Exception, *, alert_on_failure: bool) -> None:
    print(f"{stage} failed: {exc}", file=sys.stderr)
    if alert_on_failure:
        asyncio.run(send_alert(str(exc), stage))


def run_cycle(
    *,
    time_of_day: str,
    mock_date_str: str | None = None,
    send_telegram: bool = False,
    publish: bool = False,
    alert_on_failure: bool = False,
    target_branch: str = DEFAULT_TARGET_BRANCH,
    remote_name: str = DEFAULT_REMOTE_NAME,
    commit_prefix: str = DEFAULT_COMMIT_PREFIX,
) -> int:
    try:
        update_data(mock_date_str=mock_date_str)
    except Exception as exc:
        _notify_failure("update-data", exc, alert_on_failure=alert_on_failure)
        return 1

    try:
        analyze_portfolio(time_of_day=time_of_day)
    except Exception as exc:
        print(f"analyze-portfolio failed, using fallback briefing: {exc}")
        apply_fallback_briefing()

    if send_telegram:
        try:
            send_briefing(time_of_day=time_of_day)
        except Exception as exc:
            _notify_failure("send-briefing", exc, alert_on_failure=alert_on_failure)
            return 1

    if publish:
        try:
            publish_data(
                target_branch=target_branch,
                remote_name=remote_name,
                commit_prefix=commit_prefix,
            )
        except Exception as exc:
            _notify_failure("publish-data", exc, alert_on_failure=alert_on_failure)
            return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asset Management pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser("update-data")
    update_parser.add_argument("--date", dest="mock_date_str")

    analyze_parser = subparsers.add_parser("analyze-portfolio")
    analyze_parser.add_argument("--time-of-day", choices=["morning", "afternoon", "evening", "test"], required=True)

    send_parser = subparsers.add_parser("send-briefing")
    send_parser.add_argument("--time-of-day", choices=["morning", "afternoon", "evening", "test"], required=True)

    publish_parser = subparsers.add_parser("publish-data")
    publish_parser.add_argument("--target-branch", default=DEFAULT_TARGET_BRANCH)
    publish_parser.add_argument("--remote-name", default=DEFAULT_REMOTE_NAME)
    publish_parser.add_argument("--commit-prefix", default=DEFAULT_COMMIT_PREFIX)

    run_parser = subparsers.add_parser("run-cycle")
    run_parser.add_argument("--time-of-day", choices=["morning", "afternoon", "evening", "test"], required=True)
    run_parser.add_argument("--date", dest="mock_date_str")
    run_parser.add_argument("--send-telegram", action=argparse.BooleanOptionalAction, default=False)
    run_parser.add_argument("--publish", action=argparse.BooleanOptionalAction, default=False)
    run_parser.add_argument("--alert-on-failure", action=argparse.BooleanOptionalAction, default=False)
    run_parser.add_argument("--target-branch", default=DEFAULT_TARGET_BRANCH)
    run_parser.add_argument("--remote-name", default=DEFAULT_REMOTE_NAME)
    run_parser.add_argument("--commit-prefix", default=DEFAULT_COMMIT_PREFIX)

    return parser


def main() -> int:
    load_pipeline_env()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "update-data":
        update_data(mock_date_str=args.mock_date_str)
        return 0
    if args.command == "analyze-portfolio":
        analyze_portfolio(time_of_day=args.time_of_day)
        return 0
    if args.command == "send-briefing":
        send_briefing(time_of_day=args.time_of_day)
        return 0
    if args.command == "publish-data":
        publish_data(
            target_branch=args.target_branch,
            remote_name=args.remote_name,
            commit_prefix=args.commit_prefix,
        )
        return 0
    return run_cycle(
        time_of_day=args.time_of_day,
        mock_date_str=args.mock_date_str,
        send_telegram=args.send_telegram,
        publish=args.publish,
        alert_on_failure=args.alert_on_failure,
        target_branch=args.target_branch,
        remote_name=args.remote_name,
        commit_prefix=args.commit_prefix,
    )


if __name__ == "__main__":
    raise SystemExit(main())
