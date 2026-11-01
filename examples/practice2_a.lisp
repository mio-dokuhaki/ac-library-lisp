(acl-include :dsu)

(defun main ()
  (let* ((n (read))
         (q (read))
         (d (make-dsu n)))
    (dotimes (i q)
      (let ((ty (read)) (u (read)) (v (read)))
        (if (= ty 0)
            (dsu-merge d u v)
            (format t "~D~%" (if (dsu-same d u v) 1 0)))))))

(main)
