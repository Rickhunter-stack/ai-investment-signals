from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
BRIEFS = ROOT / "data" / "brief_memory.json"


def esc(value):
    return html.escape(str(value or ""))


def render_items(items):
    if not items:
        return '<div class="muted">Aucune synthèse historique enregistrée pour le moment.</div>'
    chunks = []
    for item in sorted(items, key=lambda x: x.get("date", ""), reverse=True)[:8]:
        stance = item.get("stance")
        stance_html = f' · <span style="color:var(--amber)">{esc(stance)}</span>' if stance else ""
        watch = item.get("watch_next")
        watch_html = f'<div class="muted" style="font-size:.64rem;margin-top:3px">À surveiller : {esc(watch)}</div>' if watch else ""
        chunks.append(
            '<div style="border-left:2px solid var(--accent);padding:0 0 8px 9px;margin-bottom:9px">'
            f'<div style="font-size:.66rem;color:var(--accent);font-weight:800">{esc(item.get("date"))}{stance_html}</div>'
            f'<div style="font-size:.72rem;color:#d4dddc;margin-top:3px">{esc(item.get("summary"))}</div>'
            f'{watch_html}</div>'
        )
    return "".join(chunks)


def main():
    if not INDEX.exists():
        raise SystemExit("index.html not found")
    try:
        items = json.loads(BRIEFS.read_text(encoding="utf-8")) if BRIEFS.exists() else []
    except Exception:
        items = []
    if not isinstance(items, list):
        items = []

    page = INDEX.read_text(encoding="utf-8")
    block = (
        '<section class="card readcard">'
        '<h3>Mémoire des briefs</h3>'
        '<div style="overflow:auto;max-height:100%">'
        + render_items(items)
        + '</div></section>'
    )
    pattern = re.compile(r'<section class="card readcard">.*?</section>', re.S)
    if pattern.search(page):
        page = pattern.sub(block, page, count=1)
    else:
        page = page.replace('</div><div class="details">', block + '</div><div class="details">', 1)
    INDEX.write_text(page, encoding="utf-8")
    print(INDEX)


if __name__ == "__main__":
    main()
