#!/usr/bin/env python3
"""Create an AtCoder contest workspace using ac-lisp's existing problem setup."""
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = r"[A-Za-z0-9_-]+"
CONTEST_PATH = re.compile(rf"/contests/({COMPONENT})(?:/tasks)?/?\Z")
LABEL = re.compile(rf"{COMPONENT}\Z")


def fail(message):
    print(f"ac-lisp: {message}", file=sys.stderr)
    return 1


def wait_for_next_start(last_start):
    """Pace sequential launches without adding delay after a slow download."""
    remaining = 1.0 - (time.monotonic() - last_start)
    if remaining > 0:
        time.sleep(remaining)


def format_duration(seconds):
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f"{minutes:02d}:{seconds:02d}"


class Progress:
    """Keep terminal progress on one line and redirected output readable."""
    def __init__(self, total, stream=None):
        self.total = total
        self.stream = stream if stream is not None else sys.stdout
        self.interactive = self.stream.isatty() and os.environ.get("TERM") != "dumb"
        self.started = time.monotonic()
        self.completed = 0
        self.width = 0
        self.active = False

    def render(self, label):
        elapsed = time.monotonic() - self.started
        remaining = ((elapsed * (self.total - self.completed) / self.completed)
                     if self.completed else None)
        filled = 16 * self.completed // self.total
        bar = "#" * filled + "-" * (16 - filled)
        eta = format_duration(remaining) if remaining is not None else "--:--"
        count = f"{self.completed}/{self.total}"
        percent = f"{100 * self.completed // self.total:3d}%"
        short_filled = 8 * self.completed // self.total
        short_bar = "#" * short_filled + "-" * (8 - short_filled)
        lines = (
            f"[{bar}] {count} {percent} | {format_duration(elapsed)} elapsed | ETA {eta} | {label[:20]}",
            f"[{short_bar}] {count} {percent} | {label[:20]}",
            f"{count} {percent} {label[:20]}",
            f"{count} {percent}",
            count,
        )
        # Leave the last column empty to avoid terminal auto-wrapping.
        available = max(0, shutil.get_terminal_size(fallback=(80, 24)).columns - 1)
        line = next((candidate for candidate in lines if len(candidate) <= available),
                    count[:available])
        padding = max(0, min(self.width, available) - len(line))
        self.stream.write("\r" + line + " " * padding)
        self.stream.flush()
        self.width = len(line)
        self.active = True

    def start(self, index, label):
        if self.interactive:
            self.render(label)
        else:
            print(f"[{index}/{self.total}] {label}", file=self.stream, flush=True)

    def advance(self, index, label):
        self.completed = index
        if self.interactive:
            self.render(label)

    def message(self, text):
        if self.interactive and self.active:
            available = max(0, shutil.get_terminal_size(fallback=(80, 24)).columns - 1)
            self.stream.write("\r" + " " * min(self.width, available) + "\r")
            self.active = False
            self.width = 0
        print(text, file=self.stream, flush=True)

    def finish(self):
        if self.interactive and self.active:
            self.stream.write("\n")
            self.stream.flush()
            self.active = False


class TerminationRequested(BaseException):
    pass


def terminate_progress(signum, frame):
    # Ignore repeated SIGTERM while the progress line is being finished.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raise TerminationRequested()


