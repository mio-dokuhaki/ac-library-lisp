#!/usr/bin/env python3
import http.cookiejar
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time


class ImportProblem(Exception):
    pass


def main():
    if len(sys.argv) != 2:
        raise ImportProblem('expected a Firefox profile directory')
    database = Path(sys.argv[1]).expanduser().resolve(strict=True) / 'cookies.sqlite'
    uri = database.as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True, timeout=10) as connection:
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
        scale = 1000 if schema_version >= 16 else 1
        rows = connection.execute(
            "SELECT host, path, name, value, expiry, isSecure, isHttpOnly, originAttributes "
            "FROM moz_cookies WHERE host IN ('atcoder.jp', '.atcoder.jp') "
            "AND expiry > ?", (int(time.time()) * scale,)
        ).fetchall()
    sessions = [row for row in rows if row[2] == 'REVEL_SESSION' and row[3]]
    if len(sessions) != 1:
        raise ImportProblem('expected exactly one unexpired AtCoder session cookie')
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
    origin = sessions[0][7]
    for host, path, name, value, expiry, secure, http_only, attributes in rows:
        if attributes != origin:
            continue
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=name, value=value, port=None, port_specified=False,
            domain=host, domain_specified=host.startswith('.'),
            domain_initial_dot=host.startswith('.'), path=path, path_specified=True,
            secure=bool(secure), expires=expiry // scale,
            discard=False, comment=None, comment_url=None,
            rest={'HttpOnly': None} if http_only else {}, rfc2109=False))
    fd, temporary = tempfile.mkstemp(prefix='.cookie-', dir=jar_path.parent)
    try:
        os.close(fd)
        jar.save(temporary, ignore_discard=True, ignore_expires=True)
        os.chmod(temporary, 0o600)
        result = subprocess.run(["oj", "--cookie", temporary, "login", "https://atcoder.jp/", "--check"], check=False)
        if result.returncode != 0:
            raise ImportProblem("AtCoder rejected the Firefox session; the existing cookie jar was not changed")
        os.chmod(temporary, 0o600)
        os.replace(temporary, jar_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Imported AtCoder cookies into the online-judge-tools cookie jar.')


if __name__ == '__main__':
    try:
        main()
    except ImportProblem as exc:
        print(f"Firefox cookie import failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, sqlite3.Error, ValueError, http.cookiejar.LoadError) as exc:
        print(f'Firefox cookie import failed ({type(exc).__name__}). Check the profile and cookie jar.', file=sys.stderr)
        sys.exit(1)
