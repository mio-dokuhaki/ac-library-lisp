# String (`:string`)

The input `s` may be a string or any sequence. Sequences of integers, characters or strings
are compared with the natural ordering of their elements.

| Function | Description | Complexity |
| --- | --- | --- |
| `(suffix-array s)` | Suffix array of `s`: start positions of the suffixes in sorted order. | O(n log n) for general sequences, O(n + max code) for strings |
| `(suffix-array s upper)` | `s` is a sequence of integers in `[0, upper]`. Uses SA-IS directly. | O(n + upper) |
| `(lcp-array s sa)` | Vector of length `n - 1`; element `i` is the LCP of suffixes `sa[i]` and `sa[i+1]`. | O(n) |
| `(z-algorithm s)` | Vector of length `n`; element `i` is the LCP of `s` and `s[i..]`. | O(n) |

All results are `(simple-array fixnum (*))`.

```lisp
(let* ((s "missisippi")
       (sa (suffix-array s)))
  (values sa (lcp-array s sa) (z-algorithm s)))
```
