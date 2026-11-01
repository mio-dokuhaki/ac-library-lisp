# Segment Tree (`:segtree`)

Segment tree over a monoid `(S, op, e)`: `op` must be associative and `e` must be its identity.

## Generic interface

```lisp
(let ((seg (make-segtree #(5 3 8 1) :op #'max :e most-negative-fixnum)))
  (segtree-set seg 1 10)
  (segtree-prod seg 0 3)
  (segtree-max-right seg 0 (lambda (x) (< x 9))))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-segtree n-or-vector :op op :e e)` | From a length `n` (all `e`) or a sequence of initial values. | O(n) |
| `(segtree-set seg p x)` | `a[p] = x`. | O(log n) |
| `(segtree-get seg p)` | `a[p]`. | O(1) |
| `(segtree-prod seg l r)` | `op(a[l], …, a[r-1])`, or `e` when `l = r`. | O(log n) |
| `(segtree-all-prod seg)` | `op(a[0], …, a[n-1])`. | O(1) |
| `(segtree-max-right seg l f)` | Largest `r` such that `f(op(a[l..r-1]))` is true, assuming `f` is monotone and `f(e)` is true. | O(log n) |
| `(segtree-min-left seg r f)` | Smallest `l` such that `f(op(a[l..r-1]))` is true, under the same assumptions. | O(log n) |

## Specialized interface

`define-segtree` generates a tree whose `op` is inlined into the generated code, like a C++
template instantiation.

```lisp
(define-segtree max-seg :op #'max :e most-negative-fixnum)

(let ((seg (make-max-seg 100)))
  (max-seg-set seg 3 7)
  (max-seg-prod seg 0 10))
```

`(define-segtree name :op op :e e)` defines `make-NAME`, `NAME-set`, `NAME-get`, `NAME-prod`,
`NAME-all-prod`, `NAME-max-right` and `NAME-min-left`, with the same meaning as above. `op` is
any function form such as `#'max` or `(lambda (a b) …)`.
