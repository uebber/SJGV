#!/usr/bin/env python3
"""
Cached, content-aware fetcher for index source documents.

Built because the ad-hoc sourcing pass of 17 Aug 2026 hit the same four walls
repeatedly, and every one of them is mechanical:

  1. PDFs must be downloaded and run through `pdftotext -layout`. A fetch tool
     that converts to markdown returns the compressed object stream instead.
  2. Several issuer sites (Greatland, Genesis, Vault, LSE) return 403 to a
     default user-agent and 200 to a browser one.
  3. Some issuers publish resource and reserve tables as PNG images. No text
     extraction of any kind reaches those — they need a visual read, and the
     tool's job is to say so loudly rather than silently return nothing.
  4. When an issuer blocks entirely, the same announcement is usually mirrored
     on listcorp / investegate / the ASX announcements platform.

Everything lands in .cache/ keyed by URL hash, so re-runs are free and the raw
artifact stays on disk for audit.

    python tools/fetch.py <url> [<url> ...]
    python tools/fetch.py --registry              # fetch everything in sources.json
    python tools/fetch.py --registry --ticker CYL
    python tools/fetch.py <url> --refresh         # ignore cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
REGISTRY = Path(__file__).resolve().parent / "sources.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/pdf,image/png,*/*",
    "Accept-Language": "en-AU,en;q=0.9",
}
TIMEOUT = 60


def slug(url: str) -> str:
    h = hashlib.sha256(url.encode()).hexdigest()[:12]
    tail = re.sub(r"[^a-zA-Z0-9]+", "-", url.rsplit("/", 1)[-1])[:48].strip("-")
    return f"{h}-{tail}" if tail else h


def _sniff(head: bytes, content_type: str) -> str:
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8\xff"):
        return "image"
    if "pdf" in content_type:
        return "pdf"
    if "image" in content_type:
        return "image"
    return "html"


def _strip_html(raw: bytes) -> str:
    """Tag-stripped text. Issuers increasingly render R&R tables as inline HTML
    (Genesis, Evolution), so the flattened text is genuinely useful — but script
    and style bodies have to go first or they swamp the output."""
    import html as htmlmod
    t = raw.decode("utf-8", errors="ignore")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = htmlmod.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


# Match the FILENAME only, never the whole URL — an issuer whose domain contains
# "resources" (roxresources.com.au) would otherwise return every logo on the page.
_TABLE_HINT = re.compile(r"(resource|reserve|mre|ore[-_]?res|jorc)[-_]?(table|estimate|statement)"
                         r"|(table)[-_]?(resource|reserve)", re.I)
_NOT_A_TABLE = re.compile(r"logo|cover|icon|hero|banner|header|footer|avatar|thumb|"
                          r"photo|map|chart|gdpr|cookie|badge|award|sponsor", re.I)


def _image_urls(raw: bytes, base: str) -> list[str]:
    """Image sources that look like a published resource or reserve TABLE.

    Greatland publishes both its group tables as PNGs, so without this the tool
    reports nothing on a page that plainly has the data. But the hint has to be
    read off the filename and paired with an exclusion list, or the result is
    every logo and stock photo on the site.
    """
    t = raw.decode("utf-8", errors="ignore")
    out = []
    for m in re.finditer(r'src="([^"]+\.(?:png|jpg|jpeg))"', t, re.I):
        u = m.group(1)
        fname = urllib.parse.urlparse(u).path.rsplit("/", 1)[-1]
        if _TABLE_HINT.search(fname) and not _NOT_A_TABLE.search(fname):
            out.append(urllib.parse.urljoin(base, u))
    return sorted(set(out))


def fetch(url: str, refresh: bool = False) -> dict:
    """Fetch one URL into the cache. Returns a manifest entry."""
    CACHE.mkdir(exist_ok=True)
    base = CACHE / slug(url)
    meta_path = base.with_suffix(".json")

    if meta_path.exists() and not refresh:
        meta = json.loads(meta_path.read_text())
        meta["cached"] = True
        return meta

    meta: dict = {"url": url, "cached": False}
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            meta["status"] = resp.status
            meta["final_url"] = resp.geturl()
    except urllib.error.HTTPError as e:
        meta.update(status=e.code, error=f"HTTP {e.code}",
                    hint=_hint(e.code, url))
        meta_path.write_text(json.dumps(meta, indent=2))
        return meta
    except Exception as e:
        meta.update(status=None, error=str(e)[:200])
        meta_path.write_text(json.dumps(meta, indent=2))
        return meta

    kind = _sniff(raw[:8], ctype)
    meta["kind"] = kind
    meta["bytes"] = len(raw)

    blob = base.with_suffix({"pdf": ".pdf", "image": ".png", "html": ".html"}[kind])
    blob.write_bytes(raw)
    meta["blob"] = str(blob.relative_to(ROOT))

    if kind == "pdf":
        txt = base.with_suffix(".txt")
        if shutil.which("pdftotext"):
            subprocess.run(["pdftotext", "-layout", str(blob), str(txt)],
                           capture_output=True, timeout=180)
            if txt.exists():
                meta["text"] = str(txt.relative_to(ROOT))
                meta["lines"] = txt.read_text(errors="ignore").count("\n")
        else:
            meta["error"] = "pdftotext not installed — `brew install poppler`"
    elif kind == "html":
        txt = base.with_suffix(".txt")
        txt.write_text(_strip_html(raw))
        meta["text"] = str(txt.relative_to(ROOT))
        meta["lines"] = 1
        imgs = _image_urls(raw, meta.get("final_url", url))
        if imgs:
            meta["table_images"] = imgs
            meta["needs_visual_read"] = True
    elif kind == "image":
        meta["needs_visual_read"] = True

    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def _hint(code: int, url: str) -> str:
    if code == 403:
        return ("issuer blocks automated access — try the listcorp / investegate / "
                "ASX announcements mirror of the same release")
    if code == 404:
        return "path moved — fetch the site root and grep its nav for the R&R link"
    if code == 429:
        return "rate limited — retry after a pause"
    return ""


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {"targets": []}
    return json.loads(REGISTRY.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch and cache index source documents.")
    ap.add_argument("urls", nargs="*", help="URLs to fetch")
    ap.add_argument("--registry", action="store_true", help="fetch everything in tools/sources.json")
    ap.add_argument("--ticker", help="with --registry, limit to one ticker")
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    args = ap.parse_args()

    targets: list[tuple[str, str, str]] = [("-", "-", u) for u in args.urls]
    if args.registry:
        for t in load_registry().get("targets", []):
            if args.ticker and t["ticker"] != args.ticker:
                continue
            for doc in t["documents"]:
                targets.append((t["ticker"], doc.get("for", "-"), doc["url"]))

    if not targets:
        ap.error("give URLs or --registry")

    ok = warn = fail = 0
    print(f"{'TICK':<6}{'FOR':<22}{'KIND':<7}{'STATUS':<8}{'ARTIFACT'}")
    print("─" * 108)
    for ticker, purpose, url in targets:
        m = fetch(url, refresh=args.refresh)
        if m.get("error"):
            fail += 1
            print(f"{ticker:<6}{purpose[:21]:<22}{'-':<7}{str(m.get('status') or 'ERR'):<8}"
                  f"{m['error']}")
            if m.get("hint"):
                print(f"{'':<35}→ {m['hint']}")
            continue
        tag = "cache" if m.get("cached") else "ok"
        artifact = m.get("text") or m.get("blob", "")
        if m.get("needs_visual_read"):
            warn += 1
            tag = "VISUAL"
        else:
            ok += 1
        print(f"{ticker:<6}{purpose[:21]:<22}{m.get('kind', '?'):<7}{tag:<8}{artifact}")
        for img in m.get("table_images", []):
            print(f"{'':<35}IMAGE TABLE → {img}")

    print(f"\n{ok} ok, {warn} need a visual read, {fail} failed")
    if warn:
        print("Tables published as images cannot be text-extracted. Fetch the image "
              "URL above, then read it directly.")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
