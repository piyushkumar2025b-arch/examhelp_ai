"""
youtube_player_addon.py - Full YouTube Music Player (EXPANDED)
- Real YouTube video embedded full-size, plays directly inside the app
- Search via Invidious API (multi-instance fallback, no API key)
- Queue, History, Categories, Volume, Speed controls
"""
import streamlit as st
import streamlit.components.v1 as components

PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Player</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#09090f;--s1:#111118;--s2:#18181f;--s3:#22222e;--s4:#2a2a38;
  --acc:#7c6ef7;--acc2:#f76e6e;--grn:#6ef7c4;
  --txt:#f0eeff;--mut:#6a6a8a;--bdr:rgba(124,110,247,0.15);--bdr2:rgba(124,110,247,0.35);
  --grad:linear-gradient(135deg,#7c6ef7 0%,#c46ef7 50%,#f76e6e 100%);
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:var(--bg);color:var(--txt);font-family:'Syne',sans-serif;height:100%;overflow-x:hidden}
body{padding:0;display:flex;flex-direction:column}
.topbar{display:flex;align-items:center;gap:14px;padding:12px 18px;background:var(--s1);border-bottom:1px solid var(--bdr);position:sticky;top:0;z-index:100}
.logo{font-size:18px;font-weight:800;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap;letter-spacing:-0.5px}
.logo span{font-size:10px;font-family:'JetBrains Mono',monospace;background:none;-webkit-text-fill-color:var(--mut);letter-spacing:1.5px;display:block;margin-top:-3px}
.search-bar{flex:1;display:flex;gap:8px;max-width:700px}
.si{flex:1;background:var(--s2);border:1px solid var(--bdr);color:var(--txt);border-radius:10px;padding:10px 16px;font-family:'Syne',sans-serif;font-size:14px;outline:none;transition:all .2s}
.si:focus{border-color:var(--acc);background:var(--s3)}.si::placeholder{color:var(--mut)}
.btn{padding:10px 18px;border-radius:10px;border:none;cursor:pointer;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;background:var(--grad);color:#fff;transition:opacity .2s,transform .1s;white-space:nowrap}
.btn:hover{opacity:.85}.btn:active{transform:scale(.97)}
.btn-sm{padding:7px 12px;font-size:12px;border-radius:8px}
.btn-xs{padding:5px 9px;font-size:11px;border-radius:7px}
.btn-o{background:var(--s2);color:var(--txt);border:1px solid var(--bdr)}
.btn-o:hover{border-color:var(--bdr2);background:var(--s3)}
.main{display:grid;grid-template-columns:1fr 340px;min-height:calc(100vh - 56px)}
@media(max-width:800px){.main{grid-template-columns:1fr}}
.left{padding:16px;display:flex;flex-direction:column;gap:14px;overflow-y:auto;max-height:calc(100vh - 56px)}
.left::-webkit-scrollbar{width:3px}.left::-webkit-scrollbar-thumb{background:var(--s4);border-radius:2px}
.sec-label{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--mut);font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:8px}
.sec-label::before{content:'';display:block;width:3px;height:14px;border-radius:2px;background:var(--grad)}
.cats-row{display:flex;gap:7px;flex-wrap:wrap}
.cat-pill{padding:6px 14px;border-radius:100px;border:1px solid var(--bdr);background:var(--s2);color:var(--mut);font-size:11px;cursor:pointer;transition:all .15s;font-family:'Syne',sans-serif;font-weight:600;white-space:nowrap}
.cat-pill:hover,.cat-pill.active{background:rgba(124,110,247,.18);color:var(--acc);border-color:var(--acc)}
.video-container{background:#000;border-radius:16px;overflow:hidden;border:1px solid var(--bdr);width:100%}
.video-container iframe{display:block;width:100%;height:480px;border:none}
.video-ph{height:420px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;background:var(--s2);color:var(--mut)}
.video-ph .big-icon{font-size:72px;opacity:.1}
.video-ph .ph-text{font-size:12px;font-family:'JetBrains Mono',monospace;letter-spacing:3px;opacity:.45}
.video-ph .ph-hint{font-size:10px;color:var(--mut);opacity:.3;font-family:'JetBrains Mono',monospace}
.np-bar{background:var(--s1);border:1px solid var(--bdr);border-radius:14px;padding:12px 16px;display:flex;align-items:center;gap:14px}
.np-thumb{width:56px;height:40px;border-radius:8px;object-fit:cover;background:var(--s3);flex-shrink:0}
.np-info{flex:1;min-width:0}
.np-title{font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.np-channel{font-size:10px;color:var(--mut);font-family:'JetBrains Mono',monospace;margin-top:2px}
.np-badge{padding:3px 10px;border-radius:100px;font-size:9px;font-weight:700;background:rgba(110,247,196,.12);color:var(--grn);border:1px solid rgba(110,247,196,.25);font-family:'JetBrains Mono',monospace;flex-shrink:0;letter-spacing:.5px}
.viz{height:40px;background:var(--s2);border-radius:10px;display:flex;align-items:flex-end;justify-content:center;gap:2px;padding:5px 8px;border:1px solid var(--bdr);overflow:hidden}
.viz-bar{flex:1;max-width:6px;border-radius:2px 2px 0 0;background:var(--grad);animation:vizA ease-in-out infinite;transform-origin:bottom}
@keyframes vizA{0%,100%{transform:scaleY(.1)}50%{transform:scaleY(1)}}
.controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sliders-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.slider-group{display:flex;flex-direction:column;gap:5px}
.slider-label{font-size:10px;color:var(--mut);font-family:'JetBrains Mono',monospace;display:flex;justify-content:space-between}
.slider-val{color:var(--acc);font-weight:700}
input[type=range]{-webkit-appearance:none;width:100%;height:4px;border-radius:4px;background:var(--s4);outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--acc);cursor:pointer}
.status-bar{padding:9px 14px;border-radius:9px;font-size:11px;font-family:'JetBrains Mono',monospace;border:1px solid var(--bdr);background:var(--s2);color:var(--mut);display:none;align-items:center;gap:8px}
.status-bar.visible{display:flex}
.status-bar.ok{color:var(--grn);border-color:rgba(110,247,196,.2)}
.status-bar.err{color:var(--acc2);border-color:rgba(247,110,110,.2)}
.status-bar.loading::before{content:'';display:block;width:10px;height:10px;border-radius:50%;border:2px solid var(--acc);border-top-color:transparent;animation:spin .7s linear infinite;flex-shrink:0}
@keyframes spin{to{transform:rotate(360deg)}}
.results-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:10px}
.video-card{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;overflow:hidden;cursor:pointer;transition:all .2s}
.video-card:hover{transform:translateY(-3px);border-color:rgba(124,110,247,.4);box-shadow:0 8px 28px rgba(124,110,247,.12)}
.vc-thumb-wrap{position:relative;overflow:hidden}
.vc-thumb{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--s3)}
.vc-dur{position:absolute;bottom:5px;right:6px;background:rgba(0,0,0,.8);color:#fff;font-size:9px;padding:1px 5px;border-radius:4px;font-family:'JetBrains Mono',monospace}
.vc-body{padding:8px 10px}
.vc-title{font-size:11px;font-weight:700;color:var(--txt);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:4px}
.vc-meta{font-size:9px;color:var(--mut);font-family:'JetBrains Mono',monospace}
.vc-actions{display:flex;gap:5px;padding:0 8px 8px}
.right{border-left:1px solid var(--bdr);display:flex;flex-direction:column;height:calc(100vh - 56px);position:sticky;top:56px;overflow:hidden}
.right-tabs{display:flex;border-bottom:1px solid var(--bdr);flex-shrink:0}
.rtab{flex:1;padding:12px 0;text-align:center;font-size:11px;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:.5px;color:var(--mut);cursor:pointer;border-bottom:2px solid transparent;transition:all .2s}
.rtab.active{color:var(--acc);border-bottom-color:var(--acc)}
.rtab-content{flex:1;overflow-y:auto;padding:14px}
.rtab-content::-webkit-scrollbar{width:3px}.rtab-content::-webkit-scrollbar-thumb{background:var(--s4);border-radius:2px}
.rtab-pane{display:none}.rtab-pane.active{display:block}
.q-item{display:flex;gap:8px;align-items:center;background:var(--s2);border-radius:9px;padding:8px 10px;margin-bottom:6px;border:1px solid transparent;transition:all .15s;cursor:pointer}
.q-item:hover{border-color:var(--bdr)}
.q-item.now-playing{background:rgba(124,110,247,.1);border-color:rgba(124,110,247,.3)}
.q-thumb{width:44px;height:32px;border-radius:6px;object-fit:cover;background:var(--s4);flex-shrink:0}
.q-info{flex:1;min-width:0}
.q-title{font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.q-meta{font-size:9px;color:var(--mut);font-family:'JetBrains Mono',monospace;margin-top:1px}
.q-remove{background:none;border:none;color:var(--mut);cursor:pointer;font-size:14px;flex-shrink:0;padding:2px 4px;border-radius:4px}
.q-remove:hover{color:var(--acc2)}
.q-empty{text-align:center;padding:40px 16px;color:var(--mut);font-size:10px;font-family:'JetBrains Mono',monospace;line-height:2}
.q-empty .big{font-size:36px;opacity:.12;display:block;margin-bottom:8px}
.h-item{display:flex;gap:8px;align-items:center;border-radius:9px;padding:7px 9px;margin-bottom:5px;cursor:pointer;border:1px solid transparent;transition:all .15s}
.h-item:hover{background:var(--s2);border-color:var(--bdr)}
.h-thumb{width:40px;height:28px;border-radius:5px;object-fit:cover;background:var(--s4);flex-shrink:0}
.h-info{flex:1;min-width:0}
.h-title{font-size:11px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-meta{font-size:9px;color:var(--mut);font-family:'JetBrains Mono',monospace}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">> YTPlayer<span>YOUTUBE INSIDE YOUR APP</span></div>
  <div class="search-bar">
    <input class="si" id="q" placeholder="Search any song, artist, album, video..." onkeydown="if(event.key==='Enter')doSearch()">
    <button class="btn" onclick="doSearch()">Search Search</button>
  </div>
</div>

<div class="main">
  <div class="left">

    <div>
      <div class="sec-label" style="margin-bottom:10px">Browse</div>
      <div class="cats-row" id="cats"></div>
    </div>

    <div class="status-bar" id="status"></div>

    <div>
      <div class="sec-label" style="margin-bottom:10px">Player</div>
      <div class="video-container" id="video-container">
        <div class="video-ph" id="video-ph">
          <div class="big-icon">></div>
          <div class="ph-text">YOUTUBE PLAYER</div>
          <div class="ph-hint">SEARCH ABOVE OR PICK A CATEGORY TO START</div>
        </div>
      </div>
    </div>

    <div class="np-bar" id="np-bar" style="display:none">
      <img class="np-thumb" id="np-thumb" src="" alt="">
      <div class="np-info">
        <div class="np-title" id="np-title">-</div>
        <div class="np-channel" id="np-channel">-</div>
      </div>
      <div class="np-badge">> PLAYING</div>
    </div>

    <div class="viz" id="viz"></div>

    <div>
      <div class="sec-label" style="margin-bottom:10px">Controls</div>
      <div class="controls" style="margin-bottom:10px">
        <button class="btn btn-sm btn-o" onclick="seek(-10)">&#171; 10s</button>
        <button class="btn btn-sm btn-o" onclick="seek(10)">10s &#187;</button>
        <button class="btn btn-sm btn-o" id="mute-btn" onclick="toggleMute()">(vol)</button>
        <button class="btn btn-sm btn-o" onclick="playPrev()">|< Prev</button>
        <button class="btn btn-sm btn-o" onclick="playNext()">Next >|</button>
        <button class="btn btn-sm btn-o" id="shuffle-btn" onclick="toggleShuffle()">(shuf) Shuffle OFF</button>
        <button class="btn btn-sm btn-o" id="repeat-btn" onclick="toggleRepeat()">(rep) Repeat OFF</button>
      </div>
      <div class="sliders-row">
        <div class="slider-group">
          <div class="slider-label">Volume <span class="slider-val" id="vol-val">80%</span></div>
          <input type="range" id="vol" min="0" max="100" value="80" oninput="setVol(this.value)">
        </div>
        <div class="slider-group">
          <div class="slider-label">Speed <span class="slider-val" id="spd-val">1.0x</span></div>
          <input type="range" id="spd" min="25" max="200" value="100" step="5" oninput="setSpd(this.value)">
        </div>
      </div>
    </div>

    <div id="results-section" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div class="sec-label" id="results-label">Results</div>
        <button class="btn btn-xs btn-o" onclick="clearResults()">x Clear</button>
      </div>
      <div class="results-grid" id="results-grid"></div>
      <div id="load-more-wrap" style="display:none;text-align:center;padding:8px 0">
        <button class="btn btn-o" onclick="loadMore()">Load More Results</button>
      </div>
    </div>

  </div>

  <div class="right">
    <div class="right-tabs">
      <div class="rtab active" onclick="switchTab('queue',this)">Queue</div>
      <div class="rtab" onclick="switchTab('history',this)">History</div>
    </div>
    <div class="rtab-content">
      <div class="rtab-pane active" id="tab-queue">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div class="sec-label">Up Next</div>
          <button class="btn btn-xs btn-o" onclick="clearQueue()" id="clear-q-btn" style="display:none">Clear All</button>
        </div>
        <div class="q-empty" id="q-empty"><span class="big">(note)</span>QUEUE IS EMPTY<br><span style="opacity:.4">Hit +Q on any result</span></div>
        <div id="q-list"></div>
      </div>
      <div class="rtab-pane" id="tab-history">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div class="sec-label">History</div>
          <button class="btn btn-xs btn-o" onclick="clearHistory()">Clear</button>
        </div>
        <div class="q-empty" id="h-empty"><span class="big">(time)</span>NO HISTORY YET</div>
        <div id="h-list"></div>
      </div>
    </div>
  </div>
</div>

<script>
var ytPlayer=null,ytReady=false,queue=[],history=[],results=[],cur=null,page=1,lastQuery='',_mute=false,shuffleOn=false,repeatOn=false;

var INVIDIOUS=['https://inv.nadeko.net','https://invidious.io.lol','https://yt.artemislena.eu','https://invidious.privacydev.net','https://iv.melmac.space','https://invidious.nerdvpn.de'];

var CATS=[['Trending 2025','trending music 2025'],['Lo-Fi Beats','lofi hip hop chill beats'],['Rock Classics','best rock songs all time'],['Pop Hits','top pop hits 2025'],['Hip-Hop','best hip hop rap 2025'],['Classical','relaxing classical music'],['Meditation','meditation calm sleep music'],['EDM','best electronic dance music EDM'],['Bollywood','latest bollywood songs 2025'],['Night Drive','night drive synthwave retrowave'],['Study Music','study music focus concentration'],['Jazz','smooth jazz music relaxing'],['K-Pop','kpop hits 2025'],['Devotional','devotional songs bhajans']];

(function(){var v=document.getElementById('viz');for(var i=0;i<48;i++){var b=document.createElement('div');b.className='viz-bar';b.style.animationDuration=(0.35+Math.random()*0.65)+'s';b.style.animationDelay=(Math.random()*0.5)+'s';v.appendChild(b)}})();

(function(){var row=document.getElementById('cats');CATS.forEach(function(c){var p=document.createElement('button');p.className='cat-pill';p.textContent=c[0];p.onclick=function(){document.querySelectorAll('.cat-pill').forEach(function(x){x.classList.remove('active')});p.classList.add('active');document.getElementById('q').value=c[1];doSearch(1)};row.appendChild(p)})})();

(function(){var s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';document.head.appendChild(s)})();
window.onYouTubeIframeAPIReady=function(){ytReady=true};

function playVideo(v){
  cur=v;
  history=history.filter(function(h){return h.id!==v.id});
  history.unshift(v);
  if(history.length>50)history.pop();
  document.getElementById('np-bar').style.display='flex';
  document.getElementById('np-thumb').src=v.thumb;
  document.getElementById('np-title').textContent=v.title;
  document.getElementById('np-channel').textContent=v.channel+(v.duration?'  &middot;  '+v.duration:'');
  var container=document.getElementById('video-container');
  container.innerHTML='';
  var iframe=document.createElement('iframe');
  iframe.id='yt-iframe';
  iframe.src='https://www.youtube.com/embed/'+v.id+'?autoplay=1&rel=0&modestbranding=1&playsinline=1&fs=1&iv_load_policy=3';
  iframe.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen';
  iframe.allowFullscreen=true;
  iframe.style.cssText='display:block;width:100%;height:480px;border:none';
  container.appendChild(iframe);
  renderQueue();renderHistory();
  setStatus('Now playing: '+v.title.substring(0,55),'ok');
}

function seek(sec){var f=document.getElementById('yt-iframe');if(!f)return;f.contentWindow.postMessage(JSON.stringify({event:'command',func:sec>0?'fastForward':'rewind',args:[Math.abs(sec)]},'*'))}
function toggleMute(){_mute=!_mute;document.getElementById('mute-btn').textContent=_mute?'(muted)':'(sound)'}
function setVol(v){document.getElementById('vol-val').textContent=v+'%'}
function setSpd(v){document.getElementById('spd-val').textContent=(parseInt(v)/100).toFixed(2)+'x'}
function toggleShuffle(){shuffleOn=!shuffleOn;var b=document.getElementById('shuffle-btn');b.textContent='Shuffle '+(shuffleOn?'ON':'OFF');b.style.color=shuffleOn?'var(--acc)':''}
function toggleRepeat(){repeatOn=!repeatOn;var b=document.getElementById('repeat-btn');b.textContent='Repeat '+(repeatOn?'ON':'OFF');b.style.color=repeatOn?'var(--acc)':''}

function playNext(){if(!queue.length)return;var i=cur?queue.findIndex(function(x){return x.id===cur.id}):-1;if(shuffleOn){i=Math.floor(Math.random()*queue.length)}else{i=repeatOn?i:i+1;if(i>=queue.length)i=0}playVideo(queue[i])}
function playPrev(){if(!queue.length)return;var i=cur?queue.findIndex(function(x){return x.id===cur.id}):1;i=(i-1+queue.length)%queue.length;playVideo(queue[i])}

async function doSearch(p){
  var q=document.getElementById('q').value.trim();if(!q)return;
  if(!p||p===1){lastQuery=q;page=1;results=[]}
  setStatus('Searching for "'+q+'"...','loading');
  var data=await invSearch(q,p||1);
  if(!data||!data.length){setStatus('No results found. Try a different search.','err');return}
  results=results.concat(data);page=p||1;
  renderResults();
  setStatus(results.length+' results for "'+q+'"','ok');
}
function loadMore(){doSearch(page+1)}
function clearResults(){results=[];document.getElementById('results-section').style.display='none';document.querySelectorAll('.cat-pill').forEach(function(p){p.classList.remove('active')})}

async function invSearch(q,p){
  for(var i=0;i<INVIDIOUS.length;i++){
    try{
      var r=await fetch(INVIDIOUS[i]+'/api/v1/search?q='+encodeURIComponent(q)+'&type=video&sort_by=relevance&page='+p+'&region=US',{signal:AbortSignal.timeout(8000)});
      if(!r.ok)continue;
      var d=await r.json();
      if(!Array.isArray(d))continue;
      return d.filter(function(v){return v.type==='video'&&v.videoId}).map(function(v){return{id:v.videoId,title:v.title||'Untitled',channel:v.author||'',views:v.viewCount||0,duration:v.lengthSeconds?Math.floor(v.lengthSeconds/60)+':'+String(v.lengthSeconds%60).padStart(2,'0'):'',thumb:'https://i.ytimg.com/vi/'+v.videoId+'/mqdefault.jpg'}});
    }catch(e){continue}
  }
  return[];
}

function fmtV(n){if(n>=1e9)return(n/1e9).toFixed(1)+'B';if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return n?String(n):''}

function renderResults(){
  document.getElementById('results-section').style.display='block';
  document.getElementById('results-label').textContent=results.length+' results for "'+lastQuery+'"';
  var g=document.getElementById('results-grid');g.innerHTML='';
  results.forEach(function(v,i){
    var card=document.createElement('div');card.className='video-card';
    var views=v.views?' &middot; '+fmtV(v.views)+' views':'';
    card.innerHTML='<div class="vc-thumb-wrap"><img class="vc-thumb" src="'+v.thumb+'" alt="" loading="lazy" onerror="this.style.background=\'#22222e\'">'+(v.duration?'<div class="vc-dur">'+v.duration+'</div>':'')+'</div><div class="vc-body"><div class="vc-title" title="'+v.title+'">'+v.title+'</div><div class="vc-meta">'+v.channel+views+'</div></div><div class="vc-actions"><button class="btn btn-xs" style="flex:1" onclick="playAndQueue(results['+i+'])">> Play</button><button class="btn btn-xs btn-o" onclick="addToQueue(results['+i+'],this)">+Q</button></div>';
    g.appendChild(card);
  });
  document.getElementById('load-more-wrap').style.display='block';
}

function playAndQueue(v){addToQueue(v,null,true);playVideo(v)}
function addToQueue(v,btn,silent){if(queue.find(function(x){return x.id===v.id}))return;queue.push(v);if(btn){btn.textContent='Ok';btn.disabled=true;btn.style.color='var(--grn)'}if(!silent)setStatus('Added to queue: '+v.title.substring(0,40),'ok');renderQueue()}
function removeFromQueue(i){queue.splice(i,1);renderQueue()}
function clearQueue(){queue=[];renderQueue()}

function renderQueue(){
  var list=document.getElementById('q-list');
  document.getElementById('q-empty').style.display=queue.length?'none':'block';
  document.getElementById('clear-q-btn').style.display=queue.length?'block':'none';
  list.innerHTML='';
  queue.forEach(function(v,i){
    var isNow=cur&&cur.id===v.id;
    var item=document.createElement('div');item.className='q-item'+(isNow?' now-playing':'');
    item.innerHTML='<img class="q-thumb" src="'+v.thumb+'" alt=""><div class="q-info"><div class="q-title">'+(isNow?'> ':'')+v.title+'</div><div class="q-meta">'+v.channel+(v.duration?' &middot; '+v.duration:'')+'</div></div><button class="q-remove" onclick="removeFromQueue('+i+')">x</button>';
    item.querySelector('.q-thumb').onclick=item.querySelector('.q-info').onclick=function(){playVideo(v)};
    list.appendChild(item);
  });
}

function clearHistory(){history=[];renderHistory()}
function renderHistory(){
  var list=document.getElementById('h-list');
  document.getElementById('h-empty').style.display=history.length?'none':'block';
  list.innerHTML='';
  history.forEach(function(v){
    var item=document.createElement('div');item.className='h-item';
    item.innerHTML='<img class="h-thumb" src="'+v.thumb+'" alt=""><div class="h-info"><div class="h-title">'+v.title+'</div><div class="h-meta">'+v.channel+(v.duration?' &middot; '+v.duration:'')+'</div></div>';
    item.onclick=function(){playVideo(v)};
    list.appendChild(item);
  });
}

function switchTab(name,el){
  document.querySelectorAll('.rtab').forEach(function(t){t.classList.remove('active')});
  document.querySelectorAll('.rtab-pane').forEach(function(p){p.classList.remove('active')});
  el.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
}

var statusTimer=null;
function setStatus(msg,type){
  var el=document.getElementById('status');el.textContent=msg;el.className='status-bar visible'+(type?' '+type:'');
  if(statusTimer)clearTimeout(statusTimer);
  if(type!=='loading')statusTimer=setTimeout(function(){el.classList.remove('visible')},6000);
}
</script>
</body>
</html>"""


def render_youtube_player():
    """Render the full-size expanded YouTube Player inside Streamlit."""
    st.markdown("""
<style>
section[data-testid="stMain"] .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
section[data-testid="stMain"] > div {padding: 0 !important}
footer {display: none !important}
header {display: none !important}
</style>
""", unsafe_allow_html=True)
    components.html(PLAYER_HTML, height=1080, scrolling=False)
