#!/usr/bin/env python3
"""Resource freshness radar for NATTD's nattd.json.

Extracts every verifiable resource (Flatpak app ids and http(s) URLs) from
nattd.json and checks whether it still exists. Designed to run in CI as a
NON-BLOCKING radar: results go to a markdown report and, optionally, to a
GitHub issue that is auto-created on dead resources and auto-closed when
everything is healthy again.

Classification:
    ok      - resource responds successfully (redirects are followed)
    dead    - HTTP 404/410 confirmed by both HEAD and ranged GET
    botwall - 403 from a host known to block scripted clients (resource presumed alive)
    unknown - anything else (timeouts, 5xx, other 4xx) - not asserted dead

Usage:
    python check_freshness.py                          # print report
    python check_freshness.py --report report.md       # also write file
    python check_freshness.py --github                 # + GitHub issue (CI)
    python check_freshness.py --strict                 # exit 2 when dead found

Stdlib only - no third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

UA = "Mozilla/5.0 (X11; Linux x86_64) nattd-freshness/1.0 (resource checker)"
FLATHUB_APPSTREAM_V2 = "https://flathub.org/api/v2/appstream"
FLATPAK_RE = re.compile(r"flatpak install (?:-[^\s]+ )*flathub ([A-Za-z0-9._-]+)")
# URLs may contain shell substitutions with spaces, e.g. $(rpm -E %fedora).
# The substitution pattern must be tried BEFORE the char class, otherwise the
# greedy class eats "$(rpm" and the regex happily ends the match at the space.
URL_RE = re.compile(r"https?://(?:\$\([^)]*\)|[^\s\"'<>|])+")
# Shell substitutions that appear inside URLs, mapped to checkable values.
URL_SHELL_VARS = {
    "$(rpm -E %fedora)": "44",  # rpmfusion release RPMs etc.
}
# URL "directory" endings: these are repo baseurls, not downloadable files -
# a 404 on the directory listing is normal, so only host liveness is checked.
DIR_URL_CHARS = "/"

# Hosts answering 403 to scripted clients even for perfectly alive resources.
BOT_WALL_HOSTS = {"medium.com", "rpmfusion.org"}

DEAD_CODES = {404, 410}


# ---------------------------------------------------------------- extraction


def _walk_strings(obj: Any):
    """Yield every string value found anywhere in a nested JSON structure."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def normalize_url(url: str) -> str:
    """Prepare a URL from a command string for an HTTP check."""
    for var, value in URL_SHELL_VARS.items():
        url = url.replace(var, value)
    url = url.rstrip(".,;)")
    # A URL that still contains an unmapped shell substitution cannot be
    # checked verbatim (checking it would produce a false 404) - skip it.
    return url if url.startswith(("http://", "https://")) and "$(" not in url else ""


