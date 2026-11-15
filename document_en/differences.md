# Differences from the C++ library

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

