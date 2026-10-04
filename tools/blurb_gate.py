#!/usr/bin/env python3
"""Fail the build if a stock year clause or an old lead pattern is back.

The patterns below are the retired shelf templates. They are detectors only.
Nothing in this module fills a blurb.
"""
import re

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


def check_blurb(text, slug, featured=False, title=""):
    if not text or not str(text).strip():
        raise SystemExit(f"missing blurb: {slug}")
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
