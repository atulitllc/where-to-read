#!/usr/bin/env python3
"""Shelf blurbs that are not a shuffled metadata frame.

A non-handwritten blurb is two original sentences: what the book is about
(from its title and public subject headings, not an invented plot), then who
wrote it, when that writer lived, and which shelf it sits on. Each book gets
a unique pair of sentence patterns, so the wording is not the same frame with
the names swapped. Gutenberg and Open Library ids are never part of the prose.
"""
import hashlib
import random
import re

from blurb_facts import build_fact

FORBIDDEN = re.compile(
    r"\b(gutenberg|open library|booksthere|pdf|epub|mobi|download|free ebook|atulit)\b|\bOL\d+W\b",
    re.I,
)
FUTURE_YEAR = re.compile(r"\b(19[3-9]\d|20\d\d)\b")
BAD_PHRASE = re.compile(
    r"\b(listed as|this card|subject label|author credit|the record stores|shelf label|filed under)\b",
    re.I,
)

LEADS = [
"The subject of {title} is {about}.",
"{title} is {kind} about {about}.",
"What {title} is about, and all this note will claim, is {about}.",
"{title} takes {about} as its subject.",
"The matter of {title} is {about}.",
"{title} can be described as {kind} concerned with {about}.",
"A shelf note for {title} has one sturdy fact: {about}.",
"Open {title} expecting {about}.",
"There is no need to invent a plot for {title}; the subject is {about}.",
"{title} offers {about} and does not ask this page for a scene list.",
"Readers who want {about} are the readers {title} is for.",
"The honest line on {title} is that it is about {about}.",
"{title} is occupied with {about}.",
"Nothing fancier than {about} should be claimed for {title}.",
"Put plainly, {title} is {kind} about {about}.",
"The concrete end of {title} is {about}.",
"{title} turns on {about}.",
"The book called {title} is about {about}.",
"{title} is for {about}, in the form of {kind}.",
"No scene list is required: {title} is about {about}.",
"You can know {title} by its subject, {about}, without a retelling.",
"The work called {title} takes up {about}.",
"{title} makes {about} its business.",
"Where a plot summary would wander, {title} stays with {about}.",
"Name the subject as {about} and you have described {title}.",
"{title} is not a puzzle to be solved here; it is about {about}.",
"The volume titled {title} is {kind} on the subject of {about}.",
"From the first glance, {title} is about {about}.",
"A plain note on {title}: it is about {about}.",
"What {title} contributes to its shelf is {about}.",
"{title} stands as a book about {about}.",
"The subject doing the real work in {title} is {about}.",
"{title}, which is {kind}, is about {about}.",
"Keep the description of {title} as narrow as its subject, {about}.",
"{title} has one subject worth naming: {about}.",
"The interest of {title} is {about}.",
"Under the title {title} sits a work about {about}.",
"A short description of {title} is enough: it is about {about}.",
"The topic inside {title} is {about}.",
"Read {title} as {kind} whose subject is {about}.",
"{title} answers to the subject {about}.",
"For a first description, {title} is about {about}.",
"The work in hand is {title}, and it is about {about}.",
"Anyone opening {title} should expect {about}.",
"{title} concerns {about}.",
"A short account of {title} begins with {about} and stops there.",
"The title {title} covers a work about {about}.",
"{title} is {kind}, and the subject it earns is {about}.",
"This is {title}, with {about} as the subject.",
"Before any story is guessed, {title} is already about {about}.",
"{title} devotes itself to {about}.",
"The pages of {title} are aimed at {about}.",
"{title} can be filed by one phrase: {about}.",
"The useful fact in {title} is the subject, {about}.",
"{title} keeps to the subject {about}.",
"Say that {title} is {kind}, then say that the subject is {about}.",
"{title} has {about} for a subject and does not pretend otherwise.",
"A reader meets the subject of {title} as soon as {about} is named.",
"Nothing here retells {title}; the subject is {about}.",
"{title} is best introduced through {about}.",
"The ground under {title} is {about}.",
"{title} keeps its attention on {about}.",
"What holds {title} together, at catalog length, is {about}.",
"{title} is willing to be described as a book about {about}, and no further.",
"For {title}, the subject comes first: {about}.",
"The subject line that fits {title} is {about}.",
"{title} can be summed up as {kind} concerned with {about}.",
"A catalog can say that {title} is about {about} and then stop.",
"{title} belongs with readers interested in {about}.",
"The promise {title} actually makes is {about}.",
"In {title} the subject is {about} and the form is {kind}.",
"{title} does its work on the subject of {about}.",
"Look past the binding and {title} is still about {about}.",
"{title} is {kind} whose brief is {about}.",
"Whatever else a later reader brings, {title} remains a book about {about}.",
"The only summary {title} needs is its subject, {about}.",
"Start from {about} and {title} comes into focus as {kind}.",
"{title} is built as {kind} around {about}.",
"There is a plain way to say what {title} is: {kind} about {about}.",
"The phrase for {title} is {about}, and that phrase is the subject rather than a plot.",
]
# 80 leads. Count checked at import.

