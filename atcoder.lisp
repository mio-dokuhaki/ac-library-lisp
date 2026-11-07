(require :asdf)
(require :sb-posix)

(defpackage :ac-lisp-cli (:use :cl))
(in-package :ac-lisp-cli)

(defparameter *root* (make-pathname :name nil :type nil :defaults *load-truename*))

(defun fail (control &rest arguments)
  (error "~?" control arguments))

(defun usage ()
  (format t "Usage: ac-lisp COMMAND [ARGS]~%~%
  new URL [DIR]            Create a problem directory and download samples~%
  login [--check]          Log in or check status without opening a browser~%
  login --firefox PROFILE Import an existing Firefox login and check it~%
  login --browser NAME --profile PATH  Import a browser login and check it~%
  test [DIR]               Expand, compile and test the solution (default: .)~%
  copy [DIR]               Copy expanded code to the clipboard~%
  submit [DIR] [--language ID]  Test and submit (default language: SBCL)~%"))

(defun run (program arguments)
  (let ((process (handler-case
                     (sb-ext:run-program program arguments :search t :input t :output t :error t)
                   (error (e) (fail "cannot run ~A: ~A" program e)))))
    (unless (and (eq (sb-ext:process-status process) :exited)
                 (zerop (sb-ext:process-exit-code process)))
      (fail "~A failed (status ~A)" program (sb-ext:process-exit-code process)))))

(defun valid-component-p (s)
  (and (plusp (length s))
       (every (lambda (c) (or (and (char>= c #\a) (char<= c #\z))
                              (and (char>= c #\0) (char<= c #\9))
                              (member c '(#\_ #\-)))) s)))

(defun canonical-url (url)
  (let* ((trimmed (string-right-trim "/" url))
         (prefix "https://atcoder.jp/contests/"))
    (unless (and (<= (length prefix) (length trimmed))
                 (string= prefix trimmed :end2 (length prefix)))
      (fail "expected an AtCoder task URL: ~A" url))
    (let ((parts (uiop:split-string (subseq trimmed (length prefix)) :separator "/")))
      (unless (and (= (length parts) 3) (string= (second parts) "tasks")
                   (valid-component-p (first parts)) (valid-component-p (third parts)))
        (fail "expected an AtCoder task URL: ~A" url))
      (values trimmed (third parts)))))

(defun directory-path (dir)
  (uiop:ensure-directory-pathname (merge-pathnames (uiop:ensure-directory-pathname dir)
                                                   (uiop:getcwd))))

(defun problem-file (dir name)
  (merge-pathnames name (directory-path dir)))

(defun write-new-file (path text)
  (with-open-file (stream path :direction :output :if-exists :error
                               :if-does-not-exist :create :external-format :utf-8)
    (write-string text stream)))

(defun new-problem (url requested-dir)
  (multiple-value-bind (url task) (canonical-url url)
    (let ((dir (directory-path (or requested-dir task))))
      (handler-case (sb-posix:mkdir (namestring dir) #o755)
        (sb-posix:syscall-error (e) (fail "cannot create ~A: ~A" dir e)))
      (write-new-file (merge-pathnames "problem-url.txt" dir) (format nil "~A~%" url))
      (write-new-file (merge-pathnames "main.lisp" dir)
                      (format nil "(acl-include :dsu)~%~%(defun main ()~%  )~%~%(main)~%"))
      (format t "Created ~A~%" dir)
      (finish-output)
      (handler-case
          (run "oj" (list "download" url "--directory" (namestring (merge-pathnames "test/" dir))))
        (error (e)
          (fail "~A~%Files remain in ~A. Retry with: oj download ~A -d ~A" e dir url
                (merge-pathnames "test/" dir)))))))

(defun read-problem-url (dir)
  (with-open-file (stream (problem-file dir "problem-url.txt") :direction :input :external-format :utf-8)
    (let ((line (read-line stream nil nil)))
      (unless (and line (null (read-line stream nil nil)))
        (fail "problem-url.txt must contain exactly one URL"))
      (canonical-url line))))

(defun shell-quote (s)
  (with-output-to-string (out)
    (write-char #\' out)
    (loop for c across s do
      (if (char= c #\') (write-string "'\\''" out) (write-char c out)))
    (write-char #\' out)))

(defun expand-source (dir temp)
  (let ((source (problem-file dir "main.lisp"))
        (expanded (merge-pathnames "main.lisp" temp)))
    (unless (probe-file source) (fail "solution not found: ~A" source))
    (run "sbcl" (list "--script" (namestring (merge-pathnames "expander.lisp" *root*))
                      (namestring source) "-o" (namestring expanded)))
    expanded))

(defun compile-source (expanded temp)
  (let* ((fasl (merge-pathnames "main.fasl" temp))
         (form (format nil "(multiple-value-bind (output warnings failure) (compile-file ~S :output-file ~S) (declare (ignore warnings)) (unless (and output (not failure)) (sb-ext:exit :code 1)))"
                       (namestring expanded) (namestring fasl))))
    (run "sbcl" (list "--noinform" "--no-userinit" "--no-sysinit" "--disable-debugger"
                      "--non-interactive" "--eval" form))
    fasl))

(defun regular-file-p (path)
  (handler-case
      (sb-posix:s-isreg (sb-posix:stat-mode (sb-posix:stat (namestring path))))
    (sb-posix:syscall-error () nil)))

(defun validate-samples (cases)
  (let ((stream (handler-case (sb-posix:opendir (namestring cases))
                  (sb-posix:syscall-error () (fail "sample directory not found: ~A" cases))))
        (count 0))
    (unwind-protect
         (loop for entry = (sb-posix:readdir stream)
               until (sb-alien:null-alien entry)
               for name = (sb-posix:dirent-name entry)
               for length = (length name)
               when (and (> length 3) (string= ".in" name :start2 (- length 3)))
                 do (let* ((stem (subseq name 0 (- length 3)))
                           (input (make-pathname :name stem :type "in" :defaults cases))
                           (output (make-pathname :name stem :type "out" :defaults cases)))
                      (unless (regular-file-p input) (fail "sample input is not a regular file: ~A" input))
                      (unless (regular-file-p output) (fail "sample output is missing or not a regular file: ~A" output))
                      (incf count)))
      (sb-posix:closedir stream))
    (when (zerop count) (fail "no sample input files found in ~A" cases))))

(defun test-solution (dir expanded temp)
  (let ((cases (problem-file dir "test/")))
    (validate-samples cases)
    (let ((fasl (compile-source expanded temp)))
      (run "oj" (list "test" "--directory" (namestring cases) "--command"
                      (format nil "sbcl --script ~A" (shell-quote (namestring fasl))))))))

(defun call-with-temp (function)
  (let* ((base (or (uiop:getenv "TMPDIR") "/tmp"))
         (template (namestring (merge-pathnames "ac-lisp-XXXXXX" (directory-path base))))
         (temp (pathname (concatenate 'string (sb-posix:mkdtemp template) "/"))))
    (unwind-protect (funcall function temp)
      (uiop:delete-directory-tree temp :validate t :if-does-not-exist :ignore))))

(defun copy-solution (dir)
  (call-with-temp
   (lambda (temp)
     (let* ((source (expand-source dir temp))
            (wayland (uiop:getenv "WAYLAND_DISPLAY"))
            (program (if (and wayland (plusp (length wayland))) "wl-copy" "xclip"))
            (args (if (string= program "xclip") '("-selection" "clipboard") nil)))
       (with-open-file (input source :direction :input :element-type '(unsigned-byte 8))
         (let ((process (handler-case
                            (sb-ext:run-program program args :search t :input input :output t :error t)
                          (error (e) (fail "cannot run ~A: ~A" program e)))))
           (unless (and (eq (sb-ext:process-status process) :exited)
                        (zerop (sb-ext:process-exit-code process)))
             (fail "~A failed (status ~A)" program (sb-ext:process-exit-code process)))))
       (format t "Copied expanded solution to the clipboard.~%")))))

(defun parse-submit (args)
  (let ((dir nil) (language "SBCL"))
    (loop while args for arg = (pop args) do
      (cond ((string= arg "--language")
             (unless args (fail "--language requires an ID or name"))
             (setf language (pop args))
             (when (or (zerop (length language)) (char= (char language 0) #\-))
               (fail "invalid language")))
            ((and (plusp (length arg)) (char= (char arg 0) #\-)) (fail "unknown option: ~A" arg))
            (dir (fail "too many arguments"))
            (t (setf dir arg))))
    (values (or dir ".") language)))

(defun browser-python ()
  (let* ((data (or (uiop:getenv "XDG_DATA_HOME")
                   (namestring (merge-pathnames ".local/share/" (user-homedir-pathname)))))
         (python (merge-pathnames "ac-lisp/venv/bin/python" (directory-path data))))
    (or (uiop:getenv "AC_LISP_PYTHON")
        (and (probe-file python) (namestring python))
        "python3")))

(defun browser-login (browser profile)
  (if (member browser '("firefox" "librewolf") :test #'string=)
      (run "python3" (list (namestring (merge-pathnames "tools/import-firefox-cookies.py" *root*)) profile))
      (run (browser-python) (list (namestring (merge-pathnames "tools/import-browser-cookies.py" *root*))
                                  browser profile))))

(defun main (args)
  (let ((command (pop args)))
    (cond
      ((or (null command) (member command '("-h" "--help" "help") :test #'string=)) (usage))
      ((string= command "new")
       (unless (<= 1 (length args) 2) (fail "new requires URL [DIR]"))
       (new-problem (first args) (second args)))
      ((string= command "login")
       (cond ((or (null args) (equal args '("--check")))
              (run "oj" (append (list "login" "https://atcoder.jp/" "--use-browser" "never") args)))
             ((and (= (length args) 2) (string= (first args) "--firefox"))
              (run "python3" (list (namestring (merge-pathnames "tools/import-firefox-cookies.py" *root*))
                                   (second args))))
             ((and (= (length args) 4) (string= (first args) "--browser")
                   (string= (third args) "--profile"))
              (browser-login (second args) (fourth args)))
             (t (fail "login accepts --check, --firefox PROFILE, or --browser NAME --profile PATH"))))
      ((string= command "test")
       (unless (<= (length args) 1) (fail "test accepts [DIR]"))
       (let ((dir (or (first args) ".")))
         (call-with-temp (lambda (temp) (test-solution dir (expand-source dir temp) temp)))))
      ((string= command "copy")
       (unless (<= (length args) 1) (fail "copy accepts [DIR]"))
       (copy-solution (or (first args) ".")))
      ((string= command "submit")
       (multiple-value-bind (dir language) (parse-submit args)
         (let ((url (read-problem-url dir)))
           (call-with-temp
            (lambda (temp)
              (let ((expanded (expand-source dir temp)))
                (test-solution dir expanded temp)
                (format t "Submitting ~A as ~A~%" url language)
                (finish-output)
                (handler-case
                    (run "oj" (list "submit" "--no-open" "--no-guess" "--language" language
                                    url (namestring expanded)))
                  (error (e)
                    (fail "~A~%If the request may have reached AtCoder, check your submissions before retrying." e)))))))))
      (t (fail "unknown command: ~A" command)))))

(handler-case (main (rest sb-ext:*posix-argv*))
  (error (e) (format *error-output* "ac-lisp: ~A~%" e) (sb-ext:exit :code 1)))
