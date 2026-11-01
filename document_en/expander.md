# Expander

`expander.lisp` turns a solution that uses `acl-include` into one self-contained file for
submission. It replaces ACL's `expander.py` and is written in Common Lisp.

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
```

* A line whose first form is `(acl-include :module ...)` is replaced by the source of those
  modules, their dependencies, the package definition and `(use-package :ac-library)`.
* Module names: `:dsu :fenwicktree :segtree :lazysegtree :string :math :modint :convolution
  :maxflow :mincostflow :scc :twosat`, or `:all`.
* Each module is emitted at most once, even when several `acl-include` lines name it.
* Put `acl-include` before your own `in-package`, if you use one; the expanded code switches to
  `cl-user` after the library.
* Unknown modules or a missing input file produce an error message and exit status 1.

Options:

| Option | Meaning |
| --- | --- |
| `-o FILE` | Write the result to `FILE` (default: standard output). |
| `--lib DIR` | Directory containing the library sources (default: `src/` next to `expander.lisp`). |
