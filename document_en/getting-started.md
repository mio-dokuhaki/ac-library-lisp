# Other workflows

### Manual expansion

To try the expander without changing a problem solution, create a new scratch
directory. If `acl-demo` already exists, choose a different name:

```sh
mkdir acl-demo && cd acl-demo
```

Save the following demonstration as `main.lisp` in that new directory:

```lisp
(acl-include :dsu)

(let ((d (make-dsu 3)))
  (dsu-merge d 0 1)
  (format t "~A~%" (dsu-same d 0 1)))
```

From that directory, expand it using the path to your checkout. Replace
`/path/to/ac-library-lisp` with the actual checkout path:

```sh
sbcl --script "/path/to/ac-library-lisp/expander.lisp" main.lisp -o combined.lisp
sbcl --script combined.lisp
```

The demonstration prints `T`. To expand a real solution, run the same expansion
command from its problem directory, where `main.lisp` already contains your
solution. `combined.lisp` contains the requested modules and dependencies and
can be submitted. Choose an output name that does not already exist: `-o`
overwrites its target. Use `(acl-include :all)` for every module. Each
`acl-include` must be a top-level form on its own line; see the
[expander guide](expander.md) for the full rules.

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

Run these commands from the repository root:

```sh
sbcl --script test/run.lisp
sbcl --script test/expander-test.lisp
python3 test/cli-test.py
```

These run the library, expander, and CLI tests. The CLI suite uses an `oj` test
double and does not submit. The library suite also runs with
`(asdf:test-system :ac-library)`. All three scripts run on GitHub Actions.

