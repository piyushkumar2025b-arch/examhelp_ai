"""
stocks_engine.py — AI-Powered Stock & Crypto Market Dashboard v3.0
Live data: Yahoo Finance (stocks) + CoinGecko (crypto) — both free, no key.
Fallback: yfinance library → mock data.
"""
import datetime
import random
from typing import Dict, List, Optional
from utils.ai_engine import quick_generate
from free_apis import (
    get_yahoo_quote, get_yahoo_chart, get_yahoo_batch,
    get_crypto_price, get_crypto_batch, get_crypto_market, CRYPTO_IDS,
)


# ── Core stock symbols with metadata ──────────────────────────────────────────
STOCK_META = {
    "AAPL":       {"name": "Apple Inc.",                "sector": "Technology",             "flag": "🇺🇸"},
    "MSFT":       {"name": "Microsoft Corp.",            "sector": "Technology",             "flag": "🇺🇸"},
    "GOOGL":      {"name": "Alphabet Inc.",              "sector": "Communication Services", "flag": "🇺🇸"},
    "AMZN":       {"name": "Amazon.com Inc.",            "sector": "Consumer Cyclical",      "flag": "🇺🇸"},
    "NVDA":       {"name": "NVIDIA Corp.",               "sector": "Technology",             "flag": "🇺🇸"},
    "TSLA":       {"name": "Tesla, Inc.",                "sector": "Consumer Cyclical",      "flag": "🇺🇸"},
    "META":       {"name": "Meta Platforms Inc.",        "sector": "Communication Services", "flag": "🇺🇸"},
    "AMD":        {"name": "AMD Inc.",                   "sector": "Technology",             "flag": "🇺🇸"},
    "RELIANCE.NS":{"name": "Reliance Industries",        "sector": "Energy",                 "flag": "🇮🇳"},
    "TCS.NS":     {"name": "Tata Consultancy Services",  "sector": "Technology",             "flag": "🇮🇳"},
    "HDFCBANK.NS":{"name": "HDFC Bank Ltd.",             "sector": "Financial Services",     "flag": "🇮🇳"},
    "INFY.NS":    {"name": "Infosys Ltd.",               "sector": "Technology",             "flag": "🇮🇳"},
    "WIPRO.NS":   {"name": "Wipro Ltd.",                 "sector": "Technology",             "flag": "🇮🇳"},
    "TATAMOTORS.NS":{"name":"Tata Motors",               "sector": "Automotive",             "flag": "🇮🇳"},
    "NIFTY50.NS": {"name": "Nifty 50 Index",             "sector": "Index",                  "flag": "🇮🇳"},
    "BTC-USD":    {"name": "Bitcoin",                    "sector": "Crypto",                 "flag": "₿"},
    "ETH-USD":    {"name": "Ethereum",                   "sector": "Crypto",                 "flag": "Ξ"},
}

# Mock prices used if yfinance not available
_MOCK_BASE = {
    "AAPL": 185.5,   "MSFT": 420.0,  "GOOGL": 145.0,  "AMZN": 178.0,
    "NVDA": 850.0,   "TSLA": 170.0,  "META": 490.0,   "AMD": 165.0,
    "RELIANCE.NS": 2960.0, "TCS.NS": 4100.0, "HDFCBANK.NS": 1460.0,
    "INFY.NS": 1450.0, "WIPRO.NS": 480.0, "TATAMOTORS.NS": 880.0,
    "NIFTY50.NS": 22400.0, "BTC-USD": 62000.0, "ETH-USD": 3200.0,
}


def get_crypto_data(symbol: str, vs_currency: str = "usd") -> Dict:
    """
    Fetch live cryptocurrency data via CoinGecko (free, no key).
    Returns same structure as get_stock_data() for UI compatibility.
    """
    sym = symbol.upper().replace("-USD", "").replace("-", "")
    live = get_crypto_price(sym, vs_currency)
    if live and live.get("price"):
        return {
            "symbol":     sym,
            "name":       live.get("coin_id", sym).replace("-", " ").title(),
            "sector":     "Cryptocurrency",
            "flag":       "🪩",
            "price":      live["price"],
            "change":     live["change_24h"],
            "prev_close": round(live["price"] / max(1 + live["change_24h"] / 100, 0.001), 2),
            "volume":     int(live.get("volume_24h", 0)),
            "market_cap": int(live.get("market_cap", 0)),
            "sparkline":  [],
            "currency":   vs_currency.upper(),
            "source":     "CoinGecko",
            "is_crypto":  True,
        }
    # Fallback: mock data
    mock_price = MOCK_PRICES.get(f"{sym}-USD", 100.0)
    return {
        "symbol":    sym, "name": sym, "sector": "Cryptocurrency", "flag": "🪩",
        "price":     mock_price, "change": round(random.uniform(-5, 5), 2),
        "prev_close": mock_price, "volume": 0, "market_cap": 0,
        "sparkline": [], "currency": vs_currency.upper(), "source": "mock", "is_crypto": True,
    }


def get_top_crypto(limit: int = 10, vs_currency: str = "usd") -> List[Dict]:
    """Top N cryptocurrencies by market cap via CoinGecko."""
    return get_crypto_market(limit=limit, vs_currency=vs_currency)


