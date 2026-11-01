(in-package :ac-library)

(defstruct (dsu (:constructor %make-dsu (n parent-or-size))
                (:conc-name %dsu-)
                (:copier nil))
  (n 0 :type fixnum)
  (parent-or-size (%make-index-vector 0) :type %index-vector))

(defun make-dsu (n)
  (assert (<= 0 n))
  (%make-dsu n (%make-index-vector n -1)))

(defun dsu-leader (d a)
  (let ((p (%dsu-parent-or-size d)))
    (assert (and (<= 0 a) (< a (%dsu-n d))))
    (let ((r a))
      (loop while (>= (aref p r) 0) do (setf r (aref p r)))
      (loop while (/= a r)
            do (let ((next (aref p a)))
                 (setf (aref p a) r
                       a next)))
      r)))

(defun dsu-merge (d a b)
  (let ((x (dsu-leader d a))
        (y (dsu-leader d b))
        (p (%dsu-parent-or-size d)))
    (if (= x y)
        x
        (progn
          (when (< (- (aref p x)) (- (aref p y)))
            (rotatef x y))
          (incf (aref p x) (aref p y))
          (setf (aref p y) x)
          x))))

(defun dsu-same (d a b)
  (= (dsu-leader d a) (dsu-leader d b)))

(defun dsu-size (d a)
  (- (aref (%dsu-parent-or-size d) (dsu-leader d a))))

(defun dsu-groups (d)
  (let* ((n (%dsu-n d))
         (result (make-array n :initial-element nil)))
    (loop for i from (1- n) downto 0
          do (push i (svref result (dsu-leader d i))))
    (loop for g across result
          when g collect g)))
