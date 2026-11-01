# Fenwick Tree (`:fenwicktree`)

Point add and range sum. Works with any numbers (integers never overflow in Common Lisp).

```lisp
(let ((fw (make-fenwick-tree 10)))
  (fenwick-tree-add fw 3 5)
  (fenwick-tree-sum fw 0 4))
```

| Function | Description | Complexity |
| --- | --- | --- |
| `(make-fenwick-tree n)` | Array `a_0 … a_{n-1}` of zeros. | O(n) |
| `(fenwick-tree-add fw p x)` | `a[p] += x`. `0 <= p < n`. | O(log n) |
| `(fenwick-tree-sum fw l r)` | `a[l] + … + a[r-1]`. `0 <= l <= r <= n`. | O(log n) |
