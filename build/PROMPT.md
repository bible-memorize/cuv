# Build Prompt: 和合本背經 (CUV Bible Memorization App)

Feed this entire file to an LLM to reproduce the app. The prompt is self-contained — no other context required besides a working dir, Python 3, `pdftotext` (poppler), Node 18+, and the 和合本 PDF source.

---

## Goal

Build a single-file static web app that helps a user memorize Bible verses from the **和合本 神版 (Chinese Union Version, 神 edition)** using **Leitner-box spaced repetition**, a **browse / search picker** backed by the full 66-book canon, **export/import** of progress, and **text-to-speech** (browser + optional OpenAI cloud).

The app is for Traditional Chinese readers. All UI is in Traditional Chinese. Structural fields (filenames, JSON keys, slugs, function names) stay in English.

---

## Tech stack

- **Frontend**: a single `index.html` containing HTML + CSS + JS (no build step, no framework). Plus `verses.js` (seed) and `cuv.json` (full Bible data).
- **Build script**: Python 3 + `pdftotext` (poppler), no other deps. Parses the PDF to a verse-indexed JSON.
- **Deployment**: GitHub Pages, public repo, root of `main` branch.
- **No backend.** All state lives in `localStorage`.

---

## Repo layout

```
app/memorize/
├── index.html              # The app
├── verses.js               # window.VERSES = [{ref, text}, ...]   seed verses
├── cuv.json                # Full 66-book CUV (神版), ~4.7 MB
├── .gitignore              # .DS_Store, *.swp
└── build/
    ├── parse_cuv.py        # PDF → cuv.json
    └── PROMPT.md           # This file
```

GitHub Pages serves `app/memorize/` as the site root.

---

## Data preparation

### Source PDF

A combined-book 和合本 上帝版 PDF (text-based, not scanned). Example location:
```
raw/09-archive/06-book/聖經/聖經-新標點_和合本.pdf
```

### Parser (`build/parse_cuv.py`)

Use `pdftotext -layout <pdf> -` to extract text preserving column layout. Parse with a state machine; **don't** use pdfplumber or any heavy lib.

Parser observations (specific to this PDF, may apply to similarly-typeset CUV PDFs):

- Verse lines have format `\s*<num>\s+<text>` (leading whitespace, number, space, content).
- Chapter markers are a **lone number** on its own line (e.g. just `3` between chapters 2 and 3), often indented. There is no explicit "Chapter N" header.
- Page headers look like `馬可福音 2:13           1033              馬可福音 3:10` and must be skipped.
- Footnotes at page bottom look like `2:16: 有古卷：文士和法利賽人` — skip.
- Parallel passage cross-refs look like `（太9‧9－13；路5‧27－32）` — skip.
- Section headings (e.g. `呼召利未`, `禁食的問題`) are short Chinese strings with **no Chinese punctuation**. They are NOT verse continuations. Detect by `^[no 中文 punctuation]$` and discard.
- A single verse may wrap across multiple lines. Treat any non-marker, non-header line that **contains Chinese punctuation** as a continuation of the current verse.

### Book table

Use this exact 66-book table (slug, zh-name, abbr, testament) — order matters:

