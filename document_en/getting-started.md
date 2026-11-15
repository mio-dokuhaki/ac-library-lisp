# Other workflows

### Manual expansion

For a standalone submission, include the modules you need:

```lisp
(acl-include :dsu)

(let ((d (make-dsu 3)))
  (dsu-merge d 0 1)
  (format t "~A~%" (dsu-same d 0 1)))
```

Then expand it:

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
sbcl --script combined.lisp
```

`combined.lisp` contains the requested modules and dependencies, ready for
submission. Use `(acl-include :all)` for every module. Each `acl-include` must
be a top-level form on its own line; see the [expander guide](expander.md)
for the full rules.

## Using it as a normal library

Load the ASDF system `ac-library`:

```lisp
(require :asdf)
(push #p"/path/to/ac-library-lisp/" asdf:*central-registry*)
(asdf:load-system :ac-library)
(use-package :ac-library)
```

Here, `acl-include` is a no-op, so the same solution works in the REPL.

## Development

```sh
sbcl --script test/run.lisp
sbcl --script test/expander-test.lisp
python3 test/cli-test.py
```

These run the library, expander, and CLI tests. The CLI suite uses an `oj` test
double and does not submit. The library suite also runs with
`(asdf:test-system :ac-library)`. All three scripts run on GitHub Actions.

