#!/usr/bin/env python3
"""Build data/catalog.json from the curated seed plus public-domain joins.

Inputs (local metadata, not book files):
  data/catalog.json   existing curated rows to preserve
  data/pg_catalog.csv Project Gutenberg metadata export (optional)
  /tmp/ol_pg_map.jsonl  Open Library edition rows with a Gutenberg id (optional)
  /tmp/wd_pg_ol.csv     Wikidata PG id -> OL work id (optional)

Does not fetch ebook files and does not call the Open Library API.
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
PG_PATH = ROOT / "data" / "pg_catalog.csv"
MAP_PATHS = [Path("/tmp/ol_pg_map.jsonl"), Path("/tmp/ol_search_map.jsonl"), Path("/tmp/ol_title_map.jsonl")]
WD_PATH = Path("/tmp/wd_pg_ol.csv")

FORBIDDEN = re.compile(r"\b(pdf|epub|mobi|download|free ebook)\b", re.I)

SUBJECTS = [
    {"slug": "novel", "name": "Novel", "intro": "Longer fiction still in the public domain: social worlds, moral arguments, and plots that have outlasted their first printers. Each card below is a catalog entry, not a file stored here."},
    {"slug": "romance", "name": "Romance", "intro": "Courtship, attachment, and the practical choices around them. These are older novels of feeling and manners, gathered as literature rather than as a modern romance shelf."},
    {"slug": "mystery", "name": "Mystery", "intro": "Cases, clues, and the pleasure of a pattern clicking shut. Holmes and his cousins are here only when the text is clearly public domain, and the links leave this site for Open Library."},
    {"slug": "gothic", "name": "Gothic", "intro": "Dread, old houses, and the uncanny, in the literary sense. Covers, when Open Library has them, are loaded from their cover service. Nothing gothic is stored on this host."},
    {"slug": "adventure", "name": "Adventure", "intro": "Ships, roads, wilderness, and risk. These stories were written for a wide readership and remain in the public domain. Reading happens on Open Library, not on this catalog."},
    {"slug": "childrens-books", "name": "Children's books", "intro": "Tales long passed to young readers, from nursery classics to schoolroom adventures. The catalog itself is written for a general audience looking up a public-domain text."},
    {"slug": "science-fiction", "name": "Science fiction", "intro": "Early speculative fiction about time, invention, and other worlds. The ideas travel; the editions on this shelf are the old ones, not modern retellings."},
    {"slug": "fantasy", "name": "Fantasy", "intro": "Fairy tales, invented countries, and stories that do not pretend the world works only as the census describes it. Each title is public domain, and the reading stays on Open Library."},
    {"slug": "short-stories", "name": "Short stories", "intro": "Tales and collections you can finish in a sitting. Each entry links onward; this site does not keep the text."},
    {"slug": "poetry", "name": "Poetry", "intro": "Poems and collected verse whose wording is in the public domain. A line you remember may live here under its book title, with the full text waiting on Open Library."},
    {"slug": "plays", "name": "Plays", "intro": "Drama meant first for a stage and later for a quiet reader. These scripts are public domain. This page only names them and points to Open Library."},
    {"slug": "philosophy", "name": "Philosophy", "intro": "Meditations, essays, and arguments about how to live and how power behaves. Translations, where the original is not English, are older public-domain English versions."},
    {"slug": "memoir", "name": "Memoir", "intro": "Lives told in the first person, kept as literature and as history. A catalog should say whose voice you are opening, then send you to Open Library to hear it."},
    {"slug": "biography", "name": "Biography", "intro": "Lives written by someone else, in the older public-domain sense of the word: character, work, and the years a person was given. The books are not hosted here."},
    {"slug": "history", "name": "History", "intro": "Chronicles, campaigns, and accounts of how a place changed. These are older histories, public domain as texts, which does not make every sentence in them true."},
    {"slug": "essays", "name": "Essays", "intro": "Shorter arguments and sketches gathered into books. Useful when you want a mind at work without a plot. The copies live on Open Library."},
    {"slug": "humor", "name": "Humor", "intro": "Satire, comic novels, and books that were meant to be read aloud and laughed at. The jokes are old enough to be public domain; the links are current."},
    {"slug": "travel", "name": "Travel", "intro": "Journeys written up by the people who took them, or by careful listeners. Maps are not included. The public-domain narrative is on Open Library."},
    {"slug": "religion", "name": "Religion", "intro": "Scripture, sermons, and reflections from traditions old enough that these particular texts are in the public domain. This shelf does not rank them."},
    {"slug": "science", "name": "Science", "intro": "Natural history, mathematics, and early scientific books written before the modern research article. They are here as public-domain texts, not as current advice."},
    {"slug": "letters", "name": "Letters", "intro": "Correspondence and speeches saved because someone thought the sentences should outlive the postage. Public-domain collections only; reading is on Open Library."},
    {"slug": "literature", "name": "Literature", "intro": "Public-domain writing that did not settle cleanly into a narrower shelf: miscellanies, classics, and books the old catalogs simply called literature. The text is not stored here."},
]

RULES = [
    ("poetry", ("poetry", "poems", "poem", "verse", "sonnets")),
    ("plays", ("plays", "drama", "dramatic", "theatre", "theater")),
    ("short-stories", ("short stories", "short story")),
    ("science-fiction", ("science fiction", "scientific romance", "science-fiction")),
    ("mystery", ("mystery", "detective", "crime", "sherlock")),
    ("gothic", ("gothic", "horror", "ghost stories", "supernatural")),
    ("fantasy", ("fantasy", "fairy tales", "fairy tale", "folklore")),
    ("romance", ("romance", "love stories")),
    ("adventure", ("adventure", "sea stories", "western", "pirates")),
    ("childrens-books", ("children", "juvenile", "nursery")),
    ("philosophy", ("philosoph", "ethics")),
    ("memoir", ("autobiograph", "memoir")),
    ("biography", ("biograph",)),
    ("history", ("history", "historical")),
    ("essays", ("essay",)),
    ("humor", ("humor", "humour", "satire", "comic")),
    ("travel", ("travel", "voyage", "exploration")),
    ("religion", ("religion", "bible", "theolog", "sermon")),
    ("science", ("science", "natural history", "mathematics", "astronomy", "physics", "chemistry")),
    ("letters", ("letters", "correspondence", "speeches")),
    ("novel", ("novel", "fiction")),
]


def norm(s):
    s = (s or "").lower().replace("’", "'").replace("‘", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def slugify(s):
    base = norm(s).replace(" ", "-")
    base = re.sub(r"-+", "-", base).strip("-")
    return (base[:72] or "item").strip("-")


def clean_title(title):
    title = title.replace("\r", " ").replace("\n", " ")
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s*/\s*by\s+.+$", "", title, flags=re.I)
    return title.strip(" .")


def parse_person(seg):
    seg = seg.strip()
    ancient = bool(re.search(r"\b(B\.?\s?C\.?E?\.?|BCE)\b", seg, re.I))
    years = [(int(y), era) for y, era in re.findall(r"(\d{3,4})\??\s*(BCE|BC|B\.C\.?)?", seg, flags=re.I)]
    nums = [(-n if era else n) for n, era in years]
    birth = death = None
    if len(nums) >= 2:
        birth, death = nums[0], nums[1]
    elif len(nums) == 1:
        if re.search(r"\d{3,4}\s*-\s*$", seg):
            birth = nums[0]
        elif re.search(r"-\s*\d{3,4}", seg):
            death = nums[0]
        else:
            birth = nums[0]
    name = re.sub(r",?\s+\d{3,4}\b.*$", "", seg)
    name = re.sub(r",?\s*(BCE|BC|B\.C\.?).*$", "", name, flags=re.I).strip(" ,")
    if "," in name:
        last, rest = name.split(",", 1)
        name = (rest.strip() + " " + last.strip()).strip()
    name = re.sub(r"\s+", " ", name).strip()
    return name, birth, death, ancient or (birth is not None and birth < 500) or (death is not None and death < 500)


def authors_of(raw):
    if not raw:
        return []
    return [parse_person(p) for p in re.split(r";\s*", raw) if p.strip()]


def clearly_pd(authors):
    """Lifetime publications of writers dead by 1928, plus ancient authors.

    A death year of 1928 or earlier means the writer's own books were in print
    before 1929, which is the cautious side of the United States term.
    """
    if not authors:
        return False
    saw = False
    for name, birth, death, ancient in authors:
        if re.search(r"\b(various|anonymous|unknown)\b", name, re.I):
            return False
        if ancient:
            saw = True
            continue
        if death is None or death > 1928:
            return False
        if birth is not None and birth > 1928:
            return False
        saw = True
    return saw


def subjects_for(row):
    blob = " ".join([
        row.get("Bookshelves") or "",
        row.get("Subjects") or "",
        row.get("LoCC") or "",
        row.get("Title") or "",
    ]).lower()
    def has(word):
        return re.search(r"\b" + re.escape(word) + r"\b", blob) is not None
    found = []
    for slug, keys in RULES:
        if any(has(k) for k in keys):
            if slug == "novel" and any(s in found for s in ("poetry", "plays", "short-stories")):
                continue
            if slug == "science" and "science-fiction" in found:
                continue
            if slug == "biography" and "memoir" in found:
                continue
            found.append(slug)
        if len(found) >= 3:
            break
    return found or ["literature"]



def author_intro(name, birth, death, titles):
    if birth and death:
        span = f"{birth}–{death}"
    elif death:
        span = f"died {death}"
    elif birth:
        span = f"born {birth}"
    else:
        span = "dates earlier than this catalog tries to pin down"
    n = len(titles)
    shown = titles[:3]
    if len(shown) == 1:
        examples = shown[0]
    elif len(shown) == 2:
        examples = f"{shown[0]} and {shown[1]}"
    else:
        examples = f"{shown[0]}, {shown[1]}, and {shown[2]}"
    word = "title" if n == 1 else "titles"
    return (
        f"{name} ({span}) is represented here by {n} public-domain {word}, including {examples}. "
        f"This page is a shelf list: the books are read on Open Library, not stored here."
    )


def load_maps():
    by_pg = defaultdict(list)
    for path in MAP_PATHS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rec["explicit"] = path.name != "ol_title_map.jsonl"
                for pg in rec.get("pg") or []:
                    try:
                        by_pg[str(int(pg))].append(rec)
                    except ValueError:
                        continue
    if WD_PATH.exists():
        with WD_PATH.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pg = str(int(row["pg"]))
                ol = row["ol"].strip()
                if re.fullmatch(r"OL\d+W", ol):
                    by_pg[pg].append({"pg": [pg], "work": f"/works/{ol}", "cover": None, "ocaid": None, "title": None, "wikidata": True})
    return by_pg


def title_score(pg_title, rec):
    score = 0.0
    if rec.get("cover"):
        score += 2
    if rec.get("ocaid"):
        score += 1
    a = set(norm(pg_title).split()) - {"the", "a", "an", "of", "and"}
    b = set(norm(rec.get("title") or "").split())
    if a and b:
        score += 4 * len(a & b) / len(a)
    if rec.get("wikidata") and not rec.get("title"):
        score += 0.5
    if rec.get("explicit", True):
        score += 12
    return score


def best_rec(cands, title):
    if not cands:
        return None
    return max(cands, key=lambda r: title_score(title, r))


def safe_ocaid(value):
    if not value or not isinstance(value, str):
        return None
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,160}", value):
        return value
    return None


def main():
    existing = json.loads(CATALOG_PATH.read_text())
    by_pg = load_maps()
    existing_books = {str(b["gutenberg"]): b for b in existing["books"]}
    existing_authors = {norm(a["name"]): a for a in existing["authors"]}

    pg_rows = {}
    if PG_PATH.exists():
        with PG_PATH.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["Type"] != "Text":
                    continue
                lang = (row["Language"] or "").split(";")[0].strip().lower()
                if lang != "en":
                    continue
                pg_rows[str(int(row["Text#"]))] = row

    chosen = []
    seen_pg = set()

    def add_existing(b):
        pg = str(b["gutenberg"])
        if pg in seen_pg:
            return
        seen_pg.add(pg)
        rec = dict(b)
        rec["featured"] = bool(b.get("featured"))
        rec["pd"] = True
        row = pg_rows.get(pg)
        if row and not rec.get("author_death"):
            people = authors_of(row.get("Authors") or "")
            if people:
                rec["author_birth"] = people[0][1]
                rec["author_death"] = people[0][2]
        if rec.get("year") == 1800:
            rec["year"] = None
        rec.pop("history", None)
        if not (rec.get("blurb") or "").strip():
            rec["blurb"] = ""
        chosen.append(rec)

    for b in existing["books"]:
        add_existing(b)

    # New books: PG row clearly PD and we have an OL work.
    order = sorted(pg_rows, key=lambda i: int(i))
    for pg in order:
        if pg in seen_pg:
            continue
        row = pg_rows[pg]
        authors = authors_of(row["Authors"] or "")
        if not clearly_pd(authors):
            continue
        if pg not in by_pg:
            continue
        title = clean_title(row["Title"] or "")
        if len(title) < 2 or FORBIDDEN.search(title):
            continue
        person = next((a for a in authors if a[0] and not re.search(r"\b(various|anonymous|unknown)\b", a[0], re.I)), None)
        if not person:
            continue
        name, birth, death, _ancient = person
        if not name or FORBIDDEN.search(name) or "atulit" in name.lower():
            continue
        hit = best_rec(by_pg[pg], title)
        if not hit:
            continue
        work = hit["work"]
        ol_id = work.rsplit("/", 1)[-1]
        if not re.fullmatch(r"OL\d+W", ol_id):
            continue
        subs = subjects_for(row)
        slug = slugify(title)
        if ol_id.lower() in slug:
            slug = slug.replace(ol_id.lower(), "").strip("-") or slugify(title)
        author_slug = slugify(name)
        ocaid = safe_ocaid(hit.get("ocaid"))
        book = {
            "slug": slug,
            "title": title,
            "author": author_slug,
            "year": None,
            "gutenberg": int(pg),
            "subjects": subs,
            "blurb": "",
            "author_name": name,
            "author_birth": birth,
            "author_death": death,
            "ol_id": ol_id,
            "ol_key": f"/works/{ol_id}",
            "cover_i": hit.get("cover"),
            "ia": ocaid,
            "gutenberg_url": f"https://www.gutenberg.org/ebooks/{int(pg)}",
            "ol_url": f"https://openlibrary.org/works/{ol_id}",
            "read_url": f"https://openlibrary.org/borrow/ia/{ocaid}" if ocaid else None,
            "pd": True,
            "featured": False,
        }
        m = re.search(r"\((\d{4})\)\s*$", title)
        if m and 1400 <= int(m.group(1)) <= 1928:
            book["year"] = int(m.group(1))
        if not book["year"]:
            years = [r.get("year") for r in by_pg[pg] if isinstance(r.get("year"), int) and 1400 <= r["year"] <= 1928 and r["year"] != 1800]
            if years:
                book["year"] = max(set(years), key=years.count)
        if book.get("year") == 1800:
            book["year"] = None
        book["blurb"] = ""
        chosen.append(book)
        seen_pg.add(pg)

    # Unique slugs; keep curated slugs stable.
    used_slugs = set()
    for b in chosen:
        if b.get("featured"):
            used_slugs.add(b["slug"])
    for b in chosen:
        if b.get("featured"):
            continue
        base = b["slug"] or "book"
        slug = base
        n = 2
        while slug in used_slugs:
            slug = f"{base}-{n}"
            n += 1
            if n > 50:
                slug = f"{base}-g{b['gutenberg']}"
                break
        b["slug"] = slug
        used_slugs.add(slug)
        if FORBIDDEN.search(b["blurb"]) or "atulit" in b["blurb"].lower():
            raise SystemExit("bad blurb")

    # Authors
    books_by_author = defaultdict(list)
    for b in chosen:
        books_by_author[b["author"]].append(b)

    authors_out = []
    seen_author = set()
    # curated authors that still have books, original order
    for a in existing["authors"]:
        if a["slug"] in books_by_author and a["slug"] not in seen_author:
            authors_out.append({"slug": a["slug"], "name": a["name"], "intro": a["intro"]})
            seen_author.add(a["slug"])
    # map normalized curated names onto books that slugified differently
    # If a new book slugified to a new slug but the name matches a curated author, reattach.
    curated_by_norm = {norm(a["name"]): a for a in existing["authors"]}
    reassigned = []
    for b in chosen:
        if b.get("featured"):
            continue
        hit = curated_by_norm.get(norm(b.get("author_name") or ""))
        if hit and b["author"] != hit["slug"]:
            b["author"] = hit["slug"]
            reassigned.append(b["slug"])
    if reassigned:
        books_by_author = defaultdict(list)
        for b in chosen:
            books_by_author[b["author"]].append(b)
        authors_out = []
        seen_author = set()
        for a in existing["authors"]:
            if a["slug"] in books_by_author:
                authors_out.append({"slug": a["slug"], "name": a["name"], "intro": a["intro"]})
                seen_author.add(a["slug"])

    new_author_slugs = [s for s in books_by_author if s not in seen_author]
    # name from first book
    new_authors = []
    for slug in new_author_slugs:
        sample = books_by_author[slug][0]
        name = sample.get("author_name") or slug
        titles = [b["title"] for b in sorted(books_by_author[slug], key=lambda b: b["title"].lower())]
        intro = author_intro(name, sample.get("author_birth"), sample.get("author_death"), titles)
        new_authors.append((name.lower(), {"slug": slug, "name": name, "intro": intro}))
    for _, a in sorted(new_authors, key=lambda t: t[0]):
        authors_out.append(a)

    # Subjects actually used
    used_subjects = set()
    for b in chosen:
        for s in b["subjects"]:
            used_subjects.add(s)
    subjects_out = [s for s in SUBJECTS if s["slug"] in used_subjects]

    # Strip helper fields not needed, but keep author_name etc. build ignores extras.
    # Remove author_birth/death from books? Harmless. Keep catalog smaller by dropping them.
    for a in authors_out:
        for b in books_by_author.get(a["slug"], []):
            if b.get("author_birth") or b.get("author_death"):
                if b.get("author_birth"):
                    a["birth"] = b.get("author_birth")
                if b.get("author_death"):
                    a["death"] = b.get("author_death")
                break
    books_out = []
    for b in chosen:
        books_out.append({k: v for k, v in b.items() if k != "author_name" or True})

    # author slug must exist
    author_slugs = {a["slug"] for a in authors_out}
    missing = [b["slug"] for b in books_out if b["author"] not in author_slugs]
    if missing:
        raise SystemExit(f"books missing authors: {missing[:5]}")

    catalog = {
        "brand": "Where to Read",
        "subjects": subjects_out,
        "authors": authors_out,
        "books": books_out,
    }
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print(f"books {len(books_out)} authors {len(authors_out)} subjects {len(subjects_out)} featured {sum(1 for b in books_out if b.get('featured'))}")


if __name__ == "__main__":
    main()
