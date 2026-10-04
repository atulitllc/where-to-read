#!/usr/bin/env python3
"""Facts for a shelf blurb. Subjects come from the Gutenberg catalog export."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PG_PATH = ROOT / "data" / "pg_catalog.csv"

STOP = {
    "a","an","the","of","and","or","to","in","for","on","with","from","by","at","as",
    "into","over","under","about","between","without","within","upon","among","through",
    "during","after","before","than","its","his","her","their","our","not","but","nor",
    "volume","vol","part","book","books","story","stories","tale","tales","other","being",
    "new","old","great","little","true","first","second","third","fourth","complete",
    "works","work","sketch","sketches","miscellaneous","selected","collection","edited",
    "illustrated","introduction","poems","poem","poetry",
}
FORM = {
    "fiction","juvenile fiction","juvenile literature","poetry","drama","biography",
    "autobiography","correspondence","personal narratives","sources","pictorial works",
    "illustrations","short stories","literature","essays","sermons","anecdotes",
    "miscellanea","periodicals","textbooks","bibliography","dictionaries",
    "history and criticism","description and travel","social life and customs",
    "translations into english","early works to 1800","early works to 1850","campaigns",
    "causes","history","politics and government","speeches","lectures","diaries",
}
GENRE_SAY = {
    "religious fiction":"religious fiction","historical fiction":"historical fiction",
    "political fiction":"political fiction","psychological fiction":"psychological fiction",
    "mystery fiction":"a mystery","gothic fiction":"a gothic story",
    "science fiction":"science fiction","detective and mystery stories":"detective stories",
    "domestic fiction":"domestic fiction","love stories":"love stories",
    "sea stories":"sea stories","adventure stories":"adventure stories",
    "bildungsromans":"a coming-of-age story","fantasy fiction":"fantasy",
    "fairy tales":"fairy tales","short stories":"short stories",
    "english fiction":"English fiction","american fiction":"American fiction",
    "french fiction":"French fiction","german fiction":"German fiction",
    "classical literature":"classical literature","sermons":"sermons","essays":"essays",
    "poetry":"poetry","drama":"drama","humorous stories":"humorous stories",
    "readers":"a school reader",
}
PLACES = {
    "england","scotland","ireland","wales","france","paris","london","india","europe",
    "africa","asia","america","australia","canada","germany","italy","spain","russia",
    "poland","turkey","greece","china","japan","egypt","rome","boston","new england",
    "new york","united states","great britain","britain","pennsylvania","virginia",
    "kentucky","california","texas","ohio","syria","venice","canada","gettyburg",
    "gettysburg","highlands","ireland","scotland","mexico","switzerland","holland",
    "belgium","norway","sweden","denmark","persia","palestine","jerusalem","oxford",
    "cambridge","edinburgh","dublin","florence","naples","athens","vienna","berlin",
}
KEEP = {
    "united","states","america","american","england","english","france","french","paris",
    "london","scotland","scottish","ireland","irish","britain","british","europe",
    "european","new","civil","war","gettysburg","rome","roman","greek","greece","latin",
    "christian","bible","god","napoleon","boston","york","oxford","cambridge","india",
    "indian","canada","australia","germany","german","italy","italian","spain","spanish",
    "russia","russian","eighty","venice","egypt","egyptian","syria","jerusalem",
    "virginia","pennsylvania","kentucky","california","texas","china","chinese","japan",
    "japanese","africa","african","standard","oil","netherlands","holland","dutch",
}
RESTORE = (
    ("united states","the United States"),
    ("great britain","Great Britain"),
    ("new england","New England"),
    ("civil war","the Civil War"),
    ("eighty years' war","the Eighty Years' War"),
    ("standard oil company","Standard Oil"),
)
THE_HEADS = {"industry","war","revolution","college","university","army","navy","church","battle","siege","empire","republic"}
CENTURY = {14:"fourteenth",15:"fifteenth",16:"sixteenth",17:"seventeenth",18:"eighteenth",19:"nineteenth",20:"twentieth"}
COLORS = {"brown","blue","red","green","grey","gray","black","white","yellow","crimson","scarlet","pink","purple","orange","violet","golden","silver","lilac","olive"}

_PG = None

def pg_row(gutenberg):
    global _PG
    if _PG is None:
        _PG = {}
        if PG_PATH.exists():
            with PG_PATH.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        _PG[int(row["Text#"])] = row
                    except (KeyError, ValueError):
                        pass
    try:
        return _PG.get(int(gutenberg))
    except (TypeError, ValueError):
        return None

def nice(s):
    s = re.sub(r"\s+", " ", (s or "")).strip(" ,;:-")
    if not s:
        return s
    small = {"a","an","the","of","and","or","in","on","for","to","from","with","by","at","de","du","van","von","ca"}
    out = []
    for w in s.split(" "):
        core = re.sub(r"[^A-Za-z'-]", "", w).lower()
        if any(ch.isupper() for ch in w[1:3]) and not w.isupper():
            out.append(w)
        elif core in KEEP:
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(w.lower())
    text = " ".join(out)
    for src, dst in RESTORE:
        if src in text.lower():
            text = re.sub(re.escape(src), dst, text, flags=re.I)
    return re.sub(r"\bthe the\b", "the", re.sub(r"\s+", " ", text), flags=re.I).strip()

def cap(s):
    return (s[:1].upper() + s[1:]) if s else s

def is_place(s):
    t = re.sub(r"\s*\([^)]*\)", "", s or "").strip().lower()
    t = re.sub(r"^(the)\s+", "", t)
    return t in PLACES or t.endswith(" islands") or t.endswith(" island")

def bad(phrase):
    low = (phrase or "").lower().strip()
    if not low or len(phrase) > 80:
        return True
    if "fictitious character" in low or "legendary character" in low:
        return True
    if re.search(r"\d{2,4}\s*[-–]\s*\d{2,4}", phrase):
        return True
    if re.search(r"\b(ca\.?|b\.?c\.?|bce|a\.?d\.?)\b", low):
        return True
    if re.match(r"^(to|from|circa|about)\s+\d", low):
        return True
    if re.match(r"^[A-Z][^,]{1,40}, [A-Z]", phrase):
        return True
    return False

def is_form(low):
    if low in FORM or low.startswith("early works to") or "translations into english" in low:
        return True
    if low.endswith(" fiction") or low.endswith(" literature") or low.endswith(" poetry") or low.endswith(" drama"):
        return True
    if low.endswith(" stories") and low not in {"sea stories","love stories","ghost stories"}:
        return True
    if low.endswith(" tales") and low not in {"fairy tales","horror tales"}:
        return True
    return False

def with_the(phrase):
    if not phrase or phrase.lower().startswith(("the ","a ","an ")):
        return phrase
    last = re.sub(r"[^A-Za-z]", "", phrase.split()[-1]).lower()
    if last in THE_HEADS:
        return "the " + phrase
    return phrase

def heading_phrase(heading):
    m = re.match(r"^([^,]{2,40}),\s+(Battle|Siege) of\b", heading)
    if m:
        return f"the {m.group(2)} of {m.group(1).strip()}"
    if ". " in heading:
        tail = heading.split(". ", 1)[1].split("--")[0]
        tail = re.sub(r",?\s+\d{3,4}\??\s*[-–]\s*\d{0,4}\??", "", tail)
        tail = re.sub(r"\s+", " ", tail).strip(" ,;")
        if tail and not bad(tail) and len(tail.split()) <= 8:
            return with_the(nice(tail))
    forms, bits = [], []
    for seg in [s.strip() for s in heading.split("--") if s.strip()]:
        low = seg.lower()
        if re.fullmatch(r"\d{1,2}(st|nd|rd|th) century", low) or re.fullmatch(r"\d{1,4}(\s*[-–]\s*\d{1,4})?", low):
            continue
        if re.search(r"\b(b\.?c\.?|bce|a\.?d\.?)\b", low) or low.startswith("to ") or "ca." in low:
            continue
        if is_form(low):
            forms.append(low)
            continue
        cleaned = re.sub(r",?\s+\d{3,4}\??\s*[-–]\s*\d{0,4}\??", "", seg)
        cleaned = re.sub(r"\b(19[3-9]\d|20\d\d)\b", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;")
        if cleaned and not bad(cleaned):
            bits.append(cleaned)
    if not bits:
        return None
    content = [b for b in bits if not is_place(b)]
    place = next((b for b in bits if is_place(b)), None)
    if not content and place:
        pl = nice(place)
        if pl.lower().startswith("united "):
            pl = "the " + pl
        if "description and travel" in forms:
            return "travel in " + pl
        if "social life and customs" in forms:
            return "daily life in " + pl
        if "history" in forms:
            return "the history of " + pl
        return pl
    phrase = nice(content[-1])
    if place and phrase and not is_place(phrase) and nice(place).lower() not in phrase.lower():
        pl = nice(place)
        if pl.lower().startswith("united "):
            pl = "the " + pl
        phrase = f"{phrase} in {pl}"
    elif "description and travel" in forms:
        phrase = "travel in " + phrase
    elif "social life and customs" in forms:
        phrase = "daily life in " + phrase
    return with_the(phrase) if phrase else None

def interpret(raw, title=""):
    topics, genres = [], []
    translated = early = False
    origin = None
    if not raw:
        return None, None, None, False, None, False
    title_words = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", title or "")}
    for heading in raw.split(";"):
        heading = heading.strip()
        if not heading:
            continue
        low = re.sub(r"\s+", " ", heading.lower())
        if "translations into english" in low:
            translated = True
        if "early works to 1800" in low or "early works to 1850" in low:
            early = True
        for lang, name in (("french fiction","French"),("french literature","French"),("german fiction","German"),("german literature","German"),("russian fiction","Russian"),("italian fiction","Italian"),("spanish fiction","Spanish"),("greek literature","Greek"),("latin literature","Latin")):
            if lang in low and not origin:
                origin = name
        key = low.split("--")[0].strip()
        if key in GENRE_SAY or key.endswith(" fiction") or key.endswith(" stories") or key.endswith(" tales"):
            genres.append(key)
        phrase = heading_phrase(heading)
        if phrase and not bad(phrase) and 2 < len(phrase) <= 80:
            topics.append(phrase)
    def sc(p):
        words = p.split()
        score = 4 + min(len(words), 6)
        if is_place(p) or p.lower().startswith(("travel in ","daily life in ","the history of ")):
            score -= 3
        if " in " in p.lower():
            score -= 2
        if len(words) == 1:
            score += 2
        if "," in p or "(" in p:
            score -= 4
        score += 3 * len(title_words.intersection({w.lower().strip("',") for w in words}))
        return score
    ranked = sorted(set(topics), key=sc, reverse=True)
    about = role = None
    if ranked:
        best = ranked[0]
        second = None
        for cand in ranked[1:]:
            if cand.lower() in best.lower() or best.lower() in cand.lower():
                continue
            if " in " in cand.lower() or " in " in best.lower():
                continue
            if len(cand.split()) <= 6 and "," not in cand:
                second = cand
                break
        if second and len(best.split()) <= 5 and len((best+" "+second).split()) <= 9:
            if second.lower().startswith("the ") and not best.lower().startswith("the "):
                about = f"{best} and {second}"
            elif best.lower().startswith("the ") and not second.lower().startswith("the "):
                about = f"{second} and {best}"
            else:
                about = f"{best} and {second}"
        else:
            about = best
        role = "topic"
    genre = None
    for g in genres:
        if g in GENRE_SAY:
            genre = GENRE_SAY[g]
            break
        if g.endswith(" fiction"):
            genre = g
            break
    if not about and genre:
        about, role = genre, "genre"
    return about, role, genre, translated, origin, early

def strip_volume(title):
    t = re.sub(r"\s*[—–-]\s*Volume\s+\d+.*$", "", title, flags=re.I)
    t = re.sub(r",?\s+Vol(?:ume|\.)\s+[IVXLC\d]+(?:\s*\(of\s*\d+\))?\.?$", "", t, flags=re.I)
    return t.strip(" ,;—–-")

def split_subtitle(title):
    main = strip_volume(title)
    for sep in (" — ", " -- ", ": ", "; "):
        if sep in main:
            left, right = main.split(sep, 1)
            right = right.strip()
            if len(right.split()) >= 3 and not re.match(r"(?i)(or|vol)", right):
                return left.strip(), right
    return main, None

def volume_of(title):
    m = re.search(r"(?:—|–|--|-)\s*Volume\s+0*(\d+)", title, flags=re.I)
    if m:
        return m.group(1)
    m = re.search(r"\bVol(?:ume|\.)\s+([IVXLC]+|\d+)\b", title, flags=re.I)
    return m.group(1) if m else None

def part_of(title):
    m = re.search(r"\bPart\s+([IVXLC]+|\d+)\b", title, flags=re.I)
    return m.group(1) if m else None

def title_shape(main):
    for name, pat in (
        ("rise_fall", r"(?i)^(?:the )?rise and fall of (.+)$"),
        ("history_of", r"(?i)^(?:a |the )?history of (.+)$"),
        ("life_of", r"(?i)^(?:the )?(?:life|lives) of (.+)$"),
        ("adventures", r"(?i)^(?:the )?adventures of (.+)$"),
    ):
        m = re.match(pat, main.strip())
        if m:
            return name, nice(m.group(1)[:80])
    return None, None

def content_tokens(title):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", title) if w.lower() not in STOP and len(w) >= 3]

def century_of(year):
    if year is None or year < 1 or year > 1928:
        return None
    return CENTURY.get((year - 1) // 100 + 1)

def possessive(name):
    if not name:
        return name
    return name + ("'" if name.endswith(("s","S")) else "'s")

def choose_kind(slugs, translated, origin):
    s = set(slugs or ["literature"])
    if "poetry" in s and "novel" not in s: kind = "a book of verse"
    elif "plays" in s and "novel" not in s: kind = "a play"
    elif "short-stories" in s and "novel" not in s: kind = "a collection of short stories"
    elif "letters" in s and "novel" not in s and "history" not in s: kind = "a book of letters"
    elif "essays" in s and "novel" not in s: kind = "a book of essays"
    elif "philosophy" in s and "novel" not in s: kind = "a work of philosophy"
    elif "memoir" in s and "novel" not in s: kind = "a memoir"
    elif "biography" in s and "novel" not in s: kind = "a biography"
    elif "travel" in s and "novel" not in s and "history" not in s: kind = "a travel narrative"
    elif "science" in s and "science-fiction" not in s and "novel" not in s: kind = "a science book"
    elif "religion" in s and "novel" not in s: kind = "a religious work"
    elif "humor" in s and "novel" not in s: kind = "a humorous book"
    elif "mystery" in s: kind = "a mystery"
    elif "gothic" in s: kind = "a gothic novel"
    elif "romance" in s and "novel" in s: kind = "a romance"
    elif "science-fiction" in s: kind = "a science-fiction story"
    elif "fantasy" in s and "childrens-books" in s and "novel" not in s: kind = "a children's fantasy"
    elif "fantasy" in s: kind = "a fantasy"
    elif "adventure" in s and "novel" in s: kind = "an adventure novel"
    elif "childrens-books" in s and "novel" in s: kind = "a children's novel"
    elif "childrens-books" in s: kind = "a children's book"
    elif "history" in s and "novel" in s: kind = "a historical novel"
    elif "novel" in s: kind = "a novel"
    elif "history" in s: kind = "a history"
    else: kind = "a literary work"
    if translated:
        kind += f" translated from {origin}" if origin else " in an English translation"
    return kind

def shelf_phrase(slugs, subject_names):
    labels = []
    for s in slugs or ["literature"]:
        name = subject_names.get(s, s) if isinstance(subject_names, dict) else s
        labels.append(name[:1].lower() + name[1:] if name else s)
    if len(labels) == 1:
        return f"the {labels[0]} shelf"
    if len(labels) == 2:
        return f"the {labels[0]} and {labels[1]} shelves"
    return "the " + ", ".join(labels[:-1]) + ", and " + labels[-1] + " shelves"

def valid_year(y):
    return isinstance(y, int) and 1400 <= y <= 1928 and y != 1800

def build_fact(book, subject_names):
    title = (book.get("title") or "").strip()
    author = (book.get("author_name") or "").strip() or "the writer named on it"
    birth, death = book.get("author_birth"), book.get("author_death")
    if isinstance(birth, int) and birth >= 1931: birth = None
    if isinstance(death, int) and death >= 1931: death = None
    year = book.get("year") if valid_year(book.get("year")) else None
    row = pg_row(book.get("gutenberg"))
    about, role, genre, translated, origin, early = interpret((row.get("Subjects") if row else "") or "", title)
    main, subtitle = split_subtitle(title)
    shape, shape_rest = title_shape(main)
    if subtitle and (not about or role == "genre"):
        sub = nice(subtitle)
        if sub and len(sub) <= 90 and not re.match(r"(?i)^(or|vol|volume)\b", sub):
            about = sub[:1].lower() + sub[1:]
            role = "subtitle"
    if not about:
        if shape and shape_rest:
            about, role = shape_rest, "title"
        else:
            bare = re.sub(r"(?i)^(the|a|an)\s+", "", main).strip()
            bare = re.sub(r"(?i)\s*[—–-]\s*complete$", "", bare).strip()
            bare = re.sub(r"(?i)\s*[:;]\s*(poems|poetry|and other poems|a novel|a romance|a play)$", "", bare).strip()
            about, role = nice(bare or main), "title"
    about = re.sub(r"\s+", " ", about).strip(" .")
    if len(about) > 110:
        about = about[:107].rsplit(" ", 1)[0]
    def _toks(s):
        return [w for w in re.findall(r"[a-z0-9']+", (s or "").lower()) if w not in STOP and w not in {"poems", "poem", "poetry"}]
    if _toks(about) and _toks(about) == _toks(title):
        if genre and _toks(genre) != _toks(title):
            about, role = genre, "genre"
        else:
            about, role = "what the title itself names", "title"
    hooks = content_tokens(main)
    hook = next((t for t in reversed(hooks) if t.lower() not in about.lower()), hooks[-1] if hooks else "")
    color = next((t.lower() for t in hooks if t.lower() in COLORS), "")
    ancient = (isinstance(birth, int) and birth < 500) or (isinstance(death, int) and death < 500 and (not isinstance(birth, int) or birth < 500))
    if ancient:
        era, cadj = "antiquity", "ancient"
    else:
        pivot = None
        if isinstance(birth, int) and isinstance(death, int) and birth > 0 and death > 0:
            pivot = (birth + death) // 2
        elif isinstance(death, int) and death > 0:
            pivot = death
        elif isinstance(birth, int) and birth > 0:
            pivot = birth
        cname = century_of(pivot)
        era = f"the {cname} century" if cname else "an earlier century"
        cadj = f"{cname}-century" if cname else "early"
    dates = ""
    if isinstance(birth, int) and isinstance(death, int) and birth < 0 and death < 0:
        dates = f"{abs(birth)}–{abs(death)} BCE"
    elif isinstance(birth, int) and isinstance(death, int) and 0 < birth <= 1928 and 0 < death <= 1928:
        dates = f"{birth}–{death}"
    elif isinstance(death, int) and 1 <= death <= 1928:
        dates = f"died {death}"
    elif isinstance(birth, int) and 1 <= birth <= 1928:
        dates = f"born {birth}"
    kind = choose_kind(book.get("subjects") or [], translated, origin)
    shelves = shelf_phrase(book.get("subjects") or ["literature"], subject_names)
    return {
        "title": title, "author": author, "poss": possessive(author),
        "about": about, "about_cap": cap(about), "role": role or "topic",
        "genre": genre or "", "kind": kind, "kind_cap": cap(kind),
        "era": era, "era_cap": cap(era), "cadj": cadj, "dates": dates,
        "year": str(year) if year else "", "shelves": shelves, "shelves_cap": cap(shelves),
        "hook": hook or "", "hook_cap": cap(hook) if hook else "",
        "color": color, "color_cap": cap(color) if color else "",
        "volume": volume_of(title) or "", "part": part_of(title) or "",
        "subtitle": subtitle or "", "shape": shape or "", "shape_rest": shape_rest or "",
        "translated": bool(translated), "origin": origin or "", "early": bool(early),
        "gutenberg": int(book.get("gutenberg") or 0),
    }
