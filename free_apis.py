"""
free_apis.py — Zero-Auth Free API Hub v1.0
All APIs here work without any API key.
Used throughout ExamHelp AI to enrich features with live data.
"""
from __future__ import annotations
import json
import re
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Any


TIMEOUT = 8  # default request timeout


def _get(url: str, params: dict = None, headers: dict = None, timeout: int = TIMEOUT) -> Optional[dict]:
    """Simple GET request — returns parsed JSON or None."""
    try:
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 ExamHelpAI/2.0",
            "Accept": "application/json",
            **(headers or {}),
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _get_bytes(url: str, params: dict = None, timeout: int = TIMEOUT) -> Optional[bytes]:
    """GET request returning raw bytes."""
    try:
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ExamHelpAI/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 1. DICTIONARY — Free Dictionary API (dictionaryapi.dev)
# ══════════════════════════════════════════════════════════════════════════════

def get_dictionary(word: str, lang: str = "en") -> Optional[Dict]:
    """
    Full dictionary entry for a word including phonetics, meanings, examples.
    API: https://api.dictionaryapi.dev — completely free, no key.
    """
    data = _get(f"https://api.dictionaryapi.dev/api/v2/entries/{lang}/{urllib.parse.quote(word)}")
    if not data or not isinstance(data, list) or not data:
        return None
    entry = data[0]
    result = {
        "word":       entry.get("word", word),
        "phonetic":   entry.get("phonetic", ""),
        "phonetics":  [p for p in entry.get("phonetics", []) if p.get("text")],
        "audio_url":  "",
        "meanings":   [],
    }
    for p in entry.get("phonetics", []):
        if p.get("audio"):
            result["audio_url"] = p["audio"]
            break
    for m in entry.get("meanings", []):
        definitions = []
        for d in m.get("definitions", [])[:5]:
            definitions.append({
                "definition": d.get("definition", ""),
                "example":    d.get("example", ""),
                "synonyms":   d.get("synonyms", [])[:6],
                "antonyms":   d.get("antonyms", [])[:4],
            })
        result["meanings"].append({
            "partOfSpeech": m.get("partOfSpeech", ""),
            "definitions":  definitions,
            "synonyms":     m.get("synonyms", [])[:8],
            "antonyms":     m.get("antonyms", [])[:6],
        })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 2. STOCKS / FINANCE — Yahoo Finance (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_yahoo_quote(symbol: str) -> Optional[Dict]:
    """
    Live stock quote from Yahoo Finance.
    API: https://query2.finance.yahoo.com — free, no key.
    """
    url  = "https://query2.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol)
    data = _get(url, params={"interval": "1d", "range": "5d"},
                headers={"Accept": "application/json"})
    if not data:
        return None
    try:
        meta   = data["chart"]["result"][0]["meta"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        price  = meta.get("regularMarketPrice", 0)
        prev   = meta.get("chartPreviousClose", price)
        change = round(((price - prev) / max(prev, 0.001)) * 100, 2)
        return {
            "symbol":      symbol.upper(),
            "price":       round(price, 2),
            "change_pct":  change,
            "prev_close":  round(prev, 2),
            "currency":    meta.get("currency", "USD"),
            "exchange":    meta.get("exchangeName", ""),
            "name":        meta.get("longName") or meta.get("shortName", symbol),
            "sparkline":   [round(c, 2) for c in closes[-7:]],
            "timestamp":   meta.get("regularMarketTime", 0),
        }
    except (KeyError, IndexError, TypeError):
        return None


def get_yahoo_batch(symbols: List[str]) -> Dict[str, Dict]:
    """Batch fetch multiple symbols from Yahoo Finance."""
    results = {}
    for sym in symbols[:20]:
        q = get_yahoo_quote(sym)
        if q:
            results[sym] = q
    return results


def get_yahoo_chart(symbol: str, period: str = "1mo", interval: str = "1d") -> List[Dict]:
    """Get OHLCV chart data from Yahoo Finance."""
    url  = "https://query2.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol)
    data = _get(url, params={"interval": interval, "range": period},
                headers={"Accept": "application/json"})
    if not data:
        return []
    try:
        result    = data["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        ohlcv     = result["indicators"]["quote"][0]
        opens, highs = ohlcv.get("open", []), ohlcv.get("high", [])
        lows, closes = ohlcv.get("low", []), ohlcv.get("close", [])
        volumes      = ohlcv.get("volume", [])
        rows = []
        for i, ts in enumerate(timestamps):
            try:
                rows.append({
                    "timestamp": ts,
                    "open":   round(opens[i] or 0, 2),
                    "high":   round(highs[i] or 0, 2),
                    "low":    round(lows[i] or 0, 2),
                    "close":  round(closes[i] or 0, 2),
                    "volume": int(volumes[i] or 0),
                })
            except (IndexError, TypeError):
                continue
        return rows
    except (KeyError, IndexError, TypeError):
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 3. WEATHER — Open-Meteo (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_weather(lat: float, lon: float, days: int = 3) -> Optional[Dict]:
    """
    Current + forecast weather data.
    API: https://api.open-meteo.com — completely free, no key, no limits.
    """
    data = _get("https://api.open-meteo.com/v1/forecast", params={
        "latitude":           lat,
        "longitude":          lon,
        "current":            "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
        "daily":              "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum",
        "forecast_days":      days,
        "timezone":           "auto",
    })
    if not data:
        return None
    current = data.get("current", {})
    daily   = data.get("daily", {})
    wmo = {
        0: ("Clear Sky", "☀️"),        1: ("Mainly Clear", "🌤️"),
        2: ("Partly Cloudy", "⛅"),     3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),           51: ("Light Drizzle", "🌧️"),
        61: ("Rain", "🌧️"),            71: ("Snow", "❄️"),
        80: ("Rain Showers", "🌦️"),   95: ("Thunderstorm", "⛈️"),
    }
    code = current.get("weather_code", 0)
    desc, emoji = wmo.get(code, ("Unknown", "🌡️"))
    forecast = []
    for i in range(min(days, len(daily.get("time", [])))):
        fc = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
        fd, fe = wmo.get(fc, ("Unknown", "🌡️"))
        forecast.append({
            "date":     daily.get("time", [])[i] if i < len(daily.get("time", [])) else "",
            "max_temp": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else 0,
            "min_temp": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else 0,
            "precip":   daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "condition": fd,
            "emoji":    fe,
        })
    return {
        "temperature":   current.get("temperature_2m", 0),
        "feels_like":    current.get("apparent_temperature", 0),
        "humidity":      current.get("relative_humidity_2m", 0),
        "wind_speed":    current.get("wind_speed_10m", 0),
        "condition":     desc,
        "emoji":         emoji,
        "timezone":      data.get("timezone", ""),
        "forecast":      forecast,
    }


def geocode(city: str) -> Optional[Dict]:
    """
    Convert city name to lat/lon using Open-Meteo geocoding.
    API: https://geocoding-api.open-meteo.com — free, no key.
    """
    data = _get("https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"})
    if not data:
        return None
    results = data.get("results", [])
    if not results:
        return None
    r = results[0]
    return {
        "name":      r.get("name", city),
        "lat":       r.get("latitude", 0),
        "lon":       r.get("longitude", 0),
        "country":   r.get("country", ""),
        "timezone":  r.get("timezone", ""),
        "admin1":    r.get("admin1", ""),
    }


def get_weather_by_city(city: str, days: int = 3) -> Optional[Dict]:
    """Weather for a city name — geocodes first then fetches."""
    geo = geocode(city)
    if not geo:
        return None
    weather = get_weather(geo["lat"], geo["lon"], days)
    if weather:
        weather["city"]    = geo["name"]
        weather["country"] = geo["country"]
        weather["admin1"]  = geo.get("admin1", "")
    return weather


# ══════════════════════════════════════════════════════════════════════════════
# 4. CURRENCY — Open Exchange Rates (no key, basic tier)
# ══════════════════════════════════════════════════════════════════════════════

def get_exchange_rates(base: str = "USD") -> Optional[Dict]:
    """
    Live exchange rates for 150+ currencies.
    API: https://open.er-api.com — free basic tier, no key.
    """
    data = _get(f"https://open.er-api.com/v6/latest/{base.upper()}")
    if data and data.get("result") == "success":
        return {
            "base":       data.get("base_code", base),
            "rates":      data.get("rates", {}),
            "updated":    data.get("time_last_update_utc", ""),
            "next_update": data.get("time_next_update_utc", ""),
        }
    # Fallback to exchangerate-api
    data2 = _get(f"https://api.exchangerate-api.com/v4/latest/{base.upper()}")
    if data2:
        return {
            "base":    data2.get("base", base),
            "rates":   data2.get("rates", {}),
            "updated": data2.get("date", ""),
        }
    return None


def convert_currency(amount: float, from_cur: str, to_cur: str) -> Optional[Dict]:
    """Convert an amount between two currencies."""
    rates_data = get_exchange_rates(from_cur)
    if not rates_data:
        return None
    rates = rates_data.get("rates", {})
    if to_cur.upper() not in rates:
        return None
    rate   = rates[to_cur.upper()]
    result = amount * rate
    return {
        "amount":      amount,
        "from":        from_cur.upper(),
        "to":          to_cur.upper(),
        "rate":        round(rate, 6),
        "result":      round(result, 4),
        "updated":     rates_data.get("updated", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. WIKIPEDIA — MediaWiki REST API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_wikipedia_summary(title: str, lang: str = "en") -> Optional[Dict]:
    """
    Wikipedia article summary with image and extract.
    API: https://en.wikipedia.org/api/rest_v1 — completely free.
    """
    url  = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    data = _get(url)
    if not data:
        return None
    return {
        "title":       data.get("title", title),
        "description": data.get("description", ""),
        "extract":     data.get("extract", ""),
        "url":         data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "image":       data.get("originalimage", {}).get("source", ""),
        "thumbnail":   data.get("thumbnail", {}).get("source", ""),
        "lang":        lang,
    }


def search_wikipedia(query: str, limit: int = 8, lang: str = "en") -> List[Dict]:
    """
    Wikipedia full-text search.
    API: MediaWiki OpenSearch — free, no key.
    """
    data = _get(f"https://{lang}.wikipedia.org/w/api.php", params={
        "action":   "opensearch",
        "search":   query,
        "limit":    limit,
        "format":   "json",
    })
    if not data or len(data) < 4:
        return []
    titles, descs, urls = data[1], data[2], data[3]
    results = []
    for i, title in enumerate(titles):
        results.append({
            "title":       title,
            "description": descs[i] if i < len(descs) else "",
            "url":         urls[i]  if i < len(urls)  else "",
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 6. OPEN LIBRARY — Books & Authors (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_books(query: str, limit: int = 10, search_type: str = "q") -> List[Dict]:
    """
    Search for books via Open Library.
    API: https://openlibrary.org — free, no key.
    """
    data = _get("https://openlibrary.org/search.json", params={
        search_type: query,
        "limit":     limit,
        "fields":    "title,author_name,first_publish_year,subject,isbn,cover_i,key,number_of_pages_median",
    })
    if not data:
        return []
    books = []
    for doc in data.get("docs", [])[:limit]:
        isbn    = doc.get("isbn", [""])[0] if doc.get("isbn") else ""
        cover   = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else ""
        cover_i = doc.get("cover_i")
        if cover_i and not cover:
            cover = f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
        books.append({
            "title":      doc.get("title", ""),
            "authors":    doc.get("author_name", []),
            "year":       doc.get("first_publish_year", ""),
            "subjects":   doc.get("subject", [])[:5],
            "pages":      doc.get("number_of_pages_median", 0),
            "isbn":       isbn,
            "cover_url":  cover,
            "url":        f"https://openlibrary.org{doc.get('key', '')}",
        })
    return books


def get_book_details(olid: str) -> Optional[Dict]:
    """Get detailed book info by Open Library ID (e.g. OL7353617M)."""
    data = _get(f"https://openlibrary.org/api/books", params={
        "bibkeys": f"OLID:{olid}",
        "format":  "json",
        "jscmd":   "data",
    })
    if not data:
        return None
    key  = f"OLID:{olid}"
    book = data.get(key, {})
    return {
        "title":       book.get("title", ""),
        "authors":     [a.get("name", "") for a in book.get("authors", [])],
        "description": book.get("description", ""),
        "subjects":    [s.get("name", "") for s in book.get("subjects", [])[:8]],
        "cover":       book.get("cover", {}).get("large", ""),
        "url":         book.get("url", ""),
        "publishers":  [p.get("name", "") for p in book.get("publishers", [])],
        "year":        book.get("publish_date", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 7. TRIVIA / QUIZ — Open Trivia DB (no key)
# ══════════════════════════════════════════════════════════════════════════════

TRIVIA_CATEGORIES = {
    "General Knowledge": 9,  "Books": 10,          "Film": 11,
    "Music": 12,             "Science & Nature": 17,"Computers": 18,
    "Mathematics": 19,       "Sports": 21,          "Geography": 22,
    "History": 23,           "Politics": 24,        "Art": 25,
    "Animals": 27,           "Vehicles": 28,        "Comics": 29,
    "Gadgets": 30,           "Anime": 31,           "Cartoons": 32,
}


def get_trivia(count: int = 5, category: str = "General Knowledge",
               difficulty: str = "medium", q_type: str = "multiple") -> List[Dict]:
    """
    Random trivia questions.
    API: https://opentdb.com — free, no key.
    """
    cat_id = TRIVIA_CATEGORIES.get(category, 9)
    data   = _get("https://opentdb.com/api.php", params={
        "amount":     min(count, 50),
        "category":   cat_id,
        "difficulty": difficulty,
        "type":       q_type,
        "encode":     "url3986",
    })
    if not data or data.get("response_code") != 0:
        return []
    results = []
    for q in data.get("results", []):
        question  = urllib.parse.unquote(q.get("question", ""))
        correct   = urllib.parse.unquote(q.get("correct_answer", ""))
        incorrect = [urllib.parse.unquote(a) for a in q.get("incorrect_answers", [])]
        all_opts  = incorrect + [correct]
        import random; random.shuffle(all_opts)
        results.append({
            "question":   question,
            "correct":    correct,
            "options":    all_opts,
            "category":   urllib.parse.unquote(q.get("category", "")),
            "difficulty": q.get("difficulty", ""),
            "type":       q.get("type", "multiple"),
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 8. QUOTES — Quotable API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_random_quote(tags: str = "") -> Optional[Dict]:
    """
    Random motivational/philosophical quote.
    API: https://api.quotable.io — free, no key.
    """
    params = {"maxLength": 200}
    if tags:
        params["tags"] = tags
    data = _get("https://api.quotable.io/random", params=params)
    if data and data.get("content"):
        return {
            "text":   data["content"],
            "author": data.get("author", "Unknown"),
            "tags":   data.get("tags", []),
            "length": data.get("length", 0),
        }
    # Fallback to ZenQuotes
    data2 = _get("https://zenquotes.io/api/random")
    if data2 and isinstance(data2, list) and data2:
        return {
            "text":   data2[0].get("q", ""),
            "author": data2[0].get("a", "Unknown"),
            "tags":   [],
            "length": len(data2[0].get("q", "")),
        }
    return None


def get_quotes_by_author(author: str, limit: int = 5) -> List[Dict]:
    """Get quotes by a specific author."""
    data = _get("https://api.quotable.io/search/quotes", params={
        "query": author, "limit": limit, "fields": "author",
    })
    if not data:
        return []
    return [
        {"text": q["content"], "author": q["author"], "tags": q.get("tags", [])}
        for q in data.get("results", [])
    ]


def get_today_quote() -> Optional[Dict]:
    """Get the quote of the day."""
    data = _get("https://zenquotes.io/api/today")
    if data and isinstance(data, list) and data:
        return {
            "text":   data[0].get("q", ""),
            "author": data[0].get("a", "Unknown"),
            "tags":   ["inspiration"],
            "length": len(data[0].get("q", "")),
        }
    return get_random_quote()


# ══════════════════════════════════════════════════════════════════════════════
# 9. MATH — Newton API & MathJS (no key)
# ══════════════════════════════════════════════════════════════════════════════

NEWTON_OPS = [
    "simplify", "factor", "derive", "integrate", "zeroes",
    "tangent", "area", "cos", "sin", "tan", "arccos", "arcsin",
    "arctan", "abs", "log",
]


def compute_math(expression: str, operation: str = "simplify") -> Optional[Dict]:
    """
    Symbolic math operations.
    API: https://newton.now.sh — free, no key.
    """
    if operation not in NEWTON_OPS:
        operation = "simplify"
    expr = urllib.parse.quote(expression)
    data = _get(f"https://newton.now.sh/api/v2/{operation}/{expr}")
    if data:
        return {
            "operation":  data.get("operation", operation),
            "expression": data.get("expression", expression),
            "result":     data.get("result", ""),
        }
    return None


def evaluate_expression(expr: str) -> Optional[str]:
    """
    Evaluate a math expression numerically.
    API: https://api.mathjs.org — free, no key.
    """
    data = _get("https://api.mathjs.org/v4/", params={"expr": expr, "precision": 10})
    if data and isinstance(data, dict):
        return data.get("result", None)
    # Try as plain text response
    try:
        url  = "https://api.mathjs.org/v4/?" + urllib.parse.urlencode({"expr": expr, "precision": 10})
        req  = urllib.request.Request(url, headers={"User-Agent": "ExamHelpAI/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 10. QR CODE — QR Server API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_qr_image(data: str, size: int = 300, color: str = "000000",
                 bgcolor: str = "ffffff", correction: str = "H") -> Optional[bytes]:
    """
    Generate QR code as PNG bytes via external API (no qrcode library needed).
    API: https://api.qrserver.com — completely free, no key.
    """
    params = {
        "data":  data,
        "size":  f"{size}x{size}",
        "color": color.lstrip("#"),
        "bgcolor": bgcolor.lstrip("#"),
        "ecc":   correction,
        "format": "png",
        "margin": "10",
    }
    return _get_bytes("https://api.qrserver.com/v1/create-qr-code/", params=params)


# ══════════════════════════════════════════════════════════════════════════════
# 11. COUNTRY INFO — REST Countries (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_country_info(country: str) -> Optional[Dict]:
    """
    Rich country data including capital, currency, languages, flag.
    API: https://restcountries.com — free, no key.
    """
    data = _get(f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}",
                params={"fullText": "false"})
    if not data or not isinstance(data, list):
        return None
    c = data[0]
    currencies = {k: v.get("name","") + " (" + v.get("symbol","") + ")"
                  for k, v in c.get("currencies", {}).items()}
    languages  = list(c.get("languages", {}).values())
    return {
        "name":         c.get("name", {}).get("common", country),
        "official":     c.get("name", {}).get("official", ""),
        "capital":      c.get("capital", [""])[0] if c.get("capital") else "",
        "region":       c.get("region", ""),
        "subregion":    c.get("subregion", ""),
        "population":   c.get("population", 0),
        "area":         c.get("area", 0),
        "currencies":   currencies,
        "languages":    languages,
        "flag_emoji":   c.get("flag", ""),
        "flag_url":     c.get("flags", {}).get("png", ""),
        "timezones":    c.get("timezones", []),
        "calling_code": "+" + str(c.get("idd", {}).get("root","")).lstrip("+") +
                        "".join(c.get("idd", {}).get("suffixes", [""])[:1]),
        "independent":  c.get("independent", True),
        "un_member":    c.get("unMember", True),
    }


def get_all_countries(region: str = "") -> List[Dict]:
    """List all countries, optionally filtered by region."""
    url = "https://restcountries.com/v3.1/all" if not region else \
          f"https://restcountries.com/v3.1/region/{urllib.parse.quote(region)}"
    data = _get(url, params={"fields": "name,flag,region,population,capital,cca2"})
    if not data:
        return []
    return sorted([
        {
            "name":       c.get("name", {}).get("common", ""),
            "flag":       c.get("flag", ""),
            "region":     c.get("region", ""),
            "population": c.get("population", 0),
            "capital":    c.get("capital", [""])[0] if c.get("capital") else "",
            "code":       c.get("cca2", ""),
        } for c in data
    ], key=lambda x: x["name"])


# ══════════════════════════════════════════════════════════════════════════════
# 12. PUBLIC HOLIDAYS — Nager.Date (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_public_holidays(year: int = None, country_code: str = "IN") -> List[Dict]:
    """
    Public holidays for any country and year.
    API: https://date.nager.at — free, no key.
    """
    import datetime
    if not year:
        year = datetime.date.today().year
    data = _get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}")
    if not data:
        return []
    return [
        {
            "date":     h.get("date", ""),
            "name":     h.get("name", ""),
            "local":    h.get("localName", ""),
            "type":     h.get("types", ["Public"])[0] if h.get("types") else "Public",
            "national": h.get("national", True),
        }
        for h in data
    ]


def get_available_holiday_countries() -> List[Dict]:
    """Get list of supported countries for holidays."""
    data = _get("https://date.nager.at/api/v3/AvailableCountries")
    if not data:
        return []
    return [{"code": c.get("countryCode",""), "name": c.get("name","")} for c in data]


# ══════════════════════════════════════════════════════════════════════════════
# 13. NOMINATIM — OpenStreetMap Geocoding (no key)
# ══════════════════════════════════════════════════════════════════════════════

def reverse_geocode(lat: float, lon: float) -> Optional[Dict]:
    """
    Convert coordinates to an address.
    API: https://nominatim.openstreetmap.org — free, no key (1 req/sec limit).
    """
    data = _get("https://nominatim.openstreetmap.org/reverse", params={
        "lat":            lat,
        "lon":            lon,
        "format":         "json",
        "addressdetails": 1,
    }, headers={"Accept-Language": "en"})
    if not data:
        return None
    addr = data.get("address", {})
    return {
        "display_name": data.get("display_name", ""),
        "city":     addr.get("city") or addr.get("town") or addr.get("village", ""),
        "state":    addr.get("state", ""),
        "country":  addr.get("country", ""),
        "postcode": addr.get("postcode", ""),
        "lat":      float(data.get("lat", lat)),
        "lon":      float(data.get("lon", lon)),
    }


def search_place(query: str, limit: int = 5) -> List[Dict]:
    """Search for places by name."""
    data = _get("https://nominatim.openstreetmap.org/search", params={
        "q":              query,
        "format":         "json",
        "limit":          limit,
        "addressdetails": 1,
    }, headers={"Accept-Language": "en"})
    if not data:
        return []
    return [
        {
            "name":   p.get("display_name", ""),
            "lat":    float(p.get("lat", 0)),
            "lon":    float(p.get("lon", 0)),
            "type":   p.get("type", ""),
            "class":  p.get("class", ""),
        } for p in data
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 14. NUMBER FACTS — Numbers API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_number_fact(number: int, fact_type: str = "trivia") -> str:
    """
    Interesting fact about a number.
    API: http://numbersapi.com — free, no key.
    Types: trivia, math, date, year
    """
    try:
        url = f"http://numbersapi.com/{number}/{fact_type}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelpAI/2.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return f"Interesting fact about {number}: it's {number}!"


# ══════════════════════════════════════════════════════════════════════════════
# 15. IP GEOLOCATION (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_ip_location(ip: str = "") -> Optional[Dict]:
    """
    Get location data for an IP address (or current IP if empty).
    API: https://ipapi.co — free, no key (1000 req/day).
    """
    url  = f"https://ipapi.co/{ip + '/' if ip else ''}json/"
    data = _get(url)
    if data and not data.get("error"):
        return {
            "ip":         data.get("ip", ""),
            "city":       data.get("city", ""),
            "region":     data.get("region", ""),
            "country":    data.get("country_name", ""),
            "country_code": data.get("country_code", ""),
            "lat":        data.get("latitude", 0),
            "lon":        data.get("longitude", 0),
            "timezone":   data.get("timezone", ""),
            "org":        data.get("org", ""),
            "currency":   data.get("currency", ""),
        }
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 16. RSS FEED READER — Generic (no key)
# ══════════════════════════════════════════════════════════════════════════════

def parse_rss(url: str, max_items: int = 15) -> List[Dict]:
    """
    Parse any RSS/Atom feed.
    No API key needed — works with any public RSS feed.
    """
    import xml.etree.ElementTree as ET
    raw = _get_bytes(url)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        ns   = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        for item in root.findall(".//item")[:max_items]:
            title   = item.findtext("title", "").strip()
            desc    = re.sub(r"<[^>]+>", "", item.findtext("description", "").strip())[:400]
            link    = item.findtext("link", "").strip()
            pubdate = item.findtext("pubDate", "").strip()
            if title and link:
                items.append({"title": title, "description": desc,
                              "url": link, "published": pubdate})
        if not items:
            for entry in root.findall(".//atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", namespaces=ns, default="").strip()
                link_el = entry.find("atom:link", ns)
                link  = link_el.get("href", "") if link_el is not None else ""
                summary = re.sub(r"<[^>]+>", "",
                    entry.findtext("atom:summary", namespaces=ns, default="").strip())[:400]
                pub = entry.findtext("atom:published", namespaces=ns, default="").strip()
                if title and link:
                    items.append({"title": title, "description": summary,
                                  "url": link, "published": pub})
        return items
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 17. GITHUB — Public API (no key, 60 req/hr)
# ══════════════════════════════════════════════════════════════════════════════

def get_github_repo(owner: str, repo: str) -> Optional[Dict]:
    """Get public repository info from GitHub."""
    data = _get(f"https://api.github.com/repos/{owner}/{repo}")
    if not data:
        return None
    return {
        "name":        data.get("name", ""),
        "description": data.get("description", ""),
        "stars":       data.get("stargazers_count", 0),
        "forks":       data.get("forks_count", 0),
        "language":    data.get("language", ""),
        "topics":      data.get("topics", []),
        "url":         data.get("html_url", ""),
        "homepage":    data.get("homepage", ""),
        "open_issues": data.get("open_issues_count", 0),
        "license":     data.get("license", {}).get("name", "") if data.get("license") else "",
        "updated":     data.get("updated_at", ""),
    }


def search_github_repos(query: str, language: str = "", limit: int = 10) -> List[Dict]:
    """Search GitHub repositories (no auth — rate limited)."""
    q = query + (f" language:{language}" if language else "")
    data = _get("https://api.github.com/search/repositories", params={
        "q": q, "sort": "stars", "order": "desc", "per_page": limit,
    })
    if not data:
        return []
    return [
        {
            "name":        r.get("name", ""),
            "full_name":   r.get("full_name", ""),
            "description": r.get("description", ""),
            "stars":       r.get("stargazers_count", 0),
            "language":    r.get("language", ""),
            "url":         r.get("html_url", ""),
            "topics":      r.get("topics", []),
        } for r in data.get("items", [])
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 18. DUCKDUCKGO INSTANT ANSWERS (no key)
# ══════════════════════════════════════════════════════════════════════════════

def duckduckgo_search(query: str) -> Optional[Dict]:
    """
    DuckDuckGo Instant Answer API.
    API: https://api.duckduckgo.com — free, no key (no full search, instant answers only).
    """
    data = _get("https://api.duckduckgo.com/", params={
        "q":          query,
        "format":     "json",
        "no_html":    "1",
        "skip_disambig": "1",
    })
    if not data:
        return None
    return {
        "heading":      data.get("Heading", ""),
        "abstract":     data.get("AbstractText", ""),
        "source":       data.get("AbstractSource", ""),
        "url":          data.get("AbstractURL", ""),
        "image":        data.get("Image", ""),
        "related":      [
            {"text": t.get("Text",""), "url": t.get("FirstURL","")}
            for t in data.get("RelatedTopics", [])[:6]
            if isinstance(t, dict) and t.get("FirstURL")
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 19. ISS LOCATION (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_iss_location() -> Optional[Dict]:
    """
    Real-time ISS position.
    API: http://api.open-notify.org — free, no key.
    """
    data = _get("http://api.open-notify.org/iss-now.json")
    if data and data.get("iss_position"):
        pos = data["iss_position"]
        return {
            "lat":       float(pos.get("latitude", 0)),
            "lon":       float(pos.get("longitude", 0)),
            "timestamp": data.get("timestamp", 0),
        }
    return None


def get_people_in_space() -> Optional[Dict]:
    """How many people are in space right now."""
    data = _get("http://api.open-notify.org/astros.json")
    if not data:
        return None
    return {
        "count":  data.get("number", 0),
        "people": data.get("people", []),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 20. JOKES (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_joke(category: str = "Programming", safe: bool = True) -> Optional[Dict]:
    """
    Random joke.
    API: https://v2.jokeapi.dev — free, no key.
    """
    params = {"type": "twopart", "lang": "en"}
    if safe:
        params["safe-mode"] = ""
    data = _get(f"https://v2.jokeapi.dev/joke/{urllib.parse.quote(category)}", params=params)
    if not data or data.get("error"):
        return None
    if data.get("type") == "twopart":
        return {"joke": data.get("setup",""), "punchline": data.get("delivery",""),
                "category": data.get("category", category), "type": "twopart"}
    return {"joke": data.get("joke",""), "punchline": "", 
            "category": data.get("category", category), "type": "single"}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def check_api_health() -> Dict[str, str]:
    """Quick health check on all free APIs."""
    results = {}
    checks = {
        "Dictionary API":   ("https://api.dictionaryapi.dev/api/v2/entries/en/test", None),
        "Yahoo Finance":    ("https://query2.finance.yahoo.com/v8/finance/chart/AAPL?range=1d", None),
        "Open-Meteo":       ("https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.1&current=temperature_2m", None),
        "Exchange Rates":   ("https://open.er-api.com/v6/latest/USD", None),
        "Wikipedia":        ("https://en.wikipedia.org/api/rest_v1/page/summary/Python", None),
        "Open Library":     ("https://openlibrary.org/search.json?q=python&limit=1", None),
        "Open Trivia DB":   ("https://opentdb.com/api.php?amount=1", None),
        "Quotable":         ("https://api.quotable.io/random", None),
        "REST Countries":   ("https://restcountries.com/v3.1/name/india", None),
        "QR Server":        ("https://api.qrserver.com/v1/create-qr-code/?data=test&size=50x50", None),
        "Nager Holidays":   ("https://date.nager.at/api/v3/PublicHolidays/2024/IN", None),
        "Newton Math":      ("https://newton.now.sh/api/v2/simplify/x%5E2", None),
        "JokeAPI":          ("https://v2.jokeapi.dev/joke/Programming?safe-mode", None),
        "ISS Location":     ("http://api.open-notify.org/iss-now.json", None),
        "GitHub API":       ("https://api.github.com/repos/streamlit/streamlit", None),
        "arXiv":            ("https://export.arxiv.org/api/query?search_query=machine+learning&max_results=1", None),
        "CrossRef":         ("https://api.crossref.org/works?query=machine+learning&rows=1", None),
        "PubChem":          ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/JSON", None),
        "World Bank":       ("https://api.worldbank.org/v2/country/IN/indicator/NY.GDP.MKTP.CD?format=json&mrv=1", None),
        "Datamuse":         ("https://api.datamuse.com/words?ml=intelligence&max=3", None),
        "MyMemory":         ("https://api.mymemory.translated.net/get?q=hello&langpair=en|es", None),
        "CoinGecko":        ("https://api.coingecko.com/api/v3/ping", None),
        "NASA APOD":        ("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", None),
        "USGS Earthquakes": ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson", None),
        "Disease.sh":       ("https://disease.sh/v3/covid-19/all", None),
        "World Time API":   ("https://worldtimeapi.org/api/timezone/Asia/Kolkata", None),
        "Semantic Scholar": ("https://api.semanticscholar.org/graph/v1/paper/search?query=deep+learning&limit=1", None),
        "Today in History": ("https://history.muffinlabs.com/date/4/17", None),
        "Wikidata":         ("https://www.wikidata.org/w/api.php?action=wbsearchentities&search=python&format=json&language=en&limit=1", None),
        "University API":   ("http://universities.hipolabs.com/search?name=harvard", None),
    }
    import urllib.request as ur
    for name, (url, _) in checks.items():
        try:
            req = ur.Request(url, headers={"User-Agent": "ExamHelpAI/2.0"})
            with ur.urlopen(req, timeout=5) as r:
                status = "✅ Online" if r.status == 200 else f"⚠️ HTTP {r.status}"
        except Exception:
            status = "❌ Offline"
        results[name] = status
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 21. arXiv — Academic Paper Search (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_arxiv(query: str, max_results: int = 10, category: str = "") -> List[Dict]:
    """
    Search arXiv for academic papers (preprints).
    API: https://export.arxiv.org/api — completely free, no key.
    Categories: cs.AI, cs.LG, math.NA, physics.gen-ph, q-bio, econ, etc.
    """
    import xml.etree.ElementTree as ET
    q = query
    if category:
        q = f"cat:{category} AND {query}"
    url = f"https://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    raw = _get_bytes(url)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        ns   = {"atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"}
        results = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            title    = (entry.findtext("atom:title", namespaces=ns) or "").strip().replace("\n", " ")
            summary  = (entry.findtext("atom:summary", namespaces=ns) or "").strip()[:500]
            pub_date = (entry.findtext("atom:published", namespaces=ns) or "")[:10]
            upd_date = (entry.findtext("atom:updated", namespaces=ns) or "")[:10]
            link_el  = entry.find("atom:id", ns)
            arxiv_id = (link_el.text or "").strip() if link_el is not None else ""
            authors  = [a.findtext("atom:name", namespaces=ns) or ""
                        for a in entry.findall("atom:author", ns)]
            cats     = [c.get("term", "") for c in entry.findall("atom:category", ns)]
            pdf_url  = arxiv_id.replace("abs", "pdf") if arxiv_id else ""
            results.append({
                "title":     title,
                "authors":   authors[:6],
                "abstract":  summary,
                "url":       arxiv_id,
                "pdf_url":   pdf_url,
                "published": pub_date,
                "updated":   upd_date,
                "categories": cats,
            })
        return results
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 22. CrossRef — DOI & Citation Lookup (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_crossref(query: str, limit: int = 8, year_from: int = 2010) -> List[Dict]:
    """
    Search academic papers/journals via CrossRef.
    API: https://api.crossref.org — free, no key (polite pool).
    """
    data = _get("https://api.crossref.org/works", params={
        "query":       query,
        "rows":        limit,
        "filter":      f"from-pub-date:{year_from}",
        "select":      "DOI,title,author,published,container-title,abstract,type,URL",
        "sort":        "relevance",
        "mailto":      "examhelp@study.ai",
    })
    if not data:
        return []
    results = []
    for item in data.get("message", {}).get("items", [])[:limit]:
        title   = item.get("title", [""])[0] if item.get("title") else ""
        authors = [f"{a.get('given','')} {a.get('family','')}".strip()
                   for a in item.get("author", [])[:5]]
        journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
        pub     = item.get("published", {}).get("date-parts", [[""]])[0]
        year    = pub[0] if pub else ""
        doi     = item.get("DOI", "")
        results.append({
            "title":    title,
            "authors":  authors,
            "journal":  journal,
            "year":     str(year),
            "doi":      doi,
            "url":      f"https://doi.org/{doi}" if doi else item.get("URL", ""),
            "type":     item.get("type", ""),
            "abstract": item.get("abstract", "")[:400],
        })
    return results


def get_doi_info(doi: str) -> Optional[Dict]:
    """Get full metadata for a specific DOI."""
    doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    data = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi_clean)}")
    if not data:
        return None
    item = data.get("message", {})
    title   = item.get("title", [""])[0] if item.get("title") else doi
    authors = [f"{a.get('given','')} {a.get('family','')}".strip()
               for a in item.get("author", [])[:10]]
    journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
    return {
        "title":     title,
        "authors":   authors,
        "journal":   journal,
        "doi":       doi_clean,
        "url":       f"https://doi.org/{doi_clean}",
        "publisher": item.get("publisher", ""),
        "type":      item.get("type", ""),
        "abstract":  item.get("abstract", "")[:600],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 23. PubChem — Chemical Compound & Drug Database (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_compound(name: str) -> Optional[Dict]:
    """
    Get chemical compound data by name.
    API: https://pubchem.ncbi.nlm.nih.gov — free, no key (NIH).
    Returns: formula, molecular weight, IUPAC name, uses, structure URL.
    """
    data = _get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(name)}/JSON"
    )
    if not data:
        return None
    try:
        compound = data["PC_Compounds"][0]
        cid  = compound.get("id", {}).get("id", {}).get("cid", 0)
        props = {p["urn"]["label"]: p["value"]
                 for p in compound.get("props", []) if "label" in p.get("urn", {})}

        def pval(key, sub="sval"):
            v = props.get(key, {})
            return v.get(sub, v.get("fval", v.get("ival", "")))

        return {
            "name":         name.capitalize(),
            "cid":          cid,
            "molecular_formula": pval("Molecular Formula"),
            "molecular_weight":  pval("Molecular Weight"),
            "iupac_name":   pval("IUPAC Name"),
            "inchi":        pval("InChI"),
            "smiles":       pval("SMILES", "sval"),
            "structure_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            "image_url":    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG",
        }
    except (KeyError, IndexError):
        return None


def search_compounds(query: str, limit: int = 5) -> List[Dict]:
    """Search PubChem for compounds by keyword."""
    data = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(query)}/cids/JSON")
    if not data:
        return []
    cids = data.get("IdentifierList", {}).get("CID", [])[:limit]
    results = []
    for cid in cids:
        d = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight/JSON")
        if d:
            try:
                p = d["PropertyTable"]["Properties"][0]
                results.append({
                    "cid":     cid,
                    "name":    p.get("IUPACName", str(cid)),
                    "formula": p.get("MolecularFormula", ""),
                    "weight":  p.get("MolecularWeight", ""),
                    "url":     f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                    "image_url": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG",
                })
            except (KeyError, IndexError):
                pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 24. World Bank — Economic & Development Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

WORLD_BANK_INDICATORS = {
    "GDP":              "NY.GDP.MKTP.CD",
    "GDP per capita":   "NY.GDP.PCAP.CD",
    "Population":       "SP.POP.TOTL",
    "Inflation":        "FP.CPI.TOTL.ZG",
    "Unemployment":     "SL.UEM.TOTL.ZS",
    "Life expectancy":  "SP.DYN.LE00.IN",
    "Literacy rate":    "SE.ADT.LITR.ZS",
    "CO2 emissions":    "EN.ATM.CO2E.PC",
    "Internet users %": "IT.NET.USER.ZS",
    "School enrollment": "SE.TER.ENRR",
    "Poverty rate":     "SI.POV.DDAY",
    "Forest area %":    "AG.LND.FRST.ZS",
}


def get_world_bank_data(country_code: str, indicator_name: str = "GDP",
                        years: int = 5) -> Optional[Dict]:
    """
    Fetch World Bank development indicator data.
    API: https://api.worldbank.org — free, no key.
    """
    indicator = WORLD_BANK_INDICATORS.get(indicator_name, indicator_name)
    data = _get(
        f"https://api.worldbank.org/v2/country/{country_code.upper()}/indicator/{indicator}",
        params={"format": "json", "mrv": years, "per_page": years}
    )
    if not data or len(data) < 2:
        return None
    meta   = data[0]
    series = [r for r in data[1] if r.get("value") is not None]
    if not series:
        return None
    series.sort(key=lambda x: x.get("date", "0"), reverse=True)
    return {
        "country":    series[0].get("country", {}).get("value", country_code),
        "indicator":  indicator_name,
        "code":       indicator,
        "latest":     series[0].get("value"),
        "year":       series[0].get("date", ""),
        "unit":       meta.get("indicator", {}).get("value", "") if isinstance(meta, dict) else "",
        "series":     [{"year": r["date"], "value": r["value"]} for r in series],
    }


def get_country_indicators(country_code: str) -> Dict[str, Any]:
    """Fetch all key World Bank indicators for a country."""
    results = {}
    for name in list(WORLD_BANK_INDICATORS.keys())[:6]:
        try:
            d = get_world_bank_data(country_code, name, years=1)
            if d:
                results[name] = {"value": d["latest"], "year": d["year"]}
        except Exception:
            pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 25. Datamuse — Word Intelligence API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def datamuse_words(
    means_like: str = "",
    sounds_like: str = "",
    spelled_like: str = "",
    related_to: str = "",
    adjectives_for: str = "",
    nouns_for: str = "",
    rhymes_with: str = "",
    limit: int = 10,
) -> List[Dict]:
    """
    Find words by meaning, sound, spelling, or relationship.
    API: https://api.datamuse.com — free, no key, no rate limit.
    """
    params: Dict = {"max": limit}
    if means_like:    params["ml"]  = means_like
    if sounds_like:   params["sl"]  = sounds_like
    if spelled_like:  params["sp"]  = spelled_like
    if related_to:    params["rel_trg"] = related_to
    if adjectives_for: params["rel_jja"] = adjectives_for
    if nouns_for:     params["rel_jjb"] = nouns_for
    if rhymes_with:   params["rel_rhy"] = rhymes_with
    if len(params) == 1:
        return []
    data = _get("https://api.datamuse.com/words", params=params)
    if not data:
        return []
    return [
        {"word": w.get("word", ""), "score": w.get("score", 0),
         "tags": w.get("tags", [])}
        for w in data[:limit]
    ]


def get_synonyms(word: str, limit: int = 12) -> List[str]:
    """Get synonyms for a word using Datamuse."""
    data = _get("https://api.datamuse.com/words", params={"rel_syn": word, "max": limit})
    return [w["word"] for w in (data or []) if w.get("word")]


def get_antonyms(word: str, limit: int = 8) -> List[str]:
    """Get antonyms for a word."""
    data = _get("https://api.datamuse.com/words", params={"rel_ant": word, "max": limit})
    return [w["word"] for w in (data or []) if w.get("word")]


def get_rhymes(word: str, limit: int = 12) -> List[str]:
    """Get rhyming words."""
    data = _get("https://api.datamuse.com/words", params={"rel_rhy": word, "max": limit})
    return [w["word"] for w in (data or []) if w.get("word")]


def get_word_associations(word: str, limit: int = 10) -> List[str]:
    """Words triggered by/associated with the given word."""
    data = _get("https://api.datamuse.com/words", params={"rel_trg": word, "max": limit})
    return [w["word"] for w in (data or []) if w.get("word")]


# ══════════════════════════════════════════════════════════════════════════════
# 26. MyMemory Translation API (no key — 1000 words/day free)
# ══════════════════════════════════════════════════════════════════════════════

LANG_CODES = {
    "English": "en", "Hindi": "hi", "Spanish": "es", "French": "fr",
    "German": "de", "Chinese": "zh", "Japanese": "ja", "Korean": "ko",
    "Arabic": "ar", "Portuguese": "pt", "Russian": "ru", "Italian": "it",
    "Dutch": "nl", "Turkish": "tr", "Polish": "pl", "Swedish": "sv",
    "Bengali": "bn", "Tamil": "ta", "Telugu": "te", "Urdu": "ur",
    "Gujarati": "gu", "Marathi": "mr", "Punjabi": "pa", "Indonesian": "id",
    "Malay": "ms", "Thai": "th", "Vietnamese": "vi", "Greek": "el",
}


def translate_text(text: str, target_lang: str = "hi", source_lang: str = "en") -> Optional[Dict]:
    """
    Translate text to any language.
    API: https://api.mymemory.translated.net — free, no key (1000 words/day).
    """
    # Support full language names
    src = LANG_CODES.get(source_lang, source_lang)
    tgt = LANG_CODES.get(target_lang, target_lang)
    data = _get("https://api.mymemory.translated.net/get", params={
        "q":        text[:500],
        "langpair": f"{src}|{tgt}",
        "de":       "examhelp@study.ai",   # polite pool
    })
    if not data:
        return None
    response = data.get("responseData", {})
    if data.get("responseStatus") == 200:
        return {
            "original":   text,
            "translated": response.get("translatedText", ""),
            "from":       source_lang,
            "to":         target_lang,
            "match":      response.get("match", 0),
            "source":     "MyMemory",
        }
    return None


def translate_batch(texts: List[str], target_lang: str = "hi",
                    source_lang: str = "en") -> List[Optional[Dict]]:
    """Translate multiple texts."""
    return [translate_text(t, target_lang, source_lang) for t in texts]


# ══════════════════════════════════════════════════════════════════════════════
# 27. CoinGecko — Live Crypto Prices (no key)
# ══════════════════════════════════════════════════════════════════════════════

CRYPTO_IDS = {
    "BTC": "bitcoin",    "ETH": "ethereum",   "BNB": "binancecoin",
    "XRP": "ripple",     "ADA": "cardano",     "SOL": "solana",
    "DOT": "polkadot",   "DOGE": "dogecoin",   "LTC": "litecoin",
    "LINK": "chainlink", "MATIC": "matic-network", "AVAX": "avalanche-2",
    "SHIB": "shiba-inu", "TRX": "tron",        "UNI": "uniswap",
}


def get_crypto_price(symbol: str, vs_currency: str = "usd") -> Optional[Dict]:
    """
    Live cryptocurrency price and market data.
    API: https://api.coingecko.com — free, no key (30 req/min).
    """
    coin_id = CRYPTO_IDS.get(symbol.upper(), symbol.lower())
    data = _get("https://api.coingecko.com/api/v3/simple/price", params={
        "ids":                       coin_id,
        "vs_currencies":             vs_currency,
        "include_24hr_change":       "true",
        "include_24hr_vol":          "true",
        "include_market_cap":        "true",
        "include_last_updated_at":   "true",
    })
    if not data or coin_id not in data:
        return None
    d = data[coin_id]
    return {
        "symbol":       symbol.upper(),
        "coin_id":      coin_id,
        "price":        d.get(vs_currency, 0),
        "change_24h":   round(d.get(f"{vs_currency}_24h_change", 0), 2),
        "volume_24h":   d.get(f"{vs_currency}_24h_vol", 0),
        "market_cap":   d.get(f"{vs_currency}_market_cap", 0),
        "currency":     vs_currency.upper(),
        "updated":      d.get("last_updated_at", 0),
    }


def get_crypto_batch(symbols: List[str], vs_currency: str = "usd") -> Dict[str, Dict]:
    """Get prices for multiple cryptocurrencies at once."""
    ids = [CRYPTO_IDS.get(s.upper(), s.lower()) for s in symbols]
    data = _get("https://api.coingecko.com/api/v3/simple/price", params={
        "ids":                     ",".join(ids),
        "vs_currencies":           vs_currency,
        "include_24hr_change":     "true",
        "include_market_cap":      "true",
    })
    if not data:
        return {}
    results = {}
    for sym, coin_id in zip(symbols, ids):
        if coin_id in data:
            d = data[coin_id]
            results[sym.upper()] = {
                "symbol":   sym.upper(),
                "price":    d.get(vs_currency, 0),
                "change_24h": round(d.get(f"{vs_currency}_24h_change", 0), 2),
                "market_cap": d.get(f"{vs_currency}_market_cap", 0),
            }
    return results


def get_crypto_market(limit: int = 20, vs_currency: str = "usd") -> List[Dict]:
    """Top N cryptocurrencies by market cap."""
    data = _get("https://api.coingecko.com/api/v3/coins/markets", params={
        "vs_currency":    vs_currency,
        "order":          "market_cap_desc",
        "per_page":       limit,
        "page":           1,
        "sparkline":      "false",
        "price_change_percentage": "24h",
    })
    if not data:
        return []
    return [
        {
            "rank":       r.get("market_cap_rank", 0),
            "name":       r.get("name", ""),
            "symbol":     r.get("symbol", "").upper(),
            "price":      r.get("current_price", 0),
            "change_24h": r.get("price_change_percentage_24h", 0),
            "market_cap": r.get("market_cap", 0),
            "volume":     r.get("total_volume", 0),
            "image":      r.get("image", ""),
        }
        for r in data
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 28. NASA APOD — Astronomy Picture of the Day (DEMO_KEY = free)
# ══════════════════════════════════════════════════════════════════════════════

def get_nasa_apod(date: str = "") -> Optional[Dict]:
    """
    NASA Astronomy Picture of the Day.
    API: https://api.nasa.gov — DEMO_KEY is built-in (30 req/hr, 50/day).
    """
    params: Dict = {"api_key": "DEMO_KEY"}
    if date:
        params["date"] = date
    data = _get("https://api.nasa.gov/planetary/apod", params=params)
    if not data:
        return None
    return {
        "title":       data.get("title", ""),
        "date":        data.get("date", ""),
        "explanation": data.get("explanation", "")[:600],
        "url":         data.get("url", ""),
        "hdurl":       data.get("hdurl", data.get("url", "")),
        "media_type":  data.get("media_type", "image"),
        "copyright":   data.get("copyright", "NASA"),
    }


def get_nasa_apod_range(start_date: str, end_date: str) -> List[Dict]:
    """Get APOD images for a date range."""
    data = _get("https://api.nasa.gov/planetary/apod", params={
        "api_key":    "DEMO_KEY",
        "start_date": start_date,
        "end_date":   end_date,
    })
    if not data or not isinstance(data, list):
        return []
    return [
        {
            "title":       d.get("title", ""),
            "date":        d.get("date", ""),
            "explanation": d.get("explanation", "")[:300],
            "url":         d.get("url", ""),
            "media_type":  d.get("media_type", "image"),
        }
        for d in data
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 29. USGS Earthquakes — Real-Time Seismic Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

USGS_FEEDS = {
    "significant_hour":  "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson",
    "significant_day":   "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.geojson",
    "significant_week":  "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
    "all_hour":          "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "4.5_week":          "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson",
    "2.5_day":           "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
}


def get_earthquakes(feed: str = "significant_week", limit: int = 10) -> List[Dict]:
    """
    Live earthquake data from USGS.
    API: https://earthquake.usgs.gov — completely free, no key.
    """
    url  = USGS_FEEDS.get(feed, USGS_FEEDS["significant_week"])
    data = _get(url)
    if not data:
        return []
    import datetime as _dt
    results = []
    for f in data.get("features", [])[:limit]:
        props = f.get("properties", {})
        geo   = f.get("geometry", {}).get("coordinates", [None, None, None])
        ts    = props.get("time", 0)
        try:
            dt = _dt.datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            dt = str(ts)
        results.append({
            "magnitude": props.get("mag", 0),
            "place":     props.get("place", ""),
            "time":      dt,
            "longitude": geo[0],
            "latitude":  geo[1],
            "depth_km":  geo[2],
            "alert":     props.get("alert", ""),
            "url":       props.get("url", ""),
            "tsunami":   bool(props.get("tsunami", 0)),
        })
    results.sort(key=lambda x: x.get("magnitude", 0), reverse=True)
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 30. Disease.sh — Health & Epidemic Statistics (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_global_disease_stats() -> Optional[Dict]:
    """
    Global disease statistics (COVID-19).
    API: https://disease.sh — free, no key.
    """
    data = _get("https://disease.sh/v3/covid-19/all")
    if not data:
        return None
    return {
        "cases":            data.get("cases", 0),
        "deaths":           data.get("deaths", 0),
        "recovered":        data.get("recovered", 0),
        "active":           data.get("active", 0),
        "critical":         data.get("critical", 0),
        "cases_today":      data.get("todayCases", 0),
        "deaths_today":     data.get("todayDeaths", 0),
        "tests":            data.get("tests", 0),
        "population":       data.get("population", 0),
        "updated":          data.get("updated", 0),
    }


def get_country_disease_stats(country: str) -> Optional[Dict]:
    """Disease stats for a specific country."""
    data = _get(f"https://disease.sh/v3/covid-19/countries/{urllib.parse.quote(country)}")
    if not data or data.get("message"):
        return None
    return {
        "country":      data.get("country", country),
        "flag":         data.get("countryInfo", {}).get("flag", ""),
        "cases":        data.get("cases", 0),
        "deaths":       data.get("deaths", 0),
        "recovered":    data.get("recovered", 0),
        "active":       data.get("active", 0),
        "cases_today":  data.get("todayCases", 0),
        "deaths_today": data.get("todayDeaths", 0),
        "tests":        data.get("tests", 0),
        "population":   data.get("population", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 31. World Time API — Time Zones (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_world_time(timezone: str = "Asia/Kolkata") -> Optional[Dict]:
    """
    Current time for any timezone.
    API: https://worldtimeapi.org — free, no key.
    """
    data = _get(f"https://worldtimeapi.org/api/timezone/{timezone}")
    if not data:
        return None
    return {
        "timezone":    data.get("timezone", timezone),
        "datetime":    data.get("datetime", ""),
        "utc_offset":  data.get("utc_offset", ""),
        "day_of_week": data.get("day_of_week", 0),
        "day_of_year": data.get("day_of_year", 0),
        "week_number": data.get("week_number", 0),
        "dst":         data.get("dst", False),
        "unixtime":    data.get("unixtime", 0),
    }


def list_timezones(area: str = "") -> List[str]:
    """List all available timezones, optionally filtered by area."""
    data = _get("https://worldtimeapi.org/api/timezone")
    if not data:
        return []
    tzs = data if isinstance(data, list) else []
    if area:
        tzs = [t for t in tzs if t.startswith(area)]
    return tzs


# ══════════════════════════════════════════════════════════════════════════════
# 32. Semantic Scholar — AI-Powered Research Papers (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_semantic_scholar(query: str, limit: int = 8,
                             fields: str = "title,authors,year,abstract,url,citationCount,externalIds") -> List[Dict]:
    """
    Search academic papers with AI-powered relevance.
    API: https://api.semanticscholar.org — free, no key (100 req/5min).
    """
    data = _get("https://api.semanticscholar.org/graph/v1/paper/search", params={
        "query":  query,
        "limit":  limit,
        "fields": fields,
    })
    if not data:
        return []
    results = []
    for p in data.get("data", [])[:limit]:
        authors  = [a.get("name", "") for a in p.get("authors", [])[:5]]
        doi      = p.get("externalIds", {}).get("DOI", "")
        arxiv_id = p.get("externalIds", {}).get("ArXiv", "")
        results.append({
            "title":        p.get("title", ""),
            "authors":      authors,
            "year":         p.get("year", ""),
            "abstract":     (p.get("abstract") or "")[:500],
            "citations":    p.get("citationCount", 0),
            "paper_id":     p.get("paperId", ""),
            "url":          p.get("url") or (f"https://doi.org/{doi}" if doi else ""),
            "doi":          doi,
            "arxiv_id":     arxiv_id,
            "arxiv_url":    f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
        })
    return results


def get_paper_details(paper_id: str) -> Optional[Dict]:
    """Full details for a Semantic Scholar paper by its ID."""
    data = _get(
        f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}",
        params={"fields": "title,authors,year,abstract,url,citationCount,references,fieldsOfStudy,journal"},
    )
    if not data:
        return None
    return {
        "title":      data.get("title", ""),
        "authors":    [a.get("name", "") for a in data.get("authors", [])[:10]],
        "year":       data.get("year", ""),
        "abstract":   (data.get("abstract") or "")[:800],
        "citations":  data.get("citationCount", 0),
        "fields":     data.get("fieldsOfStudy", []),
        "journal":    (data.get("journal") or {}).get("name", ""),
        "url":        data.get("url", ""),
        "references": len(data.get("references", [])),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 33. Today in History — muffinlabs (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_today_in_history(month: int = None, day: int = None) -> Optional[Dict]:
    """
    Historical events, births, and deaths on this day.
    API: https://history.muffinlabs.com — free, no key.
    """
    import datetime as _dt
    if month is None or day is None:
        today = _dt.date.today()
        month, day = today.month, today.day
    data = _get(f"https://history.muffinlabs.com/date/{month}/{day}")
    if not data:
        return None
    def extract(items, limit=5):
        result = []
        for item in (items or [])[:limit]:
            result.append({
                "year": item.get("year", ""),
                "text": item.get("text", ""),
                "links": [l.get("title", "") for l in item.get("links", [])[:2]],
            })
        return result
    return {
        "date":   f"{month}/{day}",
        "events": extract(data.get("data", {}).get("Events", []), 6),
        "births": extract(data.get("data", {}).get("Births", []), 4),
        "deaths": extract(data.get("data", {}).get("Deaths", []), 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 34. Wikidata — Structured Knowledge Base (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_wikidata(query: str, limit: int = 5, lang: str = "en") -> List[Dict]:
    """
    Search Wikidata for entities (people, places, concepts).
    API: https://www.wikidata.org/w/api.php — free, no key.
    """
    data = _get("https://www.wikidata.org/w/api.php", params={
        "action":   "wbsearchentities",
        "search":   query,
        "format":   "json",
        "language": lang,
        "limit":    limit,
        "type":     "item",
    })
    if not data:
        return []
    results = []
    for item in data.get("search", [])[:limit]:
        qid = item.get("id", "")
        results.append({
            "id":          qid,
            "label":       item.get("label", ""),
            "description": item.get("description", ""),
            "url":         f"https://www.wikidata.org/wiki/{qid}",
            "aliases":     item.get("aliases", []),
        })
    return results


def get_wikidata_entity(qid: str, lang: str = "en") -> Optional[Dict]:
    """Get full entity data from Wikidata by QID (e.g. Q42 for Douglas Adams)."""
    data = _get("https://www.wikidata.org/w/api.php", params={
        "action":       "wbgetentities",
        "ids":          qid,
        "format":       "json",
        "languages":    lang,
        "props":        "labels|descriptions|claims|sitelinks",
    })
    if not data:
        return None
    entity = data.get("entities", {}).get(qid, {})
    if not entity:
        return None
    label = entity.get("labels", {}).get(lang, {}).get("value", qid)
    desc  = entity.get("descriptions", {}).get(lang, {}).get("value", "")
    wiki  = entity.get("sitelinks", {}).get(f"{lang}wiki", {}).get("url", "")
    return {
        "id":          qid,
        "label":       label,
        "description": desc,
        "wikipedia":   wiki or f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(label)}",
        "url":         f"https://www.wikidata.org/wiki/{qid}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 35. University Search — Hipolabs (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_universities(name: str = "", country: str = "") -> List[Dict]:
    """
    Search universities by name or country.
    API: http://universities.hipolabs.com — free, no key (open source).
    """
    params: Dict = {}
    if name:    params["name"]    = name
    if country: params["country"] = country
    data = _get("http://universities.hipolabs.com/search", params=params)
    if not data or not isinstance(data, list):
        return []
    results = []
    for u in data[:30]:
        results.append({
            "name":     u.get("name", ""),
            "country":  u.get("country", ""),
            "alpha_two_code": u.get("alpha_two_code", ""),
            "web_pages": u.get("web_pages", []),
            "domains":  u.get("domains", []),
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 36. Sunrise/Sunset — Astronomy Calculations (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_sunrise_sunset(lat: float, lon: float, date: str = "") -> Optional[Dict]:
    """
    Sunrise, sunset, solar noon, day length for any coordinates + date.
    API: https://api.sunrise-sunset.org — free, no key.
    """
    params: Dict = {"lat": lat, "lng": lon, "formatted": 0}
    if date:
        params["date"] = date
    data = _get("https://api.sunrise-sunset.org/json", params=params)
    if not data or data.get("status") != "OK":
        return None
    r = data.get("results", {})
    return {
        "sunrise":        r.get("sunrise", ""),
        "sunset":         r.get("sunset", ""),
        "solar_noon":     r.get("solar_noon", ""),
        "day_length_s":   r.get("day_length", 0),
        "day_length_h":   round(r.get("day_length", 0) / 3600, 2),
        "civil_twilight_begin": r.get("civil_twilight_begin", ""),
        "civil_twilight_end":   r.get("civil_twilight_end", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 37. Air Quality — Open-Meteo (no key)
# ══════════════════════════════════════════════════════════════════════════════

AQI_LEVELS = {
    (0, 20):    ("Excellent", "🟢"),
    (20, 40):   ("Good",      "🟡"),
    (40, 80):   ("Moderate",  "🟠"),
    (80, 120):  ("Poor",      "🔴"),
    (120, 999): ("Hazardous", "⚫"),
}


def get_air_quality(lat: float, lon: float) -> Optional[Dict]:
    """
    Real-time air quality data.
    API: https://air-quality-api.open-meteo.com — free, no key.
    """
    data = _get("https://air-quality-api.open-meteo.com/v1/air-quality", params={
        "latitude":  lat,
        "longitude": lon,
        "current":   "european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,uv_index",
    })
    if not data:
        return None
    current = data.get("current", {})
    aqi     = current.get("european_aqi", 0) or 0
    level, emoji = "Unknown", "❓"
    for (lo, hi), (lv, em) in AQI_LEVELS.items():
        if lo <= aqi < hi:
            level, emoji = lv, em
            break
    return {
        "aqi":              aqi,
        "level":            level,
        "emoji":            emoji,
        "pm2_5":            current.get("pm2_5", 0),
        "pm10":             current.get("pm10", 0),
        "co":               current.get("carbon_monoxide", 0),
        "no2":              current.get("nitrogen_dioxide", 0),
        "ozone":            current.get("ozone", 0),
        "uv_index":         current.get("uv_index", 0),
        "timezone":         data.get("timezone", ""),
    }


def get_air_quality_by_city(city: str) -> Optional[Dict]:
    """Air quality for a city name."""
    geo = geocode(city)
    if not geo:
        return None
    aq = get_air_quality(geo["lat"], geo["lon"])
    if aq:
        aq["city"]    = geo["name"]
        aq["country"] = geo["country"]
    return aq


# ══════════════════════════════════════════════════════════════════════════════
# 38. PoetryDB — Classical Poetry (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_poem(author: str = "", title: str = "") -> Optional[Dict]:
    """
    Retrieve classical poems.
    API: https://poetrydb.org — free, no key.
    """
    if author and title:
        url = f"https://poetrydb.org/author,title/{urllib.parse.quote(author)};{urllib.parse.quote(title)}"
    elif author:
        url = f"https://poetrydb.org/author/{urllib.parse.quote(author)}"
    elif title:
        url = f"https://poetrydb.org/title/{urllib.parse.quote(title)}"
    else:
        url = "https://poetrydb.org/random/1"
    data = _get(url)
    if not data or not isinstance(data, list) or not data:
        return None
    p = data[0]
    return {
        "title":    p.get("title", ""),
        "author":   p.get("author", ""),
        "lines":    p.get("lines", []),
        "linecount": p.get("linecount", 0),
        "text":     "\n".join(p.get("lines", [])),
    }


def list_poets() -> List[str]:
    """Get list of all available poets."""
    data = _get("https://poetrydb.org/author")
    if not data:
        return []
    return data.get("authors", [])


# ══════════════════════════════════════════════════════════════════════════════
# 39. Random Word Generator — (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_random_words(count: int = 5, word_length: int = 0) -> List[str]:
    """
    Random English words — useful for vocab practice.
    API: https://random-word-api.herokuapp.com — free, no key.
    """
    params: Dict = {"number": min(count, 100)}
    if word_length:
        params["length"] = word_length
    data = _get("https://random-word-api.herokuapp.com/word", params=params)
    if data and isinstance(data, list):
        return data[:count]
    # Fallback: Datamuse random-ish via means_like
    return []


# ══════════════════════════════════════════════════════════════════════════════
# 40. PubMed / NCBI E-utilities — Medical Literature (no key, low volume)
# ══════════════════════════════════════════════════════════════════════════════

def search_pubmed(query: str, max_results: int = 8) -> List[Dict]:
    """
    Search PubMed for medical research papers.
    API: https://eutils.ncbi.nlm.nih.gov — free, no key for low volume.
    Returns PMIDs with titles and abstracts.
    """
    # Step 1: search for IDs
    search_data = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={
        "db":       "pubmed",
        "term":     query,
        "retmax":   max_results,
        "retmode":  "json",
        "sort":     "relevance",
    })
    if not search_data:
        return []
    ids = search_data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # Step 2: fetch summaries
    summary_data = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
        "db":     "pubmed",
        "id":     ",".join(ids),
        "retmode": "json",
    })
    if not summary_data:
        return []

    results = []
    for pmid in ids:
        doc = summary_data.get("result", {}).get(pmid, {})
        if not doc or pmid == "uids":
            continue
        authors = [a.get("name", "") for a in doc.get("authors", [])[:5]]
        results.append({
            "pmid":      pmid,
            "title":     doc.get("title", ""),
            "authors":   authors,
            "journal":   doc.get("source", ""),
            "year":      doc.get("pubdate", "")[:4],
            "url":       f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "doi":       doc.get("elocationid", ""),
        })
    return results


def get_pubmed_abstract(pmid: str) -> Optional[Dict]:
    """Fetch full abstract for a PubMed article by PMID."""
    import xml.etree.ElementTree as ET
    url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
           f"db=pubmed&id={pmid}&retmode=xml&rettype=abstract")
    raw = _get_bytes(url)
    if not raw:
        return None
    try:
        root = ET.fromstring(raw)
        title = root.findtext(".//ArticleTitle", "") or ""
        abstract = " ".join(
            node.text or "" for node in root.findall(".//AbstractText")
        ).strip()[:800]
        authors = [
            f"{a.findtext('LastName','')} {a.findtext('Initials','')}".strip()
            for a in root.findall(".//Author")[:6]
        ]
        journal = root.findtext(".//Title", "") or root.findtext(".//ISOAbbreviation", "")
        year = root.findtext(".//PubDate/Year", "") or root.findtext(".//PubDate/MedlineDate", "")[:4]
        return {
            "pmid":     pmid,
            "title":    title,
            "abstract": abstract,
            "authors":  authors,
            "journal":  journal,
            "year":     year,
            "url":      f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 41. Google Books API — Book Search (no key for basic)
# ══════════════════════════════════════════════════════════════════════════════

def search_google_books(query: str, limit: int = 8, author: str = "",
                        subject: str = "") -> List[Dict]:
    """
    Search books via Google Books API.
    API: https://www.googleapis.com/books/v1 — free, no key (rate limited).
    """
    q = query
    if author:  q += f"+inauthor:{author}"
    if subject: q += f"+subject:{subject}"
    data = _get("https://www.googleapis.com/books/v1/volumes", params={
        "q":          q,
        "maxResults": min(limit, 40),
        "printType":  "books",
        "langRestrict": "en",
    })
    if not data:
        return []
    results = []
    for item in data.get("items", [])[:limit]:
        vol = item.get("volumeInfo", {})
        iids = vol.get("industryIdentifiers", [])
        isbn = next((i["identifier"] for i in iids if "ISBN_13" in i.get("type","")), "")
        if not isbn:
            isbn = next((i["identifier"] for i in iids if "ISBN" in i.get("type","")), "")
        thumb = vol.get("imageLinks", {}).get("thumbnail", "")
        results.append({
            "title":       vol.get("title", ""),
            "authors":     vol.get("authors", []),
            "publisher":   vol.get("publisher", ""),
            "year":        vol.get("publishedDate", "")[:4],
            "description": vol.get("description", "")[:400],
            "pages":       vol.get("pageCount", 0),
            "categories":  vol.get("categories", []),
            "language":    vol.get("language", ""),
            "isbn":        isbn,
            "thumbnail":   thumb,
            "preview_url": vol.get("previewLink", ""),
            "info_url":    vol.get("infoLink", ""),
            "rating":      vol.get("averageRating", 0),
            "ratings_count": vol.get("ratingsCount", 0),
        })
    return results


def get_google_book_by_isbn(isbn: str) -> Optional[Dict]:
    """Look up a specific book by ISBN."""
    data = _get("https://www.googleapis.com/books/v1/volumes",
                params={"q": f"isbn:{isbn}", "maxResults": 1})
    if not data or not data.get("items"):
        return None
    vol = data["items"][0]["volumeInfo"]
    return {
        "title":       vol.get("title", ""),
        "authors":     vol.get("authors", []),
        "publisher":   vol.get("publisher", ""),
        "year":        vol.get("publishedDate", "")[:4],
        "description": vol.get("description", "")[:600],
        "pages":       vol.get("pageCount", 0),
        "categories":  vol.get("categories", []),
        "isbn":        isbn,
        "thumbnail":   vol.get("imageLinks", {}).get("thumbnail", ""),
        "preview_url": vol.get("previewLink", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 42. SpaceX API — Rocket & Launch Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_latest_spacex_launch() -> Optional[Dict]:
    """
    Latest SpaceX launch data.
    API: https://api.spacexdata.com/v4 — free, no key.
    """
    data = _get("https://api.spacexdata.com/v4/launches/latest")
    if not data:
        return None
    return {
        "name":        data.get("name", ""),
        "date":        data.get("date_utc", "")[:10],
        "success":     data.get("success", None),
        "rocket_id":   data.get("rocket", ""),
        "details":     (data.get("details") or "")[:400],
        "links": {
            "webcast":    data.get("links", {}).get("webcast", ""),
            "wikipedia":  data.get("links", {}).get("wikipedia", ""),
            "presskit":   data.get("links", {}).get("presskit", ""),
            "patch":      data.get("links", {}).get("patch", {}).get("small", ""),
        },
        "flight_number": data.get("flight_number", 0),
        "reused":      data.get("cores", [{}])[0].get("reused") if data.get("cores") else None,
    }


def get_upcoming_spacex_launches(limit: int = 5) -> List[Dict]:
    """Get upcoming SpaceX launches."""
    data = _get("https://api.spacexdata.com/v4/launches/upcoming")
    if not data or not isinstance(data, list):
        return []
    results = []
    for launch in data[:limit]:
        results.append({
            "name":    launch.get("name", ""),
            "date":    launch.get("date_utc", "")[:10],
            "details": (launch.get("details") or "")[:200],
            "patch":   launch.get("links", {}).get("patch", {}).get("small", ""),
            "flight_number": launch.get("flight_number", 0),
        })
    return results


def get_spacex_rockets() -> List[Dict]:
    """All SpaceX rockets with technical specs."""
    data = _get("https://api.spacexdata.com/v4/rockets")
    if not data:
        return []
    return [
        {
            "name":           r.get("name", ""),
            "active":         r.get("active", False),
            "stages":         r.get("stages", 0),
            "height_m":       r.get("height", {}).get("meters", 0),
            "diameter_m":     r.get("diameter", {}).get("meters", 0),
            "mass_kg":        r.get("mass", {}).get("kg", 0),
            "payload_leo_kg": r.get("payload_weights", [{}])[0].get("kg", 0),
            "first_flight":   r.get("first_flight", ""),
            "cost_per_launch": r.get("cost_per_launch", 0),
            "success_rate":   r.get("success_rate_pct", 0),
            "description":    (r.get("description") or "")[:300],
            "wikipedia":      r.get("wikipedia", ""),
            "image":          r.get("flickr_images", [""])[0],
        }
        for r in data
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 43. Spaceflight News API — Science/Space News (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_spaceflight_news(limit: int = 10, search: str = "") -> List[Dict]:
    """
    Latest space/science news articles.
    API: https://api.spaceflightnewsapi.net/v4 — free, no key.
    """
    params: Dict = {"limit": limit, "ordering": "-published_at"}
    if search:
        params["title_contains"] = search
    data = _get("https://api.spaceflightnewsapi.net/v4/articles/", params=params)
    if not data:
        return []
    results = []
    for a in data.get("results", [])[:limit]:
        results.append({
            "title":        a.get("title", ""),
            "summary":      (a.get("summary") or "")[:300],
            "url":          a.get("url", ""),
            "image_url":    a.get("image_url", ""),
            "news_site":    a.get("news_site", ""),
            "published":    a.get("published_at", "")[:10],
            "updated":      a.get("updated_at", "")[:10],
        })
    return results


def get_spaceflight_blogs(limit: int = 5) -> List[Dict]:
    """Get space blog posts."""
    data = _get("https://api.spaceflightnewsapi.net/v4/blogs/",
                params={"limit": limit, "ordering": "-published_at"})
    if not data:
        return []
    return [
        {
            "title":     b.get("title", ""),
            "summary":   (b.get("summary") or "")[:200],
            "url":       b.get("url", ""),
            "published": b.get("published_at", "")[:10],
            "site":      b.get("news_site", ""),
        }
        for b in data.get("results", [])[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 44. HackerNews — Tech/CS News & Discussions (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_hackernews_top(limit: int = 10, story_type: str = "top") -> List[Dict]:
    """
    Top/best/new stories from Hacker News.
    API: https://hacker-news.firebaseio.com — free, no key.
    story_type: 'top', 'best', 'new', 'ask', 'show'
    """
    url_map = {
        "top":  "https://hacker-news.firebaseio.com/v0/topstories.json",
        "best": "https://hacker-news.firebaseio.com/v0/beststories.json",
        "new":  "https://hacker-news.firebaseio.com/v0/newstories.json",
        "ask":  "https://hacker-news.firebaseio.com/v0/askstories.json",
        "show": "https://hacker-news.firebaseio.com/v0/showstories.json",
    }
    ids_data = _get(url_map.get(story_type, url_map["top"]))
    if not ids_data or not isinstance(ids_data, list):
        return []
    results = []
    import datetime as _dt
    for story_id in ids_data[:limit]:
        item = _get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not item:
            continue
        ts = item.get("time", 0)
        try:
            dt = _dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            dt = ""
        results.append({
            "id":      story_id,
            "title":   item.get("title", ""),
            "url":     item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score":   item.get("score", 0),
            "author":  item.get("by", ""),
            "comments": item.get("descendants", 0),
            "date":    dt,
            "type":    item.get("type", "story"),
            "hn_url":  f"https://news.ycombinator.com/item?id={story_id}",
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 45. TheMealDB — Food, Nutrition & Recipes (free test key = "1")
# ══════════════════════════════════════════════════════════════════════════════

def search_meal(query: str) -> List[Dict]:
    """
    Search for recipes by name.
    API: https://www.themealdb.com — free (test API key '1').
    """
    data = _get("https://www.themealdb.com/api/json/v1/1/search.php",
                params={"s": query})
    if not data or not data.get("meals"):
        return []
    results = []
    for m in (data["meals"] or [])[:10]:
        ingredients = []
        for i in range(1, 21):
            ing = m.get(f"strIngredient{i}", "")
            meas = m.get(f"strMeasure{i}", "")
            if ing and ing.strip():
                ingredients.append(f"{meas.strip()} {ing.strip()}".strip())
        results.append({
            "name":        m.get("strMeal", ""),
            "category":    m.get("strCategory", ""),
            "area":        m.get("strArea", ""),
            "instructions": (m.get("strInstructions") or "")[:600],
            "thumbnail":   m.get("strMealThumb", ""),
            "youtube":     m.get("strYoutube", ""),
            "ingredients": ingredients,
            "tags":        [t.strip() for t in (m.get("strTags") or "").split(",") if t.strip()],
            "source":      m.get("strSource", ""),
        })
    return results


def get_random_meal() -> Optional[Dict]:
    """Get a random recipe."""
    data = _get("https://www.themealdb.com/api/json/v1/1/random.php")
    if not data or not data.get("meals"):
        return None
    m = data["meals"][0]
    return {
        "name":        m.get("strMeal", ""),
        "category":    m.get("strCategory", ""),
        "area":        m.get("strArea", ""),
        "instructions": (m.get("strInstructions") or "")[:800],
        "thumbnail":   m.get("strMealThumb", ""),
        "youtube":     m.get("strYoutube", ""),
    }


def list_meal_categories() -> List[str]:
    """List all meal categories."""
    data = _get("https://www.themealdb.com/api/json/v1/1/categories.php")
    if not data:
        return []
    return [c.get("strCategory", "") for c in (data.get("categories") or [])]


# ══════════════════════════════════════════════════════════════════════════════
# 46. GBIF — Global Biodiversity Species Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_species(name: str, limit: int = 8) -> List[Dict]:
    """
    Search for biological species information.
    API: https://api.gbif.org/v1 — free, no key.
    """
    data = _get("https://api.gbif.org/v1/species/suggest", params={
        "q":       name,
        "limit":   limit,
        "datasetKey": "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",  # Backbone taxonomy
    })
    if not data or not isinstance(data, list):
        return []
    results = []
    for s in data[:limit]:
        results.append({
            "key":        s.get("key", 0),
            "name":       s.get("scientificName", ""),
            "canonical":  s.get("canonicalName", ""),
            "rank":       s.get("rank", ""),
            "kingdom":    s.get("kingdom", ""),
            "phylum":     s.get("phylum", ""),
            "class_name": s.get("class", ""),
            "order":      s.get("order", ""),
            "family":     s.get("family", ""),
            "genus":      s.get("genus", ""),
            "species":    s.get("species", ""),
            "status":     s.get("status", ""),
            "url":        f"https://www.gbif.org/species/{s.get('key','')}",
        })
    return results


def get_species_details(key: int) -> Optional[Dict]:
    """Get full species details by GBIF key."""
    data = _get(f"https://api.gbif.org/v1/species/{key}")
    if not data:
        return None
    return {
        "name":          data.get("scientificName", ""),
        "canonical":     data.get("canonicalName", ""),
        "rank":          data.get("rank", ""),
        "kingdom":       data.get("kingdom", ""),
        "class_name":    data.get("class", ""),
        "order":         data.get("order", ""),
        "family":        data.get("family", ""),
        "genus":         data.get("genus", ""),
        "authorship":    data.get("authorship", ""),
        "published_in":  data.get("publishedIn", ""),
        "extinct":       data.get("extinct", False),
        "url":           f"https://www.gbif.org/species/{key}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 47. ChEMBL — Drug & Bioactivity Database (no key, EBI)
# ══════════════════════════════════════════════════════════════════════════════

def search_chembl(query: str, limit: int = 5) -> List[Dict]:
    """
    Search ChEMBL for drug molecules and bioactivity data.
    API: https://www.ebi.ac.uk/chembl/api — free, no key.
    """
    data = _get("https://www.ebi.ac.uk/chembl/api/data/molecule.json", params={
        "pref_name__icontains": query,
        "limit": limit,
    })
    if not data:
        return []
    results = []
    for mol in data.get("molecules", [])[:limit]:
        props = mol.get("molecule_properties") or {}
        results.append({
            "chembl_id":     mol.get("molecule_chembl_id", ""),
            "name":          mol.get("pref_name", "") or query,
            "type":          mol.get("molecule_type", ""),
            "formula":       props.get("full_molformula", ""),
            "weight":        props.get("full_mwt", ""),
            "alogp":         props.get("alogp", ""),
            "hba":           props.get("hba", ""),
            "hbd":           props.get("hbd", ""),
            "psa":           props.get("psa", ""),
            "ro5_violations": props.get("num_ro5_violations", ""),
            "max_phase":     mol.get("max_phase", 0),
            "url":           f"https://www.ebi.ac.uk/chembl/compound_report_card/{mol.get('molecule_chembl_id','')}/",
        })
    return results


def get_chembl_drug(chembl_id: str) -> Optional[Dict]:
    """Get full drug info by ChEMBL ID (e.g. CHEMBL25 = aspirin)."""
    data = _get(f"https://www.ebi.ac.uk/chembl/api/data/molecule/{chembl_id}.json")
    if not data:
        return None
    props = data.get("molecule_properties") or {}
    return {
        "chembl_id":  data.get("molecule_chembl_id", ""),
        "name":       data.get("pref_name", ""),
        "type":       data.get("molecule_type", ""),
        "formula":    props.get("full_molformula", ""),
        "weight":     props.get("full_mwt", ""),
        "smiles":     (data.get("molecule_structures") or {}).get("canonical_smiles", ""),
        "max_phase":  data.get("max_phase", 0),
        "atc_codes":  [a.get("level5", "") for a in data.get("atc_classifications", [])],
        "url":        f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 48. UniProt — Protein & Biology Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_uniprot(query: str, limit: int = 5, reviewed: bool = True) -> List[Dict]:
    """
    Search UniProt protein database.
    API: https://rest.uniprot.org — free, no key.
    """
    data = _get("https://rest.uniprot.org/uniprotkb/search", params={
        "query":    query + (" AND reviewed:true" if reviewed else ""),
        "format":   "json",
        "size":     limit,
        "fields":   "accession,protein_name,gene_names,organism_name,length,cc_function",
    })
    if not data:
        return []
    results = []
    for entry in data.get("results", [])[:limit]:
        pname = entry.get("proteinDescription", {})
        rec_name = pname.get("recommendedName", {})
        full_name = rec_name.get("fullName", {}).get("value", "") if rec_name else ""
        func = ""
        for c in entry.get("comments", []):
            if c.get("commentType") == "FUNCTION":
                texts = c.get("texts", [])
                if texts:
                    func = texts[0].get("value", "")[:300]
                    break
        gene = ""
        genes = entry.get("genes", [])
        if genes:
            gene = genes[0].get("geneName", {}).get("value", "")
        results.append({
            "accession": entry.get("primaryAccession", ""),
            "name":      full_name or entry.get("uniProtkbId", ""),
            "gene":      gene,
            "organism":  entry.get("organism", {}).get("scientificName", ""),
            "length":    entry.get("sequence", {}).get("length", 0),
            "function":  func,
            "url":       f"https://www.uniprot.org/uniprotkb/{entry.get('primaryAccession','')}/entry",
        })
    return results


def get_protein(accession: str) -> Optional[Dict]:
    """Get full protein data by UniProt accession (e.g. P0DTD1)."""
    data = _get(f"https://rest.uniprot.org/uniprotkb/{accession}.json")
    if not data:
        return None
    pname = data.get("proteinDescription", {})
    rec   = pname.get("recommendedName", {})
    name  = rec.get("fullName", {}).get("value", accession) if rec else accession
    func  = ""
    for c in data.get("comments", []):
        if c.get("commentType") == "FUNCTION":
            texts = c.get("texts", [])
            if texts:
                func = texts[0].get("value", "")[:500]
                break
    genes = data.get("genes", [])
    gene  = genes[0].get("geneName", {}).get("value", "") if genes else ""
    return {
        "accession":  accession,
        "name":       name,
        "gene":       gene,
        "organism":   data.get("organism", {}).get("scientificName", ""),
        "length":     data.get("sequence", {}).get("length", 0),
        "mass":       data.get("sequence", {}).get("molWeight", 0),
        "function":   func,
        "keywords":   [k.get("name", "") for k in data.get("keywords", [])[:8]],
        "url":        f"https://www.uniprot.org/uniprotkb/{accession}/entry",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 49. Unpaywall — Open Access Research (email only, no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_open_access_paper(doi: str) -> Optional[Dict]:
    """
    Check if a paper has free/open-access PDF via Unpaywall.
    API: https://api.unpaywall.org — free, email only (no key).
    """
    doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    data = _get(
        f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi_clean)}",
        params={"email": "examhelp@study.ai"},
    )
    if not data or data.get("error"):
        return None
    best_loc = data.get("best_oa_location") or {}
    return {
        "doi":          doi_clean,
        "title":        data.get("title", ""),
        "authors":      [a.get("family", "") for a in data.get("z_authors", [])[:5]],
        "year":         data.get("year", ""),
        "journal":      data.get("journal_name", ""),
        "is_oa":        data.get("is_oa", False),
        "oa_status":    data.get("oa_status", ""),
        "pdf_url":      best_loc.get("url_for_pdf", ""),
        "landing_url":  best_loc.get("url_for_landing_page", ""),
        "host_type":    best_loc.get("host_type", ""),
        "license":      best_loc.get("license", ""),
        "doi_url":      f"https://doi.org/{doi_clean}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 50. Zenodo — Open Research Data & Preprints (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_zenodo(query: str, limit: int = 8, resource_type: str = "") -> List[Dict]:
    """
    Search Zenodo for open research datasets, papers, and software.
    API: https://zenodo.org/api — free, no key for public search.
    resource_type: 'publication', 'dataset', 'software', 'poster', 'presentation', ''=all
    """
    params: Dict = {"q": query, "size": limit, "sort": "mostrecent"}
    if resource_type:
        params["type"] = resource_type
    data = _get("https://zenodo.org/api/records", params=params)
    if not data:
        return []
    results = []
    for hit in data.get("hits", {}).get("hits", [])[:limit]:
        meta   = hit.get("metadata", {})
        files  = hit.get("files", [])
        dl_url = files[0].get("links", {}).get("self", "") if files else ""
        results.append({
            "title":       meta.get("title", ""),
            "authors":     [c.get("name", "") for c in meta.get("creators", [])[:4]],
            "description": (meta.get("description") or "")[:300],
            "year":        (meta.get("publication_date") or "")[:4],
            "doi":         meta.get("doi", ""),
            "resource_type": meta.get("resource_type", {}).get("type", ""),
            "keywords":    meta.get("keywords", [])[:6],
            "license":     meta.get("license", {}).get("id", "") if meta.get("license") else "",
            "download_url": dl_url,
            "url":         hit.get("links", {}).get("html", ""),
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 51. Internet Archive — Historical Texts & Media (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_internet_archive(query: str, limit: int = 8,
                             media_type: str = "texts") -> List[Dict]:
    """
    Search Internet Archive for books, audio, video, and software.
    API: https://archive.org/advancedsearch.php — free, no key.
    media_type: 'texts', 'audio', 'movies', 'software', 'image', 'etree'
    """
    data = _get("https://archive.org/advancedsearch.php", params={
        "q":           f"({query}) AND mediatype:{media_type}",
        "fl[]":        "identifier,title,creator,date,description,subject,downloads,avg_rating",
        "rows":        limit,
        "output":      "json",
        "sort[]":      "downloads desc",
    })
    if not data:
        return []
    results = []
    for doc in data.get("response", {}).get("docs", [])[:limit]:
        identifier = doc.get("identifier", "")
        results.append({
            "identifier":   identifier,
            "title":        doc.get("title", ""),
            "creator":      doc.get("creator", ""),
            "date":         doc.get("date", ""),
            "description":  (doc.get("description") or "")[:300],
            "subjects":     doc.get("subject", [])[:5] if isinstance(doc.get("subject"), list) else [],
            "downloads":    doc.get("downloads", 0),
            "rating":       doc.get("avg_rating", 0),
            "url":          f"https://archive.org/details/{identifier}",
            "download_url": f"https://archive.org/download/{identifier}",
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 52. Open-Meteo Historical Weather (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_historical_weather(lat: float, lon: float,
                            start_date: str, end_date: str) -> Optional[Dict]:
    """
    Historical weather data for any location and date range.
    API: https://archive-api.open-meteo.com — free, no key.
    Dates format: 'YYYY-MM-DD'
    """
    data = _get("https://archive-api.open-meteo.com/v1/archive", params={
        "latitude":   lat,
        "longitude":  lon,
        "start_date": start_date,
        "end_date":   end_date,
        "daily":      "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone":   "auto",
    })
    if not data:
        return None
    daily = data.get("daily", {})
    times = daily.get("time", [])
    records = []
    for i, date in enumerate(times):
        records.append({
            "date":       date,
            "temp_max":   daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temp_min":   daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "precip":     daily.get("precipitation_sum",  [None])[i] if i < len(daily.get("precipitation_sum",  [])) else None,
            "wind_max":   daily.get("windspeed_10m_max",  [None])[i] if i < len(daily.get("windspeed_10m_max",  [])) else None,
        })
    return {
        "lat":       data.get("latitude"),
        "lon":       data.get("longitude"),
        "timezone":  data.get("timezone", ""),
        "records":   records,
        "days":      len(records),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 53. TVMaze — TV Shows & Episodes (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_tvshow(query: str, limit: int = 5) -> List[Dict]:
    """
    Search TV shows for pop culture / media studies.
    API: https://api.tvmaze.com — free, no key.
    """
    data = _get("https://api.tvmaze.com/search/shows", params={"q": query})
    if not data or not isinstance(data, list):
        return []
    results = []
    for item in data[:limit]:
        show = item.get("show", {})
        results.append({
            "name":     show.get("name", ""),
            "type":     show.get("type", ""),
            "language": show.get("language", ""),
            "genres":   show.get("genres", []),
            "status":   show.get("status", ""),
            "premiered": show.get("premiered", ""),
            "rating":   show.get("rating", {}).get("average", 0),
            "summary":  re.sub(r"<[^>]+>", "", show.get("summary") or "")[:300],
            "network":  (show.get("network") or {}).get("name", ""),
            "image":    (show.get("image") or {}).get("medium", ""),
            "url":      show.get("url", ""),
        })
    return results


def get_show_episodes(show_id: int) -> List[Dict]:
    """Get all episodes for a show by its TVMaze ID."""
    data = _get(f"https://api.tvmaze.com/shows/{show_id}/episodes")
    if not data or not isinstance(data, list):
        return []
    return [
        {
            "season":  ep.get("season", 0),
            "episode": ep.get("number", 0),
            "name":    ep.get("name", ""),
            "airdate": ep.get("airdate", ""),
            "runtime": ep.get("runtime", 0),
            "summary": re.sub(r"<[^>]+>", "", ep.get("summary") or "")[:150],
        }
        for ep in data
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 54. TheColorAPI — Color Information & Palettes (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_color_info(hex_code: str) -> Optional[Dict]:
    """
    Get color name, RGB, HSL, and contrast info.
    API: https://www.thecolorapi.com — free, no key.
    """
    hex_clean = hex_code.lstrip("#")
    data = _get(f"https://www.thecolorapi.com/id", params={"hex": hex_clean})
    if not data:
        return None
    return {
        "hex":        data.get("hex", {}).get("value", f"#{hex_clean}"),
        "name":       data.get("name", {}).get("value", ""),
        "rgb":        data.get("rgb", {}).get("value", ""),
        "hsl":        data.get("hsl", {}).get("value", ""),
        "hsv":        data.get("hsv", {}).get("value", ""),
        "cmyk":       data.get("cmyk", {}).get("value", ""),
        "r":          data.get("rgb", {}).get("r", 0),
        "g":          data.get("rgb", {}).get("g", 0),
        "b":          data.get("rgb", {}).get("b", 0),
        "image_url":  data.get("image", {}).get("bare", ""),
        "contrast":   data.get("contrast", {}).get("value", ""),
    }


def get_color_scheme(hex_code: str, mode: str = "analogic", count: int = 5) -> List[Dict]:
    """
    Generate a color scheme/palette from a seed color.
    API: https://www.thecolorapi.com/scheme — free, no key.
    mode: 'monochrome', 'monochrome-dark', 'monochrome-light', 'analogic',
          'complement', 'analogic-complement', 'triad', 'quad'
    """
    hex_clean = hex_code.lstrip("#")
    data = _get("https://www.thecolorapi.com/scheme", params={
        "hex":   hex_clean,
        "mode":  mode,
        "count": count,
        "format": "json",
    })
    if not data:
        return []
    colors = data.get("colors", [])
    return [
        {
            "hex":  c.get("hex", {}).get("value", ""),
            "name": c.get("name", {}).get("value", ""),
            "rgb":  c.get("rgb", {}).get("value", ""),
        }
        for c in colors
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 55. Agify / Nationalize / Genderize — Name Analytics (no key)
# ══════════════════════════════════════════════════════════════════════════════

def predict_age(name: str) -> Optional[Dict]:
    """Predict age from a first name. API: https://agify.io — free, no key."""
    data = _get("https://agify.io/", params={"name": name})
    if not data:
        return None
    return {"name": data.get("name", name), "age": data.get("age", 0), "count": data.get("count", 0)}


def predict_gender(name: str) -> Optional[Dict]:
    """Predict gender from a first name. API: https://genderize.io — free, no key."""
    data = _get("https://genderize.io/", params={"name": name})
    if not data:
        return None
    return {
        "name":        data.get("name", name),
        "gender":      data.get("gender", ""),
        "probability": data.get("probability", 0),
        "count":       data.get("count", 0),
    }


def predict_nationality(name: str) -> List[Dict]:
    """Predict likely nationality from a first name. API: https://nationalize.io — free, no key."""
    data = _get("https://nationalize.io/", params={"name": name})
    if not data:
        return []
    return [
        {"country": c.get("country_id", ""), "probability": c.get("probability", 0)}
        for c in data.get("country", [])[:5]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 56. Imgflip — Meme Templates (no key for listing)
# ══════════════════════════════════════════════════════════════════════════════

def get_meme_templates(limit: int = 20) -> List[Dict]:
    """
    Get popular meme templates.
    API: https://api.imgflip.com/get_memes — free, no key.
    """
    data = _get("https://api.imgflip.com/get_memes")
    if not data or not data.get("success"):
        return []
    return [
        {
            "id":     m.get("id", ""),
            "name":   m.get("name", ""),
            "url":    m.get("url", ""),
            "width":  m.get("width", 0),
            "height": m.get("height", 0),
            "boxes":  m.get("box_count", 2),
        }
        for m in data.get("data", {}).get("memes", [])[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 57. MusicBrainz — Music Encyclopedia (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_artist(name: str, limit: int = 5) -> List[Dict]:
    """
    Search for musical artists.
    API: https://musicbrainz.org/ws/2 — free, no key (1 req/sec).
    """
    data = _get("https://musicbrainz.org/ws/2/artist/", params={
        "query":  name,
        "limit":  limit,
        "fmt":    "json",
    }, headers={"User-Agent": "ExamHelpAI/2.0 (examhelp@study.ai)"})
    if not data:
        return []
    return [
        {
            "id":         a.get("id", ""),
            "name":       a.get("name", ""),
            "type":       a.get("type", ""),
            "country":    a.get("country", ""),
            "area":       (a.get("area") or {}).get("name", ""),
            "begin":      (a.get("life-span") or {}).get("begin", ""),
            "end":        (a.get("life-span") or {}).get("end", ""),
            "score":      a.get("score", 0),
            "url":        f"https://musicbrainz.org/artist/{a.get('id','')}",
        }
        for a in data.get("artists", [])[:limit]
    ]


def search_music(title: str, artist: str = "", limit: int = 5) -> List[Dict]:
    """Search for music recordings."""
    q = f'recording:"{title}"'
    if artist:
        q += f' AND artist:"{artist}"'
    data = _get("https://musicbrainz.org/ws/2/recording/", params={
        "query": q, "limit": limit, "fmt": "json",
    }, headers={"User-Agent": "ExamHelpAI/2.0 (examhelp@study.ai)"})
    if not data:
        return []
    return [
        {
            "title":   r.get("title", ""),
            "artist":  (r.get("artist-credit") or [{}])[0].get("name", ""),
            "length_ms": r.get("length", 0),
            "releases": len(r.get("releases", [])),
            "score":   r.get("score", 0),
        }
        for r in data.get("recordings", [])[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 58. Stack Exchange — Programming & Academic Q&A (no key)
# ══════════════════════════════════════════════════════════════════════════════

STACK_SITES = {
    "stackoverflow":   "stackoverflow",
    "math":            "math.stackexchange",
    "physics":         "physics.stackexchange",
    "chemistry":       "chemistry.stackexchange",
    "biology":         "biology.stackexchange",
    "english":         "english.stackexchange",
    "cs":              "cs.stackexchange",
    "datascience":     "datascience.stackexchange",
    "stats":           "stats.stackexchange",
    "philosophy":      "philosophy.stackexchange",
    "history":         "history.stackexchange",
    "economics":       "economics.stackexchange",
    "law":             "law.stackexchange",
    "medicalsciences": "medicalsciences.stackexchange",
}


def search_stackoverflow(query: str, site: str = "stackoverflow",
                          limit: int = 5, tagged: str = "") -> List[Dict]:
    """
    Search Stack Exchange / Stack Overflow questions.
    API: https://api.stackexchange.com/2.3 — free, no key (10k req/day).
    """
    site_id = STACK_SITES.get(site, site)
    params: Dict = {
        "order":    "desc",
        "sort":     "relevance",
        "intitle":  query,
        "site":     site_id,
        "pagesize": limit,
        "filter":   "withbody",
    }
    if tagged:
        params["tagged"] = tagged
    data = _get("https://api.stackexchange.com/2.3/search/advanced", params=params)
    if not data:
        return []
    results = []
    for q in data.get("items", [])[:limit]:
        results.append({
            "title":         q.get("title", ""),
            "score":         q.get("score", 0),
            "answers":       q.get("answer_count", 0),
            "views":         q.get("view_count", 0),
            "is_answered":   q.get("is_answered", False),
            "accepted":      q.get("accepted_answer_id") is not None,
            "tags":          q.get("tags", [])[:6],
            "owner":         q.get("owner", {}).get("display_name", ""),
            "created":       q.get("creation_date", 0),
            "url":           q.get("link", ""),
            "body_snippet":  re.sub(r"<[^>]+>", "", q.get("body", ""))[:300],
        })
    return results


def get_stackoverflow_answer(question_id: int, site: str = "stackoverflow") -> Optional[Dict]:
    """Get the accepted answer for a Stack Overflow question."""
    site_id = STACK_SITES.get(site, site)
    data = _get(f"https://api.stackexchange.com/2.3/questions/{question_id}/answers", params={
        "order": "desc", "sort": "votes", "site": site_id,
        "filter": "withbody", "pagesize": 1,
    })
    if not data or not data.get("items"):
        return None
    ans = data["items"][0]
    return {
        "score":  ans.get("score", 0),
        "body":   re.sub(r"<[^>]+>", "", ans.get("body", ""))[:600],
        "owner":  ans.get("owner", {}).get("display_name", ""),
        "accepted": ans.get("is_accepted", False),
        "url":    f"https://{site_id}.com/a/{ans.get('answer_id','')}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 59. Dev.to — Developer Articles & Tutorials (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_devto_articles(tag: str = "", top: int = 7, limit: int = 10) -> List[Dict]:
    """
    Fetch articles from Dev.to developer community.
    API: https://dev.to/api — free, no key.
    """
    params: Dict = {"per_page": limit}
    if tag:
        params["tag"] = tag
    elif top:
        params["top"] = top
    data = _get("https://dev.to/api/articles", params=params)
    if not data or not isinstance(data, list):
        return []
    return [
        {
            "title":         a.get("title", ""),
            "description":   (a.get("description") or "")[:250],
            "url":           a.get("url", ""),
            "cover_image":   a.get("cover_image", ""),
            "tags":          a.get("tag_list", [])[:5],
            "author":        a.get("user", {}).get("name", ""),
            "reactions":     a.get("public_reactions_count", 0),
            "comments":      a.get("comments_count", 0),
            "reading_time":  a.get("reading_time_minutes", 0),
            "published":     (a.get("published_at") or "")[:10],
        }
        for a in data[:limit]
    ]


def search_devto(query: str, limit: int = 5) -> List[Dict]:
    """Search Dev.to articles by keyword."""
    data = _get("https://dev.to/api/articles/search", params={"q": query, "per_page": limit})
    if not data or not isinstance(data, list):
        return []
    return [
        {
            "title":       a.get("title", ""),
            "description": (a.get("description") or "")[:200],
            "url":         a.get("url", ""),
            "tags":        a.get("tag_list", [])[:4],
            "author":      a.get("user", {}).get("name", ""),
            "reactions":   a.get("public_reactions_count", 0),
        }
        for a in data[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 60. PyPI — Python Package Registry (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_pypi_package(package_name: str) -> Optional[Dict]:
    """
    Get Python package info from PyPI.
    API: https://pypi.org/pypi — free, no key.
    """
    data = _get(f"https://pypi.org/pypi/{urllib.parse.quote(package_name)}/json")
    if not data:
        return None
    info    = data.get("info", {})
    releases = data.get("releases", {})
    latest_files = releases.get(info.get("version", ""), [])
    return {
        "name":         info.get("name", ""),
        "version":      info.get("version", ""),
        "summary":      info.get("summary", ""),
        "author":       info.get("author", ""),
        "license":      info.get("license", ""),
        "home_page":    info.get("home_page", ""),
        "project_url":  info.get("project_url", ""),
        "pypi_url":     f"https://pypi.org/project/{info.get('name','')}/",
        "requires_python": info.get("requires_python", ""),
        "classifiers":  info.get("classifiers", [])[:8],
        "keywords":     info.get("keywords", ""),
        "description":  (info.get("description") or "")[:500],
        "downloads":    sum(f.get("downloads", 0) for f in latest_files),
        "release_count": len(releases),
    }


def search_pypi(query: str, limit: int = 8) -> List[Dict]:
    """Search PyPI packages by keyword."""
    data = _get("https://pypi.org/search/", params={"q": query})
    # PyPI search returns HTML; use the JSON API with simple search
    # Alternative: use libraries.io but that needs key
    # Fallback text search via PyPI XML-RPC
    try:
        import xmlrpc.client as xc
        client = xc.ServerProxy("https://pypi.org/pypi")
        results = client.search({"name": query, "summary": query}, "or")[:limit]
        return [
            {
                "name":    r.get("name", ""),
                "version": r.get("version", ""),
                "summary": r.get("summary", ""),
                "url":     f"https://pypi.org/project/{r.get('name','')}/",
            }
            for r in results
        ]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 61. Project Gutenberg — Free Classic Books (Gutendex, no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_gutenberg(query: str, limit: int = 8, language: str = "en") -> List[Dict]:
    """
    Search Project Gutenberg for free classic books.
    API: https://gutendex.com — free, no key. Over 70,000 books.
    """
    data = _get("https://gutendex.com/books/", params={
        "search":    query,
        "languages": language,
    })
    if not data:
        return []
    results = []
    for book in data.get("results", [])[:limit]:
        formats = book.get("formats", {})
        txt_url = formats.get("text/plain; charset=utf-8") or formats.get("text/plain") or ""
        epub_url = formats.get("application/epub+zip", "")
        html_url = formats.get("text/html") or formats.get("text/html; charset=utf-8") or ""
        cover    = formats.get("image/jpeg", "")
        results.append({
            "id":          book.get("id", 0),
            "title":       book.get("title", ""),
            "authors":     [a.get("name", "") for a in book.get("authors", [])],
            "subjects":    book.get("subjects", [])[:5],
            "bookshelves": book.get("bookshelves", [])[:3],
            "languages":   book.get("languages", []),
            "downloads":   book.get("download_count", 0),
            "txt_url":     txt_url,
            "epub_url":    epub_url,
            "html_url":    html_url,
            "cover_url":   cover,
            "gutenberg_url": f"https://www.gutenberg.org/ebooks/{book.get('id','')}",
        })
    results.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    return results


def get_gutenberg_book(book_id: int) -> Optional[Dict]:
    """Get a specific Gutenberg book by ID."""
    data = _get(f"https://gutendex.com/books/{book_id}/")
    if not data:
        return None
    formats  = data.get("formats", {})
    txt_url  = formats.get("text/plain; charset=utf-8") or formats.get("text/plain", "")
    epub_url = formats.get("application/epub+zip", "")
    return {
        "id":        book_id,
        "title":     data.get("title", ""),
        "authors":   [a.get("name", "") for a in data.get("authors", [])],
        "subjects":  data.get("subjects", [])[:8],
        "languages": data.get("languages", []),
        "downloads": data.get("download_count", 0),
        "txt_url":   txt_url,
        "epub_url":  epub_url,
        "gutenberg_url": f"https://www.gutenberg.org/ebooks/{book_id}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 62. Open Food Facts — Nutrition Database (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_food(query: str, limit: int = 5) -> List[Dict]:
    """
    Search food nutrition data.
    API: https://world.openfoodfacts.org — free, no key.
    """
    data = _get("https://world.openfoodfacts.org/cgi/search.pl", params={
        "search_terms":  query,
        "search_simple": 1,
        "action":        "process",
        "json":          1,
        "page_size":     limit,
    })
    if not data:
        return []
    results = []
    for p in data.get("products", [])[:limit]:
        nutriments = p.get("nutriments", {})
        results.append({
            "name":          p.get("product_name", "") or p.get("product_name_en", ""),
            "brand":         p.get("brands", ""),
            "categories":    p.get("categories", "")[:100],
            "barcode":       p.get("code", ""),
            "nutriscore":    p.get("nutriscore_grade", "").upper(),
            "energy_kcal":   nutriments.get("energy-kcal_100g", 0),
            "proteins_g":    nutriments.get("proteins_100g", 0),
            "carbs_g":       nutriments.get("carbohydrates_100g", 0),
            "fat_g":         nutriments.get("fat_100g", 0),
            "fiber_g":       nutriments.get("fiber_100g", 0),
            "sugar_g":       nutriments.get("sugars_100g", 0),
            "salt_g":        nutriments.get("salt_100g", 0),
            "image_url":     p.get("image_small_url", ""),
            "url":           f"https://world.openfoodfacts.org/product/{p.get('code','')}",
        })
    return results


def get_food_by_barcode(barcode: str) -> Optional[Dict]:
    """Look up food product by barcode EAN/UPC."""
    data = _get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
    if not data or data.get("status") != 1:
        return None
    p = data.get("product", {})
    nutriments = p.get("nutriments", {})
    return {
        "name":       p.get("product_name", ""),
        "brand":      p.get("brands", ""),
        "barcode":    barcode,
        "nutriscore": p.get("nutriscore_grade", "").upper(),
        "energy_kcal": nutriments.get("energy-kcal_100g", 0),
        "proteins_g":  nutriments.get("proteins_100g", 0),
        "carbs_g":     nutriments.get("carbohydrates_100g", 0),
        "fat_g":       nutriments.get("fat_100g", 0),
        "image_url":   p.get("image_url", ""),
        "url":         f"https://world.openfoodfacts.org/product/{barcode}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 63. ClinicalTrials.gov — Medical Research Trials (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_clinical_trials(query: str, limit: int = 5,
                            status: str = "RECRUITING") -> List[Dict]:
    """
    Search active/past clinical trials (NIH).
    API: https://clinicaltrials.gov/api — free, no key.
    status: 'RECRUITING', 'COMPLETED', 'NOT_YET_RECRUITING', '' for all.
    """
    params: Dict = {
        "query.term":   query,
        "pageSize":     limit,
        "format":       "json",
        "fields":       "NCTId,BriefTitle,Condition,Phase,OverallStatus,StartDate,CompletionDate,BriefSummary",
    }
    if status:
        params["filter.overallStatus"] = status
    data = _get("https://clinicaltrials.gov/api/v2/studies", params=params)
    if not data:
        return []
    results = []
    for study in data.get("studies", [])[:limit]:
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        desc_mod   = proto.get("descriptionModule", {})
        cond_mod   = proto.get("conditionsModule", {})
        design_mod = proto.get("designModule", {})
        nct_id = ident.get("nctId", "")
        results.append({
            "nct_id":      nct_id,
            "title":       ident.get("briefTitle", ""),
            "conditions":  cond_mod.get("conditions", [])[:3],
            "phase":       design_mod.get("phases", [""])[0] if design_mod.get("phases") else "",
            "status":      status_mod.get("overallStatus", ""),
            "start_date":  status_mod.get("startDateStruct", {}).get("date", ""),
            "end_date":    status_mod.get("completionDateStruct", {}).get("date", ""),
            "summary":     (desc_mod.get("briefSummary") or "")[:300],
            "url":         f"https://clinicaltrials.gov/study/{nct_id}",
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 64. FDA — Drug Labels & Adverse Events (no key, limited)
# ══════════════════════════════════════════════════════════════════════════════

def search_fda_drug(drug_name: str, limit: int = 3) -> List[Dict]:
    """
    Search FDA drug label database.
    API: https://api.fda.gov/drug/label.json — free, no key (rate limited).
    """
    data = _get("https://api.fda.gov/drug/label.json", params={
        "search": f"openfda.brand_name:\"{drug_name}\" OR openfda.generic_name:\"{drug_name}\"",
        "limit":  limit,
    })
    if not data or data.get("error"):
        return []
    results = []
    for d in data.get("results", [])[:limit]:
        openf = d.get("openfda", {})
        results.append({
            "brand_names":   openf.get("brand_name", [])[:3],
            "generic_names": openf.get("generic_name", [])[:3],
            "manufacturer":  openf.get("manufacturer_name", [])[:1],
            "substance":     openf.get("substance_name", [])[:2],
            "route":         openf.get("route", [])[:2],
            "indications":   (d.get("indications_and_usage") or [""])[0][:300],
            "warnings":      (d.get("warnings") or [""])[0][:200],
            "dosage":        (d.get("dosage_and_administration") or [""])[0][:200],
            "contraindications": (d.get("contraindications") or [""])[0][:200],
        })
    return results


def get_fda_adverse_events(drug_name: str, limit: int = 5) -> List[Dict]:
    """Search FDA adverse drug event reports (FAERS)."""
    data = _get("https://api.fda.gov/drug/event.json", params={
        "search": f"patient.drug.medicinalproduct:\"{drug_name}\"",
        "limit":  limit,
    })
    if not data or data.get("error"):
        return []
    events = []
    for r in data.get("results", [])[:limit]:
        patient = r.get("patient", {})
        reactions = [rx.get("reactionmeddrapt", "") for rx in patient.get("reaction", [])[:4]]
        events.append({
            "reactions":   reactions,
            "serious":     r.get("serious", ""),
            "age":         patient.get("patientonsetage", ""),
            "sex":         patient.get("patientsex", ""),
            "country":     r.get("occurcountry", ""),
            "date":        r.get("receiptdate", ""),
        })
    return events


# ══════════════════════════════════════════════════════════════════════════════
# 65. Jikan — MyAnimeList Unofficial API (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_anime(query: str, limit: int = 5) -> List[Dict]:
    """
    Search anime database (MyAnimeList via Jikan).
    API: https://api.jikan.moe/v4 — free, no key (3 req/sec).
    """
    data = _get("https://api.jikan.moe/v4/anime", params={"q": query, "limit": limit})
    if not data:
        return []
    results = []
    for a in data.get("data", [])[:limit]:
        results.append({
            "mal_id":    a.get("mal_id", 0),
            "title":     a.get("title", ""),
            "title_en":  a.get("title_english", ""),
            "type":      a.get("type", ""),
            "episodes":  a.get("episodes", 0),
            "status":    a.get("status", ""),
            "score":     a.get("score", 0),
            "rank":      a.get("rank", 0),
            "genres":    [g.get("name", "") for g in a.get("genres", [])[:5]],
            "synopsis":  (a.get("synopsis") or "")[:300],
            "image":     a.get("images", {}).get("jpg", {}).get("image_url", ""),
            "url":       a.get("url", ""),
            "year":      a.get("year", ""),
            "studio":    (a.get("studios") or [{}])[0].get("name", ""),
        })
    return results


def get_top_anime(limit: int = 10, filter_type: str = "airing") -> List[Dict]:
    """
    Top anime by filter: 'airing', 'upcoming', 'bypopularity', 'favorite'.
    """
    data = _get("https://api.jikan.moe/v4/top/anime",
                params={"filter": filter_type, "limit": limit})
    if not data:
        return []
    return [
        {
            "rank":     a.get("rank", 0),
            "title":    a.get("title", ""),
            "score":    a.get("score", 0),
            "episodes": a.get("episodes", 0),
            "genres":   [g.get("name", "") for g in a.get("genres", [])[:3]],
            "image":    a.get("images", {}).get("jpg", {}).get("image_url", ""),
            "url":      a.get("url", ""),
        }
        for a in data.get("data", [])[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 66. NVD — CVE Cybersecurity Vulnerabilities (no key)
# ══════════════════════════════════════════════════════════════════════════════

def search_cve(keyword: str, limit: int = 5) -> List[Dict]:
    """
    Search Common Vulnerabilities and Exposures (CVE) database.
    API: https://services.nvd.nist.gov — free, no key (NIST).
    """
    data = _get("https://services.nvd.nist.gov/rest/json/cves/2.0", params={
        "keywordSearch": keyword,
        "resultsPerPage": limit,
    })
    if not data:
        return []
    results = []
    for vuln in data.get("vulnerabilities", [])[:limit]:
        cve  = vuln.get("cve", {})
        cve_id = cve.get("id", "")
        descs = cve.get("descriptions", [])
        desc  = next((d["value"] for d in descs if d.get("lang") == "en"), "")[:300]
        metrics = cve.get("metrics", {})
        cvss = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30") or metrics.get("cvssMetricV2") or [{}]
        score = cvss[0].get("cvssData", {}).get("baseScore", 0) if cvss else 0
        severity = cvss[0].get("cvssData", {}).get("baseSeverity", "") if cvss else ""
        results.append({
            "cve_id":   cve_id,
            "description": desc,
            "score":    score,
            "severity": severity,
            "published": cve.get("published", "")[:10],
            "modified":  cve.get("lastModified", "")[:10],
            "url":       f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 67. npm Registry — JavaScript Package Info (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_npm_package(package_name: str) -> Optional[Dict]:
    """
    Get npm package information.
    API: https://registry.npmjs.org — free, no key.
    """
    data = _get(f"https://registry.npmjs.org/{urllib.parse.quote(package_name, safe='@/')}")
    if not data or data.get("error"):
        return None
    latest_ver = data.get("dist-tags", {}).get("latest", "")
    latest     = data.get("versions", {}).get(latest_ver, {})
    dl_data    = _get(f"https://api.npmjs.org/downloads/point/last-month/{urllib.parse.quote(package_name, safe='@/')}")
    return {
        "name":          data.get("name", ""),
        "version":       latest_ver,
        "description":   data.get("description", ""),
        "keywords":      data.get("keywords", [])[:8],
        "author":        (data.get("author") or {}).get("name", ""),
        "license":       latest.get("license", ""),
        "homepage":      data.get("homepage", ""),
        "repository":    (data.get("repository") or {}).get("url", "").replace("git+", "").replace(".git", ""),
        "npm_url":       f"https://www.npmjs.com/package/{package_name}",
        "dependencies":  list(latest.get("dependencies", {}).keys())[:10],
        "weekly_downloads": (dl_data or {}).get("downloads", 0),
        "version_count": len(data.get("versions", {})),
    }


def search_npm(query: str, limit: int = 8) -> List[Dict]:
    """Search npm packages."""
    data = _get("https://registry.npmjs.org/-/v1/search", params={"text": query, "size": limit})
    if not data:
        return []
    return [
        {
            "name":        o.get("package", {}).get("name", ""),
            "version":     o.get("package", {}).get("version", ""),
            "description": o.get("package", {}).get("description", "")[:200],
            "keywords":    o.get("package", {}).get("keywords", [])[:5],
            "author":      (o.get("package", {}).get("author") or {}).get("name", ""),
            "npm_url":     f"https://www.npmjs.com/package/{o.get('package',{}).get('name','')}",
            "score":       round(o.get("score", {}).get("final", 0), 3),
            "downloads":   o.get("downloads", {}).get("monthly", 0),
        }
        for o in data.get("objects", [])[:limit]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 68. Bored API — Activity Suggestions (no key)
# ══════════════════════════════════════════════════════════════════════════════

BORED_TYPES = ["education", "recreational", "social", "diy", "charity",
               "cooking", "relaxation", "music", "busywork"]


def get_activity(activity_type: str = "", participants: int = 0,
                 min_price: float = 0.0, max_price: float = 1.0) -> Optional[Dict]:
    """
    Get a random activity suggestion — perfect for study breaks.
    API: https://www.boredapi.com — free, no key.
    """
    params: Dict = {}
    if activity_type and activity_type in BORED_TYPES:
        params["type"] = activity_type
    if participants > 0:
        params["participants"] = participants
    params["minprice"] = min_price
    params["maxprice"] = max_price
    data = _get("https://www.boredapi.com/api/activity", params=params)
    if not data or data.get("error"):
        return None
    return {
        "activity":     data.get("activity", ""),
        "type":         data.get("type", ""),
        "participants": data.get("participants", 1),
        "price":        data.get("price", 0),
        "link":         data.get("link", ""),
        "key":          data.get("key", ""),
        "accessibility": data.get("accessibility", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 69. Advice Slip — Random Life Advice (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_advice() -> Optional[str]:
    """
    Get a random piece of life advice.
    API: https://api.adviceslip.com — free, no key.
    """
    data = _get("https://api.adviceslip.com/advice")
    if not data:
        return None
    return data.get("slip", {}).get("advice", "")


def search_advice(query: str) -> List[str]:
    """Search for advice containing a keyword."""
    data = _get(f"https://api.adviceslip.com/advice/search/{urllib.parse.quote(query)}")
    if not data or not data.get("slips"):
        return []
    return [s.get("advice", "") for s in data.get("slips", []) if s.get("advice")][:5]


# ══════════════════════════════════════════════════════════════════════════════
# 70. CocktailDB — Cocktail Recipes (free test key "1")
# ══════════════════════════════════════════════════════════════════════════════

def search_cocktail(query: str) -> List[Dict]:
    """
    Search cocktail recipes.
    API: https://www.thecocktaildb.com — free (test key '1').
    """
    data = _get("https://www.thecocktaildb.com/api/json/v1/1/search.php",
                params={"s": query})
    if not data or not data.get("drinks"):
        return []
    results = []
    for d in (data["drinks"] or [])[:8]:
        ingredients = []
        for i in range(1, 16):
            ing  = d.get(f"strIngredient{i}", "")
            meas = d.get(f"strMeasure{i}", "")
            if ing and ing.strip():
                ingredients.append(f"{meas.strip()} {ing.strip()}".strip())
        results.append({
            "name":         d.get("strDrink", ""),
            "category":     d.get("strCategory", ""),
            "alcoholic":    d.get("strAlcoholic", ""),
            "glass":        d.get("strGlass", ""),
            "instructions": (d.get("strInstructions") or "")[:400],
            "thumbnail":    d.get("strDrinkThumb", ""),
            "ingredients":  ingredients,
            "tags":         [t.strip() for t in (d.get("strTags") or "").split(",") if t.strip()],
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 71. Open-Meteo Marine — Wave & Ocean Data (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_marine_forecast(lat: float, lon: float) -> Optional[Dict]:
    """
    Ocean/wave forecast for coastal coordinates.
    API: https://marine-api.open-meteo.com — free, no key.
    """
    data = _get("https://marine-api.open-meteo.com/v1/marine", params={
        "latitude":  lat,
        "longitude": lon,
        "current":   "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
        "hourly":    "wave_height",
        "timezone":  "auto",
    })
    if not data:
        return None
    current = data.get("current", {})
    return {
        "lat":              data.get("latitude"),
        "lon":              data.get("longitude"),
        "timezone":         data.get("timezone", ""),
        "wave_height_m":    current.get("wave_height", 0),
        "wave_direction":   current.get("wave_direction", 0),
        "wave_period_s":    current.get("wave_period", 0),
        "wind_wave_height": current.get("wind_wave_height", 0),
        "swell_height":     current.get("swell_wave_height", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 72. Affirmations.dev — Positive Affirmations (no key)
# ══════════════════════════════════════════════════════════════════════════════

def get_affirmation() -> Optional[str]:
    """
    Get a random positive affirmation for motivation.
    API: https://www.affirmations.dev — free, no key.
    """
    data = _get("https://www.affirmations.dev/")
    if not data:
        return None
    return data.get("affirmation", "")
