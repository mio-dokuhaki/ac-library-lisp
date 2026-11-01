# Convolution (`:convolution`)

| Function | Description | Complexity |
| --- | --- | --- |
| `(convolution a b &optional (m 998244353))` | `c[k] = Σ_{i+j=k} a[i] b[j] mod m`. `m` must be a prime with `2^c \| m - 1` for `2^c >= |a| + |b| - 1`, and `m < 2^31`. Returns a fixnum vector of length `|a| + |b| - 1` (empty if either input is empty). | O((n + m) log(n + m)) |
| `(convolution-ll a b)` | Exact convolution of integer sequences. The result must fit in a signed 64-bit integer, as in ACL. Returns a simple-vector. | O((n + m) log(n + m)) |

Inputs may be any sequences of integers; values are reduced modulo `m` first, so negative
numbers are allowed. Small inputs (`min(|a|, |b|) <= 60`) use the naive algorithm.

```lisp
(convolution #(1 2 3 4) #(5 6 7 8 9))
(convolution-ll #(-1000000000 2) #(3 1000000000))
```
