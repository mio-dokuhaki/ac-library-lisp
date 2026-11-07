# ac-library-lisp

A Common Lisp port of [AtCoder Library (ACL)](https://github.com/atcoder/ac-library).

Everything is written in Common Lisp, including the source expander that replaces ACL's
`expander.py`. It targets SBCL, the Common Lisp implementation used on AtCoder.

[日本語版 README はこちら](#日本語)

## Modules

| ACL (C++) | Lisp module | Main API |
| --- | --- | --- |
| `dsu` | `:dsu` | `make-dsu`, `dsu-merge`, `dsu-same`, `dsu-leader`, `dsu-size`, `dsu-groups` |
| `fenwick_tree` | `:fenwicktree` | `make-fenwick-tree`, `fenwick-tree-add`, `fenwick-tree-sum` |
| `segtree` | `:segtree` | `make-segtree`, `define-segtree`, `segtree-prod`, `segtree-max-right`, ... |
| `lazy_segtree` | `:lazysegtree` | `make-lazy-segtree`, `define-lazy-segtree`, `lazy-segtree-apply`, ... |
| `suffix_array`, `lcp_array`, `z_algorithm` | `:string` | `suffix-array`, `lcp-array`, `z-algorithm` |
| `pow_mod`, `inv_mod`, `crt`, `floor_sum` | `:math` | `pow-mod`, `inv-mod`, `crt`, `floor-sum` |
| `static_modint`, `dynamic_modint` | `:modint` | `define-modint`, `define-dynamic-modint`, `modint998244353*`, ... |
| `convolution`, `convolution_ll` | `:convolution` | `convolution`, `convolution-ll` |
| `mf_graph` | `:maxflow` | `make-mf-graph`, `mf-graph-add-edge`, `mf-graph-flow`, `mf-graph-min-cut`, ... |
| `mcf_graph` | `:mincostflow` | `make-mcf-graph`, `mcf-graph-add-edge`, `mcf-graph-flow`, `mcf-graph-slope`, ... |
| `scc_graph` | `:scc` | `make-scc-graph`, `scc-graph-add-edge`, `scc-graph-scc` |
| `two_sat` | `:twosat` | `make-two-sat`, `two-sat-add-clause`, `two-sat-satisfiable`, `two-sat-answer` |

Full API references with constraints and complexities are in [`document_en/`](document_en/index.md).

## Using it on AtCoder

### Command-line workflow

The `ac-lisp` CLI creates a problem directory, downloads samples, expands the library,
compiles and tests the solution, and invokes `oj` to submit it. It requires SBCL,
Python 3 and [online-judge-tools](https://github.com/online-judge-tools/oj). For
example, with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install --python 3.13 --with setuptools online-judge-tools
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
overwrite an existing directory. `test [DIR]` expands the solution, compiles it
with SBCL and runs the downloaded samples. `submit [DIR]` repeats the tests and
passes the expanded source to `oj`, which asks for confirmation. The default
language selector is `SBCL`; use `--language ID` when necessary. The language is
selected from the contest's current list rather than a fixed ID.

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

Alternatively, install `browser-cookie3` in your Python environment and set
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

### Manual expansion

AtCoder accepts a single source file, so the library is pasted into your solution by the
expander. Write `acl-include` at the top of your file:

```lisp
(acl-include :dsu)

(defun main ()
  (let* ((n (read)) (q (read)) (d (make-dsu n)))
    (dotimes (i q)
      (let ((ty (read)) (u (read)) (v (read)))
        (if (= ty 0)
            (dsu-merge d u v)
            (format t "~D~%" (if (dsu-same d u v) 1 0)))))))

(main)
```

Then expand it:

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
sbcl --script combined.lisp < input.txt
```

`combined.lisp` contains only the modules you asked for (and their dependencies) followed by
`(use-package :ac-library)`, so it can be submitted as is. Use `(acl-include :all)` to include
everything.

Write each `acl-include` at the top level, on a single line of its own. An `acl-include` inside
another form, after a reader prefix such as `'` or `#+`, or inside a comment or string is not
expanded (the expander prints a warning for the first two cases). See
[`document_en/expander.md`](document_en/expander.md) for the exact rules.

Expander options:

| Option | Meaning |
| --- | --- |
| `-o FILE` | write to `FILE` instead of standard output |
| `--lib DIR` | read library sources from `DIR` instead of the `src/` next to `expander.lisp` |

## Using it as a normal library

The repository is an ASDF system named `ac-library`.

```lisp
(require :asdf)
(push #p"/path/to/ac-library-lisp/" asdf:*central-registry*)
(asdf:load-system :ac-library)
(use-package :ac-library)
```

`acl-include` is a no-op macro when the library is loaded this way, so the same solution file
also works in the REPL.

## Differences from the C++ library

* Indices are 0-based and ranges are half-open `[l, r)`, exactly as in ACL.
* Monoids are passed as functions: `(make-segtree n :op #'max :e 0)`. The identity `e` (and `id`
  for lazy segtrees) is a value, not a function.
* `define-segtree` and `define-lazy-segtree` generate specialized functions with `op`, `mapping`
  and `composition` inlined, which plays the role of C++ templates. Use them when speed matters.
* `modint` values are plain integers in `[0, mod)`. `define-modint` creates the functions
  `name`, `name+`, `name-`, `name*`, `name/`, `name-pow`, `name-inv` and `name-mod`.
  `modint998244353`, `modint1000000007` and the dynamic `modint` are predefined.
* Integers never overflow in Common Lisp, so there is no `convolution_ll` overflow caveat beyond
  the true result fitting in 64 bits, and `crt` / `floor-sum` accept arbitrarily large inputs.
* `scc-graph-scc` and `dsu-groups` return lists of lists; `mf-graph-min-cut` and `two-sat-answer`
  return vectors of `t` / `nil`; `mcf-graph-slope` returns a list of `(flow . cost)` conses.
* Depth-first searches (SCC, two-sat, max flow) are iterative, so deep graphs do not overflow
  the control stack.

## Development

```sh
sbcl --script test/run.lisp
sbcl --script test/expander-test.lisp
python3 test/cli-test.py
```

The first command checks every module against brute-force implementations on random inputs.
The second checks the expander: each module expanded on its own must compile with no undefined
references, and `acl-include` written inside comments, strings, `|...|` symbols, other forms,
or after a reader prefix such as `'` or `#+` must not be expanded. The unit tests can also be run with `(asdf:test-system :ac-library)`, which signals an
error when a test fails. The CLI tests use real SBCL and a local `oj` double to exercise
sample testing, submission preparation, and browser session import without submitting.
All three scripts run on GitHub Actions.

## License

[CC0 1.0](LICENSE), the same as the original AtCoder Library.

---

## 日本語

[AtCoder Library (ACL)](https://github.com/atcoder/ac-library) を Common Lisp に移植したライブラリです。
C++ と Python は使わず、ソースを1ファイルにまとめる expander も Common Lisp で書かれています。
AtCoder で使われている SBCL を対象にしています。

### AtCoder での使い方

`ac-lisp` コマンドを使うと、問題のサンプル取得、ライブラリの展開、コンパイルと
テスト、提出をターミナルから行えます。SBCL、Python 3、
[online-judge-tools](https://github.com/online-judge-tools/oj) が必要です。
例えば uv を使う場合:

```sh
uv tool install --python 3.13 --with setuptools online-judge-tools
ln -s /path/to/ac-library-lisp/bin/ac-lisp ~/.local/bin/ac-lisp
```

`~/.local/bin` を PATH に含めてください。シンボリックリンクは、このリポジトリの
expander とライブラリを参照します。

```sh
ac-lisp new https://atcoder.jp/contests/practice2/tasks/practice2_a
cd practice2_a
# main.lisp を編集
ac-lisp test
ac-lisp submit
```

`new URL [DIR]` は問題 URL とサンプルを保存し、既存ディレクトリは上書きしません。
`test [DIR]` は展開したコードを SBCL でコンパイルし、サンプルを実行します。
`submit [DIR]` はテスト後に `oj` を呼び出し、確認を経て提出します。言語は
コンテストの一覧から `SBCL` を選択し、必要なら `--language ID` で指定できます。

AtCoder のログインには Turnstile があるため、通常の `oj login` が失敗する場合が
あります。ブラウザで先にログインし、そのプロファイルのセッションを取り込めます。
Firefox、LibreWolf、Edge、Chrome、Chromium、Brave、Opera、Opera GX、Vivaldi に対応しています。

```sh
ac-lisp login --browser edge --profile ~/.config/microsoft-edge/Default
# Firefox の場合: ac-lisp login --browser firefox --profile ~/.mozilla/firefox/YOUR_PROFILE
ac-lisp login --check
```

Chromium 系ブラウザでは `browser-cookie3` と、ロック解除されたシステムのキーリングが
必要です。例えば専用環境には次のようにインストールできます。

```sh
uv venv ~/.local/share/ac-lisp/venv
uv pip install --python ~/.local/share/ac-lisp/venv/bin/python 'browser-cookie3==0.20.1'
```

別の Python 環境を使う場合は `browser-cookie3` を導入し、その実行ファイルを
`AC_LISP_PYTHON` で指定してください。セッションを検証してから `oj` の AtCoder 用
Cookie を更新し、他サイトの Cookie は保持します。Firefox と LibreWolf は
`cookies.sqlite` に保存された Cookie が対象で、メモリやセッション復元データにのみ
保持されるセッションは取り込めません。取り込み中は他の `oj` コマンドを
実行しないでください。更新前の変更は検知しますが、最終確認から置換までの間の
書き込みは防げません。

セッション Cookie は認証情報なので、`oj` の Cookie ファイルは他人に公開しないで
ください。終了済みコンテストでは提出時にも Turnstile が必要な場合があり、
[acrust](https://github.com/okaponta/acrust) と同様、CLI だけでは提出できません。
その場合は `ac-lisp copy [DIR]` で展開コードをコピーし、ブラウザの提出画面に貼り付けて
認証してください。コピーには Wayland では `wl-copy`、X11 では `xclip` が必要です。
送信後にエラーが出た場合は、再送前に提出履歴を確認してください。通信エラーでも
提出自体は受理されていることがあります。

手動で展開することもできます。

解答ファイルの先頭に `(acl-include :dsu)` のように使いたいモジュールを書き、

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
```

で展開した `combined.lisp` を提出してください。`(acl-include :all)` で全モジュールを展開します。

`acl-include` はトップレベルに、それだけで 1 行に書いてください。他のフォームの中、`'` や `#+` などのリーダー記号の直後、コメントや文字列の中にある `acl-include` は展開されません（前の 2 つの場合は警告が表示されます）。詳しいルールは [`document_en/expander.md`](document_en/expander.md) にあります。

### C++ 版との違い

* 添字は 0-indexed、区間は半開区間 `[l, r)` で ACL と同じです。
* モノイドは関数で渡します (`(make-segtree n :op #'max :e 0)`)。単位元 `e` / `id` は関数ではなく値です。
* 高速化したい場合は `define-segtree` / `define-lazy-segtree` を使うと、`op` などがインライン展開された専用関数が生成されます (C++ のテンプレートに相当)。
* modint は `[0, mod)` の普通の整数です。`define-modint` で `name+` `name*` `name/` などの関数が作られます。
* 各モジュールの詳しい説明は [`document_en/`](document_en/index.md) にあります。

### テスト

```sh
sbcl --script test/run.lisp
sbcl --script test/expander-test.lisp
python3 test/cli-test.py
```

1つ目は全モジュールをランダム入力で愚直解と比較します。2つ目は expander のテストで、各モジュールを単体で展開しても未定義関数なくコンパイルできること、コメント・文字列・`|...|` シンボル・他のフォームの中や、`'` や `#+` などの直後にある `acl-include` が展開されないことを確認します。
`(asdf:test-system :ac-library)` でもテストを実行でき、失敗するとエラーになります。3つ目は実際の SBCL と模擬 `oj` を使い、サンプルテスト、提出準備、ブラウザのセッション取り込みを検証します。3つとも GitHub Actions で実行されます。

### ライセンス

元の AtCoder Library と同じ [CC0 1.0](LICENSE) です。
