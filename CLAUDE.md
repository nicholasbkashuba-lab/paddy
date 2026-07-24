# Paddy Mac's — working notes for Claude Code

Client site for **Paddy Mac's Irish Restaurant**, 10971 N Military Trail, Palm Beach
Gardens FL. Open since December 1995. Owner is Hugh, from Cork; his son runs it now.

This is the fourth client site on the same pattern as First Rehabilitation, Palm Beach
Neurology and Legends Radio: `build.py` generator → static `dist/` → Vercel → repo
handed to the client at the end.

---

## Commands

```bash
python3 build.py            # build into dist/
python3 build.py --serve    # build, then serve dist/ at localhost:8000
```

No dependencies. Python 3.9+ standard library only. Do not add a package manager,
a framework, or a template engine — the whole point is that the client can be handed
this and it still builds in five years.

---

## How it fits together

```
content/site.json     hours, gigs, contact, story, photo slots   ← edit this
content/menu.json     menu items, no prices yet                  ← edit this
templates/index.html  {{ token }} placeholders
static/css/style.css  the entire design system
static/js/site.js     live open/closed status, nav, reveals
static/fonts/         self-hosted woff2 subsets — no Google Fonts requests
static/img/og.png     the social share card (1200×630)
build.py              fills tokens, writes dist/
dist/                 generated — never edit, never commit
```

**Content changes go in `content/*.json`, never in the template.** If something on the
page is hardcoded in `templates/index.html` and the client will want to change it later,
move it to JSON and add a token.

`build.py` prints every `_TODO` key it finds in the JSON at the end of each build. That
list is the launch checklist. Don't delete a `_TODO` without actually resolving it.

---

## Design direction — "The Gilded Snug"

The first pass at this site was too plain and got rejected for it. The correction: a
Victorian Irish pub is **ornate**, and since there are no photographs yet, the page
itself has to be the decoration.

- Ground is layered bottle greens with a fixed grain overlay and a corner vignette —
  never flat black.
- Display type is gilded, not white. `.gilt` applies a gold-leaf gradient via
  `background-clip: text`, with a solid-gold fallback. A sheen layer sweeps across it
  once — on load for the hero, on reveal for section headings (`@keyframes gleam`).
- Structural motifs are borrowed from the real thing: an etched-glass **arch** around
  the hero (gilt **keystone** at the crown, filigree curls in the lower corners,
  **etched pint windows** flanking it at ≥1200px), a slate **chalkboard in a wooden
  frame** with brass corner screws and a hand-drawn chalk underline, a **gilt picture
  frame** around every photo slot, an aged **paper menu card** (laid-paper grain, a
  triquetra watermark, a letterpress double rule), and a two-strand Celtic **plait**
  as the section rule (tiled SVG in `.knotrule`).
- Smaller flourishes carry the same voice: a gilded **drop cap** on the first story
  paragraph (`.dropcap`, class set by `build.py`), stitched leather on the pull quote,
  **shamrock bullets** in the parties list, the feed frames hung slightly **askew**
  (they straighten on hover), and a big gilt **Sláinte!** signing off the footer.
- The menu card is the only light surface on the page. That is deliberate — it should
  land like something handed to you across the bar. Don't add a second one.

### Colours — sampled from the client's 2021 logo PNG, not guessed

| Token | Hex | Use |
|---|---|---|
| `--kelly` | `#29A343` | the logo green |
| `--copper` | `#E06900` | the logo triquetra orange — accents only |
| `--gold` | `#D4A537` | gilding, rules, frames |
| `--oxblood` | `#4E1519` | pull-quote panel only |
| `--paper` | `#EFE4CA` | the menu card |
| `--pitch` / `--bottle` / `--forest` | | page grounds |

### Type

- **Alfa Slab One** — display. Hand-painted pub signwriting. Headings and dish names.
- **Archivo** — body and UI (variable weight 400–700).
- **DM Mono** — eyebrows, hours, prices, the status strip. The chalkboard voice.

All three are **self-hosted** as latin-subset woff2 in `static/fonts/` and preloaded
from the template — no Google Fonts requests, so the page renders identically offline
and there's no third-party dependency at hand-off. If you add a family or weight,
download the subset and add an `@font-face` rather than reintroducing the CDN.

Do **not** introduce Playfair Display. First Rehabilitation uses it and these two sites
should not look related.

---

## The live status strip

The bar under the nav is the signature element. It reads the real day and hour in
`America/New_York` via `Intl.DateTimeFormat`, so a visitor in California sees the pub's
clock rather than their own.

The tricky part is **after-midnight closes**. Hours are stored as minutes from midnight,
and a value over 1440 means the next morning — Friday's `1560` is 2am Saturday. At 1am on
a Saturday the pub is still open *on Friday's hours*, so `status()` checks yesterday's
carry-over before today's window. If you touch that logic, re-check these cases:

| When | Expected |
|---|---|
| Sat 01:00 | Open, last call 2am (Friday's close) |
| Sat 15:00 | Open, last call 2am |
| Sun 01:00 | Open (Saturday's close) |
| Sun 05:00 | Closed, back tomorrow at 11:30am |
| Mon 09:00 | Closed, back today at 11:30am |
| Tue 23:20 | Open, last call 12am |

Gig rows and the hours list are server-rendered by `build.py` so the page is correct
with JavaScript disabled; `site.js` only relabels tonight's row.

---

## Still unresolved — needs the client

1. **Sunday hours.** Google says closed. The old site advertises brunch 11am–3pm. Coded
   as closed. Confirm.
2. **Live music nights.** Brief says Friday and Saturday; the old site says Saturday
   only. Both are in `gigs` with `act: "TBC"`.
3. **Happy hour and early bird times.** Nobody has them. The board cards say "Times TBC".
4. **Facebook and Instagram handles.** The Lately grid renders placeholders until
   `social.instagram` is filled in.
5. **The full menu**, with prices. `menu.json` supports an optional `price` per item —
   add it and leader dots render automatically. **Do not invent prices.**
6. **The pull quote** is a real customer's Google review, verbatim. Get their blessing or
   reword it in the pub's voice before launch.

## Photos

There are none yet. Every photo slot has a `brief` in `site.json` describing the shot,
and renders as a labelled placeholder inside a gilt frame until `src` is filled in.
Setting `src` swaps the image in with no other change.

Shot list: Hugh or his son mid-pour behind the bar (portrait 4:5); the long table set
before guests arrive (portrait 4:5); four squares for the feed. Best window is 4pm on a
weekday — front-window light, empty room.

---

## Deploy and handoff

Vercel, `vercel.json` sets `buildCommand: python3 build.py` and `outputDirectory: dist`.
If the build image ever lacks Python, fall back to committing `dist/` and dropping the
build command.

Handoff is the same as the other client sites: transfer the GitHub repo to the client,
who then connects their own Vercel. Nothing in this repo is account-specific.

---

## House rules

- Don't invent facts about the business. Hours, prices, band names and happy hour times
  all come from the client. If it isn't in `content/`, ask rather than fill it in.
- Keep the page usable without JavaScript. The scroll reveals are gated behind an
  `html.js` class set by an inline script — with JS off, nothing is hidden. Keep it
  that way.
- `static/img/og.png` is the share card, rendered in the site's own styles at
  1200×630. Re-render it if the tagline or logo changes.
- Every interactive element keeps a visible focus ring, and `prefers-reduced-motion` is
  respected — check both before shipping a change.
- The gold gradient on text needs a fallback colour. `.gilt` sets one. Don't strip it.
