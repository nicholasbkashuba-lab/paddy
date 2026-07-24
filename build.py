#!/usr/bin/env python3
"""
Paddy Mac's static site generator.

    python3 build.py            build into dist/
    python3 build.py --serve    build, then serve dist/ on :8000

No third-party dependencies. Content lives in content/*.json; templates use
{{ token }} placeholders that this script fills. Anything with a _TODO key in
the JSON is reported at the end of the build so nothing ships half-finished.
"""

import json
import html
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s), quote=True)


def fmt_time(mins):
    """690 -> '11:30am'. 1560 -> '2am' (after midnight)."""
    if mins is None:
        return "Closed"
    m = mins % 1440
    h, mm = divmod(m, 60)
    ap = "pm" if h >= 12 else "am"
    h12 = h % 12 or 12
    return f"{h12}:{mm:02d}{ap}" if mm else f"{h12}{ap}"


def render(template, values):
    """Replace {{ token }} with values[token]. Unknown tokens raise."""
    def sub(match):
        key = match.group(1).strip()
        if key not in values:
            raise KeyError(f"Template uses {{{{ {key} }}}} but build.py never set it")
        return str(values[key])
    return re.sub(r"\{\{\s*([\w_]+)\s*\}\}", sub, template)


def collect_todos(node, path="", found=None):
    """Walk the JSON and gather every _TODO note so the build can report them."""
    if found is None:
        found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "_TODO":
                found.append((path or "root", v))
            elif not k.startswith("_"):
                collect_todos(v, f"{path}.{k}" if path else k, found)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            collect_todos(v, f"{path}[{i}]", found)
    return found


# ---------------------------------------------------------------- fragments
def build_board(items):
    out = []
    for it in items:
        out.append(
            '          <div class="chalk">\n'
            f'            <p class="chalk__k">{esc(it["kicker"])}</p>\n'
            f'            <h3 class="chalk__t">{esc(it["title"])}</h3>\n'
            f'            <p class="chalk__b">{esc(it["body"])}</p>\n'
            f'            <span class="chalk__d">{esc(it["detail"])}</span>\n'
            "          </div>"
        )
    return "\n".join(out)


def build_gigs(gigs):
    """Server-rendered so the page is correct with JavaScript disabled.
    site.js re-labels tonight's row on load."""
    out = []
    for g in sorted(gigs, key=lambda x: x["dow"]):
        if g["act"].upper() == "TBC":
            # Honest but not unfinished-looking while the client confirms acts.
            act = '<span class="gig__tba">Line-up to be announced</span>'
        else:
            act = esc(g["act"])
        out.append(
            f'      <div class="gig rv" data-dow="{g["dow"]}">\n'
            f'        <div class="gig__day">{esc(DAYS[g["dow"]])}</div>\n'
            f'        <div class="gig__act">{act}<small>{esc(g["note"])}</small></div>\n'
            f'        <div class="gig__time">{esc(g["time"])}</div>\n'
            "      </div>"
        )
    return "\n".join(out)


def build_sections(sections):
    """Menu sections -> HTML. A price of 'market' renders italic; sections
    may carry a note and may have no items at all (e.g. the sides list)."""
    out = []
    for sec in sections:
        out.append('        <div class="menu__section">')
        out.append(f'          <h3>{esc(sec["heading"])}</h3>')
        if sec.get("note"):
            out.append(f'          <p class="menu__secnote">{esc(sec["note"])}</p>')
        if sec["items"]:
            out.append('          <ul class="menu__list">')
            for it in sec["items"]:
                price = it.get("price")
                if price == "market":
                    price_html = '<span class="menu__price menu__price--mkt">market</span>'
                elif price:
                    price_html = f'<span class="menu__price">{esc(price)}</span>'
                else:
                    price_html = ""
                if price_html:
                    row = (
                        '              <div class="menu__row">'
                        f'<span class="menu__name">{esc(it["name"])}</span>'
                        f'<span class="menu__dots"></span>{price_html}</div>'
                    )
                else:
                    row = f'              <div class="menu__row"><span class="menu__name">{esc(it["name"])}</span></div>'
                out.append('            <li class="menu__item">')
                out.append(row)
                if it.get("desc"):
                    out.append(f'              <p class="menu__desc">{esc(it["desc"])}</p>')
                out.append("            </li>")
            out.append("          </ul>")
        out.append("        </div>")
    return "\n".join(out)


