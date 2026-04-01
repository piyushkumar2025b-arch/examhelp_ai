import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# CSS injection
css_block = """
    /* ══════════════════════════════════════════
       ✦ ADDED PREMIUM UI SECTIONS ✦
    ══════════════════════════════════════════ */

    /* ── LIVE COUNTER TICKER ── */
    .live-ticker {
        width:100%; max-width:1100px;
        display:flex; gap:0; margin-bottom:72px;
        border:1px solid rgba(0,255,180,0.12); border-radius:20px;
        overflow:hidden; background:rgba(0,0,0,0.3); backdrop-filter:blur(12px);
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .05s both;
        position:relative;
    }
    .live-ticker::before {
        content:'LIVE'; position:absolute; top:12px; left:16px;
        font-family:'Space Mono',monospace; font-size:9px; letter-spacing:4px;
        color:#00ffb4; background:rgba(0,255,180,0.1); border:1px solid rgba(0,255,180,0.3);
        border-radius:100px; padding:3px 10px;
        animation:blink 2s ease-in-out infinite;
    }
    .ticker-item {
        flex:1; padding:28px 20px 22px; text-align:center;
        border-right:1px solid rgba(255,255,255,0.05);
        position:relative; overflow:hidden;
    }
    .ticker-item:last-child { border-right:none; }
    .ticker-item::after {
        content:''; position:absolute; bottom:0; left:20%; right:20%; height:1px;
        background:linear-gradient(90deg,transparent,var(--tc,rgba(0,255,180,0.3)),transparent);
    }
    .ticker-num {
        font-family:'Orbitron',monospace; font-size:clamp(22px,3vw,38px);
        font-weight:900; line-height:1; margin-bottom:8px;
        background:var(--tg,linear-gradient(135deg,#00ffb4,#00aaff));
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 12px var(--tglow,rgba(0,255,180,0.4)));
    }
    .ticker-lbl { font-family:'Rajdhani',sans-serif; font-size:11px; letter-spacing:3px; color:rgba(255,255,255,0.35); text-transform:uppercase; }
    .ticker-sub { font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.18); letter-spacing:2px; margin-top:4px; }
    .t1{--tg:linear-gradient(135deg,#00ffb4,#00aaff);--tc:rgba(0,255,180,0.3);--tglow:rgba(0,255,180,0.4);}
    .t2{--tg:linear-gradient(135deg,#b44dff,#ff44aa);--tc:rgba(180,77,255,0.3);--tglow:rgba(180,77,255,0.4);}
    .t3{--tg:linear-gradient(135deg,#ffaa00,#ff4400);--tc:rgba(255,170,0,0.3);--tglow:rgba(255,170,0,0.4);}
    .t4{--tg:linear-gradient(135deg,#00aaff,#0044ff);--tc:rgba(0,170,255,0.3);--tglow:rgba(0,170,255,0.4);}
    .t5{--tg:linear-gradient(135deg,#ff44aa,#ff0044);--tc:rgba(255,68,170,0.3);--tglow:rgba(255,68,170,0.4);}

    /* ── HOW IT WORKS TIMELINE ── */
    .hiw-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both; }
    .hiw-steps { display:flex; gap:0; position:relative; }
    .hiw-steps::before {
        content:''; position:absolute; top:36px; left:10%; right:10%; height:1px;
        background:linear-gradient(90deg,rgba(0,255,180,0.1),rgba(0,255,180,0.3),rgba(180,77,255,0.3),rgba(0,255,180,0.1));
    }
    .hiw-step {
        flex:1; display:flex; flex-direction:column; align-items:center; text-align:center;
        padding:0 12px;
        animation: cardIn .8s cubic-bezier(.16,1,.3,1) both;
    }
    .hiw-step:nth-child(1){animation-delay:.1s;}
    .hiw-step:nth-child(2){animation-delay:.2s;}
    .hiw-step:nth-child(3){animation-delay:.3s;}
    .hiw-step:nth-child(4){animation-delay:.4s;}
    .hiw-num {
        width:72px; height:72px; border-radius:50%;
        background:rgba(0,255,180,0.06); border:1px solid rgba(0,255,180,0.2);
        display:flex; align-items:center; justify-content:center;
        font-family:'Orbitron',monospace; font-size:20px; font-weight:900;
        color:#00ffb4; margin-bottom:16px; position:relative; z-index:1;
        box-shadow:0 0 30px rgba(0,255,180,0.1);
        transition:all .4s ease;
    }
    .hiw-num:hover { background:rgba(0,255,180,0.15); box-shadow:0 0 50px rgba(0,255,180,0.25); transform:scale(1.1); }
    .hiw-icon { font-size:22px; margin-bottom:2px; }
    .hiw-title { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; color:#fff; letter-spacing:1px; margin-bottom:8px; }
    .hiw-desc { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.6; }

    /* ── CAPABILITY BARS ── */
    .cap-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .15s both; }
    .cap-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
    @media(max-width:600px){.cap-grid{grid-template-columns:1fr;}}
    .cap-item { padding:20px 24px; background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07); border-radius:16px; }
    .cap-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .cap-name { font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:700; color:#fff; letter-spacing:.5px; }
    .cap-pct { font-family:'Space Mono',monospace; font-size:11px; color:var(--cc,#00ffb4); }
    .cap-bar { height:4px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
    .cap-fill { height:100%; border-radius:100px; background:var(--cg,linear-gradient(90deg,#00ffb4,#00aaff)); width:0%; transition:width 2s cubic-bezier(.16,1,.3,1); }

    /* ── COMPARISON TABLE ── */
    .compare-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .compare-table { width:100%; border-collapse:separate; border-spacing:0; }
    .compare-table th { padding:16px 20px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; text-align:center; }
    .compare-table th:first-child { text-align:left; }
    .compare-table td { padding:14px 20px; font-family:'Rajdhani',sans-serif; font-size:14px; text-align:center; border-top:1px solid rgba(255,255,255,0.05); }
    .compare-table td:first-child { text-align:left; color:rgba(255,255,255,0.65); }
    .compare-col-us { color:#00ffb4; font-weight:700; }
    .compare-col-them { color:rgba(255,255,255,0.25); }
    .compare-yes { color:#00ffb4; font-size:18px; }
    .compare-no { color:rgba(255,255,255,0.2); font-size:18px; }
    .compare-header-us { color:#00ffb4; background:rgba(0,255,180,0.05); border-radius:12px 12px 0 0; }
    .compare-header-them { color:rgba(255,255,255,0.3); }
    .compare-wrap {
        background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; overflow:hidden; backdrop-filter:blur(10px);
    }

    /* ── FAQ ACCORDION ── */
    .faq-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .faq-item {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:16px; margin-bottom:10px; overflow:hidden;
        transition:all .3s ease;
    }
    .faq-item:hover { border-color:rgba(0,255,180,0.2); }
    .faq-q {
        padding:18px 22px; cursor:pointer; display:flex; justify-content:space-between; align-items:center;
        font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:700; color:#fff; letter-spacing:.3px;
        user-select:none;
    }
    .faq-arrow { font-size:10px; color:#00ffb4; transition:transform .3s ease; }
    .faq-a {
        max-height:0; overflow:hidden; transition:max-height .4s ease, padding .3s ease;
        font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.5); line-height:1.7;
        padding:0 22px;
    }
    .faq-item.open .faq-a { max-height:200px; padding:0 22px 18px; }
    .faq-item.open .faq-arrow { transform:rotate(180deg); color:#b44dff; }
    .faq-item.open { border-color:rgba(0,255,180,0.25); background:rgba(0,255,180,0.03); }

    /* ── TECH STACK CAROUSEL ── */
    .tech-marquee-wrap {
        width:100%; overflow:hidden; margin-bottom:72px;
        mask-image:linear-gradient(90deg,transparent 0%,black 10%,black 90%,transparent 100%);
        -webkit-mask-image:linear-gradient(90deg,transparent 0%,black 10%,black 90%,transparent 100%);
    }
    .tech-marquee { display:flex; gap:16px; animation:marquee 30s linear infinite; width:max-content; }
    .tech-marquee:hover { animation-play-state:paused; }
    @keyframes marquee { 0%{transform:translateX(0);} 100%{transform:translateX(-50%);} }
    .tech-chip {
        display:flex; align-items:center; gap:10px; padding:12px 20px;
        background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
        border-radius:100px; white-space:nowrap; flex-shrink:0;
        font-family:'Space Mono',monospace; font-size:11px; color:rgba(255,255,255,0.5);
        letter-spacing:1px; transition:all .3s ease;
    }
    .tech-chip:hover { background:rgba(255,255,255,0.07); border-color:rgba(0,255,180,0.3); color:#fff; }
    .tech-chip-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

    /* ── SUBJECT WHEEL ── */
    .subject-wheel {
        width:100%; max-width:1100px; margin-bottom:72px;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .subjects-hex {
        display:flex; flex-wrap:wrap; gap:12px; justify-content:center;
    }
    .subj-hex {
        width:130px; padding:22px 16px; text-align:center;
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
        cursor:default;
    }
    .subj-hex::before {
        content:''; position:absolute; inset:0;
        background:var(--sg,radial-gradient(ellipse at center,rgba(0,255,180,0.08),transparent));
        opacity:0; transition:opacity .3s ease;
    }
    .subj-hex:hover { transform:translateY(-8px) scale(1.05); border-color:var(--sb,rgba(0,255,180,0.4)); }
    .subj-hex:hover::before { opacity:1; }
    .subj-icon { font-size:28px; display:block; margin-bottom:8px; }
    .subj-name { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:rgba(255,255,255,0.45); text-transform:uppercase; }

    /* ── TRUST BADGES ── */
    .trust-section {
        width:100%; max-width:1100px; margin-bottom:56px;
        display:flex; flex-wrap:wrap; gap:16px; justify-content:center;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .trust-badge {
        display:flex; align-items:center; gap:10px; padding:14px 22px;
        background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;
        font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:600; color:rgba(255,255,255,0.6);
        transition:all .3s ease;
    }
    .trust-badge:hover { border-color:rgba(0,255,180,0.25); background:rgba(0,255,180,0.04); color:#fff; transform:translateY(-3px); }
    .trust-badge-icon { font-size:20px; }

    /* ── GLOW DIVIDER ── */
    .glow-divider {
        width:100%; max-width:1100px; margin:8px 0 64px;
        height:1px; position:relative;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,0.3),rgba(180,77,255,0.3),transparent);
    }
    .glow-divider::after {
        content:''; position:absolute; top:-4px; left:50%; transform:translateX(-50%);
        width:8px; height:8px; border-radius:50%;
        background:#00ffb4; box-shadow:0 0 20px rgba(0,255,180,0.8);
        animation:blink 2s ease-in-out infinite;
    }

    /* ── MINI FEATURE HIGHLIGHTS (icon + line) ── */
    .hl-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .15s both; }
    .hl-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
    @media(max-width:700px){.hl-grid{grid-template-columns:1fr;}}
    .hl-card {
        padding:28px 24px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
    }
    .hl-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:var(--hg,linear-gradient(90deg,#00ffb4,#00aaff));
        transform:scaleX(0); transform-origin:left; transition:transform .4s ease;
    }
    .hl-card:hover { transform:translateY(-6px); border-color:rgba(255,255,255,0.15); }
    .hl-card:hover::before { transform:scaleX(1); }
    .hl-icon { font-size:32px; margin-bottom:14px; display:block; }
    .hl-title { font-family:'Orbitron',monospace; font-size:13px; font-weight:700; color:#fff; letter-spacing:1px; margin-bottom:10px; }
    .hl-desc { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.7; }
    .hl-arrow { display:inline-flex; align-items:center; gap:6px; margin-top:14px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; color:var(--hc,#00ffb4); opacity:0; transition:opacity .3s ease; }
    .hl-card:hover .hl-arrow { opacity:1; }

    /* ── FLOATING NOTIFICATION POPUP ── */
    .notif-popup {
        position:fixed; bottom:32px; left:32px; z-index:999;
        background:rgba(0,20,12,0.9); border:1px solid rgba(0,255,180,0.25);
        border-radius:16px; padding:16px 20px; max-width:280px;
        backdrop-filter:blur(20px); box-shadow:0 20px 60px rgba(0,0,0,0.5),0 0 40px rgba(0,255,180,0.08);
        animation:notifSlide 0.6s cubic-bezier(.16,1,.3,1) 2s both;
        display:flex; align-items:flex-start; gap:12px;
    }
    @keyframes notifSlide{from{transform:translateX(-120%);opacity:0;}to{transform:translateX(0);opacity:1;}}
    .notif-icon { font-size:22px; flex-shrink:0; }
    .notif-body {}
    .notif-title { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; color:#00ffb4; letter-spacing:1px; margin-bottom:4px; }
    .notif-text { font-family:'Rajdhani',sans-serif; font-size:12px; color:rgba(255,255,255,0.5); line-height:1.5; }
    .notif-close { position:absolute; top:10px; right:12px; cursor:pointer; font-size:12px; color:rgba(255,255,255,0.3); transition:color .2s; }
    .notif-close:hover { color:#00ffb4; }
    .notif-dot { width:6px; height:6px; border-radius:50%; background:#00ffb4; flex-shrink:0; margin-top:7px; animation:blink 1.5s ease-in-out infinite; }

    /* ── SCROLL PROGRESS BAR ── */
    .scroll-prog {
        position:fixed; top:0; left:0; height:2px; z-index:9999;
        background:linear-gradient(90deg,#00ffb4,#00aaff,#b44dff,#ff44aa);
        width:0%; transition:width .1s linear;
        box-shadow:0 0 12px rgba(0,255,180,0.6);
    }

    /* ── ANIMATED TYPEWRITER SUBTITLE ── */
    .typewriter-wrap {
        text-align:center; margin-bottom:32px;
        font-family:'Space Mono',monospace; font-size:13px; letter-spacing:3px;
        color:rgba(255,255,255,0.3);
    }
    .typewriter { border-right:2px solid #00ffb4; padding-right:4px; animation:cursorBlink 1s step-end infinite; }
    @keyframes cursorBlink{0%,100%{border-color:#00ffb4;}50%{border-color:transparent;}}

    /* ── VIDEO DEMO PLACEHOLDER ── */
    .demo-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .demo-card {
        border-radius:24px; overflow:hidden; border:1px solid rgba(0,255,180,0.15);
        position:relative; background:rgba(0,0,0,0.4);
        box-shadow:0 0 80px rgba(0,255,180,0.08);
    }
    .demo-canvas-wrap { width:100%; height:200px; position:relative; overflow:hidden; }
    .demo-canvas-wrap canvas { width:100%; height:200px; display:block; }
    .demo-overlay {
        position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; z-index:10;
    }
    .demo-play-btn {
        width:64px; height:64px; border-radius:50%;
        background:linear-gradient(135deg,rgba(0,255,180,0.9),rgba(0,170,255,0.9));
        display:flex; align-items:center; justify-content:center;
        font-size:22px; cursor:pointer; margin-bottom:14px;
        box-shadow:0 0 40px rgba(0,255,180,0.4);
        animation:playPulse 2s ease-in-out infinite;
        transition:transform .3s ease;
    }
    .demo-play-btn:hover { transform:scale(1.15); }
    @keyframes playPulse{0%,100%{box-shadow:0 0 40px rgba(0,255,180,0.4);}50%{box-shadow:0 0 70px rgba(0,255,180,0.7);}}
    .demo-label { font-family:'Orbitron',monospace; font-size:12px; letter-spacing:3px; color:rgba(255,255,255,0.5); }
    .demo-tabs { display:flex; border-top:1px solid rgba(255,255,255,0.07); }
    .demo-tab {
        flex:1; padding:16px; text-align:center; cursor:pointer;
        font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
        color:rgba(255,255,255,0.3); border-right:1px solid rgba(255,255,255,0.05);
        transition:all .3s ease; position:relative; overflow:hidden;
    }
    .demo-tab:last-child { border-right:none; }
    .demo-tab:hover { color:#00ffb4; background:rgba(0,255,180,0.04); }
    .demo-tab.active { color:#00ffb4; }
    .demo-tab.active::after { content:''; position:absolute; bottom:0; left:20%; right:20%; height:2px; background:linear-gradient(90deg,transparent,#00ffb4,transparent); }
"""

