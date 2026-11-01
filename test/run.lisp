(require :asdf)

(let ((root (merge-pathnames "../" (make-pathname :name nil :type nil :defaults *load-truename*))))
  (push (truename root) asdf:*central-registry*))

(asdf:load-system :ac-library)
(asdf:load-system :ac-library/test)

(sb-ext:exit :code (if (uiop:symbol-call :ac-library-test :run-all) 0 1))
