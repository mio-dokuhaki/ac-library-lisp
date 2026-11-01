# MinCostFlow (`:mincostflow`)

Primal-dual algorithm with Dijkstra. Capacities and costs are non-negative integers.

```lisp
(let ((g (make-mcf-graph 3)))
  (mcf-graph-add-edge g 0 1 2 1)
  (mcf-graph-add-edge g 1 2 2 1)
  (mcf-graph-add-edge g 0 2 1 5)
  (mcf-graph-flow g 0 2))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-mcf-graph n)` | Graph with `n` vertices. | O(n) |
| `(mcf-graph-add-edge g from to cap cost)` | Adds an edge and returns its index. `0 <= cap`, `0 <= cost`. | amortized O(1) |
| `(mcf-graph-flow g s t &optional limit)` | Sends as much flow as possible (at most `limit`) at minimum cost. Returns `(values flow cost)`. | O(F (n + m) log(n + m)) |
| `(mcf-graph-slope g s t &optional limit)` | The cost function as a list of breakpoints `(flow . cost)`, starting with `(0 . 0)`; consecutive slopes are strictly increasing. | same as above |
| `(mcf-graph-get-edge g i)` | Copy of edge `i` as an `mcf-edge`. | O(1) |
| `(mcf-graph-edges g)` | List of copies of all edges. | O(m) |

`mcf-edge` accessors: `mcf-edge-from`, `mcf-edge-to`, `mcf-edge-cap`, `mcf-edge-flow`,
`mcf-edge-cost`.

As in ACL, `mcf-graph-flow` and `mcf-graph-slope` should be called at most once per graph if
you rely on the reported cost; the flow stored on edges is updated by each call.
