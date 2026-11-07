#!/usr/bin/env python3
"""Exercise the AtCoder CLI end to end with a local, deterministic oj double."""

import json
from http.cookiejar import Cookie, LWPCookieJar
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "atcoder.lisp"
TASK_URL = "https://atcoder.jp/contests/practice2/tasks/practice2_a"
SOLUTION = (ROOT / "examples/practice2_a.lisp").read_text()
SAMPLE_INPUT = (ROOT / "examples/practice2_a.in").read_text()
SAMPLE_OUTPUT = (ROOT / "examples/practice2_a.out").read_text()

FAKE_OJ = r'''#!/usr/bin/env python3
import http.cookiejar, json, os, pathlib, shlex, subprocess, sys, time

args = sys.argv[1:]
if args[:1] == ['--cookie']:
    cookie_path = pathlib.Path(args[1])
    if not cookie_path.is_file() or cookie_path.stat().st_mode & 0o077:
        sys.exit(2)
    args = args[2:]
command = args[0]
entry = {"args": args, "pythonpath": os.environ.get("PYTHONPATH"),
         "dontwritebytecode": os.environ.get("PYTHONDONTWRITEBYTECODE"),
         "sitecustomize_value": getattr(sys.modules.get("sitecustomize"), "VALUE", None)}
if command == "submit":
    source = pathlib.Path(args[-1])
    entry["source"] = source.read_text()
if command == "test":
    i = args.index("-c") if "-c" in args else args.index("--command")
    entry["command"] = args[i + 1]
    i = args.index("--directory") if "--directory" in args else args.index("-d")
    folder = pathlib.Path(args[i + 1])
    entry["files"] = {p.name: p.read_text() for p in folder.iterdir() if p.is_file()}
with open(os.environ["FAKE_OJ_LOG"], "a") as out:
    out.write(json.dumps(entry) + "\n")
if command == "login" and os.environ.get("FAKE_CONCURRENT_JAR"):
    jar_path = os.environ["FAKE_CONCURRENT_JAR"]
    if os.environ.get("FAKE_CONCURRENT_ACTION") == "delete":
        pathlib.Path(jar_path).unlink()
    else:
        jar = http.cookiejar.LWPCookieJar(jar_path)
        if pathlib.Path(jar_path).exists():
            jar.load(ignore_discard=True, ignore_expires=True)
        jar.set_cookie(http.cookiejar.Cookie(0, 'concurrent', 'preserve-update', None, False,
            'example.org', False, False, '/', True, True, int(time.time()) + 3600, False,
            None, None, {}, False))
        jar.save(ignore_discard=True, ignore_expires=True)
if os.environ.get("FAKE_OJ_FAIL") == command:
    sys.exit(17)
if command == "download":
    i = args.index("--directory") if "--directory" in args else args.index("-d")
    folder = pathlib.Path(args[i + 1])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sample-1.in").write_text(os.environ["FAKE_INPUT"])
    (folder / "sample-1.out").write_text(os.environ["FAKE_OUTPUT"])
elif command == "test":
    if os.environ.get("FAKE_MUTATE_SOURCE"):
        pathlib.Path(os.environ["FAKE_MUTATE_SOURCE"]).write_text(os.environ["FAKE_MUTATE_TEXT"])
    i = args.index("--directory") if "--directory" in args else args.index("-d")
    folder = pathlib.Path(args[i + 1])
    inputs = sorted(p for p in folder.glob("*.in") if not p.name.startswith("."))
    if not inputs:
        sys.exit(1)
    for sample in inputs:
        output = sample.with_suffix(".out")
        if not output.is_file():
            sys.exit(1)
        proc = subprocess.run(shlex.split(entry["command"]), input=sample.read_bytes(), capture_output=True)
        actual = proc.stdout.decode("utf-8", errors="replace").encode("utf-8").replace(b"\r\n", b"\n")
        expected = output.read_bytes().replace(b"\r\n", b"\n")
        if proc.returncode or actual != expected:
            sys.stderr.write(f"Sample failed: {sample.name}\n" +
                             (proc.stderr + proc.stdout).decode("utf-8", errors="replace"))
            sys.exit(1)
'''

FAKE_BROWSER_COOKIE3 = r'''import http.cookiejar, json, os, time
from pathlib import Path

def __getattr__(browser):
    def load(*, cookie_file, domain_name):
        with open(os.environ['FAKE_BROWSER_LOG'], 'a') as output:
            output.write(json.dumps({'browser': browser, 'cookie_file': cookie_file,
                                     'domain_name': domain_name}) + '\n')
        result = http.cookiejar.CookieJar()
        def add(domain, name, value, expiry=None):
            result.set_cookie(http.cookiejar.Cookie(
                0, name, value, None, False, domain, domain.startswith('.'),
                domain.startswith('.'), '/', True, True, expiry or int(time.time()) + 3600,
                False, None, None, {}, False))
        if os.environ.get('FAKE_BROWSER_MODE') != 'missing':
            add('.atcoder.jp', 'REVEL_SESSION', 'fake-browser-token')
        if os.environ.get('FAKE_BROWSER_MODE') == 'ambiguous':
            add('atcoder.jp', 'REVEL_SESSION', 'fake-other-session')
        add('.evil-atcoder.jp', 'bad-domain', 'must-not-import')
        add('.atcoder.jp', 'csrf_token', 'fake-csrf')
        add('.atcoder.jp', 'expired', 'must-not-import', int(time.time()) - 3600)
        return result
    return load
'''


class CliIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="acl cli test ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        fake = self.bin / "oj"
        fake.write_text(FAKE_OJ)
        fake.chmod(0o755)
        self.log = self.base / "oj.jsonl"
        copy = self.bin / "wl-copy"
        copy.write_text('#!/usr/bin/env python3\nimport os, pathlib, sys\n'
                        'pathlib.Path(os.environ["FAKE_CLIPBOARD"]).write_bytes(sys.stdin.buffer.read())\n')
        copy.chmod(0o755)
        self.clipboard = self.base / "clipboard"
        self.data = self.base / "user data"
        self.home = self.base / "sandboxed-home"
        self.home.mkdir()
        jar_base = self.home / "Library" / "Application Support" if sys.platform == "darwin" else self.data
        self.jar_path = jar_base / "online-judge-tools" / "cookie.jar"
        self.temp_root = self.base / "temporary files"
        self.temp_root.mkdir()
        self.env = os.environ.copy()
        self.env.pop("AC_LISP_PYTHON", None)
        self.env.pop("PYTHONPATH", None)
        self.env.pop("CL_SOURCE_REGISTRY", None)
        self.env.pop("ASDF_OUTPUT_TRANSLATIONS", None)
        self.env.update(HOME=str(self.home),
                        PATH=str(self.bin) + os.pathsep + self.env.get("PATH", ""),
                        FAKE_OJ_LOG=str(self.log), FAKE_INPUT=SAMPLE_INPUT,
                        FAKE_OUTPUT=SAMPLE_OUTPUT, TMPDIR=str(self.temp_root),
                        XDG_DATA_HOME=str(self.data), XDG_CONFIG_HOME=str(self.base / "config"),
                        XDG_CACHE_HOME=str(self.base / "cache"), XDG_STATE_HOME=str(self.base / "state"),
                        FAKE_CLIPBOARD=str(self.clipboard), WAYLAND_DISPLAY="test-display",
                        PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
        self.problem = self.base / "problem with spaces"

    def run_cli(self, *args, env=None):
        return subprocess.run(["sbcl", "--script", str(CLI), *map(str, args)],
                              cwd=self.base, env=env or self.env, text=True,
                              capture_output=True, timeout=60)

    def events(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def prepare(self):
        result = self.run_cli("new", TASK_URL, self.problem)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        (self.problem / "main.lisp").write_text(SOLUTION)

    def test_new_test_submit_and_cleanup(self):
        self.prepare()
        self.assertEqual((self.problem / "problem-url.txt").read_text().strip(), TASK_URL)
        original = (self.problem / "main.lisp").read_text()
        run = self.run_cli("test", self.problem)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        run = self.run_cli("submit", self.problem, "--language", "1234")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        events = self.events()
        self.assertEqual([e["args"][0] for e in events], ["download", "test", "test", "submit"])
        submission = events[-1]
        self.assertIn(TASK_URL, submission["args"])
        self.assertIn("1234", submission["args"])
        self.assertIn("make-dsu", submission["source"])
        self.assertNotIn("(acl-include :dsu)", submission["source"])
        self.assertFalse(Path(submission["args"][-1]).exists(), "temporary expanded source was left behind")
        self.assertEqual(list(self.temp_root.iterdir()), [])
        self.assertEqual((self.problem / "main.lisp").read_text(), original)

    def test_uppercase_contest_and_task_ids_preserved_through_submit(self):
        url = "https://atcoder.jp/contests/chokudai_S001/tasks/chokudai_S001_a"
        result = self.run_cli("new", url, self.problem)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.problem / "problem-url.txt").read_text().strip(), url)
        (self.problem / "main.lisp").write_text(SOLUTION)
        result = self.run_cli("submit", self.problem)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        events = self.events()
        self.assertEqual([entry["args"][0] for entry in events], ["download", "test", "submit"])
        self.assertIn(url, events[0]["args"])
        self.assertIn(url, events[-1]["args"])

    def test_submit_preserves_pythonpath_and_user_sitecustomize(self):
        self.prepare()
        custom = self.base / "user pythonpath"
        custom.mkdir()
        marker = self.base / "sitecustomize-runs"
        (custom / "sitecustomize.py").write_text(
            'import os\nVALUE = "kept"\nwith open(os.environ["CUSTOMIZE_MARKER"], "a") as f: f.write("ran\\n")\n'
        )
        env = self.env.copy()
        env["PYTHONPATH"] = str(custom)
        env["CUSTOMIZE_MARKER"] = str(marker)
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        result = self.run_cli("submit", self.problem, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        test_event, submit_event = self.events()[-2:]
        self.assertEqual(test_event["pythonpath"], str(custom))
        paths = submit_event["pythonpath"].split(os.pathsep)
        self.assertEqual([Path(p) for p in paths], [ROOT / "tools/oj-compat", custom])
        self.assertEqual(submit_event["dontwritebytecode"], "1")
        self.assertEqual(test_event["sitecustomize_value"], "kept")
        self.assertEqual(submit_event["sitecustomize_value"], "kept")
        self.assertEqual(marker.read_text().splitlines(), ["ran", "ran"])

    def test_submit_preserves_bytecode_preference_and_failure(self):
        self.prepare()
        env = self.env.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "0"
        env["PYTHONPYCACHEPREFIX"] = str(self.base / "bytecode-cache")
        env["FAKE_OJ_FAIL"] = "submit"
        result = self.run_cli("submit", self.problem, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events()[-1]["dontwritebytecode"], "0")

    def test_empty_pythonpath_does_not_add_working_directory(self):
        self.prepare()
        marker = self.base / "unexpected-sitecustomize"
        (self.base / "sitecustomize.py").write_text(
            'from pathlib import Path\nPath("unexpected-sitecustomize").write_text("ran")\n'
        )
        env = self.env.copy()
        env["PYTHONPATH"] = ""
        result = self.run_cli("submit", self.problem, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(Path(self.events()[-1]["pythonpath"]), ROOT / "tools/oj-compat")
        self.assertNotIn(os.pathsep, self.events()[-1]["pythonpath"])
        self.assertFalse(marker.exists())

    def test_compatibility_leaves_fixed_parser_unchanged(self):
        package = self.base / "mock-package"
        service = package / "onlinejudge" / "service"
        service.mkdir(parents=True)
        (package / "onlinejudge" / "__init__.py").touch()
        (service / "__init__.py").touch()
        (service / "atcoder.py").write_text(
            'class AtCoderProblemData:\n'
            '    @classmethod\n'
            '    def _from_html(cls, html, **kwargs): return ("fixed", html)\n'
        )
        env = self.env.copy()
        env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "tools/oj-compat"), str(package)))
        code = ('from onlinejudge.service.atcoder import AtCoderProblemData; '
                'assert AtCoderProblemData._from_html(b"1024 MiB") == ("fixed", b"1024 MiB")')
        result = subprocess.run([sys.executable, "-c", code], cwd=self.base, env=env,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(os.environ.get("AC_LISP_TEST_OJ_PYTHON"), "real oj test interpreter not configured")
    def test_real_legacy_oj_parses_binary_memory_units(self):
        python = os.environ["AC_LISP_TEST_OJ_PYTHON"]
        script = r'''
import re
from onlinejudge.service import atcoder
from onlinejudge.service.atcoder import AtCoderProblem, AtCoderProblemData
problem = AtCoderProblem(contest_id="abc483", problem_id="abc483_a")
for label, value, unit, expected in [
    ("Memory Limit", "1024", "MiB", 1073741824),
    ("メモリ制限", "1001", "KiB", 1025024),
    ("Memory Limit", "249", "MiB", 261095424),
    ("Memory Limit", "512", "MB", 512000000),
]:
    html = ('<html><head><meta charset="utf-8"><meta name="description" '
            'content="Memory Limit: 1 MiB"></head><body><span class="h2">A - Sample</span>'
            '<p>Time Limit: 2 sec / ' + label + ': ' + value + ' ' + unit + '</p></body></html>').encode()
    data = AtCoderProblemData._from_html(html, problem=problem)
    assert data.memory_limit_byte == expected, (unit, data.memory_limit_byte, expected)
    assert data.html == html
assert atcoder.re is re
bad = b'<span class="h2">A - Sample</span><p>Time Limit: 2 sec / Memory Limit: 1 GB</p>'
try:
    AtCoderProblemData._from_html(bad, problem=problem)
except AssertionError:
    pass
else:
    raise AssertionError("unexpectedly accepted unsupported unit")
'''
        env = self.env.copy()
        env["PYTHONPATH"] = str(ROOT / "tools/oj-compat")
        result = subprocess.run([python, "-c", script], cwd=self.base, env=env,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_failed_sample_aborts_submit(self):
        self.prepare()
        env = self.env.copy()
        env["FAKE_OJ_FAIL"] = "test"
        run = self.run_cli("submit", self.problem, env=env)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual([e["args"][0] for e in self.events()], ["download", "test"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_second_sample_failure_aborts_submit(self):
        self.prepare()
        cases = self.problem / "test"
        (cases / "sample-2.in").write_text("2 2\n0 0 1\n1 0 1\n")
        expected = cases / "sample-2.out"
        expected.write_text("1\n")
        result = self.run_cli("test", self.problem)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected.write_text("0\n")
        result = self.run_cli("submit", self.problem)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sample-2.in", result.stderr)
        self.assertEqual([e["args"][0] for e in self.events()], ["download", "test", "test"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_whitespace_mismatch_fails_but_crlf_matches(self):
        self.prepare()
        (self.problem / "main.lisp").write_text('(format t "1~%")\n')
        expected = self.problem / "test" / "sample-1.out"
        expected.write_bytes(b"1\r\n")
        result = self.run_cli("test", self.problem)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for data in (b" 1\n", b"1 \n", b"1", b"1\n\n", b"1\r"):
            with self.subTest(expected=data):
                expected.write_bytes(data)
                result = self.run_cli("submit", self.problem)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("sample-1.in", result.stderr)
                self.assertNotIn("submit", [e["args"][0] for e in self.events()])

    def test_sample_snapshot_excludes_unrecognized_files(self):
        self.prepare()
        cases = self.problem / "test"
        (cases / "rogue.inBAD").write_text("would otherwise be unchecked\n")
        (cases / "unchecked.in.bak").write_text("would otherwise be unchecked\n")
        result = self.run_cli("test", self.problem)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        event = self.events()[-1]
        self.assertEqual(event["args"][0], "test")
        self.assertEqual(event["files"], {"sample-1.in": SAMPLE_INPUT, "sample-1.out": SAMPLE_OUTPUT})
        index = event["args"].index("--directory")
        snapshot = Path(event["args"][index + 1])
        self.assertNotEqual(snapshot, cases)
        self.assertFalse(snapshot.exists())
        self.assertTrue((cases / "rogue.inBAD").exists())

    def test_sample_snapshot_survives_original_changes(self):
        self.prepare()
        cases = self.problem / "test"
        expected = cases / "sample-1.out"
        env = self.env.copy()
        env["FAKE_MUTATE_SOURCE"] = str(expected)
        env["FAKE_MUTATE_TEXT"] = "changed while testing\n"
        result = self.run_cli("test", self.problem, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(expected.read_text(), "changed while testing\n")
        event = self.events()[-1]
        self.assertEqual(event["files"]["sample-1.in"], SAMPLE_INPUT)
        self.assertEqual(event["files"]["sample-1.out"], SAMPLE_OUTPUT)
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_symlinked_sample_input_or_output_is_rejected(self):
        self.prepare()
        cases = self.problem / "test"
        for suffix in ("in", "out"):
            with self.subTest(suffix=suffix):
                sample = cases / ("sample-1." + suffix)
                content = sample.read_text()
                target = self.base / ("target." + suffix)
                target.write_text(content)
                sample.unlink()
                sample.symlink_to(target)
                self.assert_samples_rejected()
                sample.unlink()
                sample.write_text(content)

    def test_sample_subdirectory_and_other_symlinks_are_rejected(self):
        self.prepare()
        cases = self.problem / "test"
        folder = cases / "nested"
        folder.mkdir()
        (folder / "sample.in").write_text("1 0\n")
        (folder / "sample.out").write_text("0\n")
        self.assert_samples_rejected("subdirectory")
        (folder / "sample.in").unlink()
        (folder / "sample.out").unlink()
        folder.rmdir()
        target = self.base / "note"
        target.write_text("unrelated\n")
        link = cases / "note.txt"
        link.symlink_to(target)
        self.assert_samples_rejected()

    def assert_samples_rejected(self, message=None):
        for command in ("test", "submit"):
            with self.subTest(command=command):
                result = self.run_cli(command, self.problem)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                if message:
                    self.assertIn(message, result.stdout + result.stderr)
                self.assertEqual([e["args"][0] for e in self.events()], ["download"])
                self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_missing_sample_output_cannot_test_or_submit(self):
        self.prepare()
        (self.problem / "test" / "sample-1.out").unlink()
        self.assert_samples_rejected()

    def test_no_sample_inputs_cannot_test_or_submit(self):
        self.prepare()
        (self.problem / "test" / "sample-1.in").unlink()
        self.assert_samples_rejected()

    def test_partially_paired_samples_cannot_test_or_submit(self):
        self.prepare()
        (self.problem / "test" / "sample-2.in").write_text("1 0\n")
        self.assert_samples_rejected()

    def test_hidden_and_hash_prefixed_unpaired_inputs_are_rejected(self):
        self.prepare()
        for name in (".hidden.in", "#extra.in"):
            with self.subTest(name=name):
                input_file = self.problem / "test" / name
                input_file.write_text("1 0\n")
                self.assert_samples_rejected()
                input_file.unlink()

    def test_paired_hidden_samples_cannot_be_silently_skipped(self):
        self.prepare()
        cases = self.problem / "test"
        (cases / ".hidden.in").write_text(SAMPLE_INPUT)
        (cases / ".hidden.out").write_text(SAMPLE_OUTPUT)
        # A hidden pair is invalid both alongside visible samples and on its own.
        self.assert_samples_rejected()
        (cases / "sample-1.in").unlink()
        (cases / "sample-1.out").unlink()
        self.assert_samples_rejected()

    def test_submit_error_is_reported_and_temporary_files_removed(self):
        self.prepare()
        env = self.env.copy()
        env["FAKE_OJ_FAIL"] = "submit"
        run = self.run_cli("submit", self.problem, env=env)
        self.assertNotEqual(run.returncode, 0)
        events = self.events()
        self.assertEqual([e["args"][0] for e in events], ["download", "test", "submit"])
        self.assertIn("SBCL", events[-1]["args"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_existing_directory_is_not_overwritten(self):
        self.problem.mkdir()
        sentinel = self.problem / "main.lisp"
        sentinel.write_text("preserve me\n")
        result = self.run_cli("new", TASK_URL, self.problem)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_text(), "preserve me\n")
        self.assertEqual(self.events(), [])

    def test_missing_source_does_not_submit(self):
        self.prepare()
        (self.problem / "main.lisp").unlink()
        result = self.run_cli("submit", self.problem)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([e["args"][0] for e in self.events()], ["download"])

    def test_copy_expands_solution_without_modifying_it(self):
        self.prepare()
        original = (self.problem / "main.lisp").read_text()
        run = self.run_cli("copy", self.problem)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        copied = self.clipboard.read_text()
        self.assertIn("make-dsu", copied)
        self.assertNotIn("(acl-include :dsu)", copied)
        self.assertEqual((self.problem / "main.lisp").read_text(), original)
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_firefox_import_preserves_other_cookies_and_hides_session(self):
        profile = self.base / "Firefox profile"
        profile.mkdir()
        database = profile / "cookies.sqlite"
        token = "test-session-secret-do-not-print"
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE moz_cookies (id INTEGER PRIMARY KEY, originAttributes TEXT, "
                       "name TEXT, value TEXT, host TEXT, path TEXT, expiry INTEGER, "
                       "isSecure INTEGER, isHttpOnly INTEGER)")
            db.execute("INSERT INTO moz_cookies VALUES (1, '', 'REVEL_SESSION', ?, '.atcoder.jp', '/', ?, 1, 1)",
                       (token, int(time.time()) + 3600))
            db.execute("INSERT INTO moz_cookies VALUES (2, '', 'REVEL_SESSION', 'wrong-domain', '.evil-atcoder.jp', '/', ?, 1, 1)",
                       (int(time.time()) + 3600,))
            db.execute("INSERT INTO moz_cookies VALUES (3, '', 'same-origin', 'wanted', '.atcoder.jp', '/', ?, 1, 1)",
                       (int(time.time()) + 3600,))
            db.execute("INSERT INTO moz_cookies VALUES (4, '^userContextId=1', 'different-container', 'unwanted', '.atcoder.jp', '/', ?, 1, 1)",
                       (int(time.time()) + 3600,))
        jar_path = self.jar_path
        jar_path.parent.mkdir(parents=True)
        jar = LWPCookieJar(str(jar_path))
        jar.set_cookie(Cookie(0, 'other', 'preserved', None, False, 'example.org', False,
                              False, '/', True, True, int(time.time()) + 3600, False,
                              None, None, {}, False))
        jar.set_cookie(Cookie(0, 'REVEL_SESSION', 'old-host-session', None, False,
                              'atcoder.jp', False, False, '/', True, True,
                              int(time.time()) + 3600, False, None, None, {}, False))
        jar.set_cookie(Cookie(0, 'REVEL_SESSION', 'old-domain-session', None, False,
                              '.atcoder.jp', True, True, '/old', True, True,
                              int(time.time()) + 3600, False, None, None, {}, False))
        jar.save(ignore_discard=True, ignore_expires=True)
        jar_path.chmod(0o600)
        result = self.run_cli("login", "--firefox", profile)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(token, result.stdout + result.stderr)
        events = self.events()
        self.assertNotIn(token, json.dumps(events))
        self.assertEqual([e["args"][0] for e in events], ["login"])
        self.assertIn("--check", events[0]["args"])
        jar = LWPCookieJar(str(jar_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = {(c.domain, c.name): c.value for c in jar}
        self.assertEqual(cookies.get(("example.org", "other")), "preserved")
        self.assertEqual(cookies.get((".atcoder.jp", "REVEL_SESSION")), token)
        self.assertNotIn(("atcoder.jp", "REVEL_SESSION"), cookies)
        self.assertEqual(sum(c.name == "REVEL_SESSION" and
                             c.domain.lstrip(".") == "atcoder.jp" for c in jar), 1)
        self.assertEqual(cookies.get((".atcoder.jp", "same-origin")), "wanted")
        self.assertNotIn((".atcoder.jp", "different-container"), cookies)
        self.assertNotIn((".evil-atcoder.jp", "REVEL_SESSION"), cookies)
        self.assertEqual(jar_path.stat().st_mode & 0o077, 0)

    def test_invalid_firefox_profile_fails_without_login(self):
        result = self.run_cli("login", "--firefox", self.base / "missing profile")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events(), [])

    @unittest.skipIf(sys.platform == "darwin", "oj ignores XDG_DATA_HOME on macOS")
    def test_cookie_jar_follows_oj_when_xdg_data_home_empty_or_unset(self):
        profile = self.base / "profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-xdg', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        home = self.base / "isolated home"
        home.mkdir()
        for value, expected in (("", self.base / "online-judge-tools" / "cookie.jar"),
                                (None, home / ".local" / "share" / "online-judge-tools" / "cookie.jar")):
            with self.subTest(xdg=value):
                env = self.env.copy()
                env["HOME"] = str(home)
                if value is None:
                    env.pop("XDG_DATA_HOME", None)
                else:
                    env["XDG_DATA_HOME"] = value
                result = self.run_cli("login", "--firefox", profile, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("fake-xdg", result.stdout + result.stderr)
                self.assertTrue(expected.is_file(), str(expected))
                jar = LWPCookieJar(str(expected))
                jar.load(ignore_discard=True, ignore_expires=True)
                self.assertEqual(next(cookie.value for cookie in jar if cookie.name == "REVEL_SESSION"), "fake-xdg")

    def test_cookie_jar_macos_path_ignores_xdg(self):
        env = self.env.copy()
        env["HOME"] = str(self.base / "mac home")
        env["XDG_DATA_HOME"] = str(self.base / "ignored")
        script = ("import sys; sys.path.insert(0, sys.argv[1]); import cookie_jar; "
                  "sys.platform='darwin'; print(cookie_jar.oj_cookie_path())")
        result = subprocess.run(["python3", "-B", "-c", script, str(ROOT / "tools")],
                                cwd=self.base, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = Path(env["HOME"]) / "Library" / "Application Support" / "online-judge-tools" / "cookie.jar"
        self.assertEqual(result.stdout.strip(), str(expected))

    def test_macos_save_uses_isolated_home_and_fake_oj(self):
        script = '''import http.cookiejar, sys, time
sys.path.insert(0, sys.argv[1])
import cookie_jar
sys.platform = "darwin"
cookie = http.cookiejar.Cookie(0, "REVEL_SESSION", "fake-macos", None, False,
    ".atcoder.jp", True, True, "/", True, True, int(time.time()) + 3600,
    False, None, None, {}, False)
cookie_jar.save_validated([cookie])
'''
        result = subprocess.run(["python3", "-B", "-c", script, str(ROOT / "tools")],
                                cwd=self.base, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("fake-macos", result.stdout + result.stderr)
        expected = self.home / "Library" / "Application Support" / "online-judge-tools" / "cookie.jar"
        jar = LWPCookieJar(str(expected))
        jar.load(ignore_discard=True, ignore_expires=True)
        self.assertEqual(next(cookie.value for cookie in jar if cookie.name == "REVEL_SESSION"), "fake-macos")
        self.assertEqual(expected.stat().st_mode & 0o077, 0)
        self.assertEqual([entry["args"][0] for entry in self.events()], ["login"])
        self.assertFalse((self.data / "online-judge-tools" / "cookie.jar").exists())

    @unittest.skipIf(sys.platform == "darwin", "oj ignores XDG_DATA_HOME on macOS")
    def test_cookie_jar_relative_path_matches_oj_appdirs(self):
        env = self.env.copy()
        env["XDG_DATA_HOME"] = "relative data"
        script = "import sys; sys.path.insert(0, sys.argv[1]); import cookie_jar; print(cookie_jar.oj_cookie_path())"
        result = subprocess.run(["python3", "-B", "-c", script, str(ROOT / "tools")],
                                cwd=self.base, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "relative data/online-judge-tools/cookie.jar")

    def test_firefox_import_uses_configured_python(self):
        profile = self.base / "profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-python', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        wrapper = self.bin / "python-wrapper"
        wrapper.write_text('#!/usr/bin/env python3\nimport os, pathlib, sys\n'
                           'pathlib.Path(os.environ["PYTHON_MARKER"]).write_text("invoked")\n'
                           'os.execv(sys.executable, [sys.executable] + sys.argv[1:])\n')
        wrapper.chmod(0o755)
        env = self.env.copy()
        env["AC_LISP_PYTHON"] = str(wrapper)
        env["PYTHON_MARKER"] = str(self.base / "python-marker")
        for args in (("--firefox", profile), ("--browser", "firefox", "--profile", profile),
                     ("--browser", "librewolf", "--profile", profile)):
            with self.subTest(args=args):
                marker = Path(env["PYTHON_MARKER"])
                if marker.exists():
                    marker.unlink()
                result = self.run_cli("login", *args, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(marker.is_file())
                self.assertNotIn("fake-python", result.stdout + result.stderr)

    def test_interactive_login_uses_terminal(self):
        result = self.run_cli("login")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        args = self.events()[0]["args"]
        self.assertIn("--use-browser", args)
        self.assertEqual(args[args.index("--use-browser") + 1], "never")

    def test_firefox_multiple_container_sessions_are_not_guessed(self):
        profile = self.base / "ambiguous profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            for index, attrs in enumerate(("", "^userContextId=1")):
                db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', ?, ?, 1, 1, ?)",
                           ("fake-" + str(index), int(time.time()) + 3600, attrs))
        result = self.run_cli("login", "--firefox", profile)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events(), [])
        self.assertFalse((self.jar_path).exists())

    def test_firefox_new_schema_uses_millisecond_expiry(self):
        profile = self.base / "modern profile"
        profile.mkdir()
        now = int(time.time())
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("PRAGMA user_version=16")
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-modern', ?, 1, 1, '')",
                       ((now + 3600) * 1000,))
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'expired', 'old', ?, 1, 1, '')",
                       ((now - 3600) * 1000,))
        result = self.run_cli("login", "--firefox", profile)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        jar = LWPCookieJar(str(self.jar_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = {cookie.name: cookie for cookie in jar}
        self.assertNotIn("expired", cookies)
        self.assertEqual(cookies["REVEL_SESSION"].expires, now + 3600)

    def test_failed_firefox_login_preserves_cookie_jar(self):
        profile = self.base / "profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-invalid', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        jar_path = self.jar_path
        jar_path.parent.mkdir(parents=True)
        jar = LWPCookieJar(str(jar_path))
        jar.set_cookie(Cookie(0, 'existing', 'preserved', None, False, 'example.org', False,
                              False, '/', True, True, int(time.time()) + 3600, False,
                              None, None, {}, False))
        jar.save(ignore_discard=True, ignore_expires=True)
        jar_path.chmod(0o600)
        before = jar_path.read_bytes()
        env = self.env.copy()
        env["FAKE_OJ_FAIL"] = "login"
        result = self.run_cli("login", "--firefox", profile, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("fake-invalid", result.stdout + result.stderr)
        self.assertEqual(jar_path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in jar_path.parent.iterdir()), ["cookie.jar"])

    def test_concurrent_cookie_jar_update_is_not_overwritten(self):
        profile = self.base / "profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-concurrent', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        jar_path = self.jar_path
        jar_path.parent.mkdir(parents=True)
        jar = LWPCookieJar(str(jar_path))
        jar.set_cookie(Cookie(0, 'existing', 'preserved', None, False, 'example.org', False,
                              False, '/', True, True, int(time.time()) + 3600, False,
                              None, None, {}, False))
        jar.save(ignore_discard=True, ignore_expires=True)
        jar_path.chmod(0o600)
        env = self.env.copy()
        env["FAKE_CONCURRENT_JAR"] = str(jar_path)
        result = self.run_cli("login", "--firefox", profile, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("fake-concurrent", result.stdout + result.stderr)
        jar = LWPCookieJar(str(jar_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = {cookie.name: cookie.value for cookie in jar}
        self.assertEqual(cookies["existing"], "preserved")
        self.assertEqual(cookies["concurrent"], "preserve-update")
        self.assertNotIn("REVEL_SESSION", cookies)
        self.assertEqual(sorted(p.name for p in jar_path.parent.iterdir()), ["cookie.jar"])

    def test_concurrent_cookie_jar_creation_or_deletion_is_not_overwritten(self):
        profile = self.base / "profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-concurrent', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        jar_path = self.jar_path
        env = self.env.copy()
        env["FAKE_CONCURRENT_JAR"] = str(jar_path)
        result = self.run_cli("login", "--firefox", profile, env=env)
        self.assertNotEqual(result.returncode, 0)
        jar = LWPCookieJar(str(jar_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        self.assertEqual({cookie.name: cookie.value for cookie in jar}, {"concurrent": "preserve-update"})
        env["FAKE_CONCURRENT_ACTION"] = "delete"
        result = self.run_cli("login", "--firefox", profile, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(jar_path.exists())
        self.assertEqual(list(jar_path.parent.iterdir()), [])

    def browser_env(self):
        modules = self.base / "fake browser modules"
        modules.mkdir()
        (modules / "browser_cookie3.py").write_text(FAKE_BROWSER_COOKIE3)
        env = self.env.copy()
        env["PYTHONPATH"] = str(modules)
        env["FAKE_BROWSER_LOG"] = str(self.base / "browser.jsonl")
        return env

    def chromium_database(self, database):
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE cookies (host_key TEXT, name TEXT, expires_utc INTEGER, top_frame_site_key TEXT)")
            db.execute("INSERT INTO cookies VALUES ('.atcoder.jp', 'REVEL_SESSION', 0, '')")

    def test_browser_import_uses_requested_browser_and_checks_session(self):
        env = self.browser_env()
        database = self.base / "cookie database with spaces"
        self.chromium_database(database)
        for browser in ("edge", "chrome", "chromium", "brave", "opera", "opera_gx",
                        "vivaldi"):
            with self.subTest(browser=browser):
                result = self.run_cli("login", "--browser", browser, "--profile", database, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("fake-browser-token", result.stdout + result.stderr)
        records = [json.loads(line) for line in (self.base / "browser.jsonl").read_text().splitlines()]
        self.assertEqual([record["browser"] for record in records],
                         ["edge", "chrome", "chromium", "brave", "opera", "opera_gx",
                          "vivaldi"])
        self.assertTrue(all(record["cookie_file"] == str(database) and
                            record["domain_name"] == "atcoder.jp" for record in records))
        jar_path = self.jar_path
        jar = LWPCookieJar(str(jar_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = {(cookie.domain, cookie.name): cookie.value for cookie in jar}
        self.assertEqual(cookies[(".atcoder.jp", "REVEL_SESSION")], "fake-browser-token")
        self.assertNotIn((".evil-atcoder.jp", "bad-domain"), cookies)
        self.assertNotIn((".atcoder.jp", "expired"), cookies)
        self.assertEqual(jar_path.stat().st_mode & 0o077, 0)
        self.assertNotIn("fake-browser-token", json.dumps(self.events()))

    def test_browser_bad_or_ambiguous_session_preserves_existing_jar(self):
        env = self.browser_env()
        database = self.base / "Cookies"
        self.chromium_database(database)
        result = self.run_cli("login", "--browser", "edge", "--profile", database, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        jar_path = self.jar_path
        before = jar_path.read_bytes()
        for mode in ("missing", "ambiguous", "rejected"):
            with self.subTest(mode=mode):
                failing_env = env.copy()
                if mode == "rejected":
                    failing_env["FAKE_OJ_FAIL"] = "login"
                else:
                    failing_env["FAKE_BROWSER_MODE"] = mode
                result = self.run_cli("login", "--browser", "edge", "--profile", database, env=failing_env)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("fake-browser-token", result.stdout + result.stderr)
                self.assertEqual(jar_path.read_bytes(), before)
                self.assertEqual(sorted(p.name for p in jar_path.parent.iterdir()), ["cookie.jar"])

    def test_browser_rejects_partitioned_and_duplicate_cookies(self):
        env = self.browser_env()
        database = self.base / "Cookies"
        self.chromium_database(database)
        for host, name, partition in ((".atcoder.jp", "other", "https://example.org"),
                                      ("atcoder.jp", "REVEL_SESSION", "")):
            with self.subTest(name=name, partition=partition):
                with sqlite3.connect(database) as db:
                    db.execute("INSERT INTO cookies VALUES (?, ?, 0, ?)", (host, name, partition))
                result = self.run_cli("login", "--browser", "edge", "--profile", database, env=env)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.events(), [])
                self.assertFalse((self.jar_path).exists())
                with sqlite3.connect(database) as db:
                    db.execute("DELETE FROM cookies WHERE host_key=? AND name=? AND top_frame_site_key=?",
                               (host, name, partition))

    def test_firefox_browser_option_uses_native_importer(self):
        profile = self.base / "Firefox profile"
        profile.mkdir()
        with sqlite3.connect(profile / "cookies.sqlite") as db:
            db.execute("CREATE TABLE moz_cookies (host TEXT, path TEXT, name TEXT, "
                       "value TEXT, expiry INTEGER, isSecure INTEGER, isHttpOnly INTEGER, originAttributes TEXT)")
            db.execute("INSERT INTO moz_cookies VALUES ('.atcoder.jp', '/', 'REVEL_SESSION', 'fake-firefox', ?, 1, 1, '')",
                       (int(time.time()) + 3600,))
        for browser in ("firefox", "librewolf"):
            with self.subTest(browser=browser):
                result = self.run_cli("login", "--browser", browser, "--profile", profile)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("fake-firefox", result.stdout + result.stderr)
                jar = LWPCookieJar(str(self.jar_path))
                jar.load(ignore_discard=True, ignore_expires=True)
                self.assertEqual(next(cookie.value for cookie in jar if cookie.name == "REVEL_SESSION"), "fake-firefox")


if __name__ == "__main__":
    unittest.main()
