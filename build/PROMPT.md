# Build Prompt: 和合本背經 (CUV Bible Memorization App)

Feed this file to an LLM to reproduce the app from scratch. The prompt is self-contained — no other context required besides a working dir with Python 3, `pdftotext` (poppler), Node 18+, network access to GitHub (for OpenCC data), and the 和合本 PDF source.

---

## Goal

Build a single-file static web app that helps a Traditional-Chinese reader memorize Bible verses from the **和合本 神版 (Chinese Union Version, 神 edition)** using **Leitner-box spaced repetition**, organized as a **12-month memorization curriculum** (one theme per month). Features:

- **練習** (drill): masked-character fill-in with self-grading.
- **檢驗** (exam): voice-recognition verification with Simplified→Traditional normalization.
- **瀏覽** (browse): pick verses from the full 66-book canon.
- **我的清單** (my list): all-verses overview, grouped by month.
- **設定** (settings): voice selection, OpenAI cloud TTS.
- **Active-month filter** across drill / exam / list (defaults to current calendar month).
- **Export / import** progress as JSON.
- **TTS**: browser voice (zh-TW strict) or OpenAI cloud TTS with Taiwanese-Mandarin accent.

All UI in Traditional Chinese. Structural fields (filenames, JSON keys, slugs, function names) in English.

---

## Tech stack

- **Frontend**: a single `index.html` (HTML + CSS + JS, no framework, no build step) + `verses.js` (seed plan) + `cuv.json` (full Bible) + `s2t.js` (OpenCC char map).
- **Build scripts**: Python 3 + `pdftotext` (poppler). Two scripts: `parse_cuv.py` (PDF → JSON) and `build_s2t.py` (OpenCC → s2t.js).
- **Deployment**: GitHub Pages, public repo, root of `main` branch.
- **No backend.** All state lives in browser `localStorage`. OpenAI API key (if used) is stored client-side only.

---

## Repo layout

```
app/memorize-cuv/
├── index.html              # The app — HTML + CSS + JS
├── verses.js               # window.VERSE_PLAN — 12 monthly themes; flat window.VERSES for compat
├── cuv.json                # Full 66-book CUV (神版), ~4.7 MB, lazy-loaded
├── s2t.js                  # window.S2T — Simplified→Traditional char map, ~47 KB
├── .gitignore              # .DS_Store, *.swp
└── build/
    ├── parse_cuv.py        # PDF → cuv.json
    ├── build_s2t.py        # OpenCC data → s2t.js
    └── PROMPT.md           # This file
```

GitHub Pages serves `app/memorize-cuv/` as the site root.

---

## Data preparation

### 1. Bible PDF → `cuv.json` (`build/parse_cuv.py`)

**Source PDF**: a combined-book 和合本 上帝版 PDF (text-based, not scanned). Example location: `raw/09-archive/06-book/聖經/聖經-新標點_和合本.pdf`.

**Extraction**: `pdftotext -layout <pdf> -` (preserves column layout). State-machine parser; do NOT use pdfplumber or any heavy dependency.

**Parser rules** (specific to this PDF, may apply to similarly-typeset CUV editions):

- Verse lines: `\s*<num>\s+<text>` (leading whitespace, number, space, content).
- Chapter markers: a **lone number** on its own line (often indented). There is no explicit "Chapter N" header — the chapter number sits alone between verse 28 of chapter N and verse 1 of chapter N+1.
- Page headers like `馬可福音 2:13           1033              馬可福音 3:10` — skip.
- Footnotes at page bottom like `2:16: 有古卷：文士和法利賽人` — skip.
- Parallel passage cross-refs like `（太9‧9－13；路5‧27－32）` — skip.
- Section headings (e.g. `呼召利未`, `禁食的問題`) are short Chinese strings with **no Chinese punctuation**. They are NOT verse continuations. Detect by absence of `[，。；：「」？！、（）]` and discard.
- A single verse may wrap across multiple lines. Treat any non-marker, non-header line that **contains Chinese punctuation** as a continuation of the current verse.

