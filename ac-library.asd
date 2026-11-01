(defsystem "ac-library"
  :description "AtCoder Library ported to Common Lisp"
  :license "CC0-1.0"
  :version "1.0.0"
  :pathname "src/"
  :serial t
  :components ((:file "package")
               (:file "internal")
               (:file "dsu")
               (:file "fenwicktree")
               (:file "segtree")
               (:file "lazysegtree")
               (:file "string")
               (:file "math")
               (:file "modint")
               (:file "convolution")
               (:file "maxflow")
               (:file "mincostflow")
               (:file "scc")
               (:file "twosat"))
  :in-order-to ((test-op (test-op "ac-library/test"))))

(defsystem "ac-library/test"
  :depends-on ("ac-library")
  :pathname "test/"
  :components ((:file "test"))
  :perform (test-op (o c)
             (unless (uiop:symbol-call :ac-library-test :run-all)
               (error "ac-library test suite failed"))))
