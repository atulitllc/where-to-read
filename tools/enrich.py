#!/usr/bin/env python3
"""Modest Open Library lookups for known titles, plus Gutenberg landing-page checks.

Does not fetch ebook files. Does not download covers. One search per book.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed.json"
OUT = ROOT / "data" / "catalog.json"
UA = "WhereToReadCatalog/1.0 (personal static catalog; modest known-title lookups; +https://openlibrary.org)"

def get(url, limit=120000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html"})
    with urllib.request.urlopen(req, timeout=40) as r:
        ctype = r.headers.get("Content-Type", "")
        body = r.read(limit)
    return ctype, body

def norm(s):
    s = s.lower()
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())

def main():
    seed = json.loads(SEED.read_text())
    authors = {a["slug"]: a for a in seed["authors"]}
    books_out = []
    for i, b in enumerate(seed["books"]):
        author = authors[b["author"]]
        title = b["title"]
        print(f"[{i+1}/{len(seed['books'])}] {title}", flush=True)
        # Gutenberg landing page only
        gurl = f"https://www.gutenberg.org/ebooks/{b['gutenberg']}"
        ctype, raw = get(gurl)
        if "text/html" not in ctype and "application/xhtml" not in ctype:
            raise SystemExit(f"Gutenberg URL was not an HTML landing page: {gurl} {ctype}")
        html = raw.decode("utf-8", "replace")
        if re.search(r"\.(epub|mobi|txt)(\?|\b)", gurl):
            raise SystemExit("refusing file url")
        page_title = ""
        m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
        if m:
            page_title = re.sub(r"\s+", " ", m.group(1)).strip()
        nt = norm(title)
        nh = norm(page_title)
        # allow small title differences (Moby-Dick vs Moby Dick, Adventures vs The Adventures)
        key_words = [w for w in nt.split() if w not in {"the", "a", "an", "of", "and"}]
        missing = [w for w in key_words if w not in nh]
        if missing and "dr" in missing:
            missing = [w for w in missing if w != "dr"]
        if len(missing) > 1:
            raise SystemExit(f"Gutenberg title mismatch for {gurl}: {page_title!r} missing {missing}")
        time.sleep(0.35)
        q = urllib.parse.urlencode({
            "title": title,
            "author": author["name"],
            "limit": 5,
            "fields": "key,title,author_name,cover_i,ia,first_publish_year,edition_count",
        })
        ctype, raw = get("https://openlibrary.org/search.json?" + q)
        data = json.loads(raw.decode("utf-8"))
        docs = data.get("docs") or []
        chosen = None
        for d in docs:
            key = d.get("key") or ""
            if not key.startswith("/works/OL"):
                continue
            dt = norm(d.get("title") or "")
            # prefer close title
            if nt.split()[0] in dt or all(w in dt for w in key_words[:2]):
                chosen = d
                break
        if chosen is None and docs:
            d = docs[0]
            if (d.get("key") or "").startswith("/works/"):
                chosen = d
        if not chosen:
            raise SystemExit(f"No Open Library work for {title}")
        ol_key = chosen["key"]  # /works/OLxxxxW
        ol_id = ol_key.rsplit("/", 1)[-1]
        cover_i = chosen.get("cover_i")
        ia = None
        ias = chosen.get("ia") or []
        if ias:
            ia = ias[0]
        rec = dict(b)
        rec["author_name"] = author["name"]
        rec["ol_id"] = ol_id
        rec["ol_key"] = ol_key
        rec["cover_i"] = cover_i
        rec["ia"] = ia
        rec["gutenberg_url"] = gurl
        rec["ol_url"] = f"https://openlibrary.org{ol_key}"
        rec["read_url"] = f"https://openlibrary.org/borrow/ia/{ia}" if ia else None
        rec["pd"] = True
        rec["gutenberg_page_title"] = page_title
        books_out.append(rec)
        print(f"   OL {ol_id} cover {cover_i} ia {ia} :: {page_title[:80]}", flush=True)
        time.sleep(0.45)
    catalog = {
        "brand": seed["brand"],
        "subjects": seed["subjects"],
        "authors": seed["authors"],
        "books": books_out,
    }
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print("wrote", OUT, "books", len(books_out))

if __name__ == "__main__":
    main()
