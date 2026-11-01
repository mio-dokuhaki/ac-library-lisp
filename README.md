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
```

The first command checks every module against brute-force implementations on random inputs.
The second checks the expander: each module expanded on its own must compile with no undefined
references, and `acl-include` written inside comments, strings or `|...|` symbols must be
ignored. The unit tests can also be run with `(asdf:test-system :ac-library)`, which signals an
error when a test fails. Both scripts run on GitHub Actions.

## License

[CC0 1.0](LICENSE), the same as the original AtCoder Library.

---

## 日本語

[AtCoder Library (ACL)](https://github.com/atcoder/ac-library) を Common Lisp に移植したライブラリです。
C++ と Python は使わず、ソースを1ファイルにまとめる expander も Common Lisp で書かれています。
AtCoder で使われている SBCL を対象にしています。

### AtCoder での使い方

解答ファイルの先頭に `(acl-include :dsu)` のように使いたいモジュールを書き、

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
```

で展開した `combined.lisp` を提出してください。`(acl-include :all)` で全モジュールを展開します。

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
```

1つ目は全モジュールをランダム入力で愚直解と比較します。2つ目は expander のテストで、各モジュールを単体で展開しても未定義関数なくコンパイルできること、コメント・文字列・`|...|` シンボルの中の `acl-include` が無視されることを確認します。
`(asdf:test-system :ac-library)` でもテストを実行でき、失敗するとエラーになります。どちらも GitHub Actions で実行されます。

### ライセンス

元の AtCoder Library と同じ [CC0 1.0](LICENSE) です。
