#!/usr/bin/env python3
"""
Parse the 和合本 (Chinese Union Version) PDF into a verse-indexed JSON.

Source:  raw/09-archive/06-book/聖經/聖經-新標點_和合本.pdf  (上帝版)
Output:  app/memorize-cuv/cuv.json

Schema:
  {
    "meta": {"edition": "上帝版", "source": "...", "generated_at": "..."},
    "books": [
      {"slug": "Gen", "zh": "創世記", "abbr": "創", "order": 1, "testament": "OT"},
      ...
    ],
    "verses": [
      {"book": "Gen", "chapter": 1, "verse": 1, "text": "起初，上帝創造天地。"},
      ...
    ]
  }
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "raw/09-archive/06-book/聖經/聖經-新標點_和合本.pdf"
OUT = ROOT / "app/memorize-cuv/cuv.json"

# Canonical 66-book table: (slug, zh-name, common abbr, testament).
# zh-name must exactly match the PDF's section title text.
BOOKS = [
    ("Gen", "創世記", "創", "OT"),
    ("Exo", "出埃及記", "出", "OT"),
    ("Lev", "利未記", "利", "OT"),
    ("Num", "民數記", "民", "OT"),
    ("Deu", "申命記", "申", "OT"),
    ("Jos", "約書亞記", "書", "OT"),
    ("Jdg", "士師記", "士", "OT"),
    ("Rut", "路得記", "得", "OT"),
    ("1Sa", "撒母耳記上", "撒上", "OT"),
    ("2Sa", "撒母耳記下", "撒下", "OT"),
    ("1Ki", "列王紀上", "王上", "OT"),
    ("2Ki", "列王紀下", "王下", "OT"),
    ("1Ch", "歷代志上", "代上", "OT"),
    ("2Ch", "歷代志下", "代下", "OT"),
    ("Ezr", "以斯拉記", "拉", "OT"),
    ("Neh", "尼希米記", "尼", "OT"),
    ("Est", "以斯帖記", "斯", "OT"),
    ("Job", "約伯記", "伯", "OT"),
    ("Psa", "詩篇", "詩", "OT"),
    ("Pro", "箴言", "箴", "OT"),
    ("Ecc", "傳道書", "傳", "OT"),
    ("Sng", "雅歌", "歌", "OT"),
    ("Isa", "以賽亞書", "賽", "OT"),
    ("Jer", "耶利米書", "耶", "OT"),
    ("Lam", "耶利米哀歌", "哀", "OT"),
    ("Eze", "以西結書", "結", "OT"),
    ("Dan", "但以理書", "但", "OT"),
    ("Hos", "何西阿書", "何", "OT"),
    ("Joe", "約珥書", "珥", "OT"),
    ("Amo", "阿摩司書", "摩", "OT"),
    ("Oba", "俄巴底亞書", "俄", "OT"),
    ("Jon", "約拿書", "拿", "OT"),
    ("Mic", "彌迦書", "彌", "OT"),
    ("Nah", "那鴻書", "鴻", "OT"),
    ("Hab", "哈巴谷書", "哈", "OT"),
    ("Zep", "西番雅書", "番", "OT"),
    ("Hag", "哈該書", "該", "OT"),
    ("Zec", "撒迦利亞書", "亞", "OT"),
    ("Mal", "瑪拉基書", "瑪", "OT"),
    ("Mat", "馬太福音", "太", "NT"),
    ("Mar", "馬可福音", "可", "NT"),
    ("Luk", "路加福音", "路", "NT"),
    ("Joh", "約翰福音", "約", "NT"),
    ("Act", "使徒行傳", "徒", "NT"),
    ("Rom", "羅馬書", "羅", "NT"),
    ("1Co", "哥林多前書", "林前", "NT"),
    ("2Co", "哥林多後書", "林後", "NT"),
    ("Gal", "加拉太書", "加", "NT"),
    ("Eph", "以弗所書", "弗", "NT"),
    ("Phi", "腓立比書", "腓", "NT"),
    ("Col", "歌羅西書", "西", "NT"),
    ("1Th", "帖撒羅尼迦前書", "帖前", "NT"),
    ("2Th", "帖撒羅尼迦後書", "帖後", "NT"),
    ("1Ti", "提摩太前書", "提前", "NT"),
    ("2Ti", "提摩太後書", "提後", "NT"),
    ("Tit", "提多書", "多", "NT"),
    ("Phm", "腓利門書", "門", "NT"),
    ("Heb", "希伯來書", "來", "NT"),
    ("Jas", "雅各書", "雅", "NT"),
    ("1Pe", "彼得前書", "彼前", "NT"),
    ("2Pe", "彼得後書", "彼後", "NT"),
    ("1Jo", "約翰一書", "約一", "NT"),
    ("2Jo", "約翰二書", "約二", "NT"),
    ("3Jo", "約翰三書", "約三", "NT"),
    ("Jud", "猶大書", "猶", "NT"),
    ("Rev", "啟示錄", "啟", "NT"),
]
ZH_TO_SLUG = {b[1]: b[0] for b in BOOKS}

# A book title line is one of these names alone (possibly with surrounding spaces).
BOOK_TITLE_RE = re.compile(r"^\s*(" + "|".join(re.escape(b[1]) for b in BOOKS) + r")\s*$")

# A page-header line. Format example: "馬可福音 2:13           1033              馬可福音 3:10"
# We detect this by: contains a book name + ":" + digit AND contains the same name twice OR a page number in middle.
PAGE_HEADER_RE = re.compile(
    r"^\s*(?P<bk>" + "|".join(re.escape(b[1]) for b in BOOKS) + r")\s+\d+[:：]\d+"
)

# Footnote at bottom of page, e.g. "2:16: 有古卷：文士和法利賽人"
FOOTNOTE_RE = re.compile(r"^\s*\d+[:：]\d+[a-z]?[:：]")

# Cross-reference for synoptic parallel, e.g. "（太9‧9－13；路5‧27－32）"
XREF_RE = re.compile(r"^\s*[（(].*?[）)]\s*$")

# A bare integer alone on a line — chapter marker (e.g. "                       3")
CHAPTER_MARKER_RE = re.compile(r"^\s*(\d{1,3})\s*$")

# A verse line: leading whitespace + number + space + text.
VERSE_START_RE = re.compile(r"^\s*(\d{1,3})\s+(\S.*)$")

# Chinese punctuation. Verse text and continuations always contain some.
# A line with none is almost certainly a section heading.
CN_PUNCT_RE = re.compile(r"[，。；：「」『』？！、（）()]")


def run_pdftotext(pdf: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, check=True,
    )
    return proc.stdout.decode("utf-8", errors="replace")


def parse(text: str):
    # Strip the TOC: book content starts after the first verse-1 of 創世記.
    lines = text.split("\n")

    verses = []  # list of (slug, chapter, verse, text)
    cur_book = None
    cur_chapter = None
    cur_verse = None
    cur_buf = []  # accumulating multi-line verse text

    def flush_verse():
        nonlocal cur_verse, cur_buf
        if cur_verse is not None and cur_buf:
            joined = "".join(cur_buf).strip()
            # Remove inline footnote markers like "[a]", "*", etc — none seen in this PDF, but defensive
            joined = re.sub(r"\s+", "", joined)  # Chinese: no internal spaces needed
            verses.append((cur_book, cur_chapter, cur_verse, joined))
        cur_verse = None
        cur_buf = []

    # Heuristic: TOC has lines like "創世記 . . . . 1" with many dots. Skip until we see an actual verse.
    in_body = False

    for raw in lines:
        line = raw.rstrip()

        if not in_body:
            # Look for the FIRST occurrence of a real verse-1 line under 創世記.
            # The TOC lines for 創世記 contain dots; the body has " 1 起初，..."
            if re.match(r"^\s*1\s+起初", line):
                in_body = True
                cur_book = "Gen"
                cur_chapter = 1
                cur_verse = 1
                cur_buf = [line.split(None, 1)[1]]
                continue
            else:
                continue

        # In body now.
        if not line.strip():
            # Blank line: do NOT flush — multi-line verses may have blanks between sections.
            # We flush only when next verse/chapter/book marker appears.
            continue

        # Page header
        if PAGE_HEADER_RE.match(line) and re.search(r"\d+\s*[:：]\s*\d+.*\d+", line):
            # Looks like a page header (book name + ref ... page-num ... book name + ref)
            # More permissive check: a page header has at least 2 colons or has lots of whitespace gaps
            if line.count(":") >= 2 or len(re.findall(r"\s{4,}", line)) >= 2:
                continue

        # Footnote
        if FOOTNOTE_RE.match(line):
            continue

        # Cross-reference / parallel
        if XREF_RE.match(line):
            continue

        # Book title — switch book
        m = BOOK_TITLE_RE.match(line)
        if m:
            flush_verse()
            new_slug = ZH_TO_SLUG[m.group(1)]
            if new_slug != cur_book:
                cur_book = new_slug
                cur_chapter = 1  # first chapter of new book; no chapter marker before ch.1 in this PDF
                cur_verse = None
            continue

        # Chapter marker (lone number). A line that is *only* a number — not a verse-start —
        # in plausible chapter range. Flush whatever verse buffer we had.
        m_chap = CHAPTER_MARKER_RE.match(line)
        m_verse = VERSE_START_RE.match(line)
        if m_chap and not m_verse:
            num = int(m_chap.group(1))
            if 1 <= num <= 200:  # max chapter count is Psalm 150; cap conservatively
                flush_verse()
                cur_chapter = num
                cur_verse = None
                continue
            # else: likely a page number — skip
            continue

        # Verse start
        m = VERSE_START_RE.match(line)
        if m:
            num = int(m.group(1))
            rest = m.group(2)
            # Heuristic: if cur_verse is set and num == cur_verse + 1, it's the next verse.
            # If num == 1 and cur_verse is not None and cur_verse > 1, we missed a chapter marker — start new chapter.
            if cur_verse is None:
                # First verse of chapter
                flush_verse()
                cur_verse = num
                cur_buf = [rest]
            elif num == cur_verse + 1 or (num == 1 and cur_verse and cur_verse > 1):
                if num == 1 and cur_verse and cur_verse > 1:
                    # Implicit chapter advance
                    flush_verse()
                    cur_chapter = (cur_chapter or 0) + 1
                    cur_verse = 1
                    cur_buf = [rest]
                else:
                    flush_verse()
                    cur_verse = num
                    cur_buf = [rest]
            elif num == cur_verse:
                # Re-encounter: probably a wrapped line that looks like " 12 ..." but isn't. Treat as continuation.
                cur_buf.append(line.strip())
            else:
                # Big jump (e.g. verse 24 → 26: rare but legit when manuscript omits a verse).
                # Or a misparse. Accept it.
                flush_verse()
                cur_verse = num
                cur_buf = [rest]
            continue

        # Otherwise: either a wrapped continuation OR a section heading.
        # Section headings contain NO Chinese punctuation; verse text always does.
        if cur_verse is not None and CN_PUNCT_RE.search(line):
            cur_buf.append(line.strip())
        # else: silently drop section heading

    flush_verse()
    return verses


def main():
    if not PDF.exists():
        print(f"PDF not found: {PDF}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting {PDF.name} ...", file=sys.stderr)
    text = run_pdftotext(PDF)
    print(f"  {len(text):,} chars extracted", file=sys.stderr)

    print("Parsing ...", file=sys.stderr)
    verses = parse(text)
    print(f"  {len(verses):,} verses parsed", file=sys.stderr)

    # Sanity stats
    by_book = {}
    for slug, ch, vs, _ in verses:
        by_book.setdefault(slug, set()).add((ch, vs))
    print(f"  {len(by_book)} books seen", file=sys.stderr)

    # Convert 上帝版 → 神版 by mechanical substitution. In CUV the 上帝/神 distinction
    # is purely an edition choice for rendering the divine name; non-divine 神 (神像,
    # 神氣, 外邦神, etc.) never contains the 上帝 sequence, so 上帝→神 is unambiguous.
    n_sub = sum(t.count("上帝") for _, _, _, t in verses)
    verses = [(b, c, v, t.replace("上帝", "神")) for b, c, v, t in verses]
    print(f"  上帝→神 substitution: {n_sub:,} replacements", file=sys.stderr)

    out = {
        "meta": {
            "edition": "新標點和合本（神版）",
            "edition_note": f"由上帝版 PDF 自動轉換（上帝→神，{n_sub} 處）。raw/ 內無神版 PDF。",
            "source": str(PDF.relative_to(ROOT)),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "verse_count": len(verses),
        },
        "books": [
            {"slug": s, "zh": z, "abbr": a, "order": i + 1, "testament": t}
            for i, (s, z, a, t) in enumerate(BOOKS)
        ],
        "verses": [
            {"book": s, "chapter": c, "verse": v, "text": t}
            for s, c, v, t in verses
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"Wrote {OUT.relative_to(ROOT)} ({size_mb:.2f} MB)", file=sys.stderr)

    # Print per-book verse counts for sanity check
    print("\nPer-book verse counts:", file=sys.stderr)
    for slug, zh, abbr, _ in BOOKS:
        cnt = len(by_book.get(slug, ()))
        chs = sorted(set(c for c, _ in by_book.get(slug, ())))
        ch_range = f"{min(chs)}-{max(chs)}" if chs else "—"
        print(f"  {abbr:>4} {zh:8} {cnt:>5} verses, chapters {ch_range}", file=sys.stderr)


if __name__ == "__main__":
    main()
