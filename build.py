#!/usr/bin/env python3
"""Rigenera le pagine HTML dai testi in src/: `python3 build.py`.

I testi si scrivono in src/*.md (un Markdown ridotto: titoli, paragrafi, elenchi, tabelle,
grassetto, link). Le pagine pubblicate sono i file index.html: non vanno toccati a mano, o
alla prossima generazione si perde la modifica. I segnaposti [DA COMPLETARE: …] e
[TO BE COMPLETED: …] escono evidenziati, e lo script lo dice: una pagina con segnaposti non
va pubblicata.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

PAGES = {
    # src, cartella, descrizione
    "privacy": ("privacy", {"it": "Informativa sulla privacy di BeBurn.", "en": "BeBurn privacy policy."}),
    "termini": ("termini", {"it": "Termini d'uso di BeBurn.", "en": "BeBurn terms of use."}),
    "supporto": ("supporto", {"it": "Aiuto e contatti per BeBurn.", "en": "Help and contacts for BeBurn."}),
}
FOOTER = {
    "it": ("Privacy", "Termini d'uso", "Supporto"),
    "en": ("Privacy", "Terms of use", "Support"),
}
PLACEHOLDER = re.compile(r"\[(?:DA COMPLETARE|TO BE COMPLETED):[^\]]*\]")


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = PLACEHOLDER.sub(lambda m: f'<span class="todo">{m.group(0)[1:-1]}</span>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"&lt;(https?://[^&\s]+)&gt;", r'<a href="\1">\1</a>', text)
    return text


def convert(md: str) -> tuple[str, str]:
    """(titolo, corpo HTML)."""
    lines = md.strip("\n").split("\n")
    title = ""
    out: list[str] = []
    para: list[str] = []
    items: list[str] = []
    table: list[str] = []

    def flush():
        nonlocal para, items, table
        if para:
            text = " ".join(para)
            cls = ' class="updated"' if re.match(r"^(Ultimo aggiornamento|Last updated):", text) else ""
            out.append(f"<p{cls}>{inline(text)}</p>")
            para = []
        if items:
            out.append("<ul>\n" + "\n".join(f"<li>{inline(i)}</li>" for i in items) + "\n</ul>")
            items = []
        if table:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table]
            head, body = rows[0], [r for r in rows[2:]]
            parts = ["<div class=\"table\"><table>", "<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>", "<tbody>"]
            parts += ["<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body]
            parts.append("</tbody></table></div>")
            out.append("\n".join(parts))
            table = []

    for line in lines:
        if line.startswith("# "):
            flush()
            title = re.sub(r"^BeBurn\s*[—-]\s*", "", line[2:].strip())
        elif line.startswith("### "):
            flush()
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("## "):
            flush()
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif line.startswith("|"):
            if para or items:
                flush()
            table.append(line)
        elif line.startswith("- "):
            if para or table:
                flush()
            items.append(line[2:].strip())
        elif line.startswith("  ") and items and line.strip():
            items[-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if items or table:
                flush()
            para.append(line.strip())
    flush()
    return title, "\n".join(out)


def page(lang: str, key: str) -> tuple[Path, str, int]:
    folder, descriptions = PAGES[key]
    md = (ROOT / "src" / f"{key}.{lang}.md").read_text(encoding="utf-8")
    title, body = convert(md)
    up = "../" if lang == "it" else "../../"
    privacy, terms, support = FOOTER[lang]
    suffix = "" if lang == "it" else "en/"
    if lang == "it":
        brand, switch = f"{up}", '<a class="lang" href="en/" hreflang="en">English</a>'
    else:
        brand, switch = f"{up}en/", '<a class="lang" href="../" hreflang="it">Italiano</a>'
    doc = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · BeBurn</title>
<meta name="description" content="{html.escape(descriptions[lang])}">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<main>
<header>
<a class="brand" href="{brand}"><span>B</span>BeBurn</a>
{switch}
</header>
<h1>{html.escape(title)}</h1>
{body}
<footer><a href="{up}privacy/{suffix}">{privacy}</a> · <a href="{up}termini/{suffix}">{terms}</a> · <a href="{up}supporto/{suffix}">{support}</a></footer>
</main>
</body>
</html>
"""
    target = ROOT / folder / ("index.html" if lang == "it" else "en/index.html")
    return target, doc, len(PLACEHOLDER.findall(md))


def main() -> int:
    missing = 0
    for key in PAGES:
        for lang in ("it", "en"):
            target, doc, todo = page(lang, key)
            target.write_text(doc, encoding="utf-8")
            missing += todo
            note = f"  ({todo} da completare)" if todo else ""
            print(f"{target.relative_to(ROOT)}{note}")
    if missing:
        print(f"\nAttenzione: {missing} segnaposti ancora da completare, non pubblicare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
