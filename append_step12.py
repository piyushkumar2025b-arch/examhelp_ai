import codecs

snippet = """
SHORTCUT_OVERLAY_CODE = r'''
<style>
.kbd-overlay {
  display:none; position:fixed; inset:0; z-index:9999;
  background:rgba(0,0,0,0.75); backdrop-filter:blur(8px);
  align-items:center; justify-content:center;
}
.kbd-overlay.visible { display:flex; animation:overlayIn 0.25s ease both; }
@keyframes overlayIn{from{opacity:0;}to{opacity:1;}}
.kbd-card {
  background:rgba(15,23,42,0.97); border:1px solid rgba(99,102,241,0.3);
  border-radius:20px; padding:32px 40px; max-width:520px; width:90%;
  box-shadow:0 40px 120px rgba(0,0,0,0.6);
}
.kbd-title { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#fff; letter-spacing:2px; margin-bottom:20px; }
.kbd-row { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); }
.kbd-row:last-child { border-bottom:none; }
.kbd-action { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.6); }
.kbd-keys { display:flex; gap:5px; }
.kbd-key {
  padding:4px 10px; border-radius:6px;
  background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15);
  font-family:'Space Mono',monospace; font-size:11px; color:rgba(255,255,255,0.7);
}
.kbd-close-btn { margin-top:20px; width:100%; text-align:center; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; color:rgba(255,255,255,0.3); cursor:pointer; }
</style>
<div class="kbd-overlay" id="kbdOverlay">
  <div class="kbd-card">
    <div class="kbd-title">⌨️ KEYBOARD SHORTCUTS</div>
    <div class="kbd-row"><span class="kbd-action">Show shortcuts</span><div class="kbd-keys"><span class="kbd-key">?</span></div></div>
    <div class="kbd-row"><span class="kbd-action">New chat</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">K</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Focus mode toggle</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">.</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Submit message</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">Enter</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Close overlays</span><div class="kbd-keys"><span class="kbd-key">Esc</span></div></div>
    <div class="kbd-close-btn" onclick="document.getElementById('kbdOverlay').classList.remove('visible')">PRESS ESC TO CLOSE</div>
  </div>
</div>
<script>
document.addEventListener('keydown', function(e){
  if(e.key==='?' && document.activeElement.tagName!=='INPUT' && document.activeElement.tagName!=='TEXTAREA'){
    document.getElementById('kbdOverlay').classList.toggle('visible');
  }
  if(e.key==='Escape'){
    document.getElementById('kbdOverlay').classList.remove('visible');
  }
});
document.getElementById('kbdOverlay').addEventListener('click',function(e){
  if(e.target===this) this.classList.remove('visible');
});
</script>
'''
st.markdown(SHORTCUT_OVERLAY_CODE, unsafe_allow_html=True)
"""
with codecs.open('app.py', 'a', 'utf-8') as f:
    f.write("\n" + snippet)
