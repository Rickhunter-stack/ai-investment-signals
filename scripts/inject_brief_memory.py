from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
BRIEF_EVENTS = ROOT / "data" / "brief_events"


def esc(value):
    return html.escape(str(value or ""))


def load_events():
    """Load immutable brief-event journals, deduplicating event_ids across legacy/monthly/daily files."""
    events = {}
    if not BRIEF_EVENTS.exists():
        return []
    for path in sorted(BRIEF_EVENTS.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, list):
            continue
        for event in payload:
            if not isinstance(event, dict) or not event.get("event_id"):
                continue
            events.setdefault(event["event_id"], event)
    return sorted(
        events.values(),
        key=lambda e: (e.get("captured_at", ""), e.get("event_id", "")),
        reverse=True,
    )


def render_items(items):
    if not items:
        return '<div class="muted">Aucun événement prospectif enregistré pour le moment.</div>'
    chunks = []
    for event in items[:30]:
        captured = str(event.get("captured_at", ""))[:10]
        classification = esc(event.get("classification", ""))
        relation = esc(event.get("story_relation", ""))
        badges = " · ".join(x for x in (classification, relation) if x)
        companies = ", ".join(event.get("companies") or [])
        tickers = ", ".join(event.get("tickers") or [])
        watch = " · ".join(x for x in (companies, tickers) if x)
        chunks.append(
            '<div class="brief-memory-item" '
            f'data-date="{esc(captured)}" data-classification="{classification}" '
            f'data-relation="{relation}">'
            f'<div class="brief-memory-title">{esc(captured)}'
            f' · <span style="color:var(--amber)">{badges}</span></div>'
            f'<div class="brief-memory-summary"><b>{esc(event.get("title"))}</b><br>'
            f'{esc(event.get("factual_summary"))}</div>'
            + (f'<div class="muted brief-memory-watch">{esc(watch)}</div>' if watch else "")
            + '</div>'
        )
    return "".join(chunks)


def main():
    if not INDEX.exists():
        raise SystemExit("index.html not found")
    items = load_events()
    page = INDEX.read_text(encoding="utf-8")
    controls = (
        '<div class="brief-memory-controls" style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:7px">'
        '<input id="briefSearch" placeholder="Rechercher titre, société, ticker..." '
        'style="flex:1;min-width:150px;background:var(--panel2);color:var(--ink);border:1px solid var(--rule);border-radius:7px;padding:5px 7px">'
        '<select id="briefClass"><option value="">Tous types</option><option>FACT</option>'
        '<option>WEAK_SIGNAL</option><option>HYPOTHESIS</option></select></div>'
    )
    block = (
        '<section class="card readcard"><h3>Mémoire des signaux</h3>'
        + controls
        + '<div class="brief-memory-scroll" id="briefMemory">'
        + render_items(items)
        + '</div></section>'
    )
    pattern = re.compile(r'<section class="card readcard">.*?</section>', re.S)
    if pattern.search(page):
        page = pattern.sub(block, page, count=1)
    else:
        page = page.replace('</div><div class="details">', block + '</div><div class="details">', 1)
    filter_script = """<script>
(function(){
 const q=document.getElementById('briefSearch'), c=document.getElementById('briefClass');
 if(!q||!c)return;
 function filterBriefs(){
  const needle=q.value.toLowerCase(), cls=c.value;
  document.querySelectorAll('#briefMemory .brief-memory-item').forEach(el=>{
   el.style.display=(!needle||el.textContent.toLowerCase().includes(needle))&&(!cls||el.dataset.classification===cls)?'':'none';
  });
 }
 q.addEventListener('input',filterBriefs); c.addEventListener('change',filterBriefs);
})();
</script>"""
    page = page.replace('</body>', filter_script + '</body>', 1)
    INDEX.write_text(page, encoding="utf-8")
    print(f"{INDEX} ({len(items)} unique brief events)")


if __name__ == "__main__":
    main()
