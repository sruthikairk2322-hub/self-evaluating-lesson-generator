"""Checks done by plain code. They are cheap, repeatable and cannot be charmed by a nice-sounding lesson."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .rubric import check_by_id


@dataclass
class CheckResult:
    id: str
    passed: bool
    reason: str = ""
    evidence: str = ""
    fix: str = ""
    kind: str = "code"
    evidence_verified: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- parsing
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|(?<=[.!?]["”’)])\s+')
_NEG = re.compile(
    r"\b(not|never|no|without|cannot|unlike|instead|rather|different|myth|false)\b|n['’]t", re.I
)
GLOSSARY_TITLES = re.compile(r"words to know|glossary|key terms|key words", re.I)


def _clean_inline(s: str) -> str:
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def _clean_line(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"^>+\s*", "", s)
    s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
    return _clean_inline(s)


def parse(md: str) -> dict:
    sections: list[dict] = []
    cur: dict | None = None
    in_code = False
    lines: list[tuple[str, str]] = []  # (line, section title)
    for raw in md.splitlines():
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _HEADING.match(raw)
        if m:
            cur = {"level": len(m.group(1)), "title": _clean_inline(m.group(2)), "lines": []}
            sections.append(cur)
            continue
        line = _clean_line(raw)
        if not line:
            continue
        if cur is None:
            cur = {"level": 0, "title": "", "lines": []}
            sections.append(cur)
        cur["lines"].append(line)
        lines.append((line, cur["title"]))
    sentences: list[str] = []
    sentence_section: list[str] = []
    for line, title in lines:
        for s in _SENT_SPLIT.split(line):
            s = s.strip()
            if s:
                sentences.append(s)
                sentence_section.append(title)
    return {"sections": sections, "sentences": sentences, "sentence_section": sentence_section}


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’\-]*", text)


def _syllables(word: str) -> int:
    total = 0
    for part in word.lower().split("-"):
        w = re.sub(r"[^a-z]", "", part)
        if not w:
            continue
        if len(w) <= 3:
            total += 1
            continue
        w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
        w = re.sub(r"^y", "", w)
        total += max(1, len(re.findall(r"[aeiouy]{1,2}", w)))
    return max(1, total)


# ---------------------------------------------------------------- checks
def _result(rubric: dict, cid: str, passed: bool, reason: str, evidence: str = "") -> CheckResult:
    fix = "" if passed else check_by_id(rubric, cid)["fix_hint"]
    return CheckResult(id=cid, passed=passed, reason=reason, evidence=evidence[:300], fix=fix)


def check_reading_level(p: dict, rubric: dict) -> CheckResult:
    th = rubric["thresholds"]["reading_level"]
    sents = [(s, words(s)) for s in p["sentences"]]
    sents = [(s, w) for s, w in sents if w]
    if not sents:
        return _result(rubric, "reading_level", False, "No readable sentences found.")
    counts = [len(w) for _, w in sents]
    avg = sum(counts) / len(counts)
    all_words = [x for _, w in sents for x in w]
    syl = sum(_syllables(x) for x in all_words)
    fk = 0.39 * avg + 11.8 * (syl / len(all_words)) - 15.59
    longest_i = max(range(len(counts)), key=counts.__getitem__)
    problems = []
    if avg > th["max_avg_sentence_words"]:
        problems.append(f"average sentence is {avg:.1f} words (max {th['max_avg_sentence_words']})")
    if counts[longest_i] > th["max_sentence_words"]:
        problems.append(f"longest sentence has {counts[longest_i]} words (max {th['max_sentence_words']})")
    if fk > th["max_fk_grade"]:
        problems.append(f"reading grade is {fk:.1f} (max {th['max_fk_grade']})")
    if problems:
        return _result(rubric, "reading_level", False, "; ".join(problems), sents[longest_i][0])
    return _result(rubric, "reading_level", True, f"avg {avg:.1f} words/sentence, longest {counts[longest_i]}, grade {fk:.1f}")


def check_structure(p: dict, rubric: dict) -> CheckResult:
    h2 = [s["title"] for s in p["sections"] if s["level"] == 2]
    missing, positions = [], []
    for sec in rubric["required_sections"]:
        pat = re.compile(sec["pattern"], re.I)
        idx = next((i for i, t in enumerate(h2) if pat.search(t)), None)
        label = sec["label"].replace("{topic}", "<topic>")
        if idx is None:
            missing.append(label)
        else:
            positions.append((label, idx))
    if missing:
        return _result(rubric, "structure", False, "Missing required section(s): " + "; ".join(missing), " | ".join(h2))
    order = [i for _, i in positions]
    if order != sorted(order):
        return _result(rubric, "structure", False, "Required sections are in the wrong order.", " | ".join(h2))
    return _result(rubric, "structure", True, "All required sections are present and in order.")


def check_length(p: dict, rubric: dict) -> CheckResult:
    th = rubric["thresholds"]["length"]
    n = sum(len(words(s)) for s in p["sentences"])
    if n < th["min_words"]:
        return _result(rubric, "length", False, f"Only {n} words (minimum {th['min_words']}).")
    if n > th["max_words"]:
        return _result(rubric, "length", False, f"{n} words (maximum {th['max_words']}).")
    return _result(rubric, "length", True, f"{n} words.")


_CUE = re.compile(
    r"\b(means|stands for|is called|are called|called|refers to|short for|in other words|that is|known as)\b|\(",
    re.I,
)


def _defines(sentence: str, term_pattern: str) -> bool:
    if _CUE.search(sentence):
        return True
    return bool(re.search(term_pattern + r"[^.?!]{0,40}\b(is|are)\s+(a|an|the|when|what)\b", sentence, re.I))


def check_jargon(p: dict, rubric: dict, facts: dict) -> CheckResult:
    sents, secs = p["sentences"], p["sentence_section"]
    bad: list[tuple[str, str]] = []
    for j in facts.get("jargon", []):
        alt = "|".join(re.escape(a) for a in sorted(j["aliases"], key=len, reverse=True))
        term_pat = rf"(?<![\w-])(?:{alt})(?![\w-])"
        for i, s in enumerate(sents):
            if not re.search(term_pat, s, re.I):
                continue
            if GLOSSARY_TITLES.search(secs[i]):
                break  # first use is inside the glossary itself: fine
            # Defined in the same sentence, or in the next one if that one repeats the term itself.
            # (A neighbouring sentence that defines some OTHER word must not count.)
            window = [s]
            if i + 1 < len(sents) and re.search(term_pat, sents[i + 1], re.I):
                window.append(sents[i + 1])
            if not any(_defines(w, term_pat) for w in window):
                bad.append((j["name"], s))
            break
    if bad:
        names = ", ".join(sorted({n for n, _ in bad}))
        return _result(rubric, "jargon_defined", False, f"Not explained at first use: {names}.", bad[0][1])
    return _result(rubric, "jargon_defined", True, "Every listed technical term is explained at first use.")


def check_misconceptions(p: dict, rubric: dict, facts: dict) -> CheckResult:
    for claim in facts.get("wrong_claims", []):
        pat = re.compile(claim["pattern"], re.I)
        for s in p["sentences"]:
            if claim.get("skip_if_negated") and _NEG.search(s):
                continue
            if pat.search(s):
                return _result(rubric, "no_known_misconceptions", False,
                               f"False or unsupported claim. The truth: {claim['why']}", s)
    return _result(rubric, "no_known_misconceptions", True, "No known false or unsupported claims found.")


def check_plain_words(p: dict, rubric: dict) -> CheckResult:
    pw = rubric["plain_words"]
    found: list[tuple[str, str]] = []
    for group in ("idioms", "hard_words", "latin_abbreviations"):
        for term in pw.get(group, []):
            pat = re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", re.I)
            for s in p["sentences"]:
                if pat.search(s):
                    found.append((term, s))
                    break
    if found:
        terms = ", ".join(sorted({t for t, _ in found}))
        return _result(rubric, "plain_words", False, f"Idioms or hard words found: {terms}.", found[0][1])
    return _result(rubric, "plain_words", True, "Plain words only.")


def run_code_checks(lesson: str, rubric: dict, facts: dict) -> list[CheckResult]:
    p = parse(lesson)
    return [
        check_reading_level(p, rubric),
        check_structure(p, rubric),
        check_length(p, rubric),
        check_jargon(p, rubric, facts),
        check_misconceptions(p, rubric, facts),
        check_plain_words(p, rubric),
    ]
