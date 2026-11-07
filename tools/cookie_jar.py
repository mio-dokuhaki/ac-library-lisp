import http.cookiejar
import os
from pathlib import Path
import subprocess
import sys
import tempfile


class ImportProblem(Exception):
    pass


def oj_cookie_path():
    if sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    elif os.name == 'posix':
        base = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    else:
        raise ImportProblem('browser cookie import is supported on Unix systems only')
    return base / 'online-judge-tools' / 'cookie.jar'


def snapshot_jar(path):
    if path.is_symlink():
        raise ImportProblem('refusing to replace a symlinked cookie jar')
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def save_validated(cookies):
    jar_path = oj_cookie_path()
    jar_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    original = snapshot_jar(jar_path)
    fd, temporary = tempfile.mkstemp(prefix='.cookie-', dir=jar_path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            if original is not None:
                stream.write(original)
        jar = http.cookiejar.LWPCookieJar(temporary)
        if original is not None:
            jar.load(ignore_discard=True, ignore_expires=True)
        for cookie in list(jar):
            if cookie.domain.lstrip('.') == 'atcoder.jp':
                jar.clear(cookie.domain, cookie.path, cookie.name)
        for cookie in cookies:
            jar.set_cookie(cookie)
        jar.save(ignore_discard=True, ignore_expires=True)
        os.chmod(temporary, 0o600)
        result = subprocess.run(['oj', '--cookie', temporary, 'login',
                                 'https://atcoder.jp/', '--check'], check=False)
        if result.returncode != 0:
            raise ImportProblem('AtCoder rejected the browser session; the existing cookie jar was not changed')
        if snapshot_jar(jar_path) != original:
            raise ImportProblem('cookie jar changed during authentication; import was not saved')
        os.chmod(temporary, 0o600)
        os.replace(temporary, jar_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
