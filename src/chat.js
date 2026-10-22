// ======================================================================
// chat.js — the CHAT LANE of the virtual ʻOhana totem (totem-web).
//
// The 3D body (app.js) owns the glow. This file owns the conversation and
// drives the body through window.OhanaTotem, which plays the SAME glow
// contract DEMO MODE plays (idle 5% / listening 40% / speaking 70% with
// amplitude flicker / 300ms crossfade handoff) — there is only one contract.
//
// Laws: every fetch is bounded by an AbortController (a hung poll is a dead
// stage), no CDN, no credentials, and the text is always on screen even when
// there is no voice.
// ======================================================================
(function(){
const T = window.OhanaTotem;
if(!T){ console.error('[chat] OhanaTotem API missing — 3D app did not load'); return; }

const q = s => document.querySelector(s);
const qs = new URLSearchParams(location.search);
const logEl = q('#chatLog'), inEl = q('#chatIn'), facesEl = q('#chatFaces');
const whoEl = q('#chatWho'), modeEl = q('#chatMode');

let active = 'shaka';
let gen = 0;                       // bumped whenever the stage state changes;
                                   // a finishing say() must not stomp a newer state
let STATIC = false;                // deployed mirror with no bridge behind it:
                                   // chat answers honestly in persona, DEMO MODE
                                   // plays from the bundled script.json + mp3s
const STATIC_LINES = {
  shaka: "Aloha! 🤙 You found my body — my six brains ride on Shaka's laptop at the demo, where I remember your name even through a power cut. Tap ⚡ demo for the full show with voices.",
  oso:   "The orchestra is warming up backstage 🎻 — my live brain runs on the laptop bridge. Tap ⚡ demo to hear the show, or find the family at opensourceorchestra.org.",
  deva:  "Fact: this is the static mirror 🦄 — my oracle brain runs on the laptop bridge at the demo. What still works right here: tap ⚡ demo and watch beat two.",
  crops: "🌿 Honest report: no brain is wired to this public mirror — it runs on the laptop bridge, open-source and local. The mandate smiles on honesty. Tap ⚡ demo for the recorded show.",
  kala:  "🪕 My strings are here but my teacher-brain lives on the laptop bridge. Tap ⚡ demo — beat five teaches you C major with one finger.",
  oke:   "💙 The karaoke machine is backstage on the laptop bridge. Tap ⚡ demo and stay for the singalong finale!"
};
// 中文 variants — picked when the typed message contains any CJK character
const STATIC_LINES_ZH = {
  shaka: "阿罗哈！🤙 你找到的是我的身体——六个大脑在演示现场跑在 Shaka 的笔记本上，断电我也记得你的名字。点 ⚡ demo 看带配音的完整演出。",
  oso:   "乐团正在后台热身 🎻——我的大脑跑在笔记本的本地桥接上。点 ⚡ demo 听整场演出。",
  deva:  "事实：这里是静态镜像 🦄——我的神谕大脑在演示现场的笔记本上。此刻能做的：点 ⚡ demo，看第二拍。",
  crops: "🌿 诚实汇报：这个公开镜像没有接大脑——它跑在笔记本上，开源且本地。章程欣赏诚实。点 ⚡ demo 看录好的演出。",
  kala:  "🪕 我的琴弦在这儿，但教琴的大脑在笔记本桥接上。点 ⚡ demo——第五拍用一根手指教你 C 大调。",
  oke:   "💙 卡拉OK机在后台的笔记本上。点 ⚡ demo，留到大合唱压轴！"
};
const CJK_RE = /[一-鿿]/;
let voiceOn = qs.get('mute') !== '1';
let busy = false, demoRunning = false, demoAbort = false;
let visitor = '';
let SCRIPT = null;
let audioEl = null;

// ------------------------------------------------------------------ fetch
function api(path, body, ms){
  const ac = new AbortController();
  const t = setTimeout(()=>ac.abort(), ms || 25000);      // never hang forever
  return fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? {'Content-Type':'application/json'} : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: ac.signal, cache: 'no-store'
  }).then(r => r.json().catch(()=>({}))).finally(()=>clearTimeout(t));
}

// -------------------------------------------------------------- transcript
function line(kind, who, text, col){
  const d = document.createElement('div');
  d.className = 'cl ' + kind;
  if(who){
    const b = document.createElement('b');
    b.textContent = who;
    if(col) b.style.color = col;
    d.appendChild(b);
  }
  const s = document.createElement('span');
  s.textContent = text;
  d.appendChild(s);
  logEl.appendChild(d);
  logEl.scrollTop = logEl.scrollHeight;
  return d;
}
function sys(text){ return line('sys','',text); }

