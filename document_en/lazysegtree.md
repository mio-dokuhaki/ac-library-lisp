# Lazy Segment Tree (`:lazysegtree`)

Segment tree with range updates, for a monoid `(S, op, e)` and a set `F` of maps `S → S` that
contains the identity `id` and is closed under composition.

* `(mapping f x)` returns `f(x)`.
* `(composition f g)` returns `f ∘ g` (apply `g` first, then `f`).
* `mapping` must be a monoid homomorphism: `f(op(x, y)) = op(f(x), f(y))`.

The identity `id` is compared with `eql` to skip pushing identity tags, so passing a number or
a single shared object is fastest.

## Generic interface

```lisp
(let ((seg (make-lazy-segtree #(1 2 3 4) :op #'max :e most-negative-fixnum
                                         :mapping #'+ :composition #'+ :id 0)))
  (lazy-segtree-apply seg 0 2 10)
  (lazy-segtree-prod seg 0 4))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-lazy-segtree n-or-vector :op :e :mapping :composition :id)` | Build from a length or initial values. | O(n) |
| `(lazy-segtree-set seg p x)` | `a[p] = x`. | O(log n) |
| `(lazy-segtree-get seg p)` | `a[p]`. | O(log n) |
| `(lazy-segtree-prod seg l r)` | `op(a[l], …, a[r-1])`. | O(log n) |
| `(lazy-segtree-all-prod seg)` | Product of the whole array. | O(1) |
| `(lazy-segtree-apply-at seg p f)` | `a[p] = f(a[p])`. | O(log n) |
| `(lazy-segtree-apply seg l r f)` | `a[i] = f(a[i])` for all `l <= i < r`. | O(log n) |
| `(lazy-segtree-max-right seg l g)` | Same as `segtree-max-right`. | O(log n) |
| `(lazy-segtree-min-left seg r g)` | Same as `segtree-min-left`. | O(log n) |

## Specialized interface

```lisp
(define-lazy-segtree add-max
  :op #'max :e most-negative-fixnum
  :mapping #'+ :composition #'+ :id 0)
```

defines `make-ADD-MAX`, `ADD-MAX-set`, `ADD-MAX-get`, `ADD-MAX-prod`, `ADD-MAX-all-prod`,
`ADD-MAX-apply-at`, `ADD-MAX-apply`, `ADD-MAX-max-right` and `ADD-MAX-min-left`, with `op`,
`mapping` and `composition` inlined. This is several times faster than the generic interface
in tight loops. `examples/practice2_k.lisp` shows a complete solution.
