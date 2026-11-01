(defpackage :ac-library
  (:use :cl)
  (:nicknames :acl)
  (:export #:acl-include

           #:make-dsu #:dsu-merge #:dsu-same #:dsu-leader #:dsu-size #:dsu-groups

           #:make-fenwick-tree #:fenwick-tree-add #:fenwick-tree-sum

           #:make-segtree #:segtree-set #:segtree-get #:segtree-prod #:segtree-all-prod
           #:segtree-max-right #:segtree-min-left #:define-segtree

           #:make-lazy-segtree #:lazy-segtree-set #:lazy-segtree-get #:lazy-segtree-prod
           #:lazy-segtree-all-prod #:lazy-segtree-apply #:lazy-segtree-apply-at
           #:lazy-segtree-max-right #:lazy-segtree-min-left #:define-lazy-segtree

           #:suffix-array #:lcp-array #:z-algorithm

           #:pow-mod #:inv-mod #:crt #:floor-sum

           #:define-modint #:define-dynamic-modint
           #:modint998244353 #:modint998244353+ #:modint998244353- #:modint998244353*
           #:modint998244353/ #:modint998244353-pow #:modint998244353-inv #:modint998244353-mod
           #:modint1000000007 #:modint1000000007+ #:modint1000000007- #:modint1000000007*
           #:modint1000000007/ #:modint1000000007-pow #:modint1000000007-inv #:modint1000000007-mod
           #:modint #:modint+ #:modint- #:modint* #:modint/ #:modint-pow #:modint-inv
           #:modint-mod #:modint-set-mod #:*modint-modulus*

           #:convolution #:convolution-ll

           #:make-mf-graph #:mf-graph-add-edge #:mf-graph-flow #:mf-graph-min-cut
           #:mf-graph-get-edge #:mf-graph-edges #:mf-graph-change-edge
           #:mf-edge-from #:mf-edge-to #:mf-edge-cap #:mf-edge-flow

           #:make-mcf-graph #:mcf-graph-add-edge #:mcf-graph-flow #:mcf-graph-slope
           #:mcf-graph-get-edge #:mcf-graph-edges
           #:mcf-edge-from #:mcf-edge-to #:mcf-edge-cap #:mcf-edge-flow #:mcf-edge-cost

           #:make-scc-graph #:scc-graph-add-edge #:scc-graph-scc

           #:make-two-sat #:two-sat-add-clause #:two-sat-satisfiable #:two-sat-answer))

(in-package :ac-library)

(defmacro acl-include (&rest modules)
  (declare (ignore modules))
  nil)
