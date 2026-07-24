# Paddy Mac's Irish Restaurant

Static site for Paddy Mac's, Palm Beach Gardens FL.

## Build

    python3 build.py            # -> dist/
    python3 build.py --serve    # -> dist/ and serve on :8000

Python 3.9+, standard library only.

## Editing the site

All content lives in `content/site.json` and `content/menu.json`. Change a value,
run `build.py`, push. Vercel rebuilds on push to `main`.

Hours are minutes from midnight — `690` is 11:30am. A value above 1440 means after
midnight, so `1560` is a 2am close.

`build.py` prints anything still marked `_TODO` at the end of every build.

See `CLAUDE.md` for the design system and open questions.