| # | slug | zh | abbr | T |
|---|------|----|------|---|
| 1 | Gen | 創世記 | 創 | OT |
| 2 | Exo | 出埃及記 | 出 | OT |
| 3 | Lev | 利未記 | 利 | OT |
| 4 | Num | 民數記 | 民 | OT |
| 5 | Deu | 申命記 | 申 | OT |
| 6 | Jos | 約書亞記 | 書 | OT |
| 7 | Jdg | 士師記 | 士 | OT |
| 8 | Rut | 路得記 | 得 | OT |
| 9 | 1Sa | 撒母耳記上 | 撒上 | OT |
| 10 | 2Sa | 撒母耳記下 | 撒下 | OT |
| 11 | 1Ki | 列王紀上 | 王上 | OT |
| 12 | 2Ki | 列王紀下 | 王下 | OT |
| 13 | 1Ch | 歷代志上 | 代上 | OT |
| 14 | 2Ch | 歷代志下 | 代下 | OT |
| 15 | Ezr | 以斯拉記 | 拉 | OT |
| 16 | Neh | 尼希米記 | 尼 | OT |
| 17 | Est | 以斯帖記 | 斯 | OT |
| 18 | Job | 約伯記 | 伯 | OT |
| 19 | Psa | 詩篇 | 詩 | OT |
| 20 | Pro | 箴言 | 箴 | OT |
| 21 | Ecc | 傳道書 | 傳 | OT |
| 22 | Sng | 雅歌 | 歌 | OT |
| 23 | Isa | 以賽亞書 | 賽 | OT |
| 24 | Jer | 耶利米書 | 耶 | OT |
| 25 | Lam | 耶利米哀歌 | 哀 | OT |
| 26 | Eze | 以西結書 | 結 | OT |
| 27 | Dan | 但以理書 | 但 | OT |
| 28 | Hos | 何西阿書 | 何 | OT |
| 29 | Joe | 約珥書 | 珥 | OT |
| 30 | Amo | 阿摩司書 | 摩 | OT |
| 31 | Oba | 俄巴底亞書 | 俄 | OT |
| 32 | Jon | 約拿書 | 拿 | OT |
| 33 | Mic | 彌迦書 | 彌 | OT |
| 34 | Nah | 那鴻書 | 鴻 | OT |
| 35 | Hab | 哈巴谷書 | 哈 | OT |
| 36 | Zep | 西番雅書 | 番 | OT |
| 37 | Hag | 哈該書 | 該 | OT |
| 38 | Zec | 撒迦利亞書 | 亞 | OT |
| 39 | Mal | 瑪拉基書 | 瑪 | OT |
| 40 | Mat | 馬太福音 | 太 | NT |
| 41 | Mar | 馬可福音 | 可 | NT |
| 42 | Luk | 路加福音 | 路 | NT |
| 43 | Joh | 約翰福音 | 約 | NT |
| 44 | Act | 使徒行傳 | 徒 | NT |
| 45 | Rom | 羅馬書 | 羅 | NT |
| 46 | 1Co | 哥林多前書 | 林前 | NT |
| 47 | 2Co | 哥林多後書 | 林後 | NT |
| 48 | Gal | 加拉太書 | 加 | NT |
| 49 | Eph | 以弗所書 | 弗 | NT |
| 50 | Phi | 腓立比書 | 腓 | NT |
| 51 | Col | 歌羅西書 | 西 | NT |
| 52 | 1Th | 帖撒羅尼迦前書 | 帖前 | NT |
| 53 | 2Th | 帖撒羅尼迦後書 | 帖後 | NT |
| 54 | 1Ti | 提摩太前書 | 提前 | NT |
| 55 | 2Ti | 提摩太後書 | 提後 | NT |
| 56 | Tit | 提多書 | 多 | NT |
| 57 | Phm | 腓利門書 | 門 | NT |
| 58 | Heb | 希伯來書 | 來 | NT |
| 59 | Jas | 雅各書 | 雅 | NT |
| 60 | 1Pe | 彼得前書 | 彼前 | NT |
| 61 | 2Pe | 彼得後書 | 彼後 | NT |
| 62 | 1Jo | 約翰一書 | 約一 | NT |
| 63 | 2Jo | 約翰二書 | 約二 | NT |
| 64 | 3Jo | 約翰三書 | 約三 | NT |
| 65 | Jud | 猶大書 | 猶 | NT |
| 66 | Rev | 啟示錄 | 啟 | NT |

### 上帝版 → 神版 conversion

The 和合本 神版/上帝版 differ in **one mechanical substitution**: every occurrence of `上帝` becomes `神`. Non-divine standalone `神` (神像, 神氣, 外邦神, etc.) is unaffected because it never contains the `上帝` sequence. The parser must do this substitution at output time and record it in `meta.edition_note`.

