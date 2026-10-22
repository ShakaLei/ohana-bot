#!/usr/bin/env python3
"""
build-page.py — derive the totem-web page from the UNTOUCHED 3D source.

/workspace/ohana-bot-3d/ stays the single source of truth for the body
(app.js + template.html, three.js vendored). This script patches a COPY at
build time with structure-matched anchors and REFUSES to build if any anchor
is missing or appears more than once — so a future change upstream fails loud
instead of shipping a half-wired totem.

Patches applied to app.js:
  A1  live-glow state variables
  A2  the live branch at the top of updateGlow() — reuses the SAME contract
      numbers DEMO MODE uses (0.05 idle / 0.4 listening / 0.7 speaking with
      flick() amplitude / 300ms crossfade handoff)
  A3  face-plate tap -> callback into the chat lane
  A4  the window.OhanaTotem control surface (appended)

Patches applied to template.html:
  T1  chat-lane CSS before </style>
  T2  chat-lane markup before the module <script>
  T3  the help card learns the two new interactions
  T4  title/links adjusted for the virtual totem
  T5  chat.js inlined after app.js inside the same module
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SRC3D = Path("/workspace/ohana-bot-3d")
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "dist"

APP = SRC3D / "app.js"
TPL = SRC3D / "template.html"
CHAT = HERE / "chat.js"


def once(hay: str, needle: str, what: str):
    n = hay.count(needle)
    if n != 1:
        print(f"ANCHOR FAIL [{what}]: found {n} times, expected exactly 1")
        print(f"  anchor: {needle[:90]!r}")
        sys.exit(2)


# --------------------------------------------------------------- app.js
app = APP.read_text(encoding="utf-8")

A1_ANCHOR = "let demo = false, demoT = 0, demoIdx = 0, demoPhase = '';"
once(app, A1_ANCHOR, "A1 demo state")
app = app.replace(A1_ANCHOR, A1_ANCHOR + """
// --- totem-web: the chat lane drives the glow through the SAME contract ----
// talk = {i, ph:'listening'|'thinking'|'speaking'|'dark', t, from, fromB}
// (named `talk`, not `live`: updateGlow() already has a local `const live=[]`)
let talk = null, faceTapCb = null;""")

A2_ANCHOR = "function updateGlow(dt){\n  if(demo){"
once(app, A2_ANCHOR, "A2 updateGlow head")
app = app.replace(A2_ANCHOR, """function updateGlow(dt){
  if(talk){
    // one conversation, one contract: identical amplitudes to DEMO MODE below —
    // idle 5%, listening 40% (fast pulse), speaking 70% with flicker, 300ms handoff.
    const HO = 0.3;
    talk.t += dt;
    const i = talk.i, dark = talk.ph === 'dark';
    for(let k=0;k<6;k++) B[k] = dark ? 0 : 0.05;
    const tgt = talk.ph === 'speaking' ? 0.7 : 0.4;
    if(dark){ /* power cut: every face goes out, including the speaker */ }
    else if(talk.from >= 0 && talk.from !== i && talk.t < HO){
      const u = talk.t / HO;
      B[talk.from] = lerp(talk.fromB, 0.05, u);
      B[i] = lerp(0.05, tgt, u);
    }
    else if(talk.ph === 'speaking'){ B[i] = 0.7*(0.78+0.22*flick(clk)); }
    else if(talk.ph === 'thinking'){ B[i] = 0.4*(0.45+0.30*Math.sin(clk*4.5)); }
    else { B[i] = 0.4*(0.55+0.45*Math.sin(clk*13)); }
  } else if(demo){""")

A3_ANCHOR = """      const f = FACES[+n[0]-1];
      if(sel) cap(f.em+' '+f.nm, f.line, f.zhLine, '#'+f.col.toString(16).padStart(6,'0'));"""
once(app, A3_ANCHOR, "A3 face tap")
app = app.replace(A3_ANCHOR, """      const f = FACES[+n[0]-1];
      if(faceTapCb) faceTapCb(f.k);          // totem-web: tapping a face summons it
      if(sel) cap(f.em+' '+f.nm, f.line, f.zhLine, '#'+f.col.toString(16).padStart(6,'0'));""")

# A5: a blackout must beat every other glow source, or the plug-pull beat keeps
# a lit face whenever a part happens to be selected / a build step is open.
A5_ANCHOR = """  const sn = sel && sel.match(/^(face|ring|pad)(\\d)$/);
  if(sn) B[+sn[2]-1] = Math.max(B[+sn[2]-1], 0.42+0.1*Math.sin(clk*6));
  if(stage>=0) for(let i=0;i<6;i++) if(stageHas('ring'+(i+1))) B[i]=Math.max(B[i], 0.22+0.12*Math.sin(clk*3-i));"""
once(app, A5_ANCHOR, "A5 selection boost")
app = app.replace(A5_ANCHOR, """  const DARK = !!(talk && talk.ph === 'dark');   // totem-web: power cut wins
  const sn = sel && sel.match(/^(face|ring|pad)(\\d)$/);
  if(sn && !DARK) B[+sn[2]-1] = Math.max(B[+sn[2]-1], 0.42+0.1*Math.sin(clk*6));
  if(stage>=0 && !DARK) for(let i=0;i<6;i++) if(stageHas('ring'+(i+1))) B[i]=Math.max(B[i], 0.22+0.12*Math.sin(clk*3-i));""")

A4 = """

// ======================================================================
// totem-web control surface — the chat lane's only way into the body.
// (A4 patch, applied by ohana-totem/src/build-page.py)
// ======================================================================
const hex6 = n => '#'+n.toString(16).padStart(6,'0');
function faceIdx(k){ for(let i=0;i<FACES.length;i++) if(FACES[i].k===k) return i; return -1; }
window.OhanaTotem = {
  faces: FACES.map((f,i)=>({k:f.k, i, nm:f.nm, em:f.em, zh:f.zh, job:f.job, zhJob:f.zhJob,
                            line:f.line, zhLine:f.zhLine, col:hex6(f.col), gpio:f.gpio, px:f.px})),
  summon(k, ph){
    const i = faceIdx(k); if(i<0) return -1;
    if(demo){ demo=false; $('#bDemo').classList.remove('on'); demoPhase=''; }
    if(stage>=0) setStage(-1);
    const from = talk ? talk.i : -1, fromB = talk ? B[talk.i] : 0.05;
    talk = {i, ph: ph||'listening', t:0, from, fromB};
    return i;
  },
  phase(ph){
    if(!talk) return;
    if(talk.ph === ph) return;
    talk.ph = ph; talk.t = 0; talk.from = -1;
  },
  dark(on){
    if(on){ if(!talk) this.summon(FACES[FACES.length-1].k, 'dark'); else { talk.ph='dark'; talk.t=0; talk.from=-1; } }
    else if(talk){ talk.ph='listening'; talk.t=0; }
  },
  release(){ talk = null; cap(null); },
  caption(who, what, ph, col){ cap(who, what, ph, col); },
  onFaceTap(fn){ faceTapCb = fn; },
  assemble(ms){ tween(0, ms||1800); },
  get state(){ return talk ? {face: FACES[talk.i].k, phase: talk.ph, B: B.slice()} : null; }
};
"""
app = app + A4

# --------------------------------------------------------------- template
tpl = TPL.read_text(encoding="utf-8")

CHAT_CSS = """
/* ---------- chat lane (totem-web) ---------- */
#chat{position:fixed;right:12px;bottom:calc(var(--dockh,150px) + 8px);width:336px;z-index:8;
  display:flex;flex-direction:column;overflow:hidden;max-height:min(58vh,520px)}
#chat.closed{max-height:none}
#chatHd{font-size:11.5px;color:var(--gold);padding:10px 12px;display:flex;align-items:center;gap:7px;
  cursor:pointer;user-select:none;letter-spacing:.4px;flex:none}
