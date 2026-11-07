import http.cookiejar
import os
from pathlib import Path
import subprocess
import tempfile


class ImportProblem(Exception):
    pass


def save_validated(cookies):
    base = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    jar_path = base / 'online-judge-tools' / 'cookie.jar'
    jar_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if jar_path.is_symlink():
        raise ImportProblem('refusing to replace a symlinked cookie jar')
    jar = http.cookiejar.LWPCookieJar(str(jar_path))
    if jar_path.exists():
        jar.load(ignore_discard=True, ignore_expires=True)
    for cookie in list(jar):
        if cookie.domain.lstrip('.') == 'atcoder.jp':
            jar.clear(cookie.domain, cookie.path, cookie.name)
    for cookie in cookies:
        jar.set_cookie(cookie)
    fd, temporary = tempfile.mkstemp(prefix='.cookie-', dir=jar_path.parent)
    try:
        os.close(fd)
        jar.save(temporary, ignore_discard=True, ignore_expires=True)
        os.chmod(temporary, 0o600)
        result = subprocess.run(['oj', '--cookie', temporary, 'login',
                                 'https://atcoder.jp/', '--check'], check=False)
        if result.returncode != 0:
            raise ImportProblem('AtCoder rejected the browser session; the existing cookie jar was not changed')
        os.chmod(temporary, 0o600)
        os.replace(temporary, jar_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