function faceOf(k){ return T.faces.find(f=>f.k===k) || T.faces[0]; }

// ----------------------------------------------------------------- voices
function stopAudio(){
  if(audioEl){ try{ audioEl.pause(); }catch(e){} audioEl = null; }
}
function estimate(text){ return Math.max(1200, Math.min(14000, text.length * 62)); }

// plays `url` (or synthesizes `text`) and resolves when the mouth stops moving
function speak(text, face, url){
  stopAudio();
  if(!voiceOn) return new Promise(r=>setTimeout(r, estimate(text)));
  const play = (u) => new Promise(res=>{
    if(!u) return setTimeout(res, estimate(text));
    const a = new Audio(u);
    audioEl = a;
    let done = false;
    const fin = ()=>{ if(done) return; done = true; res(); };
    a.onended = fin;
    a.onerror = fin;
    setTimeout(fin, 40000);                       // bounded, always
    a.play().catch(()=>{ setTimeout(fin, estimate(text)); });
  });
  if(url) return play(url);
  if(STATIC) return play(null);                 // no bridge — text + timer only
  return api('/tts', {face: face, text: text}, 30000)
    .then(r => play(r && r.url))
    .catch(()=> new Promise(r=>setTimeout(r, estimate(text))));
}

// --------------------------------------------------------------- one turn
function setActive(k, phase){
  active = k;
  T.summon(k, phase || 'listening');
  const f = faceOf(k);
  [...facesEl.children].forEach(c=>{
    const on = c.dataset.k === k;
    c.classList.toggle('on', on);
    c.style.borderColor = on ? f.col : '';
    c.style.color = on ? f.col : '';
  });
  whoEl.textContent = f.em + ' ' + f.nm + ' · ' + f.job;
  whoEl.style.color = f.col;
  T.caption(f.em + ' ' + f.nm, f.job + ' · ' + f.zhJob, 'LISTENING', f.col);
}

async function say(face, text, url, capPhase){
  const f = faceOf(face);
  const myGen = gen;
  T.summon(face, 'speaking');
  T.caption(f.em + ' ' + f.nm + ' — speaking', text.slice(0, 88) + (text.length > 88 ? '…' : ''), capPhase || 'SPEAKING 70%', f.col);
  const el = line('bot', f.em + ' ' + f.nm, text, f.col);
  el.classList.add('live');
  await speak(text, face, url);
  el.classList.remove('live');
  if(myGen !== gen) return;            // the stage moved on (plug pull, new turn)
  T.phase('listening');
  T.caption(f.em + ' ' + f.nm, f.job + ' · ' + f.zhJob, 'LISTENING', f.col);
}

async function send(text){
  if(!text.trim()) return;
  if(demoRunning) stopDemo();
  // barge-in: a judge who types while the totem is talking INTERRUPTS it.
  // The older turn's reply is already on screen; it just loses the stage.
  if(busy){ gen++; stopAudio(); }
  const myGen = ++gen;
  busy = true; inEl.value = '';
  line('me', 'you', text);
  const f0 = faceOf(active);
  T.summon(active, 'thinking');
  T.caption(f0.em + ' ' + f0.nm + ' — thinking', 'persona + domain pack → reply', 'THINKING', f0.col);
  if(STATIC){
    // the mirror has no brain: answer honestly, in persona, and move on —
    // never leave the stage stuck on THINKING
    await new Promise(r2=>setTimeout(r2, 700));
    if(myGen === gen){
      const lines = CJK_RE.test(text) ? STATIC_LINES_ZH : STATIC_LINES;
      await say(active, lines[active] || lines.shaka);
      busy = false; inEl.focus();
    }
    return;
  }
  let r = null;
  try{
    r = await api('/chat', {face: active, text: text, visitor: visitor || undefined}, 60000);
  }catch(e){
    sys('bridge did not answer (' + (e.name||e) + ') — the totem is still here, try again');
  }
  const stale = () => myGen !== gen && gen > myGen;
  if(r && r.reply){
    if(r.visitor && r.visitor !== visitor){ visitor = r.visitor; memPill(); }
    if(stale()){ line('bot', faceOf(r.face).em + ' ' + faceOf(r.face).nm, r.reply, faceOf(r.face).col); }
    else{
      if(r.face !== active) setActive(r.face, 'speaking');
      await say(r.face, r.reply);
      // a face that names a sibling hands the question over: light them next
      if(r.handoff && r.handoff !== r.face && !stale()){
        const h = faceOf(r.handoff);
        setActive(r.handoff, 'listening');
        sys('→ handed to ' + h.em + ' ' + h.nm);
      }
    }
  }else if(r && r.error){
    sys('bridge error: ' + r.error);
  }
  if(!stale()) busy = false;
  if(!demoRunning && !stale()) inEl.focus();
}