def build_drinks(groups):
    """The bar list, chalked up in columns on the slate."""
    out = []
    for g in groups:
        out.append('          <div class="chalk">')
        out.append(f'            <p class="chalk__k">{esc(g["title"])}</p>')
        out.append('            <ul class="chalk__list">')
        for item in g["items"]:
            out.append(f'              <li>{esc(item)}</li>')
        out.append("            </ul>")
        out.append("          </div>")
    return "\n".join(out)


def build_shot(shot, cls="frame--tall"):
    """Renders a real photo if src is set, otherwise a labelled placeholder
    that doubles as the shot list for the photographer."""
    if shot.get("src"):
        inner = f'<img src="{esc(shot["src"])}" alt="" loading="lazy">'
    else:
        inner = (
            '<div class="shot"><p class="shot__label"><b>Photo to shoot</b>'
            f'{esc(shot["brief"])}</p></div>'
        )
    return f'<div class="frame {cls}"><div class="frame__in">{inner}</div></div>'


def build_feed(shots):
    return "\n".join(
        f'      <div class="rv">{build_shot(s, "frame--square")}</div>' for s in shots
    )


def build_hours(hours):
    out = []
    for i, h in enumerate(hours):
        val = "Closed" if h["open"] is None else f'{fmt_time(h["open"])} – {fmt_time(h["close"])}'
        out.append(f'<li data-dow="{i}"><span>{esc(h["day"])}</span><span>{val}</span></li>')
    return "".join(out)


def build_social(social, reviews):
    rows = []
    for key, label in (("facebook", "Facebook"), ("instagram", "Instagram")):
        url = social.get(key)
        if url:
            rows.append(f'        <p><a href="{esc(url)}">{label}</a></p>')
        else:
            rows.append(f'        <p style="opacity:.45">{label} — link needed</p>')
    if reviews.get("url"):
        rows.append(f'        <p><a href="{esc(reviews["url"])}">Google reviews</a></p>')
    return "\n".join(rows)


def build_jsonld(site, menu_url=""):
    a = site["address"]
    spec = []
    for h in site["hours"]:
        if h["open"] is None:
            continue
        spec.append({
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": f'https://schema.org/{h["day"]}',
            "opens": f'{h["open"]//60:02d}:{h["open"]%60:02d}',
            "closes": f'{(h["close"]%1440)//60:02d}:{h["close"]%60:02d}',
        })
    data = {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": site["name"],
        "servesCuisine": "Irish",
        "priceRange": "$$",
        "telephone": site["phone_href"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": a["street"],
            "addressLocality": a["city"],
            "addressRegion": a["state"],
            "postalCode": a["zip"],
            "addressCountry": "US",
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": site["reviews"]["rating"],
            "reviewCount": site["reviews"]["count"],
        },
        "openingHoursSpecification": spec,
    }
    if menu_url:
        data["hasMenu"] = menu_url
    return json.dumps(data, indent=None)


