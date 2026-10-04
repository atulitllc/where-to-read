#!/usr/bin/env python3
"""Fail the build if a stock year clause, an old lead, or a subject-heading frame is back.

The patterns below are detectors only. Nothing in this module fills a blurb.
An empty note is allowed. A featured book still needs its handwritten note.
"""
import re
import unicodedata

# Fixed wording from the retired LEADS list and the stock year/shelf sentences.
# Short function words are intentionally not listed; these are the repeated frames.
FORBIDDEN_SUBSTRINGS = (
    "and all this note will claim",
    "one sturdy fact",
    "no need to invent a plot",
    "does not ask this page",
    "The honest line on",
    "Nothing fancier than",
    "The concrete end of",
    "No scene list is required",
    "Where a plot summary would wander",
    "Name the subject as",
    "not a puzzle to be solved here",
    "From the first glance",
    "A plain note on",
    "contributes to its shelf",
    "doing the real work",
    "as narrow as its subject",
    "one subject worth naming",
    "is enough: it is about",
    "The topic inside",
    "answers to the subject",
    "For a first description",
    "The work in hand is",
    "and stops there",
    "the subject it earns",
    "Before any story is guessed",
    "filed by one phrase",
    "The useful fact in",
    "keeps to the subject",
    "does not pretend otherwise",
    "Nothing here retells",
    "best introduced through",
    "keeps its attention on",
    "at catalog length",
    "the subject comes first",
    "The subject line that fits",
    "can be summed up as",
    "and then stop",
    "does its work on the subject",
    "Look past the binding",
    "whose brief is",
    "a later reader brings",
    "The only summary",
    "comes into focus",
    "There is a plain way to say",
    "rather than a plot",
    "No year was invented",
    "was already the one on the book",
    "not one filled in to plug a gap",
    "The printing year we actually have",
    "sits with the title as a real date",
    "The year already recorded is",
    "because that year was already known",
    "The known year is",
    "Leave the date as",
    "which was already there",
    "Beyond the subject, the title contributes the color",
    "is the writer, and the book sits on",
    "sits on the",
    "on the subject of",
    "Another way to place",
    "easier to shelve",
    "The shelf decision for",
    "neighbored with other books",
    "life and the shelf",
    "Nothing below invents",
    "does not need a synopsis",
    "This note stays outside the plot",
    "the life dates and the shelf",
    "Nothing in this paragraph happens inside",
    "the form does the shelving",
    "without a later date being invented",
    "left unrehearsed here",
)

# "{title} is {kind} about {about}." with the old kind vocabulary.
OLD_KIND = (
    r"a book of verse|a play|a collection of short stories|a book of letters|"
    r"a book of essays|a work of philosophy|a memoir|a biography|a travel narrative|"
    r"a science book|a religious work|a humorous book|a mystery|a gothic novel|"
    r"a romance|a science-fiction story|a children's fantasy|a fantasy|"
    r"an adventure novel|a children's novel|a children's book|a historical novel|"
    r"a novel|a history|a literary work|a children's fantasy"
)
OLD_LEAD = re.compile(
    rf"\bis (?:{OLD_KIND}) about\b",
    re.I,
)
FUTURE_YEAR = re.compile(r"\b(19[3-9]\d|20\d\d)\b")
CATALOG_ID = re.compile(
    r"\bOL\d+W\b|\b(open library|wikipedia|booksthere\.com|project gutenberg)\b",
    re.I,
)