def extract_flatpak_ids(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Map every Flatpak app id referenced in additional_apps to the app ids
    (and install types) that reference it.
    """
    refs: Dict[str, List[str]] = {}
    apps = data.get("additional_apps", {})
    for category, cat in apps.items():
        for app_id, app in (cat.get("apps") or {}).items():
            strings: List[str] = []
            if isinstance(app.get("command"), str):
                strings.append(app["command"])
            for it in (app.get("installation_types") or {}).values():
                cmd = it.get("command")
                if isinstance(cmd, str):
                    strings.append(cmd)
                elif isinstance(cmd, list):
                    strings.extend(c for c in cmd if isinstance(c, str))
            for s in strings:
                for fid in FLATPAK_RE.findall(s):
                    ref = f"{category}/{app_id}"
                    if fid not in refs:
                        refs[fid] = []
                    if ref not in refs[fid]:
                        refs[fid].append(ref)
    return refs


def extract_urls(data: Dict[str, Any]) -> Set[str]:
    """Collect every unique, checkable http(s) URL used anywhere in nattd.json."""
    urls: Set[str] = set()
    for s in _walk_strings(data):
        for m in URL_RE.finditer(s):
            normalized = normalize_url(m.group(0))
            if normalized:
                urls.add(normalized)
    return urls


# ----------------------------------------------------------------- checking


def classify_status(code: int, host: str) -> Tuple[str, str]:
    """Map an HTTP status to (ok|dead|botwall|unknown, detail)."""
    if 200 <= code < 400:
        return "ok", f"HTTP {code}"
    if code in DEAD_CODES:
        return "dead", f"HTTP {code}"
    if code == 403 and any(host == h or host.endswith("." + h) for h in BOT_WALL_HOSTS):
        return "botwall", "HTTP 403 (bot wall - presumed alive)"
    return "unknown", f"HTTP {code}"


def check_url(url: str, timeout: int = 12) -> Tuple[str, str]:
    """Check a URL: HEAD first, ranged GET as fallback/retry. Never raises."""
    # Repo baseurls (ending in /) are directory listings - servers commonly
    # return 404/403 there. Checking the host root is a fair liveness probe.
    if url.endswith(DIR_URL_CHARS) or url.endswith(".repo"):
        parts = urllib.parse.urlsplit(url)
        url = f"{parts.scheme}://{parts.netloc}/"
    host = urllib.parse.urlsplit(url).netloc.split(":")[0]
    last: Tuple[str, str] = ("unknown", "no attempt")
    for method, extra in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
        headers = {"User-Agent": UA, **extra}
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return classify_status(r.status, host)
        except urllib.error.HTTPError as e:
            klass, detail = classify_status(e.code, host)
            if klass == "dead":
                # retry with the other method before declaring it dead
                last = (klass, detail)
                continue
            return klass, detail
        except (urllib.error.URLError, socket.timeout, ConnectionResetError, OSError) as e:
            last = ("unknown", f"connection error: {e}")
    return last


def check_flatpak_id(app_id: str, timeout: int = 10) -> Tuple[str, str]:
    """Check one Flatpak id against Flathub (v2 appstream API). Never raises."""
    try:
        req = urllib.request.Request(
            FLATHUB_APPSTREAM_V2,
            data=json.dumps({"ids": [app_id]}).encode(),
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            if r.status == 200:
                found = json.loads(body) if body else []
                if app_id in found:
                    return "ok", "in Flathub appstream"
                return "dead", "not in Flathub appstream"
            return classify_status(r.status, "flathub.org")
    except urllib.error.HTTPError as e:
        klass, detail = classify_status(e.code, "flathub.org")
        return (klass, detail)
    except (urllib.error.URLError, socket.timeout, ConnectionResetError, OSError) as e:
        return ("unknown", f"connection error: {e}")


# ------------------------------------------------------------------ report


def build_report(
    id_refs: Dict[str, List[str]],
    id_results: Dict[str, Tuple[str, str]],
    urls: List[str],
    url_results: Dict[str, Tuple[str, str]],
) -> Tuple[str, int, int]:
    """Render the markdown report; return (report, dead_count, unknown_count)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# 🧭 Freshness report — {now}", ""]

    dead = unknown = 0

    ok_ids = [i for i, (k, _) in id_results.items() if k == "ok"]
    dead_ids = [i for i, (k, _) in id_results.items() if k == "dead"]
    unk_ids = [(i, d) for i, (k, d) in id_results.items() if k in ("unknown", "botwall")]
    dead += len(dead_ids)
    unknown += len(unk_ids)

    lines.append(
        f"**Flatpak apps:** {len(id_results)} checked — {len(ok_ids)} ok, "
        f"{len(dead_ids)} dead, {len(unk_ids)} unknown"
    )
    for i in sorted(dead_ids):
        lines.append(f"- ❌ `{i}` missing on Flathub (referenced by: {', '.join(id_refs[i])})")
    for i, d in sorted(unk_ids):
        lines.append(f"- ⚠️ `{i}` unknown ({d})")
    lines.append("")

    ok_urls = [u for u, (k, _) in url_results.items() if k == "ok"]
    dead_urls = [u for u, (k, _) in url_results.items() if k == "dead"]
    unk_urls = [(u, d) for u, (k, d) in url_results.items() if k in ("unknown", "botwall")]
    dead += len(dead_urls)
    unknown += len(unk_urls)

    lines.append(
        f"**URLs:** {len(url_results)} checked — {len(ok_urls)} ok, "
        f"{len(dead_urls)} dead, {len(unk_urls)} unknown"
    )
    for u in sorted(dead_urls):
        lines.append(f"- ❌ `{u}`")
    for u, d in sorted(unk_urls):
        lines.append(f"- ⚠️ `{u}` — {d}")
    lines.append("")

    if dead:
        lines.append(f"**Summary:** 🧟 {dead} dead resource(s), {unknown} unknown. Update nattd.json.")
    else:
        lines.append(f"**Summary:** ✅ no dead resources, {unknown} unknown.")

    return "\n".join(lines) + "\n", dead, unknown


# ------------------------------------------------------------------ github


def _gh_request(repo: str, path: str, token: str, method: str = "GET",
                payload: Optional[Dict[str, Any]] = None) -> Tuple[int, Optional[Dict[str, Any]]]:
    url = f"https://api.github.com/repos/{repo}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, None


def github_update(dead: int, report: str) -> Optional[str]:
    """Create/comment/close the stale-links issue. Returns what happened."""
    repo = __import__("os").environ.get("GITHUB_REPOSITORY", "")
    token = __import__("os").environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        print("freshness: GITHUB_REPOSITORY/GITHUB_TOKEN not set - skipping issue update")
        return None

    label = "stale-links"
    _gh_request(repo, "labels", token, "POST",
                {"name": label, "color": "D93F0B", "description": "Dead/missing resources in nattd.json"})
    # 201 created / 422 already exists - both fine
    _code, issues = _gh_request(repo, f"issues?labels={label}&state=open", token)
    open_issues: List[Dict[str, Any]] = issues if isinstance(issues, list) else []

    if dead > 0:
        title = f"🧟 Freshness radar: {dead} dead resource(s) in nattd.json"
        if open_issues:
            number = open_issues[0]["number"]
            _gh_request(repo, f"issues/{number}/comments", token, "POST",
                        {"body": f"Updated report ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}):\n\n{report}"})
            print(f"freshness: commented on existing issue #{number}")
            return "commented"
        _code, created = _gh_request(repo, "issues", token, "POST",
                                     {"title": title, "body": report, "labels": [label]})
        if _code == 201 and created:
            print(f"freshness: created issue #{created['number']}")
            return "created"
        print(f"freshness: could not create issue (HTTP {_code}) - token may lack issues:write")
        return None

    if dead == 0 and open_issues:
        num = open_issues[0]["number"]
        _gh_request(repo, f"issues/{num}/comments", token, "POST",
                    {"body": "✅ All resources healthy again - closing. Report:\n\n" + report})
        _gh_request(repo, f"issues/{num}", token, "PATCH", {"state": "closed"})
        print(f"freshness: all healthy - closed issue #{num}")
        return "closed"
    return None


# -------------------------------------------------------------------- main


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="NATTD resource freshness radar")
    parser.add_argument("--nattd", default="nattd.json", help="path to nattd.json")
    parser.add_argument("--report", default="", help="write markdown report to this file")
    parser.add_argument("--github", action="store_true",
                        help="create/comment/close the stale-links issue (needs GITHUB_TOKEN)")
    parser.add_argument("--strict", action="store_true", help="exit 2 when dead resources found")
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args(argv)

    with open(args.nattd) as f:
        data = json.load(f)

    id_refs = extract_flatpak_ids(data)
    urls = sorted(extract_urls(data))
    print(f"freshness: checking {len(id_refs)} flatpak ids and {len(urls)} URLs...")

    with ThreadPoolExecutor(max_workers=8) as ex:
        fut_urls = {ex.submit(check_url, u, args.timeout): u for u in urls}
        fut_ids = {ex.submit(check_flatpak_id, i, args.timeout): i for i in id_refs}
        url_results = {fut_urls[f]: f.result() for f in as_completed(fut_urls)}
        id_results = {fut_ids[f]: f.result() for f in as_completed(fut_ids)}

    report, dead, unknown = build_report(id_refs, id_results, urls, url_results)
    print(report)

    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
        print(f"freshness: report written to {args.report}")

    if args.github:
        github_update(dead, report)

    if args.strict and dead:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