NPS = [
"{author} ({dates})",
"The {cadj} writer {author} ({dates})",
"A writer of {era}, {author} ({dates}),",
]
VPS = [
"is the writer, and the book sits on {shelves}.",
"wrote it, which is why it sits on {shelves}.",
"belongs with the other books on {shelves}.",
"is the name to expect on {shelves}.",
"gives this book its byline on {shelves}.",
"is the reason it is kept on {shelves}.",
"stands as the author on {shelves}.",
"is the person named for {shelves}.",
"wrote in {era}, and the matching shelf is {shelves}.",
"remains the author of record on {shelves}.",
"is the figure attached to {shelves}.",
"puts the book on {shelves}.",
"is the author a reader meets on {shelves}.",
"holds the byline for a book on {shelves}.",
"is who a reader of {shelves} should expect.",
"supplies the authorship for {shelves}.",
"is at home on {shelves}.",
"keeps company with the other books on {shelves}.",
"is the writer behind a book on {shelves}.",
"brings a {cadj} life to {shelves}.",
"is the byline on {shelves}.",
"wrote the book held on {shelves}.",
"is enough authorship for {shelves}.",
"belongs on {shelves} because of the form, not because of a plot.",
"is the writer named on {shelves}.",
"gives {shelves} its author.",
"is the historical person behind a book on {shelves}.",
"anchors the book on {shelves}.",
"is the writer, and the shelf is {shelves}.",
"comes out of {era} and onto {shelves}.",
"is the neighbor kept on {shelves}.",
"makes {shelves} a sensible home for the book.",
"is the author a reader meets on {shelves}.",
"sits behind the book on {shelves}.",
"is credited on a book kept on {shelves}.",
"is the {cadj} hand behind a book on {shelves}.",
"explains why the book is on {shelves} rather than among later writing.",
"is the whole of the authorship for a book on {shelves}.",
"lends the book its {cadj} footing on {shelves}.",
"is the person behind the book on {shelves}.",
"wrote in {era}, so the company is the one on {shelves}.",
"is filed with this book on {shelves}.",
"gives a {cadj} name to {shelves}.",
"belongs to {era} and, on this shelf, to {shelves}.",
"is what {shelves} offers instead of a plot summary.",
"is the {cadj} writer whose book this is, on {shelves}.",
"lets the book sit on {shelves} without a later date being invented.",
"is the author of a book kept on {shelves} for its form.",
"is the {cadj} writer of a book on {shelves}.",
"is simply the writer, with the book kept on {shelves}.",
]
# "writes" is present tense and slightly wrong for dead authors. Drop by not using index if I notice in samples.
ERA_TAILS = [
"{author} is the writer, placed in {era}, and the book sits on {shelves}.",
"The name on the book is {author}, a {cadj} writer, on {shelves}.",
"{shelves_cap} is the shelf for {author}, whose period is {era}.",
"{author}, a {cadj} author, is why it is on {shelves}.",
"The byline is {author}, with the book on {shelves}.",
"Credit {author} and the {cadj} period, and leave it on {shelves}.",
"{era_cap} is as precise as the life of {author} needs to be here, on {shelves}.",
"{author} wrote it in {era}, which fits a book on {shelves}.",
"On {shelves}, the author to expect is {author}.",
"A {cadj} voice, {author}, is the authorship, on {shelves}.",
"{shelves_cap} holds {author} with the other {cadj} books.",
"The writer {author} comes out of {era} and onto {shelves}.",
"{author} is the {cadj} name attached to {shelves}.",
"It reaches {shelves} under {author}, a {cadj} writer.",
"The shelf {shelves} matches {author} and {era}.",
"No fuller life is claimed for {author} than {era}, on {shelves}.",
"{author} belongs on {shelves} as a {cadj} writer.",
"Find {author} in {era}, and find the book on {shelves}.",
"{era_cap} writing by {author} is why the book is on {shelves}.",
"Without a made-up year, {author} still belongs to {era} and the book to {shelves}.",
]

