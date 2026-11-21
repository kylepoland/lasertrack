"""Small LAN web page for assigning cartridges (and testing without hardware).

Open http://lasertrack.local:8080 on a phone. Insert a cartridge, the page
shows its UID, search Plex, tap a result to assign it. The page can also
simulate inserting/removing a tag, so Plex playback can be tested before the
RC522 is wired.

No login: it is reachable on the home LAN only (v1). It cannot touch the media
files; the worst it can do is reassign a cartridge.
"""

from __future__ import annotations

import logging
from dataclasses import asdict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .cartridges import KINDS, Cartridge

log = logging.getLogger(__name__)


class AssignBody(BaseModel):
    uid: str
    rating_key: int
    kind: str
    title: str
    shuffle: bool = False


class UidBody(BaseModel):
    uid: str


def make_app(daemon) -> FastAPI:
    app = FastAPI(title="LaserTrack")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return PAGE

    @app.get("/api/status")
    def status():
        return {**asdict(daemon.status), "cartridges": [asdict(c) for c in daemon.store.all()]}

    @app.get("/api/search")
    def search(q: str):
        try:
            return daemon.plex.search(q)
        except Exception as e:
            raise HTTPException(502, f"Plex search failed: {e}")

    @app.post("/api/assign")
    def assign(body: AssignBody):
        if body.kind not in KINDS:
            raise HTTPException(400, f"kind must be one of {KINDS}")
        daemon.store.assign(Cartridge(**body.model_dump()))
        daemon.events.put(("assigned", body.uid))
        return {"ok": True}

    @app.post("/api/unassign")
    def unassign(body: UidBody):
        daemon.store.unassign(body.uid)
        return {"ok": True}

    @app.post("/api/sim/insert")
    def sim_insert(body: UidBody):
        daemon.events.put(("tag_inserted", body.uid.strip().upper()))
        return {"ok": True}

    @app.post("/api/sim/remove")
    def sim_remove():
        daemon.events.put(("tag_removed", None))
        return {"ok": True}

    @app.post("/api/control/{action}")
    def control(action: str):
        if action not in ("pause", "next", "prev", "stop"):
            raise HTTPException(400, "unknown action")
        daemon.events.put(("control", action))
        return {"ok": True}

    return app


