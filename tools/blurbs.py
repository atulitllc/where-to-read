#!/usr/bin/env python3
"""Unique catalog blurbs and history notes.

Each non-handwritten blurb is assembled from the title, author, subjects,
known year, and the Gutenberg and Open Library ids. Wording shifts with
those facts so two editions of one title do not share a paragraph.
"""
import hashlib

# Grammatical phrase after "is" / "as". Never "a plays" or "a poetry".
KIND = {
    "novel": "a novel",
    "romance": "a romance",
    "mystery": "a mystery",
    "gothic": "a gothic tale",
    "adventure": "an adventure book",
    "childrens-books": "a children's book",
    "science-fiction": "a science-fiction book",
    "fantasy": "a fantasy",
    "short-stories": "a collection of short stories",
    "poetry": "poetry",
    "plays": "a play",
    "philosophy": "a work of philosophy",
    "memoir": "a memoir",
    "biography": "a biography",
    "history": "a history",
    "essays": "a book of essays",
    "humor": "a humorous book",
    "travel": "a travel book",
    "religion": "a religious book",
    "science": "a science book",
    "letters": "a book of letters",
    "literature": "a work of literature",
}


def _n(*parts):
    raw = "\n".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _join(names):
    names = list(names)
    if not names:
        return "Literature"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _pick(n, shift, options):
    return options[(n // shift) % len(options)]


def _span(birth, death):
    if birth and death:
        return f"{birth}–{death}"
    if death:
        return f"died {death}"
    if birth:
        return f"born {birth}"
    return None


def make_blurb(book, subject_names):
    """Short original shelf note. Does not retell a plot or invent a year."""
    title = book["title"]
    author = book.get("author_name") or "the writer named on the record"
    ol = book["ol_id"]
    pg = int(book["gutenberg"])
    slugs = book.get("subjects") or ["literature"]
    primary = KIND.get(slugs[0], "a book")
    shelves = _join(subject_names.get(s, s) for s in slugs)
    year = book.get("year")
    if year == 1800:
        year = None
    birth = book.get("author_birth")
    death = book.get("author_death")
    span = _span(birth, death)
    n = _n("blurb", title, author, ol, pg)

    lead = _pick(n, 1, [
        f"{title} is listed as {primary}, credited to {author}.",
        f"{author} is the writer named on {title}, which this shelf lists as {primary}.",
        f"The title on this card is {title}. {author} is the author credited, and the text is {primary}.",
        f"{title}, credited to {author}, is held here as {primary}.",
        f"For {author}, this card is the public-domain text {title}, listed as {primary}.",
        f"This card is {title} by {author}, listed as {primary}.",
        f"The catalog names {title} under {author} and describes the text as {primary}.",
        f"{author} appears on {title}. The shelf label for that text is {primary}.",
        f"Find {title} by the author credit {author}. It is {primary}.",
        f"{title} carries the author credit {author} and the form {primary}.",
    ])
    shelf = _pick(n, 3, [
        f"Subject labels stored with it are {shelves}.",
        f"It is filed under {shelves}.",
        f"The shelves chosen for this card are {shelves}.",
        f"Catalog subjects for the row are {shelves}.",
        f"On this site the subject shelves read {shelves}.",
        f"The record places it with {shelves}.",
    ])
    bits = [lead, shelf]
    if year:
        bits.append(_pick(n, 5, [
            f"The year stored for the title is {year}.",
            f"{year} is the publication year on the record, not a year added to fill a gap.",
            f"This card keeps {year} as the date for {title}.",
            f"A publication year of {year} is already on the record.",
            f"The date filed beside the title is {year}.",
        ]))
    if span:
        bits.append(_pick(n, 9, [
            f"Author dates on the record: {span}.",
            f"The life dates filed with {author} are {span}.",
            f"{author} is dated {span} in this catalog.",
            f"Dates kept for the author credit are {span}.",
        ]))
    bits.append(_pick(n, 7, [
        f"This page is Gutenberg text {pg}, paired with Open Library work {ol}.",
        f"Open Library work {ol} is the work id; Gutenberg text {pg} marks this specific text.",
        f"Use Gutenberg {pg} and Open Library {ol} to separate this text from another copy of the title.",
        f"The identifiers on this card are Gutenberg {pg} and Open Library {ol}.",
        f"Another edition of {title} would not share this pair: Gutenberg {pg}, Open Library {ol}.",
        f"Gutenberg number {pg} and Open Library {ol} belong to this card alone.",
        f"The landing page named here is Gutenberg {pg}, for Open Library work {ol}.",
        f"This row matches Gutenberg text {pg} to Open Library work {ol}.",
    ]))
    rot = (n // 13) % len(bits)
    bits = bits[rot:] + bits[:rot]
    text = " ".join(bits)
    if title not in text or str(pg) not in text or ol not in text:
        text += f" Card keys: {title}; {author}; Gutenberg {pg}; Open Library {ol}."
    return text


def history_copy(book, author, subjects):
    """Shelf paragraph unique to this Gutenberg text. Facts only."""
    title = book["title"]
    name = author["name"]
    ol = book["ol_id"]
    pg = int(book["gutenberg"])
    year = book.get("year")
    if year == 1800:
        year = None
    birth = book.get("author_birth") or author.get("birth")
    death = book.get("author_death") or author.get("death")
    span = _span(birth, death)
    filed = _join(subjects[s]["name"] for s in book["subjects"])
    n = _n("history", title, name, ol, pg, book.get("slug"))

    if year and span:
        opening = _pick(n, 1, [
            f"{title} is listed with {year}. {name} ({span}) is the writer named on this text.",
            f"The date on {title} is {year}, and the author credit is {name} ({span}).",
            f"{name} ({span}) is named on {title}, which this catalog dates to {year}.",
        ])
    elif year:
        opening = _pick(n, 1, [
            f"The date attached to {title} is {year}. {name} is the writer named on it.",
            f"{title} carries the year {year} and the author credit {name}.",
            f"{year} is the year stored for {title}. The name on the text is {name}.",
        ])
    elif span:
        opening = _pick(n, 1, [
            f"{name} ({span}) is the writer named on {title}. No publication year is stored, so none is shown.",
            f"{title} names {name} ({span}). The publication year was left blank rather than guessed.",
            f"The author credit is {name} ({span}). This card does not invent a year for {title}.",
        ])
    else:
        opening = _pick(n, 1, [
            f"{title}, credited to {name}, is the public-domain text on this page.",
            f"{name} is the writer named on {title}. The card does not add a publication year.",
            f"This page records {title} under the name {name}.",
        ])
    middle = _pick(n, 3, [
        f"It is filed under {filed}.",
        f"Subject shelves for the page are {filed}.",
        f"The catalog places this text with {filed}.",
        f"Shelf labels here are {filed}.",
    ])
    closer = _pick(n, 5, [
        f"The reading link is Open Library work {ol}. Gutenberg text {pg} is the landing page for this card, not for every edition of the title.",
        f"This note is only for Gutenberg {pg} under Open Library {ol}. A different printing of {title} has its own page.",
        f"Open Library {ol} is the work linked from here, and Gutenberg {pg} is the text number paired with it.",
        f"Follow Open Library work {ol} to read. The Gutenberg landing page for this specific text is number {pg}.",
        f"Identifiers that keep this page distinct are Open Library {ol} and Gutenberg {pg}.",
        f"Other texts of {title} are listed separately. This one is Gutenberg {pg}, Open Library work {ol}.",
    ])
    if (n // 11) % 2:
        text = " ".join([middle, opening, closer])
    else:
        text = " ".join([opening, middle, closer])
    return text