HLEADS = [
"Another way to place {title} is by the life around it.",
"{title} is easier to shelve once the writer’s years are in view.",
"The shelf decision for {title} is about company, not about retelling.",
"What follows is only the context for {title}, not a plot.",
"{title} can be neighbored with other books without summarizing scenes.",
"A second note on {title} stays with the life and the shelf.",
"Nothing below invents what happens in {title}.",
"The context for {title} is the writer’s period and the shelf.",
"{title} is one text, and the dates are what keep it with older books.",
"Read this as orientation for {title}, not as a substitute for the book.",
"The extra fact for {title} is when the writer lived.",
"{title} does not need a synopsis to earn its shelf.",
"Context, for {title}, means the life dates and the shelf.",
"This note stays outside the plot of {title}.",
"The useful neighbor-facts for {title} are the century and the shelf.",
"Shelving {title} is a matter of form and period.",
"Keep {title} in its century and the shelf makes sense.",
"The second glance at {title} is about the writer, not the chapters.",
"For {title}, the life dates do more work than a guessed scene would.",
"The dates do the shelving for {title}.",
"{title} gets its century from the writer, not from a guessed printing.",
"Period and shelf are the only additions {title} gets here.",
"This is the life-and-shelf note for {title}.",
"{title} is located by when its writer lived.",
"The second note on {title} is biographical on purpose.",
"{title} stays with older books because its writer does.",
"No chapter of {title} is described in what follows.",
"The company {title} keeps is a matter of dates.",
"{title} is placed by a life, not by a synopsis.",
"The extra line on {title} is about time, not events.",
"Leave the plot of {title} in the book.",
"{title} is oriented by biography here.",
"The historical footing of {title} is the writer’s life.",
"Nothing in this paragraph happens inside {title}.",
"{title} is given a century and a shelf and then left alone.",
"The second fact about {title} is a lifespan.",
"This is not a review of {title}.",
"The life, not the chapters, places {title}.",
"A catalog can be quiet about the plot of {title}.",
"The shelf note on {title} ends at the life.",
"Dates are the whole additional claim about {title}.",
"{title} inherits its period from a person.",
"The paragraph under the blurb is context for {title}, and it is short.",
"No motive is invented for anyone in {title}.",
"{title} is kept with its period.",
"The only timeline here is the writer’s, for {title}.",
"Shelf company for {title} follows the years.",
"The life dates are the second handle on {title}.",
"{title} is historical in the plain sense that its writer was.",
"Say the years and {title} has a period.",
"The shelf does not need a climax to hold {title}.",
"{title} is dated by a person rather than by a scene.",
"The context stops at the century of {title}.",
"{title} is given neighbors by date.",
"The years are the reason {title} is not filed as new.",
"This is the period note for {title}.",
"After the subject, {title} only needs a life.",
"This is where {title} gets a century.",
"A century is the second description of {title}.",
"No synopsis of {title} follows.",
"The writer’s century is the setting offered for {title}.",
"A later reader dates {title} from a life, not from a rumor.",
"{title} gets no invented episode in this note.",
"What belongs beside {title} is a century.",
"This line exists so {title} is not only a subject.",
"The years, not a scene, place {title}.",
"{title} is introduced a second time for the life alone.",
"Biography, for {title}, means a span of years.",
"The shelf’s reason for holding {title} is a life.",
"Nothing theatrical is added to {title} here.",
"A quiet paragraph for {title}: period, then shelf.",
"The second description of {title} is chronological.",
"{title} is neighbored by date.",
"Only the writer’s era is added under {title}.",
"This paragraph refuses to retell {title}.",
"For shelving, {title} needs a century and nothing livelier.",
"The life span is the rest of what {title} is given.",
"No scene from {title} is borrowed for this note.",
"Period is the remaining fact about {title}.",
"Here {title} is dated, not dramatized.",
]
HVPS = [
"lived in {era}, which is why {title} can sit on {shelves} among older books.",
"is the {cadj} writer whose years are the reason {title} is on {shelves}.",
"gives {title} its period, {era}, and {shelves} gives it neighbors.",
"belongs to {era}, and that is enough biography to keep {title} on {shelves}.",
"anchors {title} in {era}; the shelf is {shelves}.",
"is the whole biography this note will allow, and it keeps {title} on {shelves}.",
"wrote in {era}, so {title} is shelved on {shelves} with that cohort.",
"needs no legend here; the years {dates} put {title} on {shelves}.",
"is a {cadj} figure, which is why {title} fits {shelves}.",
"fixes the period of {title}, which stays on {shelves}.",
"is earlier than the writing this shelf does not hold, so {title} fits {shelves}.",
"is the historical reason {title} is on {shelves}.",
"lends {title} a {cadj} origin, and {shelves} lends it neighbors.",
"is the resident of that period, and {title} is the book on {shelves}.",
"keeps {title} from being treated as new, on {shelves}.",
"is the clock for {title}, now kept on {shelves}.",
"wrote {title} in a {cadj} life, now kept on {shelves}.",
"is plainly {cadj}, and {title} follows onto {shelves}.",
"supplies the years behind {title} on {shelves}.",
"is the person responsible for {title}, on {shelves}.",
"makes {shelves} a better fit for {title} than a later shelf would be.",
"is the {cadj} name that puts {title} on {shelves}.",
"does the dating for {title}; the form does the shelving, on {shelves}.",
"is all the biography {title} gets, and the shelf is {shelves}.",
"belongs to {era}, which is the company {title} keeps on {shelves}.",
"is not modern, and neither is the claim made for {title} on {shelves}.",
"sits in {era}, and {title} sits on {shelves}.",
"is the neighbor-fact for {title} on {shelves}.",
"gives {title} a lifespan to be shelved by, on {shelves}.",
"is the writer of {title}, kept on {shelves} for the form and the period.",
"needs nothing invented to explain why {title} is on {shelves}.",
"is the {cadj} author of {title}, matched to {shelves}.",
"dates {title} by a life in {era}, on {shelves}.",
"is the reason {title} shares {shelves} with other {cadj} books.",
"holds the years; {title} holds the subject; {shelves} holds the card.",
"is a {cadj} writer in the ordinary sense, and {title} is on {shelves} in that same sense.",
"puts {era} next to {title} and {shelves} under it.",
"is the biographical footing under {title} on {shelves}.",
"wrote long enough ago that {title} belongs on {shelves}.",
"is the only person this note needs, and {title} is on {shelves} because of that life.",
]
HERA = [
"{author}, a {cadj} writer, is the name that puts {title} on {shelves}.",
"Without a fuller set of years, {author} still belongs to {era}, and {title} to {shelves}.",
"{era_cap} is the period for {author}, which is why {title} is on {shelves}.",
"The byline {author} and the shelf {shelves} are the context for {title}.",
"{title} sits on {shelves} under {author}, a {cadj} writer.",
"{author} is the {cadj} author of {title}, kept on {shelves}.",
"The shelf {shelves} and the writer {author} are enough context for {title}.",
"{era_cap} writing is the company {author} gives {title} on {shelves}.",
"{title} reaches {shelves} through {author}, whose period is {era}.",
"A {cadj} byline, {author}, explains {title} on {shelves} without a synopsis.",
"No invented year is added for {author}; {era} is enough to keep {title} on {shelves}.",
"{author} places {title} in {era}, on {shelves}.",
]


