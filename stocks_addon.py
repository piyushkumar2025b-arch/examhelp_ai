"""
stocks_addon.py — Steps 7-8
Adds: Real-time price charts (Yahoo Finance), News sentiment, Portfolio tracker
"""
import streamlit as st, json, urllib.request, random, io

def _fetch_stock_data(symbol: str) -> dict:
    """Fetch stock data from Yahoo Finance (free, no key)."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&range=1mo"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        result = data["chart"]["result"][0]
        meta = result["meta"]
        timestamps = result.get("timestamp", [])
        closes = result["indicators"]["quote"][0].get("close", [])
        return {"symbol":symbol.upper(),"price":meta.get("regularMarketPrice",0),
                "prev":meta.get("previousClose",0),"name":meta.get("shortName",symbol),
                "currency":meta.get("currency","USD"),"timestamps":timestamps,"closes":closes,
                "high52":meta.get("fiftyTwoWeekHigh",0),"low52":meta.get("fiftyTwoWeekLow",0)}
    except Exception as e:
        return {"error": str(e)}

def render_stocks_addon():
    st.markdown("""
    <style>
    .st-price { font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;color:#fff; }
    .st-up { color:#10b981; } .st-dn { color:#ef4444; }
    .st-card { background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;padding:18px;text-align:center; }
    </style>""", unsafe_allow_html=True)

    sa1,sa2,sa3 = st.tabs(["📈 Live Charts","💼 Portfolio Tracker","📰 Market Sentiment"])

    with sa1:
        sym = st.text_input("Stock Symbol:", value="AAPL", placeholder="AAPL, TSLA, MSFT, RELIANCE.NS",
                            key="sa_symbol").upper()
        period = st.selectbox("Period:", ["1d","5d","1mo","3mo","6mo","1y"], index=2, key="sa_period")
        if st.button("📊 Get Live Data & Chart", type="primary", use_container_width=True, key="sa_fetch"):
            with st.spinner(f"Fetching {sym}..."):
                data = _fetch_stock_data(sym)
            if "error" in data:
                st.error(f"Could not fetch {sym}: {data['error']}")
            else:
                chg = data['price']-data['prev']
                pct = (chg/data['prev']*100) if data['prev'] else 0
                sign = "▲" if chg>=0 else "▼"
                clr = "st-up" if chg>=0 else "st-dn"
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f'<div class="st-card"><div class="st-price">${data["price"]:.2f}</div><div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">PRICE</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="st-card"><div class="{clr}" style="font-size:1.4rem;font-weight:800;">{sign} {abs(chg):.2f} ({abs(pct):.1f}%)</div><div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">CHANGE</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="st-card"><div style="font-size:1.1rem;font-weight:800;color:#10b981;">${data["high52"]:.2f}</div><div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">52W HIGH</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="st-card"><div style="font-size:1.1rem;font-weight:800;color:#ef4444;">${data["low52"]:.2f}</div><div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">52W LOW</div></div>', unsafe_allow_html=True)
                st.caption(f"**{data['name']}** · {data['currency']}")

                if data.get("closes"):
                    try:
                        import matplotlib; matplotlib.use("Agg")
                        import matplotlib.pyplot as plt
                        closes = [c for c in data["closes"] if c is not None]
                        fig,ax=plt.subplots(figsize=(10,4),facecolor='#0a0e1e')
                        ax.set_facecolor('#0f172a')
                        color='#10b981' if closes[-1]>=closes[0] else '#ef4444'
                        ax.plot(closes,color=color,linewidth=2.5)
                        ax.fill_between(range(len(closes)),closes,alpha=0.15,color=color)
                        ax.grid(True,color='#ffffff10'); ax.tick_params(colors='#ffffff80')
                        for sp in ax.spines.values(): sp.set_edgecolor('#ffffff20')
                        ax.set_title(f'{sym} — 1 Month Price',color='#c7d2fe',fontsize=12)
                        plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=150,bbox_inches='tight')
                        buf.seek(0); plt.close(); st.image(buf,use_container_width=True)
                    except Exception as e:
                        st.warning(f"Chart error: {e}")

                # AI Analysis
                if st.button("🤖 AI Stock Analysis", key="sa_ai", use_container_width=True):
                    with st.spinner("Analyzing..."):
                        try:
                            from utils.ai_engine import generate
                            ans = generate(f"Analyze {sym} ({data['name']}) stock: current price ${data['price']:.2f}, 52w high ${data['high52']:.2f}, low ${data['low52']:.2f}, change {pct:.1f}%. Give: trend analysis, key support/resistance levels, risk assessment, and short-term outlook. Be concise and professional.")
                            st.markdown(ans)
                        except Exception as e: st.error(str(e))

    with sa2:
        st.markdown("**💼 Portfolio Tracker** — Add stocks to track your holdings")
        if "sa_portfolio" not in st.session_state: st.session_state.sa_portfolio = []
        pc1,pc2,pc3 = st.columns(3)
        new_sym = pc1.text_input("Symbol:", key="sa_port_sym")
        new_qty = pc2.number_input("Qty:", min_value=0.01, value=1.0, key="sa_port_qty")
        new_buy = pc3.number_input("Buy Price ($):", min_value=0.01, value=100.0, key="sa_port_buy")
        if st.button("➕ Add to Portfolio", key="sa_port_add", use_container_width=True):
            if new_sym:
                st.session_state.sa_portfolio.append({"sym":new_sym.upper(),"qty":new_qty,"buy":new_buy})
                st.success(f"Added {new_sym.upper()}")
                st.rerun()

        if st.session_state.sa_portfolio:
            total_invested = sum(p['qty']*p['buy'] for p in st.session_state.sa_portfolio)
            st.markdown(f"**Total Invested: ${total_invested:,.2f}**")
            for p in st.session_state.sa_portfolio:
                invested = p['qty']*p['buy']
                st.markdown(f"• **{p['sym']}** — {p['qty']} shares @ ${p['buy']:.2f} = **${invested:,.2f}**")
            if st.button("🗑️ Clear Portfolio", key="sa_port_clear"):
                st.session_state.sa_portfolio = []; st.rerun()

    with sa3:
        st.markdown("**📰 Market Sentiment Analysis**")
        sent_sym = st.text_input("Stock/Company name:", value="Apple Inc", key="sa_sent_sym")
        if st.button("📰 Analyze Sentiment", key="sa_sent_btn", use_container_width=True, type="primary"):
            with st.spinner("Analyzing market sentiment..."):
                try:
                    from utils.ai_engine import generate
                    sent = generate(f"Provide a market sentiment analysis for {sent_sym}. Cover: 1) Current sentiment (bullish/bearish/neutral), 2) Key catalysts, 3) Analyst consensus, 4) Recent news impact, 5) Social media buzz, 6) Risk factors. Rate overall sentiment 1-10.")
                    st.markdown(sent)
                except Exception as e: st.error(str(e))