// ------------------------------------------------------------- demo mode
function stopDemo(){
  gen++;
  demoAbort = true; demoRunning = false;
  q('#chatDemo').classList.remove('on');
  stopAudio();
}

async function runDemo(){
  if(demoRunning){ stopDemo(); return; }
  if(!SCRIPT){ sys('demo script not loaded'); return; }
  demoRunning = true; demoAbort = false; busy = true;
  q('#chatDemo').classList.add('on');
  logEl.innerHTML = '';
  sys('⚡ DEMO MODE — the 6-beat Demo Day script' +
      (SCRIPT.prerendered ? ' · ' + SCRIPT.prerendered + ' lines pre-rendered, no network needed'
                          : ' · no pre-rendered audio (run prerender.py)'));
  const wait = ms => new Promise(r=>setTimeout(r, ms));
  for(const b of SCRIPT.beats){
    if(demoAbort) break;
    const f = faceOf(b.face);
    line('beat', 'beat ' + b.id, b.title + ' — ' + b.note);
    await wait(500);
    if(demoAbort) break;

    if(b.kind === 'powercycle'){
      // the money beat: faces die, then boot and resume from memory.json
      line('me', 'you', b.visitor);
      gen++;                           // anything still speaking loses the stage
      stopAudio();
      T.caption('⚡ POWER CUT', 'the cable comes out mid-sentence · 断电', 'DARK 0%', '#ff6b6b');
      T.dark(true);
      await wait(b.dark_ms || 2000);
      if(demoAbort) break;
      T.caption('🗿 booting…', 'memory.json survived · 记忆保留', 'BOOT', '#ffb443');
      setActive(b.face, 'thinking');
      await wait(900);
      if(demoAbort) break;
      let text = b.reply, url = b.audio;
      if(visitor){
        const personal = text.replace('my friend', visitor);
        if(personal !== text){
          text = personal;
          // say the judge's NAME if we can synthesize it right now; if the
          // network is dead, fall back to the pre-rendered generic take —
          // the on-screen line always carries the name either way
          if(voiceOn && !STATIC){
            const r = await api('/tts', {face: b.face, text: personal}, 12000).catch(()=>null);
            if(r && r.url) url = r.url;
          }
        }
      }
      await say(b.face, text, url, 'RESUMED FROM MEMORY');
      await wait(700);
      continue;
    }

    line('me', 'you', b.visitor);
    setActive(b.face, 'thinking');
    await wait(650);
    if(demoAbort) break;
    await say(b.face, b.reply, b.audio);
    await wait(650);
  }
  if(!demoAbort) sys('— end of demo · six faces, one totem, zero cloud 🗿');
  demoRunning = false; busy = false;
  q('#chatDemo').classList.remove('on');
}

// ------------------------------------------------------------------- mic
function initMic(){
  const btn = q('#chatMic');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
    btn.classList.add('dead');
    btn.title = 'this browser has no speech recognition — type to talk (the Pi build uses faster-whisper offline)';
    btn.onclick = ()=> sys('no speech recognition in this browser — type to talk. ' +
      'On the hardware totem this is faster-whisper, fully offline.');
    return;
  }
  let rec = null, listening = false;
  btn.title = 'hold-to-talk (browser speech recognition — needs network)';
  btn.onclick = ()=>{
    if(listening){ rec && rec.stop(); return; }
    rec = new SR();
    rec.lang = 'en-US'; rec.interimResults = false; rec.maxAlternatives = 1;
    listening = true; btn.classList.add('on');
    const f = faceOf(active);
    T.summon(active, 'listening');
    T.caption(f.em + ' ' + f.nm + ' — listening', 'push-to-talk · 按住说话', 'LISTENING 40%', f.col);
    rec.onresult = e => { const t = e.results[0][0].transcript; if(t) send(t); };
    rec.onerror = e => sys('mic: ' + (e.error || 'failed') + ' — type to talk');
    rec.onend = ()=>{ listening = false; btn.classList.remove('on'); };
    try{ rec.start(); }catch(e){ listening = false; btn.classList.remove('on'); }
  };
}

// ------------------------------------------------------------------- boot
function memPill(){
  const el = q('#chatMem');
  el.textContent = visitor ? '🧠 ' + visitor : '🧠 —';
  el.title = visitor ? 'memory.json remembers ' + visitor + ' — survives a power cycle'
                     : 'no name yet — say "my name is …"';
}

