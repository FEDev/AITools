/**
 * sentiment.ts — sentiment tools. Mirrors ../../python/ai_trader_tools/sentiment.py.
 *
 * getFearGreedIndex: REAL, no API key — free alternative.me endpoint.
 * fetchNewsHeadlines: pluggable provider, bring your own API key.
 *
 * NOTE: this file does not include a VADER-equivalent text-sentiment function out of the
 * box — Node's ecosystem doesn't have a drop-in VADER port as battle-tested as Python's.
 * Recommended: install the `vader-sentiment` npm package yourself, or call the Python
 * analyze_text_sentiment tool via the REST API / MCP server from your Node app instead.
 */
import fetch from "node-fetch";

export async function getFearGreedIndex(limit = 1) {
  const resp = await fetch(`https://api.alternative.me/fng/?limit=${limit}`);
  if (!resp.ok) throw new Error(`alternative.me request failed: ${resp.status}`);
  const json: any = await resp.json();
  return {
    source: "alternative.me",
    readings: (json.data || []).map((d: any) => ({
      value: parseInt(d.value, 10),
      classification: d.value_classification,
      timestamp: d.timestamp,
    })),
  };
}

async function fetchNewsApi(query: string, apiKey: string, limit: number) {
  const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(query)}&sortBy=publishedAt&pageSize=${limit}&apiKey=${apiKey}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`newsapi request failed: ${resp.status}`);
  const json: any = await resp.json();
  return (json.articles || []).map((a: any) => ({ title: a.title, source: a.source?.name, publishedAt: a.publishedAt, url: a.url }));
}

async function fetchCryptoPanic(query: string, apiKey: string, limit: number) {
  const url = `https://cryptopanic.com/api/v1/posts/?auth_token=${apiKey}&currencies=${encodeURIComponent(query)}&public=true`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`cryptopanic request failed: ${resp.status}`);
  const json: any = await resp.json();
  return (json.results || []).slice(0, limit).map((p: any) => ({ title: p.title, source: p.source?.title, publishedAt: p.published_at, url: p.url }));
}

const PROVIDERS: Record<string, (q: string, k: string, l: number) => Promise<any[]>> = {
  newsapi: fetchNewsApi,
  cryptopanic: fetchCryptoPanic,
};

export async function fetchNewsHeadlines(query: string, apiKey: string, provider = "newsapi", limit = 20) {
  const fn = PROVIDERS[provider];
  if (!fn) throw new Error(`Unknown provider '${provider}'. Available: ${Object.keys(PROVIDERS).join(", ")}`);
  const headlines = await fn(query, apiKey, limit);
  return { provider, query, headlines };
}
