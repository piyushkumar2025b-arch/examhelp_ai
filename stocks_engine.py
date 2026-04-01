"""
stocks_engine.py — AI-Powered Stock Market Analysis
===================================================
Simulated live data + AI Reasoning for investment insights.
"""

import datetime
import random
from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

# Mock data for demonstration (Since no Yahoo Finance API yet)
MOCK_STOCKS = {
    "AAPL": {"name": "Apple Inc.", "price": 182.52, "change": 1.25, "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corp.", "price": 415.10, "change": -0.45, "sector": "Technology"},
    "GOOGL": {"name": "Alphabet Inc.", "price": 142.12, "change": 2.10, "sector": "Communication Services"},
    "AMZN": {"name": "Amazon.com Inc.", "price": 175.05, "change": 0.85, "sector": "Consumer Cyclical"},
    "NVDA": {"name": "NVIDIA Corp.", "price": 820.45, "change": 4.12, "sector": "Technology"},
    "TSLA": {"name": "Tesla, Inc.", "price": 175.22, "change": -3.50, "sector": "Consumer Cyclical"},
    "RELIANCE": {"name": "Reliance Industries", "price": 2950.40, "change": 1.12, "sector": "Energy"},
    "TCS": {"name": "Tata Consultancy Services", "price": 4120.15, "change": -0.25, "sector": "Technology"},
    "HDFCBANK": {"name": "HDFC Bank Ltd.", "price": 1450.60, "change": 0.45, "sector": "Financial Services"},
}

def get_stock_data(symbol: str) -> Dict:
    """Fetch mock stock data (simulates a live API call)."""
    symbol = symbol.upper()
    if symbol in MOCK_STOCKS:
        data = MOCK_STOCKS[symbol].copy()
        # Add some random jitter
        data["price"] *= (1 + random.uniform(-0.001, 0.001))
        return data
    return {}

def get_ai_market_analysis(symbol: str, data: Dict) -> str:
    """Generate AI analysis for a specific stock."""
    prompt = f"""
    Analyze the technical and fundamental outlook for {symbol} ({data['name']}).
    Current Price: ${data['price']:.2f}
    Daily Change: {data['change']}%
    Sector: {data['sector']}
    
    Provide:
    1. Short-term Trend Analysis
    2. Key Support/Resistance Levels (Estimated)
    3. Potential Catalysts (News/Earnings)
    4. Verdict (Bullish/Bearish/Neutral)
    
    Be professional and analytical. Today: {datetime.date.today()}
    """
    return quick_generate(prompt=prompt, engine_name="researcher")

def get_market_overview() -> str:
    """Generate a brief market sentiment summary."""
    prompt = "Provide a 3-sentence summary of the current global and Indian stock market sentiment for today."
    return quick_generate(prompt=prompt, engine_name="researcher")