**66-book canonical table** (slug, zh, abbr, testament — order matters):

| # | slug | zh | abbr | T |   | # | slug | zh | abbr | T |
|---|------|----|------|---|---|---|------|----|------|---|
| 1 | Gen | 創世記 | 創 | OT |   | 34 | Nah | 那鴻書 | 鴻 | OT |
| 2 | Exo | 出埃及記 | 出 | OT |   | 35 | Hab | 哈巴谷書 | 哈 | OT |
| 3 | Lev | 利未記 | 利 | OT |   | 36 | Zep | 西番雅書 | 番 | OT |
| 4 | Num | 民數記 | 民 | OT |   | 37 | Hag | 哈該書 | 該 | OT |
| 5 | Deu | 申命記 | 申 | OT |   | 38 | Zec | 撒迦利亞書 | 亞 | OT |
| 6 | Jos | 約書亞記 | 書 | OT |   | 39 | Mal | 瑪拉基書 | 瑪 | OT |
| 7 | Jdg | 士師記 | 士 | OT |   | 40 | Mat | 馬太福音 | 太 | NT |
| 8 | Rut | 路得記 | 得 | OT |   | 41 | Mar | 馬可福音 | 可 | NT |
| 9 | 1Sa | 撒母耳記上 | 撒上 | OT |  | 42 | Luk | 路加福音 | 路 | NT |
| 10 | 2Sa | 撒母耳記下 | 撒下 | OT |  | 43 | Joh | 約翰福音 | 約 | NT |
| 11 | 1Ki | 列王紀上 | 王上 | OT |  | 44 | Act | 使徒行傳 | 徒 | NT |
| 12 | 2Ki | 列王紀下 | 王下 | OT |  | 45 | Rom | 羅馬書 | 羅 | NT |
| 13 | 1Ch | 歷代志上 | 代上 | OT |  | 46 | 1Co | 哥林多前書 | 林前 | NT |
| 14 | 2Ch | 歷代志下 | 代下 | OT |  | 47 | 2Co | 哥林多後書 | 林後 | NT |
| 15 | Ezr | 以斯拉記 | 拉 | OT |   | 48 | Gal | 加拉太書 | 加 | NT |
| 16 | Neh | 尼希米記 | 尼 | OT |   | 49 | Eph | 以弗所書 | 弗 | NT |
| 17 | Est | 以斯帖記 | 斯 | OT |   | 50 | Phi | 腓立比書 | 腓 | NT |
| 18 | Job | 約伯記 | 伯 | OT |   | 51 | Col | 歌羅西書 | 西 | NT |
| 19 | Psa | 詩篇 | 詩 | OT |   | 52 | 1Th | 帖撒羅尼迦前書 | 帖前 | NT |
| 20 | Pro | 箴言 | 箴 | OT |   | 53 | 2Th | 帖撒羅尼迦後書 | 帖後 | NT |
| 21 | Ecc | 傳道書 | 傳 | OT |   | 54 | 1Ti | 提摩太前書 | 提前 | NT |
| 22 | Sng | 雅歌 | 歌 | OT |   | 55 | 2Ti | 提摩太後書 | 提後 | NT |
| 23 | Isa | 以賽亞書 | 賽 | OT |   | 56 | Tit | 提多書 | 多 | NT |
| 24 | Jer | 耶利米書 | 耶 | OT |   | 57 | Phm | 腓利門書 | 門 | NT |
| 25 | Lam | 耶利米哀歌 | 哀 | OT |   | 58 | Heb | 希伯來書 | 來 | NT |
| 26 | Eze | 以西結書 | 結 | OT |   | 59 | Jas | 雅各書 | 雅 | NT |
| 27 | Dan | 但以理書 | 但 | OT |   | 60 | 1Pe | 彼得前書 | 彼前 | NT |
| 28 | Hos | 何西阿書 | 何 | OT |   | 61 | 2Pe | 彼得後書 | 彼後 | NT |
| 29 | Joe | 約珥書 | 珥 | OT |   | 62 | 1Jo | 約翰一書 | 約一 | NT |
| 30 | Amo | 阿摩司書 | 摩 | OT |   | 63 | 2Jo | 約翰二書 | 約二 | NT |
| 31 | Oba | 俄巴底亞書 | 俄 | OT |   | 64 | 3Jo | 約翰三書 | 約三 | NT |
| 32 | Jon | 約拿書 | 拿 | OT |   | 65 | Jud | 猶大書 | 猶 | NT |
| 33 | Mic | 彌迦書 | 彌 | OT |   | 66 | Rev | 啟示錄 | 啟 | NT |

