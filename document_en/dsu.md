# DSU (`:dsu`)

Disjoint set union (union-find) with union by size and path compression.

```lisp
(let ((d (make-dsu 5)))
  (dsu-merge d 0 1)
  (dsu-same d 0 1)
  (dsu-size d 0)
  (dsu-groups d))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-dsu n)` | `n` singleton sets `0 … n-1`. `0 <= n`. | O(n) |
| `(dsu-merge d a b)` | Joins the sets of `a` and `b`; returns the new leader. | amortized O(α(n)) |
| `(dsu-same d a b)` | `t` when `a` and `b` are in the same set. | amortized O(α(n)) |
| `(dsu-leader d a)` | Representative of the set containing `a`. | amortized O(α(n)) |
| `(dsu-size d a)` | Size of the set containing `a`. | amortized O(α(n)) |
| `(dsu-groups d)` | List of all sets, each a list of vertices in increasing order. | O(n) |

Constraints: `0 <= a, b < n`.
