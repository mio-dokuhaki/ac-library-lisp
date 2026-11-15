# Command-line workflow

The `ac-lisp` CLI creates a problem directory, downloads samples, expands the library,
compiles and tests the solution, and invokes `oj` to submit it. It requires SBCL,
Python 3 and [online-judge-tools](https://github.com/online-judge-tools/oj). For
example, with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install --python 3.13 --with setuptools --with-executables-from online-judge-api-client online-judge-tools
ln -s /path/to/ac-library-lisp/bin/ac-lisp ~/.local/bin/ac-lisp
```

Make sure `~/.local/bin` is on your `PATH`. Keep the checkout in place: the symlink
uses its expander and library sources.

```sh
ac-lisp new https://atcoder.jp/contests/practice2/tasks/practice2_a
cd practice2_a
# Edit main.lisp, including the ACL modules you need.
ac-lisp test
ac-lisp submit
```

`new URL [DIR]` saves the exact problem URL in `problem-url.txt` and refuses to
overwrite an existing directory.

To prepare every problem in an AtCoder contest at once, pass a contest ID, the
contest URL, or its `/tasks` URL instead. Query strings such as `?lang=ja`
and URL fragments are accepted:

```sh
ac-lisp new typical90
# URL form; the optional second argument selects the workspace directory:
ac-lisp new https://atcoder.jp/contests/abc484/tasks abc484-work
cd typical90/007
# Edit main.lisp, then run ac-lisp test.
```

The default workspace directory is the contest ID. Each problem directory uses
its official label from the task list, such as `001` or `A`, and contains a
solution template, its URL, and any downloaded samples. Contest setup requires `python3`, `oj`,
and `oj-api` on `PATH`. Sample downloads run sequentially, with at least one
second between launches; download time counts toward this interval. Interactive
terminals show a progress bar, while redirected output shows one line per task.
If samples cannot be
found for a problem, setup warns and continues with the other problems, then
exits with a nonzero status. Other failures, including network failures, stop
setup. In either case, already created files remain for inspection; an existing
destination is never overwritten. Interactive tasks need a separate interactive
judge; the current `test` and `submit` commands require ordinary sample files and
do not support interactive testing or submission. There is no automatic resume:
after an interruption, inspect the existing files and use `ac-lisp new TASK_URL
workspace/LABEL` for each problem whose directory was not created.

`test [DIR]` expands the solution, compiles it
with SBCL and runs the downloaded samples. `submit [DIR]` repeats the tests and
passes the expanded source to `oj`, which asks for confirmation. The default
language selector is `SBCL`; use `--language ID` when necessary. The language is
selected from the contest's current list rather than a fixed ID.
Sample files must be regular files in `test/`, with matching `.in` and `.out`
names. Hidden inputs, symlinks, and subdirectories are rejected; other files are
not run. Tests use a temporary snapshot of the sample pairs.

For contest lookup, sample download, and `submit`, the CLI applies a process-local
compatibility fix when it detects
the older `online-judge-api-client` parser that cannot read AtCoder's `KiB` and
`MiB` memory limits. The installed `oj` package is not modified. This requires a
normal Python `oj` installation that loads `sitecustomize` at startup; an updated
client is left unchanged. Any existing `PYTHONPATH` and `sitecustomize` are kept.

AtCoder uses Turnstile on its login page, so ordinary `oj login` may fail. Log in
in your browser first, then import that profile's session and check it. Firefox,
LibreWolf, Edge, Chrome, Chromium, Brave, Opera, Opera GX and Vivaldi are supported:

```sh
ac-lisp login --browser edge --profile ~/.config/microsoft-edge/Default
# For Firefox: ac-lisp login --browser firefox --profile ~/.mozilla/firefox/YOUR_PROFILE
ac-lisp login --check
```

Chromium-based browsers require `browser-cookie3` and an unlocked system keyring.
One way to install the dependency in an isolated environment is:

```sh
uv venv ~/.local/share/ac-lisp/venv
uv pip install --python ~/.local/share/ac-lisp/venv/bin/python 'browser-cookie3==0.20.1'
```

For a browser import, explicitly use that interpreter for this command:

```sh
env AC_LISP_PYTHON="$HOME/.local/share/ac-lisp/venv/bin/python" ac-lisp login --browser edge --profile ~/.config/microsoft-edge/Default
```

The importer uses `AC_LISP_PYTHON` if set; otherwise, it looks for
`${XDG_DATA_HOME:-$HOME/.local/share}/ac-lisp/venv/bin/python` and falls back to
`python3` if that file is absent. An existing `AC_LISP_PYTHON` or a custom
`XDG_DATA_HOME` can therefore select a different Python from the one above.
Alternatively, install `browser-cookie3` in another Python environment and set
`AC_LISP_PYTHON` to that interpreter. The importer validates the session before
replacing AtCoder cookies in the `oj` jar, preserving cookies for other sites.
Firefox and LibreWolf imports use persistent cookies in `cookies.sqlite`; a
session kept only in browser memory or session restore data cannot be imported.
Avoid running other `oj` commands during an import: the importer detects changes
before replacement, but cannot prevent a write between its final check and replacement.

The session cookie is a credential; keep the `oj` cookie jar private. AtCoder may
also require Turnstile for submissions to finished contests. As with
[acrust](https://github.com/okaponta/acrust), CLI submission cannot complete that
challenge. Use `ac-lisp copy [DIR]` to copy the expanded solution, then paste it
into the contest's submission page and complete the browser challenge. `copy`
requires `wl-copy` on Wayland or `xclip` on X11. If a submission fails after the
request was sent, check your AtCoder submission history before trying again: a
network error can leave the outcome unknown.