**上帝版 → 神版 conversion**: The 和合本 神版/上帝版 publishing variants differ in **one mechanical substitution**: every occurrence of `上帝` becomes `神`. Non-divine standalone `神` (神像, 神氣, 外邦神, etc.) never contains the `上帝` sequence, so `上帝→神` is unambiguous. The parser must perform this substitution at output time and document it in `meta.edition_note`.

**Output schema** (`cuv.json`):
```json
{
  "meta": {
    "edition": "新標點和合本（神版）",
    "edition_note": "由上帝版 PDF 自動轉換（上帝→神，<N> 處）。",
    "source": "raw/.../聖經-新標點_和合本.pdf",
    "generated_at": "<ISO 8601>",
    "verse_count": 30951
  },
  "books": [
    {"slug": "Gen", "zh": "創世記", "abbr": "創", "order": 1, "testament": "OT"},
    ...
  ],
  "verses": [
    {"book": "Gen", "chapter": 1, "verse": 1, "text": "起初，神創造天地。"},
    ...
  ]
}
```

Expected size: ~4.7 MB. Expected verse count: ~30,950 (~99.5% of canonical ~31,103). Validation: `創 1:1`, `約 1:1`, `約 3:16` (神愛世人), `詩 23:1`, `詩 150:6` (final 詩篇 verse), `啟 22:21` (final NT verse). No verse text contains `上帝`.

### 2. Simplified→Traditional map → `s2t.js` (`build/build_s2t.py`)

