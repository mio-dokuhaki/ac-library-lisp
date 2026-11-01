(acl-include :string)

(defun main ()
  (let* ((s (read-line))
         (n (length s))
         (lcp (lcp-array s (suffix-array s))))
    (format t "~D~%" (- (floor (* n (1+ n)) 2) (reduce #'+ lcp)))))

(main)