# ---------------------------------------------------------------- build
def build():
    site = json.loads((CONTENT / "site.json").read_text())
    menu = json.loads((CONTENT / "menu.json").read_text())

    a = site["address"]

    if menu.get("full_menu_url"):
        menu_button = f'<a class="btn btn--gold" href="{esc(menu["full_menu_url"])}">Full menu</a>'
    else:
        # No menu link yet — send people to the phone rather than a dead button.
        menu_button = (
            f'<a class="btn btn--gold" href="tel:{esc(site["phone_href"])}">'
            f'Ask about today’s menu — {esc(site["phone_display"])}</a>'
        )

    story_html = "\n".join(
        f'        <p class="dropcap">{esc(p)}</p>' if i == 0 else f"        <p>{esc(p)}</p>"
        for i, p in enumerate(site["story"])
    )
    parties_html = "\n".join(f"          <li>{esc(p)}</li>" for p in site["parties"])

    js_data = json.dumps({
        "hours": [{"day": h["day"], "open": h["open"], "close": h["close"]} for h in site["hours"]],
        "gigs": [{"dow": g["dow"], "act": g["act"]} for g in site["gigs"]],
    })

    values = {
        "name": esc(site["name"]),
        "tagline": esc(site["tagline"]),
        "established": esc(site["established"]),
        "years": site["years"],
        "street": esc(a["street"]),
        "city": esc(a["city"]),
        "state": esc(a["state"]),
        "zip": esc(a["zip"]),
        "maps_url": esc(a["maps_url"]),
        "phone_display": esc(site["phone_display"]),
        "phone_href": esc(site["phone_href"]),
        "rating": esc(site["reviews"]["rating"]),
        "review_count": esc(site["reviews"]["count"]),
        "kitchen_note": esc(site["kitchen_note"]),
        "quote_text": esc(site["pull_quote"]["text"]),
        "quote_cite": esc(site["pull_quote"]["cite"]),
        "menu_intro": esc(menu["intro"]),
        "menu_note": esc(menu["note"]),
        "menu_button": menu_button,
        "board_html": build_board(site["board"]),
        "gigs_html": build_gigs(site["gigs"]),
        "menu_html": build_sections(menu["sections"]),
        "story_html": story_html,
        "parties_html": parties_html,
        "hours_html": build_hours(site["hours"]),
        "social_html": build_social(site["social"], site["reviews"]),
        "shot_story": build_shot(site["shots"]["story"]),
        "shot_parties": build_shot(site["shots"]["parties"]),
        "feed_html": build_feed(site["shots"]["feed"]),
        "jsonld": build_jsonld(site, menu.get("full_menu_url", "")),
        "js_data": js_data,
        "year": datetime.now().year,
    }

    page = render((TEMPLATES / "index.html").read_text(), values)

    mp = menu["page"]
    menu_values = dict(values)
    menu_values.update({
        "page_tagline": esc(mp["tagline"]),
        "fine_print": esc(mp["fine_print"]),
        "market_note": esc(mp["market_note"]),
        "menu_page_html": build_sections(mp["food"]),
        "drinks_heading": esc(mp["drinks"]["heading"]),
        "drinks_sub": esc(mp["drinks"]["sub"]),
        "drinks_note": esc(mp["drinks"]["note"]),
        "drinks_html": build_drinks(mp["drinks"]["groups"]),
    })
    menu_page = render((TEMPLATES / "menu.html").read_text(), menu_values)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    (DIST / "index.html").write_text(page)
    (DIST / "menu").mkdir()
    (DIST / "menu" / "index.html").write_text(menu_page)
    for sub in ("css", "js", "img", "fonts"):
        src = STATIC / sub
        if src.exists():
            shutil.copytree(src, DIST / sub)

    print(f"built dist/index.html       ({len(page.encode()) / 1024:.1f} KB)")
    print(f"built dist/menu/index.html  ({len(menu_page.encode()) / 1024:.1f} KB)")

    todos = collect_todos(site) + collect_todos(menu)
    if todos:
        print(f"\n{len(todos)} thing(s) still to confirm with the client:")
        for where, note in todos:
            print(f"  · {where}: {note}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, socketserver, os
        os.chdir(DIST)
        print("\nserving http://localhost:8000  (ctrl-c to stop)")
        socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler).serve_forever()
