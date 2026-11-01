# SCC (`:scc`)

Strongly connected components of a directed graph (Tarjan's algorithm, iterative).

```lisp
(let ((g (make-scc-graph 4)))
  (scc-graph-add-edge g 0 1)
  (scc-graph-add-edge g 1 0)
  (scc-graph-add-edge g 1 2)
  (scc-graph-scc g))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-scc-graph n)` | Graph with `n` vertices. | O(n) |
| `(scc-graph-add-edge g from to)` | Adds a directed edge. | amortized O(1) |
| `(scc-graph-scc g)` | List of components in topological order: for every edge `u → v`, the component of `u` comes no later than that of `v`. Each component is a list of vertices in increasing order. | O(n + m) |
