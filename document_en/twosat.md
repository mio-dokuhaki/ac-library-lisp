# 2-SAT (`:twosat`)

```lisp
(let ((ts (make-two-sat 2)))
  (two-sat-add-clause ts 0 t 1 t)
  (two-sat-add-clause ts 0 nil 1 nil)
  (when (two-sat-satisfiable ts)
    (two-sat-answer ts)))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-two-sat n)` | `n` boolean variables `x_0 … x_{n-1}`. | O(n) |
| `(two-sat-add-clause ts i f j g)` | Adds the clause `(x_i = f) ∨ (x_j = g)`; `f` and `g` are generalized booleans. | amortized O(1) |
| `(two-sat-satisfiable ts)` | `t` if some assignment satisfies every clause, otherwise `nil`. | O(n + m) |
| `(two-sat-answer ts)` | Vector of `t` / `nil` with a satisfying assignment from the last successful `two-sat-satisfiable`. | O(n) |
