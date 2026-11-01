# Modint (`:modint`)

A modint is represented as an ordinary integer in `[0, mod)`. The macros below generate a
family of inline functions for one modulus.

## Static modulus

```lisp
(define-modint mint 998244353)

(mint -1)
(mint* (mint+ 3 4) (mint-inv 2))
```

`(define-modint name modulus)` defines:

| Name | Meaning |
| --- | --- |
| type `name` | `(integer 0 (modulus))` |
| `(name x)` | `x mod modulus` for any integer `x` |
| `(name+ a b)`, `(name- a b)`, `(name* a b)` | arithmetic on normalized values |
| `(name/ a b)` | `a * b^-1` |
| `(name-pow a e)` | `a^e`, `0 <= e` |
| `(name-inv a)` | inverse; errors if it does not exist |
| `(name-mod)` | the modulus |

`modint998244353` and `modint1000000007` are predefined, e.g. `modint998244353*`.

## Dynamic modulus

```lisp
(define-dynamic-modint dmint)
(dmint-set-mod 12345)
(dmint* 100 200)
```

`(define-dynamic-modint name &optional (default 998244353))` defines the same functions plus
`(name-set-mod m)` and the special variable `*NAME-MODULUS*`. The predefined dynamic family is
`modint`: `modint-set-mod`, `modint+`, `modint*`, ….

Arguments of `+`, `-`, `*` must already be normalized (in `[0, mod)`); use `(name x)` to
normalize. Inverses exist only when `gcd(a, mod) = 1`.
