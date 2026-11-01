(in-package :ac-library)

(defstruct (scc-graph (:constructor %make-scc-graph (n from to))
                      (:conc-name %scc-)
                      (:copier nil))
  (n 0 :type fixnum)
  from
  to)

(defun make-scc-graph (n)
  (assert (<= 0 n))
  (%make-scc-graph n (%make-growing-vector) (%make-growing-vector)))

(defun scc-graph-add-edge (graph from to)
  (let ((n (%scc-n graph)))
    (assert (and (<= 0 from) (< from n) (<= 0 to) (< to n)))
    (vector-push-extend from (%scc-from graph))
    (vector-push-extend to (%scc-to graph))
    graph))

(defun scc-graph-scc (graph)
  (let ((n (%scc-n graph)))
    (multiple-value-bind (start elist)
        (%csr n (%scc-from graph) (%scc-to graph))
      (multiple-value-bind (num ids) (%scc-ids n start elist)
        (let ((groups (make-array num :initial-element nil)))
          (loop for i from (1- n) downto 0
                do (push i (svref groups (aref ids i))))
          (coerce groups 'list))))))