// chips read top-of-the-pole first: SHAKA · OSO · DEVA · CROPS · KALA · OKE
T.faces.slice().reverse().forEach(f=>{
  const b = document.createElement('div');
  b.className = 'cface'; b.dataset.k = f.k;
  b.innerHTML = '<i>' + f.em + '</i>' + f.nm;
  b.title = f.nm + ' — ' + f.job + ' · ' + f.zhJob;
  b.onclick = ()=>{ gen++; stopAudio(); setActive(f.k, 'listening'); inEl.focus(); };
  facesEl.appendChild(b);
});

q('#chatSend').onclick = ()=> send(inEl.value);
inEl.addEventListener('keydown', e=>{ if(e.key === 'Enter'){ e.preventDefault(); send(inEl.value); } });
q('#chatDemo').onclick = runDemo;
q('#chatVoice').onclick = ()=>{
  voiceOn = !voiceOn;
  q('#chatVoice').classList.toggle('on', voiceOn);
  q('#chatVoice').textContent = voiceOn ? '🔊' : '🔇';
  if(!voiceOn) stopAudio();
};
q('#chatForget').onclick = async ()=>{
  stopDemo();
  if(!STATIC) await api('/forget', {}).catch(()=>{});
  visitor = ''; memPill(); logEl.innerHTML = '';
  sys('memory.json wiped — fresh judge, fresh totem');
  setActive('shaka', 'listening');
};
q('#chatHd').onclick = ()=>{
  const c = q('#chat');
  c.classList.toggle('closed');
  document.body.classList.toggle('chatopen', !c.classList.contains('closed'));
  q('#chatTog').textContent = c.classList.contains('closed') ? '▸' : '▾';
};
initMic();
setActive('shaka', 'listening');
memPill();
if(window.innerWidth < 620){
  q('#chat').classList.add('closed');
  q('#chatTog').textContent = '▸';
}else{
  document.body.classList.add('chatopen');
}

(async function boot(){
  let h = null;
  try{ h = await api('/health', null, 8000); }catch(e){ h = null; }
  if(h && h.mode){
    modeEl.textContent = (h.mode === 'mock' ? 'mock brain · ¥0' : 'llm: ' + h.mode);
    modeEl.title = h.mode === 'mock'
      ? 'no LLM key: canned in-persona answers from the real persona + pack files'
      : 'live LLM lane';
  }else{
    // a 404/{} from a static host and a dead local bridge look the same:
    // no h.mode. Treat both as the public mirror — never hang the stage.
    STATIC = true;
    modeEl.textContent = 'static mirror · demo plays';
    modeEl.title = 'public mirror — the talking brains run on the laptop bridge at the demo; ⚡ demo plays the recorded 6-beat show with voices';
    sys('🔌 public mirror — the six brains ride on the laptop bridge at Demo Day. ⚡ demo plays the recorded show with voices; tap any part of the totem to explore the build.');
  }
  try{ SCRIPT = await api(STATIC ? 'script.json' : '/script', null, 8000); }
  catch(e){ SCRIPT = null; }
  if(SCRIPT && !SCRIPT.beats) SCRIPT = null;    // an html 404 parsed to {}
  if(!STATIC) try{
    const r = await api('/resume', null, 15000);
    if(r && r.reply){
      visitor = r.visitor || ''; memPill();
      if(r.resumed) sys('⚡ resumed from memory.json' + (visitor ? ' — it remembers ' + visitor : ''));
      setActive(r.face, 'speaking');
      // a page load is a user gesture only sometimes; a blocked autoplay is harmless
      await say(r.face, r.reply, r.resumed ? (SCRIPT && SCRIPT.extra &&
        SCRIPT.extra.resume_generic && !visitor ? SCRIPT.extra.resume_generic.audio : null) : null);
    }
  }catch(e){ /* the page still works without a greeting */ }
  if(qs.get('demo') === '1'){
    sys('demo armed — press ⚡ demo, or wait'); setTimeout(()=>{ if(!busy) runDemo(); }, 1500);
  }
})();

// the 3D body tells us when a face plate was tapped — that IS a summon
T.onFaceTap(k => {
  if(demoRunning) return;
  gen++; stopAudio();
  setActive(k, 'listening');
  const c = q('#chat');
  if(c.classList.contains('closed')) q('#chatHd').click();
  inEl.focus();
});

window.__chat = {
  get active(){ return active; }, get visitor(){ return visitor; },
  get busy(){ return busy; }, get demoRunning(){ return demoRunning; },
  send, runDemo, stopDemo, setActive,
  log(){ return [...logEl.children].map(c=>c.textContent); }
};
})();