#chatHd:hover{background:rgba(255,180,67,.06)}
#chatHd em{font-style:normal;color:var(--dim);font-size:9.5px;margin-left:auto;
  border:1px solid var(--line);border-radius:999px;padding:2px 7px}
#chatHd i{font-style:normal;color:var(--dim);font-size:10px}
#chatBody{display:flex;flex-direction:column;min-height:0;padding:0 10px 10px}
#chat.closed #chatBody{display:none}
#chatFaces{display:flex;gap:4px;flex-wrap:wrap;padding-bottom:7px;flex:none}
.cface{font-size:9.5px;letter-spacing:.2px;padding:5px 7px;border-radius:999px;border:1px solid var(--line);
  background:rgba(18,21,29,.8);cursor:pointer;color:var(--dim);display:flex;align-items:center;gap:3px}
.cface i{font-style:normal;font-size:12px}
.cface:hover{border-color:rgba(255,180,67,.45);color:var(--ink)}
.cface.on{background:rgba(255,180,67,.1);box-shadow:0 0 12px rgba(255,180,67,.14)}
#chatLog{flex:1 1 auto;min-height:92px;overflow-y:auto;padding:4px 2px 6px;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);scrollbar-width:thin}
.cl{font-size:11.5px;line-height:1.5;padding:4px 2px;color:#d6d0c4}
.cl b{display:block;font-size:9.5px;letter-spacing:.6px;color:var(--dim);font-weight:600}
.cl.me{color:#9fd0ff}
.cl.me b{color:#5c87b8}
.cl.sys{font-size:10px;color:var(--dim);font-style:italic}
.cl.beat{font-size:10px;color:var(--gold);border-top:1px dashed #2b3040;margin-top:5px;padding-top:6px}
.cl.bot.live span{border-bottom:1px solid rgba(255,180,67,.35)}
#chatRow{display:flex;gap:5px;padding-top:8px;flex:none}
#chatIn{flex:1;min-width:0;font-family:inherit;font-size:12px;color:var(--ink);background:rgba(10,12,17,.9);
  border:1px solid var(--line);border-radius:9px;padding:8px 10px}
#chatIn:focus{outline:none;border-color:rgba(255,180,67,.55)}
#chatRow button{padding:7px 10px}
#chatMic.dead{opacity:.45}
#chatMic.on{background:rgba(255,107,107,.22);border-color:#ff6b6b;color:#ffd9d9}
#chatFoot{display:flex;align-items:center;gap:5px;padding-top:7px;flex:none;font-size:10px;color:var(--dim)}
#chatWho{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:10px}
button.mini{font-size:10px;padding:4px 7px;border-radius:8px}
button.mini.on{background:rgba(255,180,67,.18);border-color:var(--gold);color:var(--gold)}
#chatMem{font-size:10px;color:var(--dim);border:1px solid var(--line);border-radius:999px;padding:3px 7px}
@media (max-width:620px),(max-height:520px){
  #chat{left:8px;right:8px;width:auto;bottom:calc(var(--dockh,150px) + 6px);max-height:44vh;z-index:9}
  #chatLog{min-height:70px}
  body.chatopen #steps{display:none}
  body.chatopen #info{bottom:auto;top:74px;max-height:34vh}
}
"""
once(tpl, "</style>", "T1 style close")
tpl = tpl.replace("</style>", CHAT_CSS + "</style>")

CHAT_HTML = """<div id="chat" class="card">
  <h3 id="chatHd">💬 TALK TO THE TOTEM <em id="chatMode">…</em><i id="chatTog">▾</i></h3>
  <div id="chatBody">
    <div id="chatFaces"></div>
    <div id="chatLog"></div>
    <div id="chatRow">
      <input id="chatIn" type="text" autocomplete="off" spellcheck="false"
             placeholder="type to talk · 打字对话 — try &quot;my name is …&quot;">
      <button class="pri" id="chatSend" title="send">▶</button>
      <button id="chatMic" title="push to talk">🎤</button>
    </div>
    <div id="chatFoot">
      <span id="chatWho">—</span>
      <span id="chatMem">🧠 —</span>
      <button class="mini on" id="chatVoice" title="voice on/off">🔊</button>
      <button class="mini" id="chatDemo" title="run the 6-beat demo script">⚡ demo</button>
      <button class="mini" id="chatForget" title="wipe memory.json">forget</button>
    </div>
  </div>
</div>

"""
SCRIPT_ANCHOR = '<script type="importmap">'
once(tpl, SCRIPT_ANCHOR, "T2 script head")
tpl = tpl.replace(SCRIPT_ANCHOR, CHAT_HTML + SCRIPT_ANCHOR)

T3_ANCHOR = ("      <li>✨ <b>DEMO MODE</b> plays the real glow contract: "
             "idle breathing → a face speaks → 300ms handoff</li>")
once(tpl, T3_ANCHOR, "T3 help list")
tpl = tpl.replace(T3_ANCHOR, T3_ANCHOR + """
      <li>💬 <b>talk to it</b> — tap a face or type; the speaking face glows, the rest dim
        <span>· 和图腾对话</span></li>
      <li>⚡ <b>pull the plug</b> — kill the bridge, start it again, reload: it greets you by name
        <span>· 断电也记得你</span></li>""")

T4_ANCHOR = ('<div id="title"><b>🗿 ʻOHANA BOT · ASSEMBLY</b>'
             '<span>虚拟装配模型 · 六个声音，一个图腾 · tap any part</span></div>')
once(tpl, T4_ANCHOR, "T4 title")
tpl = tpl.replace(T4_ANCHOR,
                  '<div id="title"><b>🗿 ʻOHANA BOT · THE VIRTUAL TOTEM</b>'
                  '<span>六个声音，一个图腾 · tap a face to talk · tap a part to inspect</span></div>')

T5_ANCHOR = "/*__APP__*/"
once(tpl, T5_ANCHOR, "T5 app marker")
chat = CHAT.read_text(encoding="utf-8")
page = tpl.replace(T5_ANCHOR, app + "\n" + chat)

# ------------------------------------------------------------- write + gate
OUT.mkdir(parents=True, exist_ok=True)
(HERE / ".app.patched.js").write_text(app, encoding="utf-8")
for f in ("three.module.js", "OrbitControls.js"):
    src = SRC3D / f
    dst = OUT / f
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        dst.write_bytes(src.read_bytes())

for f, label in [(HERE / ".app.patched.js", "patched app.js"), (CHAT, "chat.js")]:
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"SYNTAX ERROR in {label}:\n{r.stderr}")
        sys.exit(3)

# GFW law: nothing may be fetched at runtime
bad = re.findall(r'(?:src|href)="https?://[^"]+"', page)
bad += re.findall(r'import[^;\n]*from\s*[\'"]https?://', page)
if bad:
    print("GFW LAW VIOLATION — remote references in the shipped page:", bad[:5])
    sys.exit(4)

(OUT / "index.html").write_text(page, encoding="utf-8")
print(f"built {OUT/'index.html'}  {len(page):,} bytes "
      f"(app {len(app):,} + chat {len(chat):,})")
print(f"  remote refs: 0 · 'https://' occurrences in page: {page.count('https://')}")

# ---------------------------------------------------------------- static mirror
# A deployed copy of dist/ has NO bridge behind it. So dist also carries the
# demo script as a flat file (script.json, RELATIVE audio paths) plus the
# pre-rendered demo mp3s — chat.js detects the missing bridge (STATIC mode)
# and still plays the full 6-beat show from these files.
import json
import shutil

sys.path.insert(0, str(HERE.parent))
import demo_script  # noqa: E402

man = {}
man_p = HERE.parent / "audio" / "demo" / "manifest.json"
if man_p.exists():
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
    except Exception:
        man = {}

def _rel(entry):  # "audio/demo/beatN.mp3" — relative to the page, never "/..."
    f = (entry or {}).get("file")
    return f if f else None

beats = []
for b in demo_script.BEATS:
    e = dict(b)
    e["audio"] = _rel(man.get(f"beat{b['id']}"))
    beats.append(e)
extra = {x["id"]: {"text": x["text"], "face": x["face"],
                   "audio": _rel(man.get(x["id"]))} for x in demo_script.EXTRA}
(OUT / "script.json").write_text(json.dumps(
    {"beats": beats, "extra": extra,
     "prerendered": sum(1 for b in beats if b["audio"]), "static": True},
    ensure_ascii=False), encoding="utf-8")

dst_demo = OUT / "audio" / "demo"
dst_demo.mkdir(parents=True, exist_ok=True)
n_mp3 = 0
for p in sorted((HERE.parent / "audio" / "demo").glob("*.mp3")):
    shutil.copy2(p, dst_demo / p.name)
    n_mp3 += 1
print(f"  static mirror: script.json ({len(beats)} beats) + {n_mp3} demo mp3s → dist/audio/demo/")