Browser speech recognizers (especially Google's, used by Chrome) often return Simplified characters even with `lang="zh-TW"` set. The 檢驗 view normalizes recognized text before comparison.

**Sources** (fetched at build time from OpenCC's GitHub):
- `STCharacters.txt` — Simplified → Traditional (3,882 entries).
- `TWVariants.txt` — General Traditional → TW-variant Traditional. Read **reversed** so TW-variant chars (e.g. 著, 裡, 爲) map back to general Traditional (着, 裏, 為) which is what CUV uses.

**Merge logic**:
1. Parse STCharacters into `s2t = {simp: trad}` (first Traditional candidate per Simplified).
2. Parse TWVariants reversed into `tw2t = {tw_variant: general}`.
3. For each `(simp → trad)` in s2t, if `trad ∈ tw2t`, replace with `tw2t[trad]`.
4. Add direct `tw2t` entries to the merged map for chars that recognizers might emit directly as TW-variant Traditional.

**Output**: `s2t.js` = `window.S2T = { "简": "簡", ... };` — ~47 KB.

---

## Verse plan: 12-month curriculum

`verses.js` exposes both a structured 12-month plan and a flat array (backward compat):

```js
window.VERSE_PLAN = {
  meta: { name: "12 個月背經計劃", description: "每月一個主題,逐節背誦。" },
  months: [
    { month: 1,  theme: "屬靈的軍裝 (弗 6:12-18)",      verses: [...] },
    { month: 2,  theme: "效法基督 (腓 3:10-14)",        verses: [...] },
    { month: 3,  theme: "八福 (太 5:3-10)",            verses: [...] },
    { month: 4,  theme: "受苦的救主 (彼前 2:21-25)",     verses: [...] },
    { month: 5,  theme: "教會異象 (啟 22:1-5)",         verses: [...] },
    { month: 6,  theme: "成全聖徒 (弗 4:11-16)",        verses: [...] },
    { month: 7,  theme: "團隊事奉 (腓 2:1-5)",          verses: [...] },
    { month: 8,  theme: "信心跨越 (來 11:1-6)",         verses: [...] },
    { month: 9,  theme: "不斷更新 (賽 43:15-19)",       verses: [...] },
    { month: 10, theme: "慷慨樂施 (林後 9:6-11)",       verses: [...] },
    { month: 11, theme: "信靠跟隨 (詩 23:1-6)",         verses: [...] },
    { month: 12, theme: "主禱文 (太 6:9-13)",          verses: [...] },
  ],
};

// Each verse gets month + theme attached when flattened (legacy compat):
window.VERSES = window.VERSE_PLAN.months.flatMap(m =>
  m.verses.map(v => ({ ...v, month: m.month, theme: m.theme }))
);
```

**Total: 69 verses across 12 months.** All verse text must be copied **exactly** from `cuv.json` — do not retype, as punctuation widths (`，` vs `,`) and Han forms must match exactly.

---

## Application requirements

### Storage keys (localStorage)

```
bible-memorize-progress-v1   → { "<ref>": { box: 0..4, lastReviewed: ISO } }
bible-memorize-custom-v1     → [{ ref, text }, ...]   user-added via 瀏覽
bible-memorize-settings-v1   → { voiceURI, rate, pitch, openai: { enabled, apiKey, voice, model } }
bible-memorize-month-v1      → "all" | "1".."12"   active-month filter
```

### Top navigation

Five tabs: **練習** | **檢驗** | **瀏覽** | **我的清單** | **設定**

Header stats: `<月份>月 · 今日 N · 共 N · 已熟練 N` (the month prefix omitted when active month = `"all"`).

Footer: `匯出進度` | `匯入進度` (file picker) | `清除進度` (with confirm).

### Active-month filter

Default = current calendar month (`new Date().getMonth()+1`), or `"all"` if the current month has zero verses. Selection persists in `MONTH_KEY`.

A `📅` selector bar renders above the card in **練習** / **檢驗** / **我的清單** (NOT 瀏覽 / 設定). Options:
- `全部月份`
- `1月 — 屬靈的軍裝 (弗 6:12-18) (7)` — each option lists month, theme, and verse count. `(空)` if zero.

Drill / exam queues use `activeVerses()` (= `allVerses().filter(v => v.month === activeMonth)`). Stats and box distribution also use `activeVerses()` so user sees focused progress.

### View 1 — 練習 (drill, masked-character)

- Verses = seed (`window.VERSES`) ∪ custom-added, deduped by `ref`.
- Queue = `activeVerses().filter(isDue)`, ordered: never-reviewed first, then by oldest review date.
- Due: `now - lastReviewed >= INTERVALS[box]` days. New cards (no `lastReviewed`) always due.
- **INTERVALS = `[0, 1, 3, 7, 15]` days. MAX_BOX = 4.**

**Card layout:**
- Top: `🔊 <ref> · 盒 <N>` (click 🔊 to speak the verse).
- Sub: small grey `<month>月 · <theme>` line.
- Body: verse text — every 3rd Han character visible, the rest masked as `〇` (faded). Non-Han chars always visible.
- Controls before reveal: `[提示]` (reveal one random masked char) `[顯示答案 — primary]` `[跳過]`
- After **顯示答案**: `[記得 — green]` (`box+1`) | `[忘了 — red]` (`box=0`).
- Box distribution bar at bottom.

**Empty states:** "尚未加入經文" if zero verses; "今日已完成 ✓" if zero due; "<月>月暫無經文" if active month is empty.

### View 2 — 檢驗 (voice-recognition verification)

Uses `SpeechRecognition` / `webkitSpeechRecognition` with `lang="zh-TW"`, `continuous=true`, `interimResults=true`. Pulls from `activeVerses()` queue (same Leitner rules as 練習).

**State machine** — 4 phases:

1. **ready** — show `<ref> · 盒 <N>` + theme line + **3-character hint**: `「<verse.text.slice(0,3)>…」` (centered, large). Below: small label "憑記憶背誦完整經文". Buttons: `💭 顯示經文` | `🎤 開始錄音 (primary)` | `跳過`.
2. **preview** — show full verse text (escape hatch). Buttons: `🎤 開始錄音` | `返回`.
3. **listening** — show live transcript (`traditionalize(final + interim)`). Button: `🛑 完成`.
4. **result** — show diff + stats + actions (see below).

**Normalization pipeline** (`traditionalize`): for each Han char in input, look up `window.S2T[c]` and substitute if present. Applied to:
- Spoken text before comparison (in `compareVerse`).
- Live transcript during listening.
- 你說 display in result panel.

**Comparison** (`compareVerse(canonical, spoken)`):
1. Strip both to Han-only arrays.
2. Apply `traditionalize` to the spoken array.
3. Run **LCS-based alignment**. Ops: `match` (in both, consume both pointers), `missing` (in canonical only), `extra` (in spoken only).
4. Stats: `total = canonical char count`, `matched = ops.filter(match).length`, `accuracy = matched / total`, `extras = string of extra chars`.

**Result rendering:**
- Big stat line: `✓ X / Y 字正確 (Z%)` green if Z ≥ 80, else `✗ ...` red.
- Canonical verse char-by-char: green if matched, red+bold if missed.
- Sub-block: 原文 / 你說 (final transcript, traditionalized) / 多餘字 (extras, if any, red).
- Action buttons: `通過` (box+1, same as 記得) | `不通過` (box=0, same as 忘了) | `再試` (back to ready, same verse) | implicit `下一節` via next render.

**Resource lifecycle:**
- Abort active recognition when navigating away from 檢驗 (`setView` cleanup).
- `rec.onend` → `finalizeExamListening()`, which guards against re-entry by checking `exam.phase === "listening"`.

**Error handling:**
- If `SpeechRecognition` unavailable (Firefox), show notice pointing to Chrome / Safari / Edge.
- `not-allowed` → alert about mic permission.
- `no-speech` / `aborted` → silently reset to ready.

**Platform notes:**
- iOS Safari 14.5+: works; `continuous=true` may auto-stop on long pauses — user can re-trigger.
- Chrome: requires HTTPS or localhost; LAN HTTP origins are silently blocked.

### View 3 — 瀏覽 (browse)

Three sub-tabs:
- **直接輸入**: parse `可 10:45` / `馬可福音 10:45` / `mar 10:45`. Live preview + `加入` button.
- **搜尋經文**: substring search across all `cuv.json` verses. Min 2 chars, debounced 150 ms, cap 50 results.
- **按卷目錄**: book grid (舊約 / 新約) → chapter grid → verse list with `加入` per row.

`cuv.json` is **lazy-loaded** on first browse open. The `加入` button becomes `已加入` (green) once added. Adds store `{ref, text}` into `customVerses` (no month attached, so they group under "其他 / 自訂" in 我的清單).

### View 4 — 我的清單 (my list)

All verses grouped by month with section headers:
- `1月 — 屬靈的軍裝 (弗 6:12-18) (7)` — per-month subhead with verse count.
- For each verse: `<ref> · 盒 <N> · <due-status>` + verse body + 內建 tag OR 移除 button (red).
- Custom verses appear under "其他 / 自訂".

Removing a custom verse also deletes its progress entry.

### View 5 — 設定 (settings)

**Section A — Browser voice (Web Speech API)**

- Voice dropdown: **strict zh-TW only**. Within zh-TW, prefer voices whose `name` matches `/google/i`; fall back to all zh-TW voices. If no zh-TW voice exists, fall back to all zh voices and add a `⚠ 非 TW` tag.
- Empty state: "此瀏覽器找不到 zh-TW 聲音。可改用 Chrome,或啟用下方 OpenAI 雲端朗讀(可指定台灣國語腔調)。"
- Sliders: 語速 (rate, 0.5–1.5, default 0.85), 音高 (pitch, 0.5–1.5, default 1.0).
- Buttons: `🔊 試聽` (always uses browser voice for A/B comparison) | `恢復預設`.
- `speakViaBrowser` sets `u.lang = "zh-TW"` regardless of picked voice's lang, to hint Taiwanese pronunciation.

**Section B — OpenAI cloud TTS (optional)**

- Header: "OpenAI 雲端朗讀(更自然的人聲)" + checkbox `啟用`.
- Hint: explain that 🔊 will use OpenAI, ~$0.0015 cent / 字 ($15/1M chars on `tts-1`).
- Password input for API key (`sk-...`). Stored in localStorage only; warn user.
- Voice dropdown: alloy / echo / fable / onyx / nova / shimmer (with Chinese gender hints).
- Model dropdown (this exact order):
  - `gpt-4o-mini-tts(推薦,支援台灣國語腔調)` ← default
  - `tts-1-hd(高品質,通用普通話)`
  - `tts-1(快、便宜,通用普通話)`
- `🔊 試聽 OpenAI` button (disabled when no key) — shows "下載中…" during fetch.

**Dispatch:**
```js
async function speak(text) {
  if (settings.openai?.enabled && settings.openai?.apiKey) return speakViaOpenAI(text);
  return speakViaBrowser(text);
}
```

**OpenAI request:**
```js
POST https://api.openai.com/v1/audio/speech
Authorization: Bearer <key>
Content-Type: application/json
{
  model, input: text, voice,
  speed: clamp(settings.rate, 0.25, 4.0),
  response_format: "mp3",
  // ONLY for gpt-4o-mini-tts (which supports `instructions`):
  instructions: "請以台灣國語(繁體中文)朗讀這段聖經經文。發音清晰、語速穩定、語氣莊重恭敬,符合 zh-TW 口音,不要使用大陸普通話腔調。"
}
```

Older `tts-1` / `tts-1-hd` ignore `instructions`; omit the field for those models.

Cache the resulting MP3 blob URL in an in-memory `Map<"voice|model|rate|text", url>`. Reuse for repeated 🔊 of the same verse within a session.

### Export / Import

**Export**: download `背經進度-YYYY-MM-DD.json`:
```json
{ "progress": {...}, "customVerses": [...], "exportedAt": "<ISO>", "version": 1 }
```

**Import**: file picker → parse JSON → merge:
- `progress`: per-ref keep the entry with higher `box`; on tie, the later `lastReviewed`.
- `customVerses`: dedupe by `ref`, append new ones.

### Reset

`清除進度` footer link with `confirm()` — wipes `PROGRESS_KEY` and `CUSTOM_KEY`; preserves `SETTINGS_KEY` and `MONTH_KEY`.

---

## Visual style

Quiet, readable, slightly warm. NOT material design, NOT iOS chrome.

```css
:root {
  --bg:    #fafaf7;
  --card:  #ffffff;
  --ink:   #2a2a2a;
  --muted: #8a8a8a;
  --accent:#6b4f3a;
  --ok:    #4a7c59;
  --no:    #a8615a;
  --line:  #e5e0d8;
}
```

- Body font: `-apple-system, "PingFang TC", "Microsoft JhengHei", "Noto Serif TC", serif`
- Verse text font: `"Noto Serif TC", "Songti TC", serif`, size 1.35rem, line-height 2.1
- Container max-width: 720 px
- Mobile-friendly: `<meta viewport>` + flex/grid layouts.

---

## Default seed verses (`verses.js`, 12 months × ~5–8 verses = 69 cards)

Build the `VERSE_PLAN.months` array using these (ref, text) pairs. **Text must come from `cuv.json` verbatim** — full-width punctuation, Han forms must match exactly. (Examples shown abbreviated; full text per verse is whatever `cuv.json` returns for that reference.)

| 月 | 主題 | 經文範圍 | 節數 |
|---|---|---|---|
| 1 | 屬靈的軍裝 | 弗 6:12-18 | 7 |
| 2 | 效法基督 | 腓 3:10-14 | 5 |
| 3 | 八福 | 太 5:3-10 | 8 |
| 4 | 受苦的救主 | 彼前 2:21-25 | 5 |
| 5 | 教會異象 | 啟 22:1-5 | 5 |
| 6 | 成全聖徒 | 弗 4:11-16 | 6 |
| 7 | 團隊事奉 | 腓 2:1-5 | 5 |
| 8 | 信心跨越 | 來 11:1-6 | 6 |
| 9 | 不斷更新 | 賽 43:15-19 | 5 |
| 10 | 慷慨樂施 | 林後 9:6-11 | 6 |
| 11 | 信靠跟隨 | 詩 23:1-6 | 6 |
| 12 | 主禱文 | 太 6:9-13 | 5 |
|   |   | **總計** | **69** |

Use `parse_cuv.py` output → `cuv.json` to pull the canonical text per verse. Do NOT retype.

---

## Deployment

1. `cd app/memorize-cuv`
2. `git init -b main`
3. `git add -A && git commit -s -m "Initial commit"` (always use `-s`)
4. Create a public repo on GitHub. Public URL: `https://<user>.github.io/<repo>/`.
5. `git remote add origin git@github.com:<user>/<repo>.git` (SSH recommended; HTTPS needs PAT or credential helper)
6. `git push -u origin main`
7. Repo Settings → Pages → Source: `main` / `/ (root)` → Save.
8. Wait ~1 min for first build. URL appears in green banner.

`cuv.json` is 4.7 MB — well under the 100 MB per-file Pages limit. Total repo size well under 1 GB limit.

---

## Non-goals (do NOT build)

- A backend / database.
- User accounts / multi-device sync (use export/import for cross-device).
- A real native iOS app (deployed web app + "Add to Home Screen" on iPhone Safari is sufficient).
- Multiple Bible translations in one app (would be a separate dropdown if added later).
- A "type the verse from memory" mode (deferred — 練習 fill-in-blank + 檢驗 voice are the primaries).
- Streak counters, gamification, social features.

---

## Testing checklist (manual)

After build, verify on localhost or GitHub Pages:

**練習**
- [ ] Default 30+ verses loaded; active month bar appears at top.
- [ ] Card body: every 3rd Han char visible, rest 〇.
- [ ] 提示 reveals one char; 顯示答案 unmasks all and switches to OK/NG.
- [ ] 記得 → next card with `box+1`; 忘了 → resets to box 0.
- [ ] Month selector switches the queue.

**檢驗**
- [ ] Ready screen shows `「<first-3-chars>…」` hint, not the full verse.
- [ ] 開始錄音 triggers mic permission prompt (first time).
- [ ] Live transcript updates as you speak.
- [ ] Recognized Simplified chars (`城内`, `当中`, `从神`) are converted to Traditional in 你說 and used for comparison.
- [ ] Result: green/red highlights match expected diff; 多餘字 shown if applicable.
- [ ] 通過 / 不通過 advance / reset Leitner box.
- [ ] Navigating away while listening cancels recognition cleanly.

**瀏覽**
- [ ] 直接輸入 `可 10:45` → shows verse + 加入.
- [ ] 搜尋 `愛是恆久` → finds 林前 13:4.
- [ ] 按卷目錄 → 馬可福音 → 1 → list of all 馬可福音 1 verses.

**我的清單**
- [ ] Verses grouped by month with subheads.
- [ ] Seed tagged 內建; custom verses have 移除.

**設定**
- [ ] Voice dropdown shows only zh-TW voices.
- [ ] 試聽 plays a sample with browser voice.
- [ ] OpenAI section accepts key; 試聽 OpenAI plays MP3 via cloud.
- [ ] Switching to gpt-4o-mini-tts uses Taiwanese-Mandarin instruction.

**Export / import**
- [ ] 匯出 downloads a JSON.
- [ ] 匯入 the same file merges idempotently.
- [ ] 清除進度 wipes progress + customVerses; preserves settings.

**Mobile (iPhone Safari)**
- [ ] App loads and is responsive.
- [ ] Mic permission flow works after "Add to Home Screen".
- [ ] Voice falls back to Apple voices (e.g. 美嘉) when Google not available.
