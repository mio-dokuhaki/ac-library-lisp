#!/usr/bin/env python3
import http.cookiejar
from pathlib import Path
import sqlite3
import sys
import time
from cookie_jar import ImportProblem, save_validated


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
    selected = []
    origin = sessions[0][7]
    for host, path, name, value, expiry, secure, http_only, attributes in rows:
        if attributes != origin:
            continue
        selected.append(http.cookiejar.Cookie(
            version=0, name=name, value=value, port=None, port_specified=False,
            domain=host, domain_specified=host.startswith('.'),
            domain_initial_dot=host.startswith('.'), path=path, path_specified=True,
            secure=bool(secure), expires=expiry // scale,
            discard=False, comment=None, comment_url=None,
            rest={'HttpOnly': None} if http_only else {}, rfc2109=False))
    save_validated(selected)
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