### Output JSON shape

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

Expected size: ~4.7 MB. Expected verse count: ~30,950 (~99.5% of the canonical ~31,103).

### Validation

After parsing, sanity-check that these famous verses match the canonical CUV text exactly:

- 創 1:1 = `起初，神創造天地。`
- 約 1:1 = `太初有道，道與神同在，道就是神。`
- 約 3:16 contains `神愛世人`
- 詩 23:1 = `耶和華是我的牧者，我必不致缺乏。`
- 詩篇 ends at chapter 150 verse 6
- 啟示錄 ends at chapter 22 verse 21
- All 66 books are present
- No verse text contains `上帝` anywhere

---

## Application requirements

### Storage keys

```
bible-memorize-progress-v1   → { "<ref>": { box: 0..4, lastReviewed: ISO } }
bible-memorize-custom-v1     → [{ ref, text }, ...]   user-added via browse
bible-memorize-settings-v1   → { voiceURI, rate, pitch, openai: { enabled, apiKey, voice, model } }
```

### Top navigation

Five tabs: **練習** | **檢驗** | **瀏覽** | **我的清單** | **設定**

Header shows: `今日 <N> · 全部 <N> · 已熟練 <N>`

Footer: `匯出進度` | `匯入進度` (file picker) | `清除進度` (with confirm)

### View 1 — 練習 (drill)

The current card to memorize.

- All verses = seed (`window.VERSES` from `verses.js`) ∪ custom-added, deduped by `ref`.
- Queue = verses where `isDue(ref) == true`, ordered: never-reviewed first, then by oldest review date.
- A verse is **due** if `now - lastReviewed >= INTERVALS[box]` days. New cards (no `lastReviewed`) are always due.
- INTERVALS = `[0, 1, 3, 7, 15]` days. MAX_BOX = 4.

Card layout:
- Top line: `🔊 <ref> · 盒 <N>`. Click 🔊 to speak the verse.
- Body: verse text with **every 3rd Han character visible**, the rest masked as `〇` (faded color). Non-Han characters (punctuation, digits, ASCII) always visible.
- Controls (before answer reveal): `[提示]` (reveal one random masked char) `[顯示答案 — primary]` (reveal everything; show OK/NG buttons next) `[跳過]`
- After **顯示答案** clicked: `[記得 — green]` (advance box, save lastReviewed=now) `[忘了 — red]` (reset box to 0, save lastReviewed=now)
- Box distribution shown at bottom: `盒 0: N | 盒 1: N | 盒 2: N | 盒 3: N | 盒 4: N`

Empty states:
- No verses at all → "尚未加入經文。切換到「瀏覽」分頁,搜尋或選取要背的經文。"
- No due verses → "今日已完成 ✓ 下一輪複習依 Leitner 間隔自動安排。"

### View 2 — 檢驗 (voice-recognition verification)

Uses `SpeechRecognition` / `webkitSpeechRecognition` with `lang="zh-TW"`, `continuous=true`, `interimResults=true`. Pulls from the same Leitner queue as 練習.

**State machine** with 4 phases:
1. **ready** — show `<ref> · 盒 <N>` + placeholder "憑記憶背誦". Buttons: 💭 顯示經文 | 🎤 開始錄音 | 跳過
2. **preview** — show full verse text (escape hatch). Buttons: 🎤 開始錄音 | 返回
3. **listening** — show live transcript (interim + final). Button: 🛑 完成
4. **result** — show diff + stats + actions

**Comparison algorithm** (`compareVerse`):
- Normalize both canonical and spoken text by **stripping everything except Han characters** (`[一-鿿]`).
- Run **LCS-based alignment** on the two character arrays. For each position emit one of: `match` (in both), `missing` (in canonical only), `extra` (in spoken only).
- Per-canon statuses: `match` or `miss`.
- Stats: `total = canonical char count`, `matched = match count`, `accuracy = matched / total`, `extras = string of extra chars`.

