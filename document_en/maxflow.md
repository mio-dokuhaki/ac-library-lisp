# MaxFlow (`:maxflow`)

Dinic's algorithm. Capacities are arbitrary non-negative integers.

```lisp
(let ((g (make-mf-graph 4)))
  (mf-graph-add-edge g 0 1 3)
  (mf-graph-add-edge g 1 3 2)
  (mf-graph-add-edge g 0 2 2)
  (mf-graph-add-edge g 2 3 3)
  (mf-graph-flow g 0 3))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-mf-graph n)` | Graph with `n` vertices and no edges. | O(n) |
| `(mf-graph-add-edge g from to cap)` | Adds an edge and returns its index (0, 1, 2, …). | amortized O(1) |
| `(mf-graph-flow g s t &optional limit)` | Pushes flow from `s` to `t` (at most `limit`, unlimited when omitted) and returns the amount. Can be called repeatedly. `s ≠ t`. | O(n² m) in general, O(min(n^(2/3) m, m^(3/2))) for unit capacities |
| `(mf-graph-min-cut g s)` | After `mf-graph-flow`, a vector whose element `v` is `t` when `v` is reachable from `s` in the residual graph. | O(n + m) |
| `(mf-graph-get-edge g i)` | Current state of edge `i` as an `mf-edge`. | O(1) |
| `(mf-graph-edges g)` | List of all edges as `mf-edge` structures. | O(m) |
| `(mf-graph-change-edge g i new-cap new-flow)` | Sets the capacity and flow of edge `i`. `0 <= new-flow <= new-cap`. | O(1) |

`mf-edge` accessors: `mf-edge-from`, `mf-edge-to`, `mf-edge-cap`, `mf-edge-flow`.

The search is iterative, so long paths do not overflow the control stack. The flow on each
edge may differ from the C++ version; the total flow and the minimum cut are the same.
