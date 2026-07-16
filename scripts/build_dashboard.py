#!/usr/bin/env python3
"""Build the portfolio progress dashboard.

Reads projects.json + todos/*.md, counts checked/total tasks per project,
appends today's snapshot to data/history.json (one row per day, idempotent),
and renders a self-contained docs/index.html with per-project progress bars and
completion sparklines. Stdlib only - no pip install needed in CI.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODOS_DIR = ROOT / "todos"
HISTORY = ROOT / "data" / "history.json"
OUT = ROOT / "docs" / "index.html"

CHECK_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s+(.*\S)")


def count_todos(path: Path) -> tuple[int, int]:
    """Return (done, total) checkbox tasks in a markdown file."""
    done = total = 0
    for line in path.read_text().splitlines():
        m = CHECK_RE.match(line)
        if m:
            total += 1
            if m.group(1).lower() == "x":
                done += 1
    return done, total


def load_history() -> list:
    if HISTORY.exists():
        return json.loads(HISTORY.read_text()).get("snapshots", [])
    return []


def spark(values, w=220, h=40, color="#6ea8fe"):
    """Tiny SVG sparkline (0..100 percentages) with a filled area."""
    if not values:
        return ""
    if len(values) == 1:
        values = values * 2
    n = len(values)
    dx = w / (n - 1)
    pts = [(i * dx, h - (v / 100) * (h - 4) - 2) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{h} " + line + f" {w},{h}"
    return (
        f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'width="100%" height="{h}">'
        f'<polygon points="{area}" fill="{color}" opacity="0.12"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3" fill="{color}"/>'
        f"</svg>"
    )


def main() -> None:
    reg = json.loads((ROOT / "projects.json").read_text())
    owner = reg["owner"]
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    projects = []
    for t in reg["tracks"]:
        p = TODOS_DIR / t["todo"]
        done, total = count_todos(p) if p.exists() else (0, 0)
        projects.append({**t, "done": done, "total": total})

    o_done = sum(p["done"] for p in projects)
    o_total = sum(p["total"] for p in projects)

    # --- snapshot history (idempotent per day) --------------------------------
    hist = load_history()
    snap = {
        "date": today,
        "overall": {"done": o_done, "total": o_total},
        "tracks": {p["key"]: {"done": p["done"], "total": p["total"]} for p in projects},
    }
    if hist and hist[-1]["date"] == today:
        hist[-1] = snap
    else:
        hist.append(snap)
    hist = hist[-365:]
    HISTORY.parent.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps({"snapshots": hist}, indent=2) + "\n")

    def pct_series(key):
        out = []
        for s in hist[-30:]:
            d = s["overall"] if key is None else s["tracks"].get(key, {"done": 0, "total": 0})
            out.append(100 * d["done"] / d["total"] if d["total"] else 0.0)
        return out

    o_pct = round(100 * o_done / o_total) if o_total else 0

    # --- per-project cards ----------------------------------------------------
    cards = []
    for p in sorted(projects, key=lambda x: (-(x["done"] / x["total"] if x["total"] else 0), x["label"])):
        pct = round(100 * p["done"] / p["total"]) if p["total"] else 0
        hue = p["hue"]
        repo_link = (
            f'<a class="repo" href="https://github.com/{owner}/{p["repo"]}">{p["repo"]}</a>'
            if p.get("repo") else '<span class="repo muted">no repo</span>'
        )
        live = f'<a class="live" href="{p["url"]}">live &#8599;</a>' if p.get("url") else ""
        vis = p.get("visibility", "")
        vis_badge = f'<span class="badge {vis}">{vis}</span>' if vis in ("public", "private") else ""
        cards.append(f"""
      <article class="card" style="--hue:{hue}">
        <div class="card-top">
          <div>
            <h3>{p['label']}</h3>
            <p class="note">{p['note']}</p>
          </div>
          <div class="pct">{pct}<span>%</span></div>
        </div>
        <div class="bar"><span style="width:{pct}%"></span></div>
        <div class="counts">{p['done']} / {p['total']} done</div>
        {spark(pct_series(p['key']), color=hue)}
        <div class="card-foot">{repo_link} {vis_badge} {live}</div>
      </article>""")

    ring_c = 2 * 3.14159 * 52
    ring_off = ring_c * (1 - o_pct / 100)
    updated = now.strftime("%Y-%m-%d %H:%M UTC")
    active = sum(1 for p in projects if p["total"] and p["done"] < p["total"])
    done_projects = sum(1 for p in projects if p["total"] and p["done"] == p["total"])

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Portfolio Planning &amp; Tracking</title>
<style>
  :root {{
    --bg:#0b0f17; --panel:#111725; --panel-2:#0e1420; --line:#1e2636;
    --ink:#e8edf6; --muted:#8b97ad; --accent:#6ea8fe; --accent-2:#8b7cff;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:radial-gradient(1200px 600px at 70% -10%, #14203a 0%, var(--bg) 55%);
    color:var(--ink); font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:48px 24px 80px; }}
  header .eyebrow {{ color:var(--accent); font:600 12px/1 ui-monospace,"JetBrains Mono",monospace;
    letter-spacing:.16em; text-transform:uppercase; margin:0 0 12px; }}
  h1 {{ margin:0; font-size:34px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); margin:8px 0 0; }}
  .hero {{
    display:grid; grid-template-columns:auto 1fr; gap:36px; align-items:center;
    background:linear-gradient(180deg,var(--panel),var(--panel-2)); border:1px solid var(--line);
    border-radius:18px; padding:28px 32px; margin:32px 0 28px;
  }}
  .ring {{ position:relative; width:132px; height:132px; }}
  .ring .lbl {{ position:absolute; inset:0; display:grid; place-content:center; text-align:center; }}
  .ring .lbl b {{ font-size:30px; }} .ring .lbl small {{ color:var(--muted); font-size:12px; }}
  .stats {{ display:flex; gap:32px; flex-wrap:wrap; }}
  .stat b {{ display:block; font-size:26px; }} .stat span {{ color:var(--muted); font-size:13px; }}
  .hero-spark {{ margin-top:14px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; }}
  .card {{
    background:linear-gradient(180deg,var(--panel),var(--panel-2)); border:1px solid var(--line);
    border-radius:14px; padding:18px 18px 16px; border-top:3px solid var(--hue);
  }}
  .card-top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }}
  .card h3 {{ margin:0; font-size:16px; }}
  .note {{ color:var(--muted); margin:3px 0 0; font-size:12.5px; }}
  .pct {{ font-size:22px; font-weight:700; color:var(--hue); }} .pct span {{ font-size:12px; opacity:.7; }}
  .bar {{ height:7px; background:#0a0e17; border:1px solid var(--line); border-radius:99px; margin:14px 0 8px; overflow:hidden; }}
  .bar span {{ display:block; height:100%; background:var(--hue); border-radius:99px; }}
  .counts {{ color:var(--muted); font-size:12.5px; }}
  .spark {{ display:block; margin:10px 0 6px; }}
  .card-foot {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:8px;
    font:12px/1 ui-monospace,"JetBrains Mono",monospace; }}
  .repo {{ color:var(--accent); text-decoration:none; }} .repo:hover {{ text-decoration:underline; }}
  .repo.muted, .muted {{ color:#5c6780; }}
  .live {{ color:var(--accent-2); text-decoration:none; }}
  .badge {{ font-size:10px; padding:2px 7px; border-radius:99px; border:1px solid var(--line); text-transform:uppercase; letter-spacing:.05em; }}
  .badge.public {{ color:#5ecb8b; }} .badge.private {{ color:#c9a24b; }}
  h2.sec {{ font-size:13px; text-transform:uppercase; letter-spacing:.12em; color:var(--muted); margin:0 0 16px; }}
  footer {{ margin-top:44px; color:var(--muted); font-size:12.5px; border-top:1px solid var(--line); padding-top:18px; }}
  footer code {{ color:var(--accent); background:#0a0e17; padding:1px 6px; border-radius:5px; }}
  @media (max-width:640px) {{ .hero {{ grid-template-columns:1fr; }} h1 {{ font-size:27px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="eyebrow">Project Planning &middot; Tracking &middot; Code Review</p>
    <h1>Portfolio Progress</h1>
    <p class="sub">Every project's todo list in one place, tracked daily. Updated {updated}.</p>
  </header>

  <section class="hero">
    <div class="ring">
      <svg width="132" height="132" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="52" fill="none" stroke="#1a2234" stroke-width="12"/>
        <circle cx="60" cy="60" r="52" fill="none" stroke="url(#g)" stroke-width="12"
          stroke-linecap="round" stroke-dasharray="{ring_c:.1f}" stroke-dashoffset="{ring_off:.1f}"
          transform="rotate(-90 60 60)"/>
        <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#6ea8fe"/><stop offset="1" stop-color="#8b7cff"/>
        </linearGradient></defs>
      </svg>
      <div class="lbl"><div><b>{o_pct}%</b><br/><small>{o_done}/{o_total} tasks</small></div></div>
    </div>
    <div>
      <div class="stats">
        <div class="stat"><b>{len(projects)}</b><span>projects tracked</span></div>
        <div class="stat"><b>{active}</b><span>in progress</span></div>
        <div class="stat"><b>{done_projects}</b><span>fully shipped</span></div>
        <div class="stat"><b>{o_total - o_done}</b><span>tasks remaining</span></div>
      </div>
      <div class="hero-spark">{spark(pct_series(None), w=560, h=54)}</div>
    </div>
  </section>

  <h2 class="sec">Projects</h2>
  <div class="grid">{''.join(cards)}
  </div>

  <footer>
    Todo lists live in <code>todos/*.md</code>. Check a box with <code>[x]</code>, push, and this
    board refreshes automatically. A snapshot is recorded every day at 07:00 UTC to build the trend lines.
    Every project repo runs a Claude code-quality review on each pull request.
  </footer>
</div>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html)
    print(f"Dashboard: {o_done}/{o_total} ({o_pct}%) across {len(projects)} projects -> {OUT}")


if __name__ == "__main__":
    main()