**Result rendering:**
- Big stat line: `✓ X / Y 字正確 (Z%)` if accuracy ≥ 80%, else `✗ ...` with red color.
- Canonical verse rendered char-by-char: green if matched, red+bold if missed.
- Sub-block showing 原文, 你說 (final transcript), and 多餘字 (extras, if any).
- Action buttons: **通過** (advance Leitner box, same as 練習's 記得) | **不通過** (reset to box 0, same as 忘了) | **再試** (back to ready phase, same verse).

**Resource lifecycle:**
- Always abort active recognition when navigating away from 檢驗 (`setView` cleanup).
- Use `rec.onend` to finalize results (works both for manual stop and browser auto-stop).
- Guard `finalizeExamListening()` with phase check to prevent double-finalize.

**Error handling:**
- If `SpeechRecognition` is not present (Firefox), show a notice pointing to Chrome / Safari / Edge.
- On `not-allowed` error (mic permission denied), alert the user.
- On `no-speech` or `aborted`, silently reset to ready.

**iOS notes:** the recognition must be started from a user gesture (clicking the button satisfies this). Microphone permission is requested on first use per origin.

### View 3 — 瀏覽 (browse)

Three sub-tabs:

**a. 直接輸入** — text input for reference like `可 10:45` or `馬可福音 10:45` or `mar 10:45`. Parses live; shows the verse with **加入** button. Supports abbrev (`可`), full Chinese name (`馬可福音`), and slug (`mar`, case-insensitive).

**b. 搜尋經文** — text input for substring search across all `cuv.json` verses. Minimum 2 chars, debounced 150 ms, cap 50 results. Each result shows ref + verse + **加入** button.

**c. 按卷目錄** — book grid (舊約 / 新約 sections) → click a book → chapter grid → click a chapter → all verses in that chapter with **加入** button.

`cuv.json` is **lazy-loaded** the first time 瀏覽 is opened (don't fetch on app start — it's 4.7 MB).

The **加入** button changes to **已加入** (green border, disabled) when the verse is already in the user's list. Adding stores `{ref, text}` into `customVerses` in `localStorage`.

### View 4 — 我的清單 (my list)

All verses (seed + custom). For each:
- `<ref> · 盒 <N> · <due-status>`
- Verse body
- If custom-added: **移除** button (red border)
- If seed: small grey "內建" tag (read-only)

Removing a custom verse also deletes its progress entry.

### View 5 — 設定 (settings)

Two sections:

**Section A — Browser voice (Web Speech API)**
- Dropdown: list of zh-* voices. **Filter to Google voices only** if any exist (`/google/i` test on `voice.name`); else show all zh voices. Show lang code in parens.
- Empty state: "此瀏覽器找不到中文聲音。"
- Sliders: 語速 (rate, 0.5–1.5, default 0.85) | 音高 (pitch, 0.5–1.5, default 1.0)
- Buttons: **🔊 試聽** (sample = 約 3:16 text, uses browser voice always) | **恢復預設**
- Save to `settings` on any change. Persist immediately.

**Section B — OpenAI cloud TTS (optional)**
- Header: "OpenAI 雲端朗讀(更自然的人聲)" + checkbox **啟用**
- Hint: explain that 🔊 will then use OpenAI, costs ~$15/1M chars on `tts-1`.
- Password input for API key (`placeholder="sk-..."`)
- Voice dropdown: alloy, echo, fable, onyx, nova, shimmer (with Chinese gender hints)
- Model dropdown: tts-1, tts-1-hd, gpt-4o-mini-tts
- **🔊 試聽 OpenAI** button (disabled when no key) — shows "下載中…" while fetching
- Save on any change.

**Dispatch logic:**
```
function speak(text):
  if settings.openai.enabled && settings.openai.apiKey:
    speakViaOpenAI(text)
  else:
    speakViaBrowser(text)
```

**OpenAI fetch:**
```
POST https://api.openai.com/v1/audio/speech
Authorization: Bearer <key>
Content-Type: application/json
{ model, input: text, voice, speed: clamp(rate, 0.25, 4.0), response_format: "mp3" }
```
Cache the blob URL in an in-memory `Map<"voice|model|rate|text", url>`. Reuse for repeated 🔊 of the same verse in the same session.

### Export / import

**Export**: download a JSON file named `背經進度-YYYY-MM-DD.json` containing:
```json
{ "progress": {...}, "customVerses": [...], "exportedAt": "<ISO>", "version": 1 }
```

**Import**: file picker, parse JSON, merge:
- `progress`: per-ref, keep the entry with higher `box` (or, if equal box, the later `lastReviewed`).
- `customVerses`: dedupe by `ref`, append new ones.

### Reset

`清除進度` link in footer with `confirm()` — wipes `PROGRESS_KEY` and `CUSTOM_KEY` from localStorage; preserves `SETTINGS_KEY`.

---

## Visual style

Quiet, readable, slightly warm. NOT material design, NOT iOS chrome.

```
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
- Mobile-friendly: rely on `<meta viewport>` and flex/grid layouts.

---

## Default seed verses (`verses.js`)

```js
window.VERSES = [
  // 啟 22:1-5 (新天新地)
  { ref: "啟 22:1", text: "天使又指示我在城內街道當中一道生命水的河，明亮如水晶，從神和羔羊的寶座流出來。" },
  { ref: "啟 22:2", text: "在河這邊與那邊有生命樹，結十二樣果子，每月都結果子；樹上的葉子乃為醫治萬民。" },
  { ref: "啟 22:3", text: "以後再沒有咒詛；在城裏有神和羔羊的寶座；他的僕人都要事奉他，" },
  { ref: "啟 22:4", text: "也要見他的面。他的名字必寫在他們的額上。" },
  { ref: "啟 22:5", text: "不再有黑夜；他們也不用燈光、日光，因為主神要光照他們。他們要作王，直到永永遠遠。" },

  // 彼前 2:21-25 (基督受苦的榜樣)
  { ref: "彼前 2:21", text: "你們蒙召原是為此；因基督也為你們受過苦，給你們留下榜樣，叫你們跟隨他的腳蹤行。" },
  { ref: "彼前 2:22", text: "他並沒有犯罪，口裏也沒有詭詐。" },
  { ref: "彼前 2:23", text: "他被罵不還口；受害不說威嚇的話，只將自己交託那按公義審判人的主。" },
  { ref: "彼前 2:24", text: "他被掛在木頭上，親身擔當了我們的罪，使我們既然在罪上死，就得以在義上活。因他受的鞭傷，你們便得了醫治。" },
  { ref: "彼前 2:25", text: "你們從前好像迷路的羊，如今卻歸到你們靈魂的牧人監督了。" },

  // 太 5:3-10 (八福)
  { ref: "太 5:3",  text: "虛心的人有福了！因為天國是他們的。" },
  { ref: "太 5:4",  text: "哀慟的人有福了！因為他們必得安慰。" },
  { ref: "太 5:5",  text: "溫柔的人有福了！因為他們必承受地土。" },
  { ref: "太 5:6",  text: "飢渴慕義的人有福了！因為他們必得飽足。" },
  { ref: "太 5:7",  text: "憐恤人的人有福了！因為他們必蒙憐恤。" },
  { ref: "太 5:8",  text: "清心的人有福了！因為他們必得見神。" },
  { ref: "太 5:9",  text: "使人和睦的人有福了！因為他們必稱為神的兒子。" },
  { ref: "太 5:10", text: "為義受逼迫的人有福了！因為天國是他們的。" },

  // 腓 3:10-14 (向標竿直跑)
  { ref: "腓 3:10", text: "使我認識基督，曉得他復活的大能，並且曉得和他一同受苦，效法他的死，" },
  { ref: "腓 3:11", text: "或者我也得以從死裏復活。" },
  { ref: "腓 3:12", text: "這不是說我已經得着了，已經完全了；我乃是竭力追求，或者可以得着基督耶穌所以得着我的。" },
  { ref: "腓 3:13", text: "弟兄們，我不是以為自己已經得着了；我只有一件事，就是忘記背後，努力面前的，" },
  { ref: "腓 3:14", text: "向着標竿直跑，要得神在基督耶穌裏從上面召我來得的獎賞。" },

  // 弗 6:12-18 (神的全副軍裝)
  { ref: "弗 6:12", text: "因我們並不是與屬血氣的爭戰，乃是與那些執政的、掌權的、管轄這幽暗世界的，以及天空屬靈氣的惡魔爭戰。" },
  { ref: "弗 6:13", text: "所以，要拿起神所賜的全副軍裝，好在磨難的日子抵擋仇敵，並且成就了一切，還能站立得住。" },
  { ref: "弗 6:14", text: "所以要站穩了，用真理當作帶子束腰，用公義當作護心鏡遮胸，" },
  { ref: "弗 6:15", text: "又用平安的福音當作預備走路的鞋穿在腳上。" },
  { ref: "弗 6:16", text: "此外，又拿着信德當作盾牌，可以滅盡那惡者一切的火箭；" },
  { ref: "弗 6:17", text: "並戴上救恩的頭盔，拿着聖靈的寶劍，就是神的道；" },
  { ref: "弗 6:18", text: "靠着聖靈，隨時多方禱告祈求；並要在此警醒不倦，為眾聖徒祈求，" },
];
```

(30 cards total. Verse text must be copied **exactly** from `cuv.json` — do not retype, as full-width vs half-width punctuation and traditional vs simplified characters must match.)

---

## Deployment

1. `cd app/memorize`
2. `git init -b main`
3. `git add -A && git commit -s -m "Initial commit"`
4. Create a public repo on GitHub (named anything — the URL will be `https://<user>.github.io/<repo>/`)
5. `git remote add origin git@github.com:<user>/<repo>.git`
6. `git push -u origin main`
7. Repo Settings → Pages → Source: `main` / `/ (root)` → Save
8. Wait ~1 min for first build. URL appears in green banner.

`cuv.json` is 4.7 MB — well under the 100 MB per-file Pages limit. Total repo well under 1 GB limit.

---

## Non-goals (do NOT build)

- A backend / database.
- User accounts / multi-device sync (use export/import for cross-device).
- A real native iOS app (the deployed PWA works fine on iPhone Safari + Add to Home Screen).
- Multiple Bible translations in one app (could be a separate dropdown if added later).
- A "type the verse from memory" mode (deferred — fill-in-blank is the primary).
- Streak counters, gamification, social features.

---

## Testing checklist (manual)

After build, verify on localhost:

- [ ] App loads at `http://localhost:8765/` with default 30 verses showing in 練習
- [ ] Masked card: every 3rd Han char visible, punctuation kept
- [ ] 提示 reveals one more char; 顯示答案 reveals all and switches to OK/NG
- [ ] 記得 → next card; 忘了 → same card stays due
- [ ] 瀏覽 → 直接輸入 `可 10:45` shows the verse, **加入** adds it; second click is **已加入**
- [ ] 瀏覽 → 搜尋 `愛是恆久` finds 林前 13:4
- [ ] 瀏覽 → 按卷目錄 → 馬可福音 → 1 → list of verses
- [ ] 我的清單: seed verses tagged 內建; custom verses have 移除
- [ ] 匯出 downloads a JSON, 匯入 the same file merges idempotently
- [ ] 清除進度 confirm + wipe
- [ ] 設定: 試聽 plays sample with browser voice
- [ ] 設定: OpenAI section accepts key, 試聽 plays MP3 via OpenAI
- [ ] iPhone Safari: same flow works, voice falls back to Apple voices
- [ ] 檢驗: 🎤 開始錄音 triggers mic permission prompt; live transcript shown
- [ ] 檢驗 result: green/red char highlighting matches expected diff
- [ ] 檢驗: navigating away from 檢驗 while listening cancels recognition cleanly