def run_problem(command, *, cwd, env, timeout=120, stderr=subprocess.STDOUT):
    """Run a helper, stopping its process group if work is interrupted."""

    process = None
    terminating = False
    interrupting = False
    cleaning = False
    # Only replace the default action or our progress handler. An embedding
    # caller's custom handler or explicit SIG_IGN keeps its existing behavior.
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    handle_sigterm = (os.name == "posix"
                      and threading.current_thread() is threading.main_thread()
                      and previous_sigterm in (signal.SIG_DFL, terminate_progress))
    handle_sigint = (os.name == "posix"
                     and threading.current_thread() is threading.main_thread()
                     and signal.getsignal(signal.SIGINT) == signal.default_int_handler)
    if handle_sigterm:
        def request_termination(signum, frame):
            nonlocal terminating
            if not terminating:
                terminating = True
                if process is not None and not cleaning:
                    raise TerminationRequested()

        signal.signal(signal.SIGTERM, request_termination)
    if handle_sigint:
        def request_interrupt(signum, frame):
            nonlocal interrupting
            if not interrupting:
                interrupting = True
                if process is not None and not cleaning:
                    raise KeyboardInterrupt

        signal.signal(signal.SIGINT, request_interrupt)
    try:
        process = subprocess.Popen(
            command, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=stderr, text=True, encoding="utf-8", errors="replace",
            start_new_session=(os.name == "posix"),
        )
        # A SIGTERM delivered while Popen was starting is deferred until the
        # process handle is available, so its group can still be stopped.
        if terminating:
            raise TerminationRequested()
        if interrupting:
            raise KeyboardInterrupt
        output, error_output = process.communicate(timeout=timeout)
    except BaseException:
        cleaning = True
        if process is not None and os.name == "posix":
            # The direct process can already have exited while its oj child
            # still holds the output pipe; kill the whole group in either case.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        elif process is not None:
            # No portable process-group termination exists outside POSIX.
            # Reap the child and close our pipe even if a descendant holds it.
            try:
                process.kill()
            except ProcessLookupError:
                pass
            process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        raise
    finally:
        if handle_sigterm:
            signal.signal(signal.SIGTERM, previous_sigterm)
        if handle_sigint:
            signal.signal(signal.SIGINT, signal.default_int_handler)
        # Recheck after restoring the handlers: a signal can arrive at any
        # point during cleanup, including immediately before the re-raise.
        if terminating:
            if previous_sigterm is terminate_progress:
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                raise TerminationRequested()
            os.kill(os.getpid(), signal.SIGTERM)
        if interrupting:
            raise KeyboardInterrupt
    return subprocess.CompletedProcess(command, process.returncode, output, error_output)


def main(args):
    if not 1 <= len(args) <= 2:
        return fail("contest setup requires CONTEST [DIR]")
    target = args[0]
    if LABEL.fullmatch(target):
        contest = target
    else:
        try:
            parsed = urlsplit(target)
        except ValueError:
            return fail("expected an AtCoder contest ID or URL")
        match = CONTEST_PATH.fullmatch(parsed.path)
        if parsed.scheme != "https" or parsed.netloc != "atcoder.jp" or not match:
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
        result = run_problem(
            ["oj-api", "get-contest", contest_url], cwd=None, env=api_env,
            stderr=subprocess.PIPE, timeout=60,
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
    progress = Progress(len(tasks))
    last_start = None
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    handle_sigterm = (os.name == "posix"
                      and threading.current_thread() is threading.main_thread()
                      and previous_sigterm == signal.SIG_DFL)
    try:
        if handle_sigterm:
            signal.signal(signal.SIGTERM, terminate_progress)
        try:
            for index, (label, url) in enumerate(tasks, 1):
                if last_start is not None:
                    wait_for_next_start(last_start)
                progress.start(index, label)
                last_start = time.monotonic()
                try:
                    result = run_problem([str(cli), "new", url, label], cwd=destination, env=env)
                except (OSError, subprocess.TimeoutExpired) as error:
                    progress.finish()
                    return fail(f"problem {label} failed: {error}; created files remain in {destination}")
                if result.returncode:
                    # The downloader also emits this when it cannot parse samples, so do
                    # not infer that the problem is interactive or silently succeed.
                    errors = [line.strip() for line in result.stdout.splitlines()
                              if line.strip().startswith(("[ERROR]", "[FAILURE]"))]
                    if errors == ["[ERROR] Sample not found"]:
                        progress.message(f"Warning: samples not found for {label}; files remain in {destination / label}")
                        missing.append(label)
                        progress.advance(index, label)
                        continue
                    progress.finish()
                    print(result.stdout, file=sys.stderr, end="")
                    return fail(f"problem {label} failed; created files remain in {destination}")
                progress.advance(index, label)
        finally:
            progress.finish()
    except TerminationRequested:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        if handle_sigterm:
            signal.signal(signal.SIGTERM, previous_sigterm)
    if missing:
        return fail(f"workspace created at {destination}, but samples were not found for: {', '.join(missing)}")
    print(f"Created contest workspace: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