html_block = """
      <!-- ✦ NEW: SCROLL PROGRESS BAR ✦ -->
      <div class="scroll-prog" id="scrollProg"></div>

      <!-- ✦ NEW: LIVE TICKER ✦ -->
      <div class="live-ticker">
        <div class="ticker-item t1"><div class="ticker-num">9+</div><div class="ticker-lbl">Specialist Engines</div><div class="ticker-sub">Active & Loaded</div></div>
        <div class="ticker-item t2"><div class="ticker-num">9-Key</div><div class="ticker-lbl">Gemini Rotation</div><div class="ticker-sub">Zero limits</div></div>
        <div class="ticker-item t3"><div class="ticker-num">30+</div><div class="ticker-lbl">AI Personas</div><div class="ticker-sub">Einstein to Feynman</div></div>
        <div class="ticker-item t4"><div class="ticker-num">10M+</div><div class="ticker-lbl">Tokens Processed</div><div class="ticker-sub">High-bandwidth</div></div>
        <div class="ticker-item t5"><div class="ticker-num">&lt;1s</div><div class="ticker-lbl">Response Time</div><div class="ticker-sub">Ultra-fast Groq</div></div>
      </div>

      <!-- ✦ NEW: COMPARISON TABLE ✦ -->
      <div class="section-label">◈ WHY WE STAND OUT ◈</div>
      <div class="section-title">The ExamHelp Advantage</div>
      <div class="compare-section">
        <div class="compare-wrap">
          <table class="compare-table">
            <thead>
              <tr>
                <th>FEATURE</th>
                <th class="compare-header-us">EXAMHELP AI</th>
                <th class="compare-header-them">STANDARD AI</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Usage Limits</td>
                <td class="compare-col-us">Unlimited / 9-Key Pool</td>
                <td class="compare-col-them">Strict Quotas</td>
              </tr>
              <tr>
                <td>Voice & Visual Chat</td>
                <td class="compare-col-us"><span class="compare-yes">✓</span> Whisper + OCR</td>
                <td class="compare-col-them"><span class="compare-no">✗</span> Text only</td>
              </tr>
              <tr>
                <td>UI & Aesthetics</td>
                <td class="compare-col-us">Premium Glassmorphism</td>
                <td class="compare-col-them">Basic layouts</td>
              </tr>
              <tr>
                <td>Specialized Tools</td>
                <td class="compare-col-us">15+ Distinct Apps</td>
                <td class="compare-col-them">General bot</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ✦ NEW: FAQ ACCORDION ✦ -->
      <div class="section-label">◈ GOT QUESTIONS? ◈</div>
      <div class="section-title">Common Queries</div>
      <div class="faq-section" id="faqAccordion">
        <div class="faq-item">
          <div class="faq-q">Is the 9-Key auto-rotation truly seamless? <span class="faq-arrow">▼</span></div>
          <div class="faq-a">Yes. Under the hood, we check quota blocks. If one key runs out, the engine automatically injects the next healthy key mid-generation without dropping your context.</div>
        </div>
        <div class="faq-item">
          <div class="faq-q">Can the Circuit Solver do visual nodes? <span class="faq-arrow">▼</span></div>
          <div class="faq-a">Absolutely. Upload a diagram. It utilizes multi-modal OCR to trace lines and identify resistors, mapping them to KVL equations algebraically!</div>
        </div>
      </div>

      <!-- ✦ NEW: NOTIFICATION POPUP ✦ -->
      <div class="notif-popup" id="notifPopup">
        <div class="notif-icon">💡</div>
        <div class="notif-body">
          <div class="notif-title">System Update</div>
          <div class="notif-text">Project Architect engine is now fully integrated with Mermaid.js rendering!</div>
        </div>
        <div class="notif-close" onclick="document.getElementById('notifPopup').style.display='none'">✕</div>
      </div>

      <!-- ✦ NEW: ANIMATED TYPEWRITER ✦ -->
      <div class="typewriter-wrap">
        > <span id="typewriterText" class="typewriter"></span>
      </div>

      <!-- ✦ INTERACTIVE JS FOR ALL NEW SECTIONS ✦ -->
      <script>
      (function(){
        // 1. Scroll Progress
        window.addEventListener('scroll', function() {
          var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
          var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          var scrolled = (winScroll / height) * 100;
          var prog = document.getElementById("scrollProg");
          if(prog) prog.style.width = scrolled + "%";
        });

        // 2. FAQ Interactivity
        setTimeout(function(){
          var faqItems = document.querySelectorAll('.faq-item');
          faqItems.forEach(function(item) {
            var q = item.querySelector('.faq-q');
            if(q) {
              q.addEventListener('click', function() {
                item.classList.toggle('open');
              });
            }
          });
        }, 1000);

        // 3. Typewriter Effect
        var typeWords = ["Initializing Elite Engines...", "Loading 9-Key Vault...", "Connecting to Gemini 1.5 Pro...", "System Ready."];
        var typeIndex = 0;
        var charIndex = 0;
        var typeDelay = 100;
        var currentEl = null;

        function type() {
          currentEl = document.getElementById("typewriterText");
          if(!currentEl) return;
          if(charIndex < typeWords[typeIndex].length) {
            currentEl.innerHTML += typeWords[typeIndex].charAt(charIndex);
            charIndex++;
            setTimeout(type, typeDelay);
          } else {
            setTimeout(erase, 2000);
          }
        }
        function erase() {
          if(!currentEl) return;
          if(charIndex > 0) {
            currentEl.innerHTML = typeWords[typeIndex].substring(0, charIndex-1);
            charIndex--;
            setTimeout(erase, 50);
          } else {
            typeIndex = (typeIndex + 1) % typeWords.length;
            setTimeout(type, 500);
          }
        }
        setTimeout(type, 1500);
      })();
      </script>
"""

if "/* ── LIVE COUNTER TICKER ── */" not in content:
    content = content.replace("    </style>", css_block + "\n    </style>")
    print("Injected CSS")

if "scroll-prog" not in content:
    content = content.replace("      <!-- GATE -->", html_block + "\n      <!-- GATE -->")
    print("Injected HTML")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