def get_stock_data(symbol: str) -> Dict:
    """Fetch live stock data: Yahoo Finance API → yfinance → mock."""
    symbol = symbol.upper().replace(" ", "")
    meta   = STOCK_META.get(symbol, {"name": symbol, "sector": "Unknown", "flag": "🌐"})

    # ── 1. Try Yahoo Finance (free, no key) ───────────────────────────
    live = get_yahoo_quote(symbol)
    if live and live.get("price"):
        return {
            "symbol":     symbol,
            "name":       live.get("name") or meta["name"],
            "sector":     meta["sector"],
            "flag":       meta["flag"],
            "price":      live["price"],
            "change":     live["change_pct"],
            "prev_close": live["prev_close"],
            "volume":     0,
            "market_cap": 0,
            "sparkline":  live.get("sparkline", []),
            "currency":   live.get("currency", "USD"),
            "exchange":   live.get("exchange", ""),
            "live":       True,
            "source":     "Yahoo Finance",
        }

    # ── 2. Try yfinance library ─────────────────────────────────────
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info   = ticker.fast_info
        price  = float(info.last_price or 0)
        prev   = float(info.previous_close or price)
        change = round(((price - prev) / max(1, prev)) * 100, 2)
        vol    = int(info.three_month_average_volume or 0)
        mc     = float(info.market_cap or 0)
        hist   = ticker.history(period="5d", interval="1d")
        spark  = list(hist["Close"].round(2)) if not hist.empty else []
        return {
            "symbol": symbol, "name": meta["name"], "sector": meta["sector"],
            "flag":   meta["flag"], "price": round(price, 2), "change": change,
            "prev_close": round(prev, 2), "volume": vol,
            "market_cap": mc, "sparkline": spark, "live": True, "source": "yfinance",
        }
    except Exception:
        pass

    # ── 3. Mock fallback ───────────────────────────────────────────────
    base   = _MOCK_BASE.get(symbol, 100.0)
    jitter = random.uniform(-0.015, 0.015)
    price  = round(base * (1 + jitter), 2)
    change = round(random.uniform(-3.5, 3.5), 2)
    spark  = [round(base * (1 + random.uniform(-0.01, 0.01)), 2) for _ in range(5)]
    return {
        "symbol": symbol, "name": meta["name"], "sector": meta["sector"],
        "flag":   meta["flag"], "price": price, "change": change,
        "prev_close": round(price / (1 + change / 100), 2),
        "volume": 0, "market_cap": 0, "sparkline": spark,
        "live": False, "source": "mock",
    }


def get_portfolio_summary(symbols: List[str]) -> List[Dict]:
    """Batch-fetch multiple stocks using Yahoo Finance batch API."""
    batch  = get_yahoo_batch(symbols)
    result = []
    for sym in symbols:
        if sym in batch:
            live = batch[sym]
            meta = STOCK_META.get(sym.upper(), {"name": sym, "sector": "Unknown", "flag": "🌐"})
            result.append({
                "symbol":     sym,
                "name":       live.get("name") or meta["name"],
                "sector":     meta["sector"],
                "flag":       meta["flag"],
                "price":      live["price"],
                "change":     live["change_pct"],
                "prev_close": live["prev_close"],
                "sparkline":  live.get("sparkline", []),
                "live":       True,
                "source":     "Yahoo Finance",
            })
        else:
            result.append(get_stock_data(sym))
    return result


def get_ai_market_analysis(symbol: str, data: Dict) -> str:
    """Generate AI analysis for a specific stock."""
    change_word = "up" if data.get("change", 0) >= 0 else "down"
    prompt = f"""Analyze the investment outlook for {symbol} ({data.get('name','')}).

Current: {data.get('flag','')} ${data.get('price',0):.2f} ({change_word} {abs(data.get('change',0)):.2f}% today)
Sector: {data.get('sector','')}
Date: {datetime.date.today().strftime('%B %Y')}

Provide a SHORT, sharp analysis:
**Trend**: (1 sentence)
**Key Levels**: Support ~$X, Resistance ~$Y
**Catalysts**: (1-2 bullets)
**Verdict**: 🟢 Bullish / 🔴 Bearish / 🟡 Neutral — (1 sentence why)

Be direct. No disclaimers. Use $ for prices. Max 120 words."""
    return quick_generate(prompt=prompt, engine_name="researcher") or "Analysis unavailable."


def get_market_overview() -> str:
    """Generate a brief market sentiment summary."""
    return quick_generate(
        prompt=f"In exactly 3 bullet points, give today's ({datetime.date.today().strftime('%B %Y')}) global stock market and crypto sentiment. Be sharp and current. Use emoji bullets.",
        engine_name="researcher"
    ) or "Market data unavailable."


def get_sector_rotation_view() -> str:
    """Explain current sector rotation trends."""
    return quick_generate(
        prompt=f"In 3-4 bullet points, which sectors are currently hot and which are cold ({datetime.date.today().strftime('%B %Y')})? Be specific with examples.",
        engine_name="researcher"
    ) or "Unavailable."


def sparkline_html(prices: List[float], color: str = "#10b981") -> str:
    """Generate a tiny SVG sparkline for a list of prices."""
    if not prices or len(prices) < 2:
        return ""
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1
    w, h = 80, 30
    pts  = []
    for i, p in enumerate(prices):
        x = int((i / (len(prices) - 1)) * w)
        y = int(h - ((p - mn) / rng) * h)
        pts.append(f"{x},{y}")
    poly = " ".join(pts)
    return f'<svg width="{w}" height="{h}" style="vertical-align:middle;"><polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def format_market_cap(mc: float) -> str:
    if mc >= 1e12: return f"${mc/1e12:.2f}T"
    if mc >= 1e9:  return f"${mc/1e9:.2f}B"
    if mc >= 1e6:  return f"${mc/1e6:.2f}M"
    return f"${mc:.0f}"


# Default watchlist for the stocks page
DEFAULT_WATCHLIST = ["AAPL", "MSFT", "NVDA", "TSLA", "TCS.NS", "RELIANCE.NS", "BTC-USD"]
