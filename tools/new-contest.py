#!/usr/bin/env python3
"""Create an AtCoder contest workspace using ac-lisp's existing problem setup."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = r"[A-Za-z0-9_-]+"
CONTEST = re.compile(rf"(?:https://atcoder\.jp/contests/)?({COMPONENT})(?:/tasks)?/?\Z")
LABEL = re.compile(rf"{COMPONENT}\Z")


def fail(message):
    print(f"ac-lisp: {message}", file=sys.stderr)
    return 1


def main(args):
    if not 1 <= len(args) <= 2:
        return fail("contest setup requires CONTEST [DIR]")
    match = CONTEST.fullmatch(args[0])
    if not match:
        return fail("expected an AtCoder contest ID or URL")
    contest = match.group(1)
    contest_url = f"https://atcoder.jp/contests/{contest}"
    destination = Path(args[1] if len(args) == 2 else contest)
    # lexists rejects dangling symlinks as well as existing files and directories.
    if os.path.lexists(destination):
        return fail(f"destination already exists: {destination}")

    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    api_env = env.copy()
    compat = str(ROOT / "tools" / "oj-compat")
    previous_pythonpath = api_env.get("PYTHONPATH")
    api_env["PYTHONPATH"] = (compat + os.pathsep + previous_pythonpath
                             if previous_pythonpath else compat)
    try:
        result = subprocess.run(
            ["oj-api", "get-contest", contest_url], env=api_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return fail(f"cannot retrieve contest problem list: {error}")
    if result.returncode:
        return fail(f"oj-api failed to retrieve contest problem list (status {result.returncode}); "
                    "check contest access and network connection, then retry")
    try:
        data = json.loads(result.stdout)
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
        if data.get("status") != "ok":
            raise ValueError("oj-api did not return a successful result")
        problems = data["result"]["problems"]
        if not isinstance(problems, list) or not problems:
            raise ValueError("problem list is empty or invalid")
        tasks = []
        labels = set()
        urls = set()
        task_url = re.compile(rf"https://atcoder\.jp/contests/{re.escape(contest)}/tasks/{COMPONENT}\Z")
        for item in problems:
            label = item["context"]["alphabet"]
            url = item["url"]
            if not isinstance(label, str) or not LABEL.fullmatch(label):
                raise ValueError("invalid problem label")
            if not isinstance(url, str) or not task_url.fullmatch(url):
                raise ValueError("invalid problem URL or different contest")
            if label.casefold() in labels or url in urls:
                raise ValueError("duplicate problem label or URL")
            labels.add(label.casefold())
            urls.add(url)
            tasks.append((label, url))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return fail(f"invalid contest problem list: {error}")

    try:
        destination.mkdir()
    except OSError as error:
        return fail(f"cannot create {destination}: {error}")
    cli = ROOT / "bin" / "ac-lisp"
    missing = []
    for index, (label, url) in enumerate(tasks, 1):
        if index > 1:
            time.sleep(1)
        print(f"[{index}/{len(tasks)}] {label}", flush=True)
        try:
            result = subprocess.run(
                [str(cli), "new", url, label], cwd=destination, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return fail(f"problem {label} failed: {error}; created files remain in {destination}")
        if result.returncode:
            # The downloader also emits this when it cannot parse samples, so do
            # not infer that the problem is interactive or silently succeed.
            errors = [line.strip() for line in result.stdout.splitlines()
                      if line.strip().startswith(("[ERROR]", "[FAILURE]"))]
            if errors == ["[ERROR] Sample not found"]:
                print(f"Warning: samples not found for {label}; files remain in {destination / label}", flush=True)
                missing.append(label)
                continue
            print(result.stdout, file=sys.stderr, end="")
            return fail(f"problem {label} failed; created files remain in {destination}")
    if missing:
        return fail(f"workspace created at {destination}, but samples were not found for: {', '.join(missing)}")
    print(f"Created contest workspace: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