def _folded(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _title_core(title):
    short = re.sub(r"\s*[—–-]\s*Volume\b.*$", "", title or "", flags=re.I)
    short = re.sub(r",?\s+Vol(?:ume|\.)\s+.*$", "", short, flags=re.I)
    return re.sub(r"^(the|a|an)\s+", "", _folded(short))


def _title_in(text, title):
    core = _title_core(title)
    hay = _folded(text)
    if not core or not hay:
        return False
    if core in hay or hay in core:
        return True
    prefix = " ".join(core.split()[:5])
    if len(prefix) >= 16 and prefix in hay:
        return True
    words = [w for w in core.split() if len(w) > 2]
    if not words:
        return core in hay
    hit = sum(1 for w in words if w in hay.split())
    return hit >= max(1, int(round(len(words) * 0.7)))


def _fold_abbreviations(text):
    text = re.sub(
        r"\b(?:Jr|Sr|St|Mr|Mrs|Ms|Dr|Vol|No|vs|Prof|Rev|Gen|Capt|Lt|Col|etc|e\.g|i\.e|Hon|Jos|Mme|Chas)\.",
        lambda m: m.group(0).replace(".", "@"),
        text,
        flags=re.I,
    )
    text = re.sub(r"\b[A-Z][a-z]{1,2}\.", lambda m: m.group(0).replace(".", "@"), text)
    return re.sub(r"\b[A-Z]\.", lambda m: m.group(0).replace(".", "@"), text)


def wrote_frame(text, title):
    """The whole note is '{Author} wrote {Title}.'"""
    raw = (text or "").strip()
    match = re.fullmatch(r"(.+?)\s+wrote\s+(.+)\.", raw)
    if not match:
        return False
    who, what = match.group(1).strip(), match.group(2).strip()
    if len(who.split()) > 14:
        return False
    if re.search(r"\.\s+[A-Z]", _fold_abbreviations(who)):
        return False
    core = _title_core(title)
    got = re.sub(r"^(the|a|an)\s+", "", _folded(what))
    if not core or not got:
        return False
    got_words = got.split()
    core_words = core.split()
    if len(got_words) > len(core_words) + 3:
        return False
    hit = sum(1 for w in got_words if w in core_words)
    return hit / len(got_words) >= 0.75


def subject_heading_frame(text, title, author=""):
    """The whole note is '{subjects}, in {Author’s Title}.'"""
    raw = (text or "").strip()
    if ", in " not in raw or not raw.endswith("."):
        return False
    parts = raw.split(", in ")
    limit = len(_title_core(title)) + len(author or "") + 60
    for i in range(1, len(parts)):
        head = ", in ".join(parts[:i]).strip()
        tail = ", in ".join(parts[i:]).strip()
        body = tail[:-1].strip()
        break_in_tail = re.search(r"\.\s+[A-Z][a-z]", _fold_abbreviations(body))
        break_in_title = re.search(r"\.\s+[A-Z][a-z]", _fold_abbreviations(title or ""))
        if break_in_tail and not break_in_title:
            continue
        if re.match(r"^In\s+", head) and _title_in(head, title):
            continue
        if re.search(r"\b(is|was|were|are|recounts|describes|follows|tells)\b", head, re.I):
            continue
        if _title_in(body, title) and len(body) <= limit:
            return True
    return False


def check_blurb(text, slug, featured=False, title="", author=""):
    text = (text or "").strip()
    if not text:
        if featured:
            raise SystemExit(f"missing featured blurb: {slug}")
        return
    if wrote_frame(text, title):
        raise SystemExit(f"wrote frame in {slug}")
    if subject_heading_frame(text, title, author):
        raise SystemExit(f"subject-heading frame in {slug}")
    if ",," in text:
        raise SystemExit(f"punched-out date in {slug}")
    for phrase in FORBIDDEN_SUBSTRINGS:
        if phrase.lower() in text.lower():
            raise SystemExit(f"retired lead in {slug}: {phrase}")
    if OLD_LEAD.search(text):
        raise SystemExit(f"retired kind-about lead in {slug}")
    ident = text
    if title:
        ident = re.sub(re.escape(title), " ", ident, flags=re.I)
    if CATALOG_ID.search(ident):
        raise SystemExit(f"catalog id or site name in blurb: {slug}")
    # A year that is already part of the book's title is the record, not an invented date.
    scrub = text
    for year in re.findall(r"\b(?:19[3-9]\d|20\d\d)\b", title or ""):
        scrub = scrub.replace(year, "")
    if FUTURE_YEAR.search(scrub):
        raise SystemExit(f"year after 1928 in {slug}")


def check_catalog(catalog):
    featured = [b for b in catalog["books"] if b.get("featured")]
    if len(featured) != 45:
        raise SystemExit(f"expected 45 featured books, found {len(featured)}")
    for b in catalog["books"]:
        if b.get("history"):
            raise SystemExit(f"history template still stored on {b.get('slug')}")
        check_blurb(
            b.get("blurb") or "",
            b.get("slug") or "?",
            featured=bool(b.get("featured")),
            title=b.get("title") or "",
            author=b.get("author_name") or "",
        )
    titles_by_author = {}
    for b in catalog["books"]:
        titles_by_author.setdefault(b.get("author"), []).append(b.get("title") or "")
    for author in catalog.get("authors") or []:
        intro = author.get("intro") or ""
        if not intro:
            continue
        scrub = intro
        for year in re.findall(r"\b(?:19[3-9]\d|20\d\d)\b", " ".join(titles_by_author.get(author.get("slug"), []))):
            scrub = scrub.replace(year, "")
        if FUTURE_YEAR.search(scrub):
            raise SystemExit(f"year after 1928 in author note: {author.get('slug')}")
    return len(catalog["books"])
