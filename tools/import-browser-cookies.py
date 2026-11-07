#!/usr/bin/env python3
import http.cookiejar
from pathlib import Path
import sqlite3
import sys
import time

from cookie_jar import ImportProblem, save_validated

BROWSERS = {'edge', 'chrome', 'chromium', 'brave', 'opera', 'opera_gx', 'vivaldi'}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in BROWSERS:
        raise ImportProblem('expected a supported browser and profile path')
    browser, profile = sys.argv[1:]
    path = Path(profile).expanduser().resolve(strict=True)
    if path.is_dir():
        candidates = [p for p in (path / 'Cookies', path / 'Network' / 'Cookies') if p.is_file()]
        if len(candidates) != 1:
            raise ImportProblem('profile must contain exactly one Cookies database')
        path = candidates[0]
    if not path.is_file():
        raise ImportProblem('Cookies database not found')
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=10) as db:
        columns = {row[1] for row in db.execute('PRAGMA table_info(cookies)')}
        partition = 'top_frame_site_key' if 'top_frame_site_key' in columns else "''"
        rows = db.execute(
            f"SELECT name, expires_utc, {partition} FROM cookies "
            "WHERE host_key IN ('atcoder.jp', '.atcoder.jp')"
        ).fetchall()
    now_nt = (int(time.time()) + 11644473600) * 1000000
    active = [row for row in rows if row[1] == 0 or row[1] > now_nt]
    if any(row[2] for row in active):
        raise ImportProblem('partitioned AtCoder cookies cannot be imported safely')
    if sum(row[0] == 'REVEL_SESSION' for row in active) != 1:
        raise ImportProblem('expected exactly one unexpired AtCoder session cookie')
    try:
        import browser_cookie3
    except ImportError:
        raise ImportProblem('browser-cookie3 is required for this browser') from None
    try:
        jar = getattr(browser_cookie3, browser)(cookie_file=str(path), domain_name='atcoder.jp')
    except Exception:
        raise ImportProblem('cannot read browser cookies; check the profile and unlocked keyring') from None
    now = time.time()
    cookies = [cookie for cookie in jar if cookie.domain in ('atcoder.jp', '.atcoder.jp')
               and (cookie.expires is None or cookie.expires > now)]
    if sum(cookie.name == 'REVEL_SESSION' and bool(cookie.value) for cookie in cookies) != 1:
        raise ImportProblem('expected exactly one readable AtCoder session cookie')
    save_validated(cookies)
    print('Imported AtCoder cookies into the online-judge-tools cookie jar.')


if __name__ == '__main__':
    try:
        main()
    except ImportProblem as exc:
        print(f'Browser cookie import failed: {exc}', file=sys.stderr)
        sys.exit(1)
    except (OSError, sqlite3.Error, ValueError, http.cookiejar.LoadError) as exc:
        print(f'Browser cookie import failed ({type(exc).__name__}). Check the profile and cookie jar.', file=sys.stderr)
        sys.exit(1)
