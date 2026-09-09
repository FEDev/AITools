"""
sentiment.py — sentiment analysis tools.

- get_fear_greed_index: REAL, no API key — hits the free alternative.me Fear & Greed API.
- analyze_text_sentiment: REAL, no API key — VADER lexicon sentiment (pip install vaderSentiment).
- fetch_news_headlines: pluggable provider interface. Bring your own API key for NewsAPI or
  CryptoPanic (or add your own provider — see PROVIDERS below).
"""
from typing import List, Optional

import requests

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
except ImportError:
    _analyzer = None


def get_fear_greed_index(limit: int = 1) -> dict:
    resp = requests.get("https://api.alternative.me/fng/", params={"limit": limit}, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return {
        "source": "alternative.me",
        "readings": [
            {"value": int(d["value"]), "classification": d["value_classification"], "timestamp": d["timestamp"]}
            for d in data
        ],
    }


def analyze_text_sentiment(texts: List[str]) -> dict:
    if _analyzer is None:
        raise ImportError("vaderSentiment is required — install with: pip install vaderSentiment")
    results = []
    total = 0.0
    for text in texts:
        scores = _analyzer.polarity_scores(text)
        results.append({"text": text, "compound": scores["compound"], "pos": scores["pos"], "neu": scores["neu"], "neg": scores["neg"]})
        total += scores["compound"]
    avg = total / len(texts) if texts else 0.0
    label = "bullish" if avg > 0.15 else "bearish" if avg < -0.15 else "neutral"
    return {"results": results, "average_compound": round(avg, 4), "label": label}


def _fetch_newsapi(query: str, api_key: str, limit: int) -> list:
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={"q": query, "sortBy": "publishedAt", "pageSize": limit, "apiKey": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    return [{"title": a["title"], "source": a["source"]["name"], "publishedAt": a["publishedAt"], "url": a["url"]} for a in articles]


def _fetch_cryptopanic(query: str, api_key: str, limit: int) -> list:
    resp = requests.get(
        "https://cryptopanic.com/api/v1/posts/",
        params={"auth_token": api_key, "currencies": query, "public": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    posts = resp.json().get("results", [])[:limit]
    return [{"title": p["title"], "source": p.get("source", {}).get("title"), "publishedAt": p["published_at"], "url": p["url"]} for p in posts]


PROVIDERS = {"newsapi": _fetch_newsapi, "cryptopanic": _fetch_cryptopanic}


def fetch_news_headlines(query: str, api_key: str, provider: str = "newsapi", limit: int = 20) -> dict:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(PROVIDERS)}. Add your own in PROVIDERS.")
    headlines = PROVIDERS[provider](query, api_key, limit)
    return {"provider": provider, "query": query, "headlines": headlines}
