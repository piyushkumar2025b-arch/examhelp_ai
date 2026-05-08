"""
youtube_player_addon.py — Full YouTube Music Player
Single self-contained HTML component:
  - Real search via Invidious API (multiple fallback instances)
  - Live YouTube playback via IFrame embed
  - Queue, categories, speed/volume controls
  - No API key needed, no login
"""
import streamlit as st
import streamlit.components.v1 as components

PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Music Player</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#0a0a0f;--s1:#12121a;--s2:#1a1a26;--s3:#22223a;--acc:#7c6ef7;--red:#f76e6e;--grn:#6ef7c4;--txt:#f0eeff;--mut:#7a7a9a;--bdr:rgba(124,110,247,0.18);--grad:linear-gradient(135deg,#7c6ef7,#f76e6e)}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:'Syne',sans-serif;padding:14px}
.layout{display:grid;grid-template-columns:1fr 300px;gap:14px}
@media(max-width:700px){.layout{grid-template-columns:1fr}}
.card{background:var(--s1);border:1px solid var(--bdr);border-radius:18px;padding:16px;margin-bottom:12px}
.ct{font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--mut);font-family:'JetBrains Mono',monospace;margin-bottom:12px}
.ct::before{content:'▸ ';color:var(--acc)}
.search-row{display:flex;gap:8px;margin-bottom:10px}
.si{flex:1;background:var(--s2);border:1px solid var(--bdr);color:var(--txt);border-radius:10px;padding:10px 14px;font-family:'Syne',sans-serif;font-size:14px;outline:none;transition:border-color .2s}
.si:focus{border-color:var(--acc)}.si::placeholder{color:var(--mut)}
.btn{padding:10px 16px;border-radius:10px;border:none;cursor:pointer;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;background:var(--grad);color:#fff;transition:opacity .2s,transform .1s;white-space:nowrap}
.btn:hover{opacity:.88}.btn:active{transform:scale(.97)}
.btn-sm{padding:6px 11px;font-size:12px;border-radius:8px}
.btn-o{background:transparent;color:var(--txt);border:1px solid var(--bdr)}
.btn-o:hover{background:var(--s2)}
.cats{display:flex;gap:6px;flex-wrap:wrap}
.cat{padding:5px 12px;border-radius:100px;border:1px solid var(--bdr);background:var(--s2);color:var(--mut);font-size:11px;cursor:pointer;transition:all .15s;font-family:'Syne',sans-serif;font-weight:600}
.cat:hover,.cat.on{background:rgba(124,110,247,.15);color:var(--acc);border-color:var(--acc)}
.video-wrap{position:relative;border-radius:12px;overflow:hidden;background:#000;border:1px solid var(--bdr);margin-bottom:12px}
.video-wrap iframe{display:block;width:100%;height:280px;border:none}
.ph{height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;background:var(--s2);border-radius:12px;border:1px solid var(--bdr);margin-bottom:12px;color:var(--mut)}
.ph .icon{font-size:44px;opacity:.25}
.ph .lbl{font-size:11px;font-family:'JetBrains Mono',monospace;letter-spacing:2px}
.np{background:var(--s2);border:1px solid var(--bdr);border-radius:12px;padding:10px 12px;display:flex;align-items:center;gap:10px;margin-bottom:10px}
.np-img{width:44px;height:32px;border-radius:6px;object-fit:cover;background:var(--s3);flex-shrink:0}
.np-inf{flex:1;min-width:0}
.np-t{font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.np-c{font-size:10px;color:var(--mut);font-family:'JetBrains Mono',monospace}
.np-live{padding:2px 8px;border-radius:100px;font-size:9px;font-weight:700;background:rgba(110,247,196,.1);color:var(--grn);border:1px solid rgba(110,247,196,.2);font-family:'JetBrains Mono',monospace;flex-shrink:0}
.viz{height:44px;background:var(--s2);border-radius:8px;display:flex;align-items:flex-end;justify-content:center;gap:3px;padding:6px;overflow:hidden;border:1px solid var(--bdr);margin-bottom:10px}
.bar{width:4px;border-radius:2px 2px 0 0;background:var(--grad);animation:ba ease-in-out infinite;transform-origin:bottom}
@keyframes ba{0%,100%{transform:scaleY(.15)}50%{transform:scaleY(1)}}
.ctrls{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.sliders{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.sl-g{display:flex;flex-direction:column;gap:4px}
.sl-l{font-size:10px;color:var(--mut);font-family:'JetBrains Mono',monospace;display:flex;justify-content:space-between}
.sl-v{color:var(--acc);font-weight:600}
input[type=range]{-webkit-appearance:none;width:100%;height:4px;border-radius:4px;background:var(--s3);outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:13px;height:13px;border-radius:50%;background:var(--acc);box-shadow:0 0 5px rgba(124,110,247,.5)}
.res-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px}
@media(max-width:500px){.res-grid{grid-template-columns:1fr 1fr}}
.vc{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;overflow:hidden;cursor:pointer;transition:all .2s}
.vc:hover{transform:translateY(-2px);border-color:rgba(124,110,247,.4);box-shadow:0 6px 20px rgba(124,110,247,.1)}
.vc img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--s3)}
.vc-b{padding:7px 8px}
.vc-t{font-size:11px;font-weight:700;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px}
.vc-m{font-size:9px;color:var(--mut);font-family:'JetBrains Mono',monospace}
.vc-btns{display:flex;gap:4px;padding:0 7px 7px}
.q-item{display:flex;gap:8px;align-items:center;background:var(--s2);border-radius:8px;padding:7px 9px;margin-bottom:6px;border:1px solid transparent;transition:all .15s}
.q-item:hover{border-color:var(--bdr)}
.q-item.now{background:rgba(124,110,247,.1);border-color:rgba(124,110,247,.3)}
.q-img{width:42px;height:30px;border-radius:5px;object-fit:cover;background:var(--s3);flex-shrink:0;cursor:pointer}
.q-inf{flex:1;min-width:0;cursor:pointer}
.q-t{font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.q-m{font-size:9px;color:var(--mut);font-family:'JetBrains Mono',monospace}
.q-x{background:none;border:none;color:var(--mut);cursor:pointer;font-size:13px;flex-shrink:0}
.q-x:hover{color:var(--red)}
.st{padding:10px 14px;border-radius:8px;font-size:11px;font-family:'JetBrains Mono',monospace;margin-bottom:8px;border:1px solid var(--bdr);background:var(--s2);color:var(--mut);display:none}
.st.on{display:block}.st.err{color:var(--red)}.st.ok{color:var(--grn)}
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:var(--s3);border-radius:2px}
</style>
</head>
<body>
<div class="layout">
  <!-- LEFT -->
  <div>
    <div class="card">
      <div class="ct">Search YouTube</div>
      <div class="search-row">
        <input class="si" id="q" placeholder="Search songs, artists, albums…" onkeydown="if(event.key==='Enter')doSearch()">
        <button class="btn" onclick="doSearch()">🔍 Search</button>
      </div>
      <div class="cats" id="cats"></div>
    </div>
    <div class="st" id="st"></div>
    <div class="card">
      <div class="ct">Now Playing</div>
      <div id="pslot">
        <div class="ph"><div class="icon">🎵</div><div class="lbl">SEARCH &amp; CLICK PLAY</div></div>
      </div>
      <div class="np" id="np" style="display:none">
        <img class="np-img" id="np-img" src="" alt="">
        <div class="np-inf">
          <div class="np-t" id="np-t">—</div>
          <div class="np-c" id="np-c">—</div>
        </div>
        <div class="np-live">▶ LIVE</div>
      </div>
      <div class="viz" id="viz"></div>
      <div class="ctrls">
        <button class="btn btn-sm btn-o" onclick="seek(-10)">« 10s</button>
        <button class="btn btn-sm btn-o" onclick="seek(10)">10s »</button>
        <button class="btn btn-sm btn-o" id="mb" onclick="toggleMute()">🔊</button>
        <button class="btn btn-sm btn-o" onclick="playNext()">⏭ Next</button>
      </div>
      <div class="sliders">
        <div class="sl-g">
          <div class="sl-l">Volume <span class="sl-v" id="vv">80%</span></div>
          <input type="range" id="vol" min="0" max="100" value="80" oninput="setVol(this.value)">
        </div>
        <div class="sl-g">
          <div class="sl-l">Speed <span class="sl-v" id="sv">1.0×</span></div>
          <input type="range" id="spd" min="25" max="200" value="100" step="5" oninput="setSpd(this.value)">
        </div>
      </div>
    </div>
    <div class="card" id="rcard" style="display:none">
      <div class="ct" id="rlabel">Results</div>
      <div class="res-grid" id="rgrid"></div>
      <button class="btn btn-o" onclick="loadMore()" style="width:100%">Load More</button>
    </div>
  </div>
  <!-- RIGHT -->
  <div>
    <div class="card" style="position:sticky;top:10px">
      <div class="ct">Queue</div>
      <div id="qempty" style="text-align:center;padding:24px 0;color:var(--mut);font-size:11px;font-family:'JetBrains Mono',monospace">EMPTY<br><span style="opacity:.5">Hit ➕ on any video</span></div>
      <div id="qlist"></div>
      <div id="qact" style="display:none;margin-top:8px">
        <button class="btn btn-o" onclick="clearQueue()" style="width:100%">🗑 Clear Queue</button>
      </div>
    </div>
  </div>
</div>
<div id="ytp" style="position:fixed;bottom:-9999px;left:-9999px;width:1px;height:1px"></div>
<script>
let ytP=null,ytR=false,muted=false,queue=[],cur=null,results=[],page=1,lastQ='';
const INV=['https://inv.nadeko.net','https://invidious.io.lol','https://yt.artemislena.eu','https://invidious.privacydev.net','https://iv.melmac.space'];
const CATS=[['🔥 Trending','trending music 2025'],['💿 Lo-Fi','lofi hip hop music'],['🎸 Rock','best rock songs'],['🎵 Pop','top pop songs 2025'],['🎤 Hip-Hop','hip hop rap music'],['🎻 Classical','classical music relaxing'],['🧘 Meditation','meditation music calm'],['⚡ Electronic','electronic dance music'],['💃 Bollywood','bollywood songs 2025'],['🌙 Night Drive','night drive synthwave']];

// Visualizer
(function(){const v=document.getElementById('viz');for(let i=0;i<32;i++){const b=document.createElement('div');b.className='bar';b.style.height=(8+Math.random()*26)+'px';b.style.animationDuration=(0.4+Math.random()*.7)+'s';b.style.animationDelay=(Math.random()*.4)+'s';v.appendChild(b)}})();

// Categories
(function(){const row=document.getElementById('cats');CATS.forEach(([l,q])=>{const p=document.createElement('button');p.className='cat';p.textContent=l;p.onclick=()=>{document.querySelectorAll('.cat').forEach(x=>x.classList.remove('on'));p.classList.add('on');document.getElementById('q').value=q;doSearch()};row.appendChild(p)})})();

// YT API
(function(){const s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';document.head.appendChild(s)})();
window.onYouTubeIframeAPIReady=function(){ytR=true;ytP=new YT.Player('ytp',{height:'1',width:'1',videoId:'',playerVars:{autoplay:0,rel:0},events:{onStateChange:function(e){if(e.data===YT.PlayerState.ENDED)playNext()}}})};

function playVideo(v){
  cur=v;
  document.getElementById('np').style.display='flex';
  document.getElementById('np-img').src=v.thumb;
  document.getElementById('np-t').textContent=v.title;
  document.getElementById('np-c').textContent=v.channel+(v.duration?' · '+v.duration:'');
  const slot=document.getElementById('pslot');
  const old=document.getElementById('yt-frame');if(old)old.parentNode.remove();
  const ph=slot.querySelector('.ph');if(ph)ph.remove();
  const wrap=document.createElement('div');wrap.className='video-wrap';
  const iframe=document.createElement('iframe');
  iframe.id='yt-frame';
  iframe.src='https://www.youtube.com/embed/'+v.id+'?autoplay=1&rel=0&modestbranding=1&playsinline=1&enablejsapi=1';
  iframe.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen';
  iframe.allowFullscreen=true;
  wrap.appendChild(iframe);
  slot.insertBefore(wrap,slot.firstChild);
  if(ytP&&ytP.loadVideoById)try{ytP.loadVideoById(v.id)}catch(e){}
  renderQueue();
  setStatus('▶ Now playing: '+v.title.substring(0,50),'ok');
}

function seek(s){if(ytP&&ytP.seekTo)try{ytP.seekTo((ytP.getCurrentTime()||0)+s,true)}catch(e){}}
function toggleMute(){muted=!muted;document.getElementById('mb').textContent=muted?'🔇':'🔊';if(ytP)try{muted?ytP.mute():ytP.unMute()}catch(e){}}
function setVol(v){document.getElementById('vv').textContent=v+'%';if(ytP&&ytP.setVolume)try{ytP.setVolume(parseInt(v))}catch(e){}}
function setSpd(v){const s=(parseInt(v)/100).toFixed(2);document.getElementById('sv').textContent=s+'×';if(ytP&&ytP.setPlaybackRate)try{ytP.setPlaybackRate(parseFloat(s))}catch(e){}}
function playNext(){if(!queue.length)return;const i=cur?queue.findIndex(x=>x.id===cur.id):-1;playVideo(queue[i+1]||queue[0])}

async function doSearch(p){
  const q=document.getElementById('q').value.trim();if(!q)return;
  if(!p||p===1){lastQ=q;page=1;results=[]}
  setStatus('Searching for "'+q+'"…','');
  const data=await invSearch(q,p||1);
  if(!data||!data.length){setStatus('No results found. Try another search.','err');return}
  results=results.concat(data);page=p||1;
  renderResults();setStatus(results.length+' results for "'+q+'"','ok');
}
function loadMore(){doSearch(page+1)}

async function invSearch(q,p){
  for(const base of INV){
    try{
      const r=await fetch(base+'/api/v1/search?q='+encodeURIComponent(q)+'&type=video&sort_by=relevance&page='+p+'&region=US',{signal:AbortSignal.timeout(7000)});
      if(!r.ok)continue;
      const d=await r.json();
      if(!Array.isArray(d))continue;
      return d.filter(v=>v.type==='video'&&v.videoId).map(v=>({id:v.videoId,title:v.title||'Untitled',channel:v.author||'',views:v.viewCount||0,duration:v.lengthSeconds?Math.floor(v.lengthSeconds/60)+':'+String(v.lengthSeconds%60).padStart(2,'0'):'',thumb:'https://i.ytimg.com/vi/'+v.videoId+'/mqdefault.jpg'}));
    }catch(e){continue}
  }
  return[];
}

function fmtV(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return n?String(n):''}

function renderResults(){
  document.getElementById('rcard').style.display='block';
  document.getElementById('rlabel').textContent='▸ '+results.length+' results for "'+lastQ+'"';
  const g=document.getElementById('rgrid');g.innerHTML='';
  results.forEach((v,i)=>{
    const d=document.createElement('div');d.className='vc';
    d.innerHTML='<img src="'+v.thumb+'" alt="" loading="lazy" onerror="this.style.background=\'#1a1a26\'">'
      +'<div class="vc-b"><div class="vc-t" title="'+v.title+'">'+v.title+'</div>'
      +'<div class="vc-m">'+v.channel+(v.duration?' · '+v.duration:'')+(v.views?' · '+fmtV(v.views):'')+'</div></div>'
      +'<div class="vc-btns">'
      +'<button class="btn btn-sm" style="flex:1" onclick="playVideo(results['+i+'])">▶ Play</button>'
      +'<button class="btn btn-sm btn-o" onclick="addQ(results['+i+'],this)" title="Queue">➕</button>'
      +'</div>';
    g.appendChild(d);
  });
}

function addQ(v,btn){if(queue.find(x=>x.id===v.id))return;queue.push(v);if(btn){btn.textContent='✓';btn.disabled=true}renderQueue()}
function removeQ(i){queue.splice(i,1);renderQueue()}
function clearQueue(){queue=[];renderQueue()}

function renderQueue(){
  const list=document.getElementById('qlist');
  const empty=document.getElementById('qempty');
  const act=document.getElementById('qact');
  list.innerHTML='';empty.style.display=queue.length?'none':'block';act.style.display=queue.length?'block':'none';
  queue.forEach((v,i)=>{
    const isNow=cur&&cur.id===v.id;
    const d=document.createElement('div');d.className='q-item'+(isNow?' now':'');
    d.innerHTML='<img class="q-img" src="'+v.thumb+'" alt="" onerror="this.style.background=\'#22223a\'">'
      +'<div class="q-inf"><div class="q-t">'+v.title+'</div><div class="q-m">'+v.channel+(v.duration?' · '+v.duration:'')+'</div></div>'
      +'<button class="q-x" onclick="removeQ('+i+')">✕</button>';
    d.querySelector('.q-img').onclick=d.querySelector('.q-inf').onclick=()=>playVideo(v);
    list.appendChild(d);
  });
}

let stT=null;
function setStatus(msg,type){
  const s=document.getElementById('st');s.textContent=msg;s.className='st on'+(type?' '+type:'');
  if(stT)clearTimeout(stT);stT=setTimeout(()=>s.classList.remove('on'),5000);
}
</script>
</body>
</html>"""


def render_youtube_player():
    """Render the fully self-contained YouTube Music Player."""
    st.markdown("""
<style>
section[data-testid="stMain"] .block-container {
    padding-top: 0.5rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)
    components.html(PLAYER_HTML, height=920, scrolling=True)