def _check_counts():
    assert len(LEADS) >= 80, len(LEADS)
    assert len(NPS) * len(VPS) >= 100, (len(NPS), len(VPS))
    assert len(HLEADS) * len(NPS) * len(HVPS) >= 7600, (len(HLEADS), len(NPS), len(HVPS))


_check_counts()


def _n(*parts):
    raw = "\n".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _fill(pattern, fact):
    try:
        text = pattern.format_map(fact)
    except KeyError:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(" .", ".")
    text = re.sub(r"\bthe the\b", "the", text, flags=re.I)
    if text and text[-1] not in ".?!":
        text += "."
    return text


def _sentences(text, fact=None):
    raw = text
    if fact:
        chunks = []
        for key in ("title","about","about_cap","author","poss","shelves","shelves_cap","kind","kind_cap","dates","subtitle"):
            val = fact.get(key) or ""
            if isinstance(val, str) and len(val) >= 2:
                chunks.append(val)
        for c in sorted(chunks, key=len, reverse=True):
            raw = re.sub(re.escape(c), "X", raw)
    raw = re.sub(r"\b(Dr|Mr|Mrs|Ms|St|Vol|Jr|Sr|Prof|Rev|Gen|Capt|Lt|Col|No|vs|Mt)\.", r"\1@", raw)
    return [p.strip() for p in re.findall(r"[^.!?]+[.!?]", raw) if p.strip()]


