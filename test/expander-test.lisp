(require :sb-posix)

(defpackage :ac-library-expander-test
  (:use :cl))

(in-package :ac-library-expander-test)

(defvar *root* (truename (merge-pathnames "../" (make-pathname :name nil :type nil :defaults *load-truename*))))
(defvar *work* (let ((dir (format nil "/tmp/acl-expander-test-~D/" (sb-posix:getpid))))
                 (ensure-directories-exist dir)
                 (pathname dir)))
(defvar *failures* 0)

(defun write-file (path text)
  (with-open-file (out path :direction :output :if-exists :supersede)
    (write-string text out)))

(defun run (args &optional input)
  (let ((output (make-string-output-stream)))
    (let ((process (sb-ext:run-program "sbcl" args
                                       :search t
                                       :input (and input (make-string-input-stream input))
                                       :output output
                                       :error nil)))
      (values (get-output-stream-string output) (sb-ext:process-exit-code process)))))

(defun expand (name source)
  (let ((in (merge-pathnames (format nil "~A.lisp" name) *work*))
        (out (merge-pathnames (format nil "~A-expanded.lisp" name) *work*)))
    (write-file in source)
    (multiple-value-bind (text code)
        (run (list "--script" (namestring (merge-pathnames "expander.lisp" *root*))
                   (namestring in) "-o" (namestring out)))
      (declare (ignore text))
      (unless (zerop code)
        (error "expander failed for ~A" name)))
    out))

(defun report (ok name)
  (format t "~A ~A~%" (if ok "ok  " "FAIL") name)
  (unless ok (incf *failures*)))

(defun compile-problems (file)
  (let ((messages '()))
    (handler-case
        (handler-bind ((warning (lambda (w)
                                  (let ((text (princ-to-string w)))
                                    (when (search "undefined" (string-downcase text))
                                      (push text messages)))
                                  (muffle-warning w))))
          (let ((*error-output* (make-broadcast-stream))
                (*standard-output* (make-broadcast-stream)))
            (multiple-value-bind (output warnings-p failure-p)
                (compile-file file :output-file (merge-pathnames "tmp.fasl" *work*))
              (declare (ignore warnings-p))
              (when (or (null output) failure-p)
                (push "compile-file reported failure" messages)))))
      (error (e)
        (push (format nil "compile-file signaled: ~A" e) messages)))
    messages))

(defun check-standalone-modules ()
  (dolist (module '("dsu" "fenwicktree" "segtree" "lazysegtree" "string" "math" "modint"
                    "convolution" "maxflow" "mincostflow" "scc" "twosat"))
    (let* ((file (expand (format nil "only-~A" module) (format nil "(acl-include :~A)~%" module)))
           (messages (compile-problems file)))
      (report (null messages) (format nil "standalone :~A compiles with no undefined references" module))
      (dolist (m messages) (format t "      ~A~%" m))))
  (let* ((file (expand "broken-source" (format nil "(acl-include :dsu)~%(defun broken () (let ((x)) (1+ x) (unknown-macro-form . 3)))~%")))
         (messages (compile-problems file)))
    (report (not (null messages)) "compile failures are detected")))

(defun check-output (name source expected)
  (let ((file (expand name source)))
    (multiple-value-bind (text code) (run (list "--script" (namestring file)))
      (report (and (zerop code) (string= (string-trim '(#\Newline #\Space) text) expected))
              name)
      (unless (string= (string-trim '(#\Newline #\Space) text) expected)
        (format t "      expected ~S, got ~S~%" expected text)))))

(defun main ()
  (check-standalone-modules)
  (check-output "convolution-ll-standalone"
                (format nil "(acl-include :convolution)~%(let ((a (make-array 100 :initial-element 3)) (b (make-array 100 :initial-element 5))) (princ (aref (convolution-ll a b) 99)))~%")
                "1500")
  (check-output "include-inside-block-comment"
                (format nil "#|~%(acl-include :dsu)~%|#~%(acl-include :dsu)~%(princ (dsu-size (make-dsu 3) 0))~%")
                "1")
  (check-output "include-inside-multiline-string"
                (format nil "(defvar *doc* \"~%(acl-include :dsu)~%\")~%(acl-include :dsu)~%(princ (dsu-same (make-dsu 2) 0 1))~%")
                "NIL")
  (check-output "include-after-character-literals"
                (format nil "(defvar *c* (list #\\\" #\\|))~%(acl-include :math)~%(princ (pow-mod 2 10 1000))~%")
                "24")
  (check-output "include-after-pipe-escaped-symbol"
                (format nil "(defvar |\"| 1)~%(acl-include :dsu)~%(princ (dsu-size (make-dsu 2) 1))~%")
                "1")
  (check-output "include-after-backslash-escaped-symbol"
                (format nil "(defvar a\\\"b 1)~%(acl-include :dsu)~%(princ (dsu-size (make-dsu 2) 1))~%")
                "1")
  (check-output "include-inside-multiline-pipe-symbol"
                (format nil "(defvar |multi~%(acl-include :math)~%line| 1)~%(acl-include :dsu)~%(princ (dsu-same (make-dsu 2) 1 1))~%")
                "T")
  (check-output "nested-include-is-not-expanded"
                (format nil "(acl-include :dsu)~%(defvar *x* (list~%(acl-include :math)~%))~%(princ (list (dsu-size (make-dsu 2) 0) (fboundp 'pow-mod)))~%")
                "(1 NIL)")
  (check-output "parens-in-literals-do-not-hide-include"
                (format nil "(defvar *c* (list #\\( \"((\" '|(|))~%(acl-include :dsu)~%(princ (dsu-size (make-dsu 2) 1))~%")
                "1")
  (format t "~D failures~%" *failures*)
  (sb-ext:exit :code (if (zerop *failures*) 0 1)))

(main)