def serve(daemon) -> None:
    cfg = daemon.cfg.web
    uvicorn.run(make_app(daemon), host=cfg.host, port=cfg.port, log_level="warning")


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LaserTrack</title>
<style>
:root { --bg:#111; --fg:#eee; --dim:#888; --acc:#e8b13a; --card:#1c1c1c; }
* { box-sizing:border-box; }
body { margin:0; padding:16px; background:var(--bg); color:var(--fg);
       font:16px/1.4 ui-monospace, Menlo, monospace; max-width:640px; }
h1 { font-size:20px; letter-spacing:.2em; color:var(--acc); margin:0 0 12px; }
h2 { font-size:14px; color:var(--dim); text-transform:uppercase; margin:20px 0 8px; }
.card { background:var(--card); border-radius:8px; padding:12px; }
button { background:#333; color:var(--fg); border:0; border-radius:6px; padding:10px 14px;
         font:inherit; margin:4px 4px 4px 0; }
button.acc { background:var(--acc); color:#111; }
input { width:100%; padding:10px; font:inherit; background:#000; color:var(--fg);
        border:1px solid #444; border-radius:6px; }
.row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.res { padding:8px 0; border-bottom:1px solid #2a2a2a; display:flex; justify-content:space-between; gap:8px; }
.kind { color:var(--dim); font-size:12px; }
.err { color:#f66; }
pre { white-space:pre-wrap; color:var(--dim); font-size:12px; margin:0; }
</style></head><body>
<h1>LASERTRACK</h1>
<div class="card" id="status">…</div>

<h2>Controls</h2>
<div class="row">
  <button onclick="ctl('prev')">◀◀</button><button onclick="ctl('pause')">▶ / ❚❚</button>
  <button onclick="ctl('next')">▶▶</button><button onclick="ctl('stop')">■ Stop</button>
</div>

<h2>Assign the cartridge in the slot</h2>
<div class="row"><input id="q" placeholder="Search Plex…" onkeydown="if(event.key==='Enter')search()"></div>
<label class="row" style="margin-top:8px"><input type="checkbox" id="shuffle" style="width:auto"> Shuffle (playlists/collections)</label>
<div id="results"></div>

<h2>Simulate a tag (testing)</h2>
<div class="row">
  <input id="simuid" placeholder="UID, e.g. 04:A1:B2:C3:D4:E5:F6" style="flex:1">
  <button onclick="simInsert()">Insert</button><button onclick="simRemove()">Remove</button>
</div>

<h2>Cartridges</h2>
<div class="card" id="carts"></div>

<h2>Log</h2>
<div class="card"><pre id="log"></pre></div>

<script>
let st = {};
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function post(url, body) {
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body || {})});
  if (!r.ok) alert(await r.text());
  refresh();
}
async function refresh() {
  st = await (await fetch('/api/status')).json();
  const pos = st.position_s ? ` · ${Math.floor(st.position_s/60)}:${String(Math.floor(st.position_s%60)).padStart(2,'0')}` : '';
  $('status').innerHTML =
    `<div><b>${esc(st.mode)}</b>${st.uid ? ' · tag ' + esc(st.uid) : ''}</div>` +
    (st.cartridge ? `<div>${esc(st.cartridge.title)} <span class="kind">${esc(st.cartridge.kind)}</span></div>` : '') +
    (st.now_playing ? `<div>▶ ${esc(st.now_playing)}${pos}</div>` : '') +
    (st.error ? `<div class="err">${esc(st.error)}</div>` : '') +
    (!st.uid && st.last_uid ? `<div class="kind">last tag: ${esc(st.last_uid)}</div>` : '');
  $('carts').innerHTML = st.cartridges.length ? st.cartridges.map(c =>
    `<div class="res"><span>${esc(c.title)} <span class="kind">${esc(c.kind)}${c.shuffle?' · shuffle':''}<br>${esc(c.uid)}</span></span>
     <span><button onclick="$('simuid').value='${esc(c.uid)}'">Use</button>
     <button onclick="if(confirm('Unassign?'))post('/api/unassign',{uid:'${esc(c.uid)}'})">✕</button></span></div>`).join('')
    : '<span class="kind">none yet</span>';
  $('log').textContent = st.log.slice().reverse().join('\\n');
}
async function search() {
  $('results').innerHTML = '<div class="kind">searching…</div>';
  const r = await fetch('/api/search?q=' + encodeURIComponent($('q').value));
  if (!r.ok) { $('results').innerHTML = `<div class="err">${esc(await r.text())}</div>`; return; }
  const items = await r.json();
  window._results = items;
  $('results').innerHTML = items.map((it, i) =>
    `<div class="res"><span>${esc(it.title)} <span class="kind">${esc(it.kind)}</span></span>
     <button class="acc" onclick="assign(${i})">Assign</button></div>`).join('') || '<div class="kind">no results</div>';
}
function assign(i) {
  const uid = st.uid || st.last_uid;
  if (!uid) { alert('Insert a cartridge (or simulate one) first.'); return; }
  const it = window._results[i];
  post('/api/assign', {uid, rating_key: it.rating_key, kind: it.kind, title: it.title, shuffle: $('shuffle').checked});
  $('results').innerHTML = '';
}
const ctl = a => post('/api/control/' + a);
function simInsert() { const u = $('simuid').value.trim() || 'SIM:00:00:01'; post('/api/sim/insert', {uid: u}); }
const simRemove = () => post('/api/sim/remove');
refresh(); setInterval(refresh, 2000);
</script></body></html>
"""