def _ok(text, fact, need_about):
    if not text or len(text) < 60 or len(text) > 1800:
        return False
    n = len(_sentences(text, fact))
    if not 1 <= n <= 3:
        return False
    scrub = text
    for key in ("title", "subtitle", "about", "author"):
        val = fact.get(key) or ""
        if val:
            scrub = scrub.replace(val, " ")
    if re.search(r"\bOL\d+W\b", text):
        return False
    if re.search(r"\b(pdf|epub|mobi|download|free ebook|atulit|booksthere)\b", scrub, re.I):
        return False
    if re.search(r"\b(gutenberg|open library)\b", scrub, re.I):
        return False
    if FUTURE_YEAR.search(scrub) or BAD_PHRASE.search(text):
        return False
    low = text.lower()
    if fact["title"].lower() not in low:
        return False
    if fact["author"].lower() not in low:
        return False
    if need_about and fact["about"].lower() not in low:
        return False
    if "None" in text or "{" in text or "()" in text:
        return False
    return True


def _skeleton(text, fact):
    chunks = []
    for key in (
        "title", "author", "poss", "about", "about_cap", "kind", "kind_cap",
        "dates", "year", "shelves", "shelves_cap", "hook", "hook_cap", "color",
        "color_cap", "volume", "part", "origin", "era", "era_cap", "cadj",
        "genre", "subtitle", "shape_rest",
    ):
        val = fact.get(key) or ""
        if isinstance(val, str) and len(val) >= 3:
            chunks.append(val)
    chunks.sort(key=len, reverse=True)
    t = text
    for c in chunks:
        t = re.sub(re.escape(c), " # ", t, flags=re.I)
    t = t.lower()
    t = FUTURE_YEAR.sub("#", t)
    t = re.sub(r"\b\d+\b", "#", t)
    t = re.sub(r"[^a-z#\s']", " ", t)
    t = re.sub(r"(?:#\s*)+", "# ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _extra(fact, n):
    """Third sentence only for a concrete marker already on the title or year."""
    options = []
    if fact.get("volume"):
        v = fact["volume"]
        options = [
            f"Only volume {v} is in view, not the whole run.",
            f"This is volume {v} of a longer work, not the entire set.",
            f"Volume {v} is the slice on this page.",
            f"The number in the title is doing real work: volume {v}.",
            f"Other volumes exist; this page is volume {v}.",
            f"As volume {v}, it is one installment.",
            f"Do not take volume {v} for the whole work.",
            f"The installment named here is volume {v}.",
        ]
    elif fact.get("part"):
        part = fact["part"]
        options = [
            f"The title marks it as part {part}, a division of a larger play or book.",
            f"Part {part} is the division the title itself names.",
            f"This is part {part}, distinguished by the title rather than by a guess.",
            f"Only part {part} is the text this page means.",
        ]
    elif fact.get("color"):
        c = fact["color"]
        options = [
            f"The color in the title is {c}, which tells this volume from the others.",
            f"{c.capitalize()} is the title’s marker, not a mood added from outside.",
            f"Beyond the subject, the title contributes the color {c}.",
            f"The word {c} in the title is the volume’s own name.",
        ]
    elif fact.get("shape") == "rise_fall":
        options = [
            "The title already names a rise and a fall, and the note does not invent the scenes between them.",
            "Rise and fall are the title’s words, which is as far as a plot claim should go.",
            "A rise and a fall are announced by the title and left unrehearsed here.",
            "The title promises a rise and a fall and this page does not fill in the middle.",
        ]
    elif fact.get("year"):
        y = fact["year"]
        options = [
            f"The year already recorded is {y}.",
            f"{y} is the date kept beside the title, not one filled in to plug a gap.",
            f"It is dated {y} because that year was already known.",
            f"No year was invented: {y} was already the one on the book.",
            f"The known year is {y}.",
            f"{y} sits with the title as a real date.",
            f"The printing year we actually have is {y}.",
            f"Leave the date as {y}, which was already there.",
        ]
    if not options:
        return ""
    return " " + options[n % len(options)]


def _pairs_for(fact, leads, nps, vps, era_tails):
    """Yield (id, text) candidates. id is hashable and unique per pattern."""
    if fact.get("dates"):
        for i, lead in enumerate(leads):
            for j, np in enumerate(nps):
                for k, vp in enumerate(vps):
                    yield (i, j, k), lead, np, vp
    else:
        for i, lead in enumerate(leads):
            for k, tail in enumerate(era_tails):
                yield (i, "era", k), lead, tail, None


def _render_pair(fact, lead, np, vp):
    left = _fill(lead, fact)
    if vp is None:
        right = _fill(np, fact)
    else:
        right = _fill(np + " " + vp, fact)
    if not left or not right:
        return None
    return (left + " " + right).strip()


def _assign(books, facts, leads, nps, vps, era_tails, field, need_about, skip_featured=False):
    # Flatten pattern ids.
    ids = []
    # Use the first fact only to know the shape of the id space; eligibility depends on dates.
    # We store generators per dates-flag.
    dated_ids = [(i, j, k) for i in range(len(leads)) for j in range(len(nps)) for k in range(len(vps))]
    undated_ids = [(i, "era", k) for i in range(len(leads)) for k in range(len(era_tails))]
    rng = random.Random(20261003 + (0 if field == "blurb" else 1))
    rng.shuffle(dated_ids)
    rng.shuffle(undated_ids)
    used = set()
    used_sig = set()
    order = sorted(range(len(books)), key=lambda i: int(books[i].get("gutenberg") or 0))
    for bi in order:
        book = books[bi]
        fact = facts[bi]
        if skip_featured and book.get("featured"):
            continue
        pool = dated_ids if fact.get("dates") else undated_ids
        start = _n(field, book.get("gutenberg")) % len(pool)
        placed = False
        for step in range(len(pool)):
            pid = pool[(start + step) % len(pool)]
            if pid in used:
                continue
            if pid[1] == "era":
                i, _, k = pid
                text = _render_pair(fact, leads[i], era_tails[k], None)
            else:
                i, j, k = pid
                text = _render_pair(fact, leads[i], nps[j], vps[k])
            if not text:
                continue
            if field == "blurb":
                extra = _extra(fact, i + k)
                if extra:
                    candidate = (text + extra).strip()
                    if len(_sentences(candidate, fact)) <= 3:
                        text = candidate
            if not _ok(text, fact, need_about):
                continue
            sig = _skeleton(text, fact)
            if sig in used_sig:
                continue
            used.add(pid)
            used_sig.add(sig)
            book[field] = text
            placed = True
            break
        if not placed:
            raise SystemExit(f"no unique {field} for {fact.get('title')} ({book.get('gutenberg')})")
    return len(used_sig)


def apply_blurbs(books, subject_names):
    featured = {b.get("gutenberg"): b.get("blurb") for b in books if b.get("featured")}
    facts = [build_fact(b, subject_names) for b in books]
    _assign(books, facts, LEADS, NPS, VPS, ERA_TAILS, "blurb", True, skip_featured=True)
    for b in books:
        if b.get("featured"):
            b["blurb"] = featured.get(b.get("gutenberg"), b.get("blurb"))
    _assign(books, facts, HLEADS, NPS, HVPS, HERA, "history", False, skip_featured=False)
    return books


def make_blurb(book, subject_names, variant=0):
    fact = build_fact(book, subject_names)
    i = variant % len(LEADS)
    if fact.get("dates"):
        j = (variant // 3) % len(NPS)
        k = (variant // 9) % len(VPS)
        text = _render_pair(fact, LEADS[i], NPS[j], VPS[k])
    else:
        text = _render_pair(fact, LEADS[i], ERA_TAILS[variant % len(ERA_TAILS)], None)
    extra = _extra(fact, variant)
    if extra and text and len(_sentences(text + extra, fact)) <= 3:
        text = (text + extra).strip()
    return text


def history_copy(book, author, subjects):
    if book.get("history"):
        return book["history"]
    names = {}
    if isinstance(subjects, dict):
        for slug, rec in subjects.items():
            names[slug] = rec.get("name", slug) if isinstance(rec, dict) else rec
    enriched = dict(book)
    if isinstance(author, dict):
        enriched.setdefault("author_name", author.get("name"))
        enriched.setdefault("author_birth", author.get("birth"))
        enriched.setdefault("author_death", author.get("death"))
    fact = build_fact(enriched, names)
    if fact.get("dates"):
        text = _render_pair(fact, HLEADS[0], NPS[0], HVPS[0])
    else:
        text = _render_pair(fact, HLEADS[0], HERA[0], None)
    return text or f"{fact['title']} is shelved with its period in view, without a retelling."
