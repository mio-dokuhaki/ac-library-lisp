# Math (`:math`)

| Function | Description | Complexity |
| --- | --- | --- |
| `(pow-mod x n m)` | `x^n mod m`. `0 <= n`, `1 <= m`. `x` may be negative. | O(log n) |
| `(inv-mod x m)` | `y` in `[0, m)` with `x * y ≡ 1 (mod m)`. Requires `gcd(x, m) = 1`. | O(log m) |
| `(crt r m)` | Chinese remainder theorem for sequences `r` and `m` of equal length. Returns `(values y z)` where the solutions are exactly `x ≡ y (mod z)` with `0 <= y < z = lcm(m)`, or `(values 0 0)` if there is no solution. For empty input returns `(values 0 1)`. | O(k log lcm) |
| `(floor-sum n m a b)` | `Σ_{i=0}^{n-1} floor((a*i + b) / m)`. `0 <= n`, `1 <= m`. | O(log m) |

Arguments may be arbitrarily large integers.

```lisp
(crt '(2 3) '(3 5))
(floor-sum 4 10 6 3)
```
