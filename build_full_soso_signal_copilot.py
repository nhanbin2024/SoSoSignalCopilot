from pathlib import Path
import json
import zipfile
import shutil

ROOT = Path.cwd()
ZIP_NAME = "SoSoSignalCopilot_FULL.zip"

FILES = {}

FILES["package.json"] = r'''
{
  "name": "soso-signal-copilot-full",
  "version": "3.0.0",
  "private": true,
  "description": "SoSoValue + SoDEX live research terminal. No demo data.",
  "type": "module",
  "scripts": {
    "smoke": "node scripts/smoke-test.mjs"
  },
  "keywords": ["sosovalue", "sodex", "ssi", "ai", "crypto", "wave2", "vercel"]
}
'''

FILES["vercel.json"] = r'''
{
  "version": 2,
  "cleanUrls": true,
  "trailingSlash": false
}
'''

FILES[".gitignore"] = r'''
node_modules/
.vercel/
.env
.env.local
.env.*.local
*.log
.DS_Store
SoSoSignalCopilot_FULL.zip
'''

FILES[".env.example"] = r'''
SOSO_API_KEY=your_private_sosovalue_api_key
SOSO_BASE_URL=https://openapi.sosovalue.com/openapi/v1

# Optional exact SoSoValue paths from docs, comma-separated
SOSO_MARKET_PATHS=
SOSO_ETF_PATHS=
SOSO_NEWS_PATHS=
SOSO_SSI_PATHS=

# Optional SoDEX bases if docs change
SODEX_SPOT_BASE=
SODEX_PERPS_BASE=
'''

FILES["README.md"] = r'''
# SoSo Signal Copilot FULL

A live AI x On-Chain Finance research terminal for Wave 2.

## Data sources

- SoSoValue API for market, ETF, news, and SSI research data.
- SoDEX public API for live spot/perps market data.
- No demo data.
- No fake fallback.
- No CoinGecko.

If the SoSoValue key is invalid, the app clearly shows the real key/API error. SoDEX can still run as the live market/action layer.

## Modules

- Command Center
- Market Intelligence
- Narrative Radar
- Signal Engine
- SSI Builder
- Portfolio Risk
- API Console

## Vercel

Framework Preset: Other  
Build Command: empty  
Output Directory: empty  
Root Directory: ./

Environment Variables:

```env
SOSO_API_KEY=your_private_sosovalue_api_key
SOSO_BASE_URL=https://openapi.sosovalue.com/openapi/v1
```

Optional exact paths from SoSoValue docs:

```env
SOSO_MARKET_PATHS=/real/path
SOSO_ETF_PATHS=/real/path
SOSO_NEWS_PATHS=/real/path
SOSO_SSI_PATHS=/real/path
```

## Test

```txt
/api/health
/api/soso?resource=all
/api/sodex?resource=all
```

Research only. Not financial advice.
'''

FILES["docs/submission.md"] = r'''
# Wave 2 Submission

## Project
SoSo Signal Copilot FULL

## One-liner
An AI x On-Chain Finance research terminal that turns live SoSoValue API data and live SoDEX market data into narrative radar, scored signal cards, SSI allocation ideas, portfolio risk analysis, and exportable research plans.

## Demo flow
1. Refresh Live APIs.
2. Inspect SoSoValue + SoDEX API Console.
3. Review Market Intelligence.
4. Open Narrative Radar.
5. Review Signal Engine.
6. Build SSI allocation.
7. Analyze portfolio risk.
8. Export research plan.
9. Open SoDEX BTC/USDC.

## Note
No demo data is generated. All cards are computed only from live records that were successfully loaded.
'''

FILES["LICENSE"] = r'''
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files to deal in the Software
without restriction.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
'''

FILES["logo.svg"] = r'''
<svg width="160" height="160" viewBox="0 0 160 160" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="18" y1="12" x2="142" y2="148" gradientUnits="userSpaceOnUse"><stop stop-color="#39E8FF"/><stop offset=".52" stop-color="#9D72FF"/><stop offset="1" stop-color="#78FFB7"/></linearGradient><filter id="s" x="0" y="0" width="160" height="160" filterUnits="userSpaceOnUse"><feDropShadow dx="0" dy="18" stdDeviation="15" flood-color="#000" flood-opacity=".45"/></filter></defs>
  <rect x="16" y="18" width="128" height="124" rx="38" fill="url(#g)" filter="url(#s)"/>
  <path d="M39 84C39 58 57 38 80 38s41 20 41 46v15c0 9-7 16-16 16H55c-9 0-16-7-16-16V84Z" fill="#06101F" fill-opacity=".96"/>
  <circle cx="64" cy="81" r="10" fill="#39E8FF"/><circle cx="96" cy="81" r="10" fill="#78FFB7"/>
  <path d="M66 102c8 6 20 6 28 0" stroke="#F7FBFF" stroke-width="6" stroke-linecap="round"/>
  <path d="M80 31V14" stroke="#78FFB7" stroke-width="8" stroke-linecap="round"/><circle cx="80" cy="12" r="8" fill="#78FFB7"/>
</svg>
'''

FILES["api/health.js"] = r'''
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  return res.status(200).json({
    ok: true,
    service: "SoSo Signal Copilot FULL",
    mode: "live APIs only, no demo data",
    time: new Date().toISOString()
  });
}
'''

FILES["api/soso.js"] = r'''
const DEFAULT_BASE_URL = "https://openapi.sosovalue.com/openapi/v1";

const DEFAULT_PATHS = {
  market: ["/market/overview", "/coins/markets", "/crypto/market", "/currency/market", "/market/tickers", "/coins/list", "/token/market", "/tokens/market"],
  etf: ["/etf/flow", "/etf/net-inflow", "/etf/historical", "/bitcoin/spot-etf", "/btc/spot-etf", "/ethereum/spot-etf", "/eth/spot-etf"],
  news: ["/news", "/news/list", "/insight/news", "/articles", "/research/news", "/feeds/news"],
  ssi: ["/ssi/assets", "/indices/ssi/assets", "/index/assets", "/ssi", "/index/list", "/indices/list"]
};

const ENV_KEYS = {
  market: ["SOSO_MARKET_PATHS", "SOSO_MARKET_PATH", "SOSOVALUE_MARKET_PATHS"],
  etf: ["SOSO_ETF_PATHS", "SOSO_ETF_PATH", "SOSOVALUE_ETF_PATHS"],
  news: ["SOSO_NEWS_PATHS", "SOSO_NEWS_PATH", "SOSOVALUE_NEWS_PATHS"],
  ssi: ["SOSO_SSI_PATHS", "SOSO_SSI_PATH", "SOSOVALUE_SSI_PATHS"]
};

function clean(v = "") {
  return String(v).trim().replace(/^['"]|['"]$/g, "");
}

function apiKey() {
  return clean(process.env.SOSO_API_KEY || process.env.SOSOVALUE_API_KEY || "");
}

function baseUrl() {
  return clean(process.env.SOSO_BASE_URL || process.env.SOSOVALUE_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, "");
}

function fingerprint(key) {
  if (!key) return "missing";
  return `${key.slice(0, 4)}...${key.slice(-4)} (${key.length} chars)`;
}

function splitPaths(v) {
  return clean(v).split(",").map((x) => x.trim()).filter(Boolean);
}

function paths(resource) {
  const envPaths = (ENV_KEYS[resource] || []).flatMap((key) => splitPaths(process.env[key]));
  return [...new Set([...envPaths, ...(DEFAULT_PATHS[resource] || [])])];
}

function urlFor(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${baseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function arrays(value, depth = 0, out = []) {
  if (depth > 8 || value == null) return out;
  if (Array.isArray(value)) {
    if (value.some((x) => x && typeof x === "object")) out.push(value);
    for (const item of value.slice(0, 12)) arrays(item, depth + 1, out);
    return out;
  }
  if (typeof value === "object") {
    for (const key of ["data", "result", "items", "list", "records", "rows", "content"]) {
      if (value[key] !== undefined) arrays(value[key], depth + 1, out);
    }
    for (const child of Object.values(value)) arrays(child, depth + 1, out);
  }
  return out;
}

function extractItems(payload) {
  const best = arrays(payload).map((a) => a.filter((x) => x && typeof x === "object")).sort((a, b) => b.length - a.length)[0] || [];
  const seen = new Set();
  const items = [];
  for (const item of best) {
    const key = JSON.stringify(item).slice(0, 600);
    if (!seen.has(key)) {
      seen.add(key);
      items.push(item);
    }
  }
  return items.slice(0, 100);
}

function preview(payload) {
  const text = JSON.stringify(payload, null, 2);
  return text.length > 5500 ? `${text.slice(0, 5500)}\n...trimmed` : text;
}

async function call(path) {
  const key = apiKey();
  const url = urlFor(path);
  const started = Date.now();

  if (!key) {
    return { ok: false, source: "sosovalue-api-error", status: 0, path, url, latencyMs: 0, updatedAt: new Date().toISOString(), itemCount: 0, items: [], keyFingerprint: "missing", warning: "Missing SOSO_API_KEY in Vercel Environment Variables." };
  }

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { accept: "application/json", "x-soso-api-key": key, "X-SOSO-API-KEY": key }
    });
    const text = await response.text();
    let payload;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { text }; }
    const items = response.ok ? extractItems(payload) : [];
    const live = response.ok && items.length > 0;
    return {
      ok: live,
      source: live ? "sosovalue-api" : response.ok ? "sosovalue-api-empty" : "sosovalue-api-error",
      status: response.status,
      path,
      url,
      latencyMs: Date.now() - started,
      updatedAt: new Date().toISOString(),
      itemCount: items.length,
      items,
      keyFingerprint: fingerprint(key),
      rawPreview: preview(payload),
      errorPreview: response.ok ? "" : String(text).slice(0, 1800),
      warning: response.ok && !items.length ? "SoSoValue responded, but no list-like records were found at this endpoint." : ""
    };
  } catch (error) {
    return { ok: false, source: "sosovalue-api-error", status: 0, path, url, latencyMs: Date.now() - started, updatedAt: new Date().toISOString(), itemCount: 0, items: [], keyFingerprint: fingerprint(key), warning: error.message };
  }
}

async function fetchResource(resource) {
  const tried = [];
  for (const p of paths(resource)) {
    const r = await call(p);
    tried.push({ path: p, status: r.status, ok: r.ok, source: r.source, itemCount: r.itemCount, warning: r.warning || r.errorPreview || "" });
    if (r.source === "sosovalue-api") return { resource, ...r, pathsTried: tried };
  }
  return { resource, ok: false, source: "sosovalue-api-error", updatedAt: new Date().toISOString(), itemCount: 0, items: [], keyFingerprint: fingerprint(apiKey()), warning: "No SoSoValue endpoint returned live records. Check API key first, then set exact SOSO_*_PATHS from docs.", pathsTried: tried };
}

async function explore() {
  const out = {};
  for (const resource of ["market", "etf", "news", "ssi"]) {
    out[resource] = [];
    for (const p of paths(resource)) out[resource].push(await call(p));
  }
  return out;
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();

  const resource = String(req.query.resource || "all").toLowerCase();
  const customPath = req.query.path ? String(req.query.path) : "";

  try {
    if (customPath) {
      const custom = await call(customPath);
      return res.status(200).json({ ok: custom.source === "sosovalue-api", hasApiKey: Boolean(apiKey()), keyFingerprint: fingerprint(apiKey()), baseUrl: baseUrl(), custom });
    }
    if (resource === "explore") {
      const data = await explore();
      return res.status(200).json({ ok: true, hasApiKey: Boolean(apiKey()), keyFingerprint: fingerprint(apiKey()), baseUrl: baseUrl(), explore: data });
    }
    if (resource === "all") {
      const [market, etf, news, ssi] = await Promise.all([fetchResource("market"), fetchResource("etf"), fetchResource("news"), fetchResource("ssi")]);
      const liveBlocks = [market, etf, news, ssi].filter((x) => x.source === "sosovalue-api").length;
      return res.status(200).json({ ok: liveBlocks > 0, hasApiKey: Boolean(apiKey()), keyFingerprint: fingerprint(apiKey()), baseUrl: baseUrl(), liveBlocks, market, etf, news, ssi });
    }
    if (!["market", "etf", "news", "ssi"].includes(resource)) return res.status(400).json({ ok: false, error: "Use resource=all, market, etf, news, ssi, explore, or path=/custom/endpoint." });
    const data = await fetchResource(resource);
    return res.status(200).json({ ok: data.source === "sosovalue-api", hasApiKey: Boolean(apiKey()), keyFingerprint: fingerprint(apiKey()), baseUrl: baseUrl(), [resource]: data });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}
'''

FILES["api/sodex.js"] = r'''
const ROUTES = {
  symbols: "/markets/symbols",
  coins: "/markets/coins",
  tickers: "/markets/tickers",
  miniTickers: "/markets/miniTickers",
  bookTickers: "/markets/bookTickers",
  markPrices: "/markets/mark-prices"
};

const DEFAULT_BASES = {
  spot: ["https://mainnet-gw.sodex.dev/api/v1/spot", "https://mainnet-gw.sodex.com/api/v1/spot", "https://api.sodex.com/api/v1/spot"],
  perps: ["https://mainnet-gw.sodex.dev/api/v1/perps", "https://mainnet-gw.sodex.com/api/v1/perps", "https://api.sodex.com/api/v1/perps"]
};

function clean(v = "") { return String(v).trim().replace(/^['"]|['"]$/g, ""); }
function bases(market) {
  const env = market === "perps" ? clean(process.env.SODEX_PERPS_BASE) : clean(process.env.SODEX_SPOT_BASE);
  return [...new Set([env, ...(DEFAULT_BASES[market] || [])].filter(Boolean).map((x) => x.replace(/\/$/, "")))];
}

function arrays(value, depth = 0, out = []) {
  if (depth > 7 || value == null) return out;
  if (Array.isArray(value)) {
    if (value.some((x) => x && typeof x === "object")) out.push(value);
    for (const item of value.slice(0, 10)) arrays(item, depth + 1, out);
    return out;
  }
  if (typeof value === "object") {
    for (const key of ["data", "result", "items", "list", "records", "rows"]) if (value[key] !== undefined) arrays(value[key], depth + 1, out);
    for (const child of Object.values(value)) arrays(child, depth + 1, out);
  }
  return out;
}

function extractItems(payload) {
  const best = arrays(payload).map((a) => a.filter((x) => x && typeof x === "object")).sort((a, b) => b.length - a.length)[0] || [];
  const seen = new Set();
  const items = [];
  for (const item of best) {
    const key = JSON.stringify(item).slice(0, 600);
    if (!seen.has(key)) { seen.add(key); items.push(item); }
  }
  return items.slice(0, 140);
}

function preview(payload) {
  const text = JSON.stringify(payload, null, 2);
  return text.length > 5500 ? `${text.slice(0, 5500)}\n...trimmed` : text;
}

async function callOne({ market = "spot", type = "tickers", path = "", base = "" }) {
  const route = path || ROUTES[type] || ROUTES.tickers;
  const url = /^https?:\/\//i.test(route) ? route : `${base}${route.startsWith("/") ? route : `/${route}`}`;
  const started = Date.now();
  try {
    const response = await fetch(url, { method: "GET", headers: { accept: "application/json" } });
    const text = await response.text();
    let payload;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { text }; }
    const items = response.ok ? extractItems(payload) : [];
    const live = response.ok && items.length > 0;
    return { ok: live, source: live ? "sodex-api" : response.ok ? "sodex-api-empty" : "sodex-api-error", market, type, path: route, base, url, status: response.status, latencyMs: Date.now() - started, updatedAt: new Date().toISOString(), itemCount: items.length, items, rawPreview: preview(payload), warning: response.ok && !items.length ? "SoDEX responded, but no list-like records were found." : "", errorPreview: response.ok ? "" : text.slice(0, 1800) };
  } catch (error) {
    return { ok: false, source: "sodex-api-error", market, type, path: route, base, url, status: 0, latencyMs: Date.now() - started, updatedAt: new Date().toISOString(), itemCount: 0, items: [], warning: error.message };
  }
}

async function callSodex({ market = "spot", type = "tickers", path = "" }) {
  const tried = [];
  for (const base of bases(market)) {
    const r = await callOne({ market, type, path, base });
    tried.push({ base, path: r.path, status: r.status, source: r.source, itemCount: r.itemCount, warning: r.warning || r.errorPreview || "" });
    if (r.source === "sodex-api") return { ...r, basesTried: tried };
  }
  return { ok: false, source: "sodex-api-error", market, type, path: path || ROUTES[type] || ROUTES.tickers, status: 0, updatedAt: new Date().toISOString(), itemCount: 0, items: [], warning: "No SoDEX endpoint returned live records. Check SoDEX API base/route in API Console.", basesTried: tried };
}

async function all() {
  const [spotTickers, spotBook, spotSymbols, perpsTickers, perpsMarks, perpsSymbols] = await Promise.all([
    callSodex({ market: "spot", type: "tickers" }),
    callSodex({ market: "spot", type: "bookTickers" }),
    callSodex({ market: "spot", type: "symbols" }),
    callSodex({ market: "perps", type: "tickers" }),
    callSodex({ market: "perps", type: "markPrices" }),
    callSodex({ market: "perps", type: "symbols" })
  ]);
  const blocks = { spotTickers, spotBook, spotSymbols, perpsTickers, perpsMarks, perpsSymbols };
  const liveBlocks = Object.values(blocks).filter((x) => x.source === "sodex-api").length;
  const items = [...spotTickers.items.map((x) => ({ ...x, __venue: "SoDEX Spot" })), ...spotBook.items.map((x) => ({ ...x, __venue: "SoDEX Book" })), ...perpsTickers.items.map((x) => ({ ...x, __venue: "SoDEX Perps" })), ...perpsMarks.items.map((x) => ({ ...x, __venue: "SoDEX Mark" }))];
  return { ok: liveBlocks > 0, source: liveBlocks > 0 ? "sodex-api" : "sodex-api-error", updatedAt: new Date().toISOString(), liveBlocks, itemCount: items.length, items: items.slice(0, 180), ...blocks };
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  try {
    const resource = String(req.query.resource || "").toLowerCase();
    const market = String(req.query.market || "spot").toLowerCase();
    const type = String(req.query.type || "tickers");
    const path = req.query.path ? String(req.query.path) : "";
    if (resource === "all") {
      const data = await all();
      return res.status(200).json({ ok: data.ok, bases: { spot: bases("spot"), perps: bases("perps") }, data });
    }
    if (!["spot", "perps"].includes(market)) return res.status(400).json({ ok: false, error: "market must be spot or perps" });
    const data = await callSodex({ market, type, path });
    return res.status(200).json({ ok: data.source === "sodex-api", bases: { spot: bases("spot"), perps: bases("perps") }, data });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}
'''

FILES["api/ai.js"] = r'''
function textOf(v) {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number") return String(v);
  if (Array.isArray(v)) return v.map(textOf).join(" ");
  if (typeof v === "object") return Object.values(v).map(textOf).join(" ");
  return "";
}
function num(v) {
  if (typeof v === "number") return v;
  if (typeof v === "string") {
    const n = Number(v.replace(/[$,%+,]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}
function labelOf(x) { return x.symbol || x.ticker || x.name || x.asset || x.title || x.coin || x.currency || x.symbolName || x.pair || "Live record"; }
function items(data, key) {
  const block = data?.[key];
  if (!block || !["sosovalue-api", "sodex-api"].includes(block.source)) return [];
  return Array.isArray(block.items) ? block.items.map((x) => ({ ...x, __module: key, __apiSource: block.source })) : [];
}
function allItems(data) { return ["sosoMarket", "sodexMarket", "etf", "news", "ssi"].flatMap((k) => items(data, k)); }
function radar(data) {
  const dict = { ETF: ["etf", "inflow", "outflow", "fund", "spot etf", "net flow"], BTC: ["btc", "bitcoin", "vbtc"], ETH: ["eth", "ethereum", "veth"], SOL: ["sol", "solana"], DeFi: ["defi", "dex", "lend", "yield", "liquidity", "swap"], Meme: ["meme", "doge", "shib", "pepe"], RWA: ["rwa", "real world", "treasury", "tokenized"], AI: [" ai ", "artificial intelligence", "agent", "compute"], Macro: ["fed", "rate", "inflation", "macro", "dollar", "cpi"], SSI: ["ssi", "index", "basket", "mag7", "defi.ssi", "meme.ssi"], SoDEX: ["sodex", "spot", "perps", "orderbook", "vbtc", "vusdc"] };
  const blobs = allItems(data).map((x) => textOf(x).toLowerCase());
  return Object.entries(dict).map(([name, words]) => {
    let hits = 0;
    for (const blob of blobs) for (const word of words) if (blob.includes(word)) hits += 1;
    const heat = Math.min(100, Math.round(hits * 12 + (hits ? 24 : 0)));
    return { name, heat, hits, state: heat >= 75 ? "High Conviction" : heat >= 45 ? "Active" : heat > 0 ? "Emerging" : "Quiet" };
  }).sort((a, b) => b.heat - a.heat);
}
function changeOf(x) { return num(x.change24h ?? x.change ?? x.priceChangePercent ?? x.priceChangeRate ?? x.percentChange ?? x.changePercent ?? x.chg); }
function priceOf(x) { return num(x.lastPrice ?? x.price ?? x.close ?? x.markPrice ?? x.indexPrice ?? x.last ?? x.midPrice); }
function signalCards(data) {
  const records = allItems(data);
  if (!records.length) return [];
  const market = [...items(data, "sosoMarket"), ...items(data, "sodexMarket")];
  const etf = items(data, "etf");
  const news = items(data, "news");
  const ssi = items(data, "ssi");
  const changes = market.map(changeOf).filter((x) => Number.isFinite(x) && x !== 0);
  const avgChange = changes.length ? changes.reduce((s, x) => s + Math.max(-25, Math.min(25, x)), 0) / changes.length : 0;
  const priced = market.filter((x) => priceOf(x) > 0).length;
  const etfFlow = etf.reduce((s, x) => s + num(x.netFlow ?? x.net_inflow ?? x.flow ?? x.value ?? x.amount ?? x.totalNetInflow), 0);
  const positive = news.filter((x) => /positive|bull|inflow|rise|gain|surge|up|approval|record/i.test(textOf(x))).length;
  const negative = news.filter((x) => /negative|bear|outflow|fall|drop|risk|hack|lawsuit/i.test(textOf(x))).length;
  const r = radar(data);
  const top = r[0] || { name: "Market", heat: 0, hits: 0, state: "Quiet" };
  const topSsi = ssi.slice().sort((a, b) => changeOf(b) - changeOf(a))[0];
  const score = Math.round(Math.max(0, Math.min(100, 45 + avgChange * 2 + (priced ? 16 : 0) + (etfFlow > 0 ? 14 : etfFlow < 0 ? -12 : 0) + positive * 4 - negative * 5)));
  const cards = [
    { title: "Live Market Momentum", source: items(data, "sodexMarket").length ? "SoDEX + SoSoValue" : "SoSoValue", score, confidence: score >= 78 ? "High" : score >= 55 ? "Medium" : "Low", evidence: [`Live market records: ${market.length}`, `Priced records: ${priced}`, `Average change metric: ${avgChange.toFixed(2)}`, `ETF flow aggregate: ${etfFlow || "not available"}`], invalidation: "Momentum weakens, liquidity records disappear, or ETF/news risk increases.", action: "Create a watchlist plan, then open the related SoDEX market only after confirmation." },
    { title: `${top.name} Narrative Radar`, source: "Local engine over live records", score: top.heat, confidence: top.heat >= 75 ? "High" : top.heat >= 45 ? "Medium" : "Low", evidence: [`Narrative heat: ${top.heat}/100`, `Keyword hits: ${top.hits}`, `State: ${top.state}`], invalidation: "Narrative heat drops below 35 or conflicting live records dominate.", action: "Track related assets, compare SSI exposure, and export a research plan." }
  ];
  if (topSsi) {
    const c = changeOf(topSsi);
    cards.push({ title: `${labelOf(topSsi)} SSI Research Signal`, source: "SoSoValue SSI", score: Math.round(Math.max(10, Math.min(95, 55 + c * 6))), confidence: "Medium", evidence: [`Top SSI candidate: ${labelOf(topSsi)}`, `Change metric: ${c || "not available"}`, "Computed from live SoSoValue SSI records."], invalidation: "SSI trend weakens or basket exposure no longer matches the selected risk profile.", action: "Use SSI Builder to create a diversified research allocation." });
  }
  return cards;
}
function allocation(data, profile = "balanced") {
  const ssi = items(data, "ssi");
  if (!ssi.length) return { profile, allocations: [], note: "No live SSI records loaded. Fix SoSoValue key/path to activate SSI Builder." };
  const names = ssi.slice(0, 5).map(labelOf);
  const presets = { conservative: [45, 25, 15, 10, 5], balanced: [35, 25, 20, 12, 8], aggressive: [25, 25, 20, 18, 12], hunter: [20, 20, 20, 20, 20] };
  const weights = presets[profile] || presets.balanced;
  return { profile, allocations: names.map((name, i) => ({ name, weight: weights[i] || 0 })).filter((x) => x.weight > 0), note: "Research-only allocation computed locally from live SoSoValue SSI records." };
}
function risk(holdings = []) {
  const clean = holdings.map((h) => ({ asset: String(h.asset || "").trim(), weight: num(h.weight) })).filter((h) => h.asset && h.weight > 0);
  if (!clean.length) return { score: 0, concentration: "No holdings", ssiExposure: 0, suggestion: "Add manual holdings to analyze portfolio risk." };
  const total = clean.reduce((s, h) => s + h.weight, 0) || 1;
  const normalized = clean.map((h) => ({ ...h, weight: h.weight / total * 100 }));
  const maxWeight = normalized.reduce((m, h) => Math.max(m, h.weight), 0);
  const memeWeight = normalized.filter((h) => /meme|pepe|doge|shib/i.test(h.asset)).reduce((s, h) => s + h.weight, 0);
  const ssiWeight = normalized.filter((h) => /ssi|index/i.test(h.asset)).reduce((s, h) => s + h.weight, 0);
  const score = Math.round(Math.min(100, 35 + maxWeight * 0.45 + memeWeight * 0.35 - Math.min(ssiWeight, 35) * 0.2));
  return { score, concentration: maxWeight >= 50 ? "High" : maxWeight >= 30 ? "Medium" : "Low", ssiExposure: Math.round(ssiWeight), suggestion: score >= 75 ? "Reduce concentration and increase diversified SSI/index exposure." : score >= 50 ? "Keep position sizes controlled and monitor narrative concentration." : "Portfolio looks relatively diversified for a research plan." };
}
async function readJson(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString("utf8");
  return raw ? JSON.parse(raw) : {};
}
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ ok: false, error: "Method not allowed" });
  try {
    const body = await readJson(req);
    const data = body.data || {};
    const liveModules = ["sosoMarket", "sodexMarket", "etf", "news", "ssi"].filter((k) => ["sosovalue-api", "sodex-api"].includes(data?.[k]?.source)).length;
    const nr = radar(data);
    return res.status(200).json({ ok: true, liveModules, brief: liveModules ? `Live data loaded across ${liveModules}/5 modules. Top narrative: ${nr[0]?.name || "n/a"}.` : "No live records loaded. Open API Console to inspect SoSoValue and SoDEX status.", radar: nr, signals: signalCards(data), allocation: allocation(data, body.profile || "balanced"), portfolioRisk: risk(body.holdings || []) });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}
'''

FILES["index.html"] = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SoSo Signal Copilot FULL</title>
  <meta name="description" content="Live SoSoValue and SoDEX AI research terminal" />
  <link rel="icon" href="/logo.svg" />
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <div class="bg-orb orb-a"></div><div class="bg-orb orb-b"></div><div class="bg-orb orb-c"></div><div class="bg-grid"></div><div class="noise"></div>
  <aside class="side glass">
    <div class="brand"><img src="/logo.svg" alt="logo" /><div><small>SoSo × SoDEX</small><h1>Signal Copilot</h1></div></div>
    <div class="guide"><span></span><p><b>Guide:</b> Refresh APIs, inspect console, then Radar → Signals → SSI → Portfolio.</p></div>
    <nav>
      <button class="nav active" data-tab="command">Command Center</button><button class="nav" data-tab="market">Market Intelligence</button><button class="nav" data-tab="radar">Narrative Radar</button><button class="nav" data-tab="signals">Signal Engine</button><button class="nav" data-tab="ssi">SSI Builder</button><button class="nav" data-tab="portfolio">Portfolio Risk</button><button class="nav" data-tab="api">API Console</button>
    </nav>
    <div class="side-links"><a href="https://sosovalue.com/join/9RZ4FYNK" target="_blank" rel="noreferrer">SoSoValue <em>Research</em></a><a href="https://sodex.com/" target="_blank" rel="noreferrer">SoDEX <em>Exchange</em></a><a href="https://sodex.com/trade/spot/BTC_USDC" target="_blank" rel="noreferrer">BTC/USDC <em>Spot</em></a><a href="https://ssi.sosovalue.com/vi/assets" target="_blank" rel="noreferrer">SSI Assets <em>Index</em></a></div>
    <p class="disclaimer">Research only. Not financial advice.</p>
  </aside>
  <main class="app">
    <header class="hero glass"><div><p class="eyebrow">AI × On-Chain Finance × SoSoValue × SoDEX</p><h2>Research Terminal for live crypto signals.</h2><p class="hero-copy">No demo data. SoSoValue is the research layer. SoDEX is the live market/action layer. API errors are visible instead of hidden.</p><div class="actions"><button id="refresh" class="primary">Refresh Live APIs</button><button id="exportMd">Export Research Plan</button><button id="openApi">Inspect API</button></div></div><div class="hero-right"><div class="status-orb"><div class="ring ring-1"></div><div class="ring ring-2"></div><strong id="liveScore">0/5</strong><span>Live Modules</span></div><div class="mini-status"><span id="sosoBadge" class="badge wait">SoSo checking</span><span id="sodexBadge" class="badge wait">SoDEX checking</span></div></div></header>
    <section class="stats"><div class="stat glass-soft"><small>SoSo Market</small><b id="sosoMarketCount">0</b></div><div class="stat glass-soft"><small>SoDEX Market</small><b id="sodexMarketCount">0</b></div><div class="stat glass-soft"><small>ETF Records</small><b id="etfCount">0</b></div><div class="stat glass-soft"><small>News Records</small><b id="newsCount">0</b></div><div class="stat glass-soft"><small>SSI Records</small><b id="ssiCount">0</b></div></section>
    <section id="command" class="tab show"><div class="panel glass"><div class="head"><div><p class="eyebrow">Command Center</p><h3>Daily Research Brief</h3></div><span id="apiBadge" class="badge wait">Loading</span></div><p id="brief" class="brief">Loading live APIs...</p><div id="topSignals" class="signal-grid"></div></div></section>
    <section id="market" class="tab"><div class="panel glass"><p class="eyebrow">Market Intelligence</p><h3>Live SoDEX + SoSoValue Market Records</h3><div class="market-panels"><div><h4>SoDEX Spot / Perps</h4><div id="sodexRows" class="rows"></div></div><div><h4>SoSoValue Market</h4><div id="sosoMarketRows" class="rows"></div></div></div></div></section>
    <section id="radar" class="tab"><div class="panel glass"><p class="eyebrow">Narrative Radar</p><h3>Heatmap computed from live records</h3><div id="radarList" class="radar"></div></div></section>
    <section id="signals" class="tab"><div class="panel glass"><p class="eyebrow">Signal Engine</p><h3>Scored Research Cards</h3><div id="signalList" class="signal-grid"></div></div></section>
    <section id="ssi" class="tab"><div class="panel glass"><p class="eyebrow">SSI Builder</p><h3>Allocation from live SSI records</h3><select id="profile"><option value="conservative">Conservative</option><option value="balanced" selected>Balanced</option><option value="aggressive">Aggressive</option><option value="hunter">Narrative Hunter</option></select><div id="allocation" class="allocation"></div></div></section>
    <section id="portfolio" class="tab"><div class="panel glass"><p class="eyebrow">Portfolio Risk</p><h3>Manual holdings, research-only scoring</h3><textarea id="holdings" placeholder="BTC 40&#10;ETH 25&#10;MAG7.ssi 25&#10;MEME.ssi 10"></textarea><button id="analyzePortfolio" class="primary">Analyze Risk</button><div id="riskBox" class="risk-box"></div></div></section>
    <section id="api" class="tab"><div class="panel glass"><div class="head"><div><p class="eyebrow">API Console</p><h3>Real API status</h3></div><div class="api-actions"><button id="exploreSoso">Explore SoSoValue</button><button id="exploreSodex">Explore SoDEX</button></div></div><p class="brief">SoSoValue requires <b>SOSO_API_KEY</b>. SoDEX market endpoints are public. No demo data is generated.</p><div class="console-grid"><div><label>SoSoValue custom path</label><input id="sosoPath" placeholder="/paste/official/soso/endpoint/path" /><button id="testSosoPath">Test SoSo Path</button></div><div><label>SoDEX custom path</label><input id="sodexPath" placeholder="/markets/tickers" /><select id="sodexMarket"><option value="spot">spot</option><option value="perps">perps</option></select><button id="testSodexPath">Test SoDEX Path</button></div></div><pre id="apiLog">Waiting...</pre></div></section>
    <section class="data-grid"><div class="panel glass"><p class="eyebrow">ETF Records</p><div id="etfRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">News Records</p><div id="newsRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">SSI Records</p><div id="ssiRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">API Diagnostics</p><div id="diagnostics" class="rows"></div></div></section>
  </main>
  <div id="toast" class="toast"></div><script src="/app.js" type="module"></script>
</body>
</html>
'''

FILES["styles.css"] = r'''
:root{--panel:rgba(14,22,45,.74);--panel2:rgba(30,42,82,.48);--line:rgba(255,255,255,.13);--text:#f7fbff;--muted:#9aa8ce;--cyan:#39e8ff;--violet:#9d72ff;--green:#78ffb7;--red:#ff6d8d;--gold:#ffd166;--shadow:0 30px 100px rgba(0,0,0,.36)}*{box-sizing:border-box}body{margin:0;min-height:100vh;color:var(--text);font-family:Inter,ui-sans-serif,system-ui,Segoe UI,sans-serif;background:radial-gradient(circle at 15% 12%,rgba(57,232,255,.18),transparent 28%),radial-gradient(circle at 86% 12%,rgba(157,114,255,.24),transparent 30%),radial-gradient(circle at 60% 90%,rgba(120,255,183,.08),transparent 28%),linear-gradient(135deg,#050713,#0a1028 52%,#12173a);overflow-x:hidden}button,input,select,textarea{font:inherit}.bg-orb{position:fixed;border-radius:999px;filter:blur(28px);pointer-events:none;animation:float 12s ease-in-out infinite;opacity:.7}.orb-a{width:360px;height:360px;left:-120px;top:18%;background:rgba(57,232,255,.16)}.orb-b{width:480px;height:480px;right:-160px;bottom:-40px;background:rgba(157,114,255,.16);animation-delay:-4s}.orb-c{width:260px;height:260px;left:42%;top:-80px;background:rgba(120,255,183,.08);animation-delay:-7s}.bg-grid{position:fixed;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,#000,transparent 90%);pointer-events:none}.noise{position:fixed;inset:0;opacity:.06;pointer-events:none;background-image:repeating-radial-gradient(circle at 0 0,#fff 0,#fff 1px,transparent 1px,transparent 7px)}@keyframes float{50%{transform:translateY(-30px) scale(1.05)}}.glass{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);backdrop-filter:blur(18px)}.glass-soft{background:var(--panel2);border:1px solid var(--line);backdrop-filter:blur(14px)}.side{position:fixed;left:16px;top:16px;bottom:16px;width:292px;border-radius:32px;padding:20px;display:flex;flex-direction:column;gap:14px;z-index:4}.brand{display:flex;gap:14px;align-items:center;margin-bottom:8px}.brand img{width:60px;height:60px;border-radius:20px;animation:mascot 3.4s ease-in-out infinite}@keyframes mascot{50%{transform:translateY(-5px) rotate(2deg);filter:brightness(1.15)}}.brand small,.eyebrow{color:var(--cyan);text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:900;margin:0 0 6px}.brand h1{font-size:20px;line-height:1.05;margin:0}.guide{position:relative;border:1px solid rgba(57,232,255,.18);background:linear-gradient(135deg,rgba(57,232,255,.1),rgba(157,114,255,.1));border-radius:22px;padding:14px;color:var(--muted);line-height:1.45}.guide span{position:absolute;right:14px;top:14px;width:9px;height:9px;border-radius:99px;background:var(--green);box-shadow:0 0 0 0 rgba(120,255,183,.6);animation:ping 1.6s infinite}@keyframes ping{70%{box-shadow:0 0 0 13px rgba(120,255,183,0)}}.guide p{margin:0;font-size:13px}nav{display:grid;gap:9px}.nav,button{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);border-radius:16px;padding:12px 14px;cursor:pointer;transition:.2s}.nav{text-align:left;font-weight:750}.nav:hover,.nav.active,button:hover{transform:translateY(-1px);border-color:rgba(57,232,255,.45);background:rgba(57,232,255,.12)}.primary{background:linear-gradient(135deg,var(--cyan),var(--violet));font-weight:900;color:#fff}.side-links{margin-top:auto;display:grid;gap:8px}.side-links a{display:flex;justify-content:space-between;gap:12px;color:var(--text);text-decoration:none;border:1px solid var(--line);background:rgba(255,255,255,.045);padding:11px 12px;border-radius:15px}.side-links em{color:var(--muted);font-style:normal;font-size:12px}.disclaimer{color:var(--muted);font-size:12px;margin:0}.app{margin-left:324px;padding:16px;display:grid;gap:18px;position:relative;z-index:2}.hero{border-radius:34px;padding:clamp(24px,4vw,42px);display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:28px;align-items:center;position:relative;overflow:hidden}.hero:before{content:"";position:absolute;inset:-2px;background:linear-gradient(120deg,rgba(57,232,255,.13),transparent 36%,rgba(157,114,255,.14)),radial-gradient(circle at 78% 20%,rgba(120,255,183,.1),transparent 24%);pointer-events:none}.hero>*{position:relative}.hero h2{font-size:clamp(36px,5.5vw,76px);line-height:.92;letter-spacing:-.065em;margin:4px 0 14px}.hero-copy{color:var(--muted);max-width:860px;line-height:1.7}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}.hero-right{display:grid;gap:12px}.status-orb{height:236px;border-radius:30px;background:rgba(255,255,255,.05);border:1px solid var(--line);display:grid;place-items:center;position:relative;overflow:hidden}.ring{position:absolute;border-radius:50%;animation:spin 8s linear infinite}.ring-1{width:158px;height:158px;border:1px solid rgba(57,232,255,.46);border-top-color:var(--violet)}.ring-2{width:112px;height:112px;border:12px solid rgba(255,255,255,.06);border-top-color:var(--green);animation-duration:5s;animation-direction:reverse}@keyframes spin{to{transform:rotate(360deg)}}.status-orb strong{font-size:46px;font-weight:1000;z-index:1}.status-orb span{color:var(--muted);margin-top:70px;z-index:1}.mini-status{display:grid;grid-template-columns:1fr 1fr;gap:10px}.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}.stat{border-radius:24px;padding:18px}.stat small{color:var(--muted)}.stat b{display:block;font-size:34px;margin-top:8px}.tab{display:none}.tab.show{display:block}.panel{border-radius:30px;padding:22px}.head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}h3{font-size:24px;margin:0 0 14px}h4{margin:10px 0}.badge{display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:999px;padding:8px 12px;font-size:13px;font-weight:900}.badge.good{color:var(--green);background:rgba(120,255,183,.1);border-color:rgba(120,255,183,.25)}.badge.bad{color:var(--red);background:rgba(255,109,141,.1);border-color:rgba(255,109,141,.25)}.badge.wait{color:var(--gold);background:rgba(255,209,102,.1);border-color:rgba(255,209,102,.25)}.brief{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:18px;padding:16px;color:var(--muted);line-height:1.65}.signal-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.signal{border:1px solid var(--line);background:linear-gradient(180deg,rgba(255,255,255,.085),rgba(255,255,255,.035));border-radius:24px;padding:16px;min-height:285px;display:flex;flex-direction:column;gap:8px;animation:rise .45s ease both}.score{font-size:34px;font-weight:1000;color:var(--green)}.signal h4{margin:0;font-size:18px}.signal p,.signal li{color:var(--muted);font-size:13px;line-height:1.55}.signal ul{margin:0;padding-left:18px}.radar,.allocation,.rows{display:grid;gap:10px}.radar-row,.allocation-row,.row,.risk-card{border:1px solid var(--line);background:rgba(255,255,255,.045);border-radius:17px;padding:12px}.radar-row,.allocation-row{display:grid;grid-template-columns:150px 1fr 100px;gap:12px;align-items:center}.bar{height:14px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--violet),var(--green));border-radius:999px}.data-grid,.market-panels,.console-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.row{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start}.row small{display:block;color:var(--muted);margin-top:4px;line-height:1.45;word-break:break-word}.row strong{color:var(--green)}input,select,textarea{width:100%;border:1px solid var(--line);background:rgba(255,255,255,.07);color:var(--text);border-radius:16px;padding:12px;margin:8px 0 12px;outline:none}textarea{min-height:170px;resize:vertical}pre{white-space:pre-wrap;max-height:560px;overflow:auto;background:#050813;border:1px solid var(--line);border-radius:18px;padding:16px;color:#c9d7ff}.api-actions{display:flex;gap:10px;flex-wrap:wrap}.toast{position:fixed;right:24px;bottom:24px;opacity:0;transform:translateY(12px);transition:.25s;z-index:9;background:rgba(14,22,45,.96);border:1px solid var(--line);border-radius:16px;padding:12px 14px;box-shadow:var(--shadow)}.toast.show{opacity:1;transform:translateY(0)}@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}@media(max-width:1180px){.side{position:relative;left:auto;top:auto;bottom:auto;width:auto;margin:16px}.app{margin-left:0}.hero,.stats,.signal-grid,.data-grid,.market-panels,.console-grid{grid-template-columns:1fr}.radar-row,.allocation-row{grid-template-columns:1fr}}
'''

FILES["app.js"] = r'''
const state = { data: null, sosoPayload: null, sodexPayload: null, ai: null };
const $ = (id) => document.getElementById(id);
function toast(msg){ const el=$("toast"); el.textContent=msg; el.classList.add("show"); setTimeout(()=>el.classList.remove("show"),2600); }
function esc(v){ return String(v ?? "").replace(/[&<>'"]/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;" }[c])); }
function label(x){ return x.symbol || x.ticker || x.name || x.asset || x.title || x.coin || x.currency || x.symbolName || x.pair || "Live record"; }
function value(x){ return x.lastPrice ?? x.price ?? x.close ?? x.markPrice ?? x.indexPrice ?? x.change24h ?? x.change ?? x.priceChangePercent ?? x.percentChange ?? x.netFlow ?? x.net_inflow ?? x.flow ?? x.sentiment ?? x.status ?? x.date ?? ""; }
function fmt(v){ if(v===undefined||v===null||v==="") return ""; const n=typeof v==="number"?v:Number(String(v).replace(/[$,%+,]/g,"")); if(Number.isFinite(n)){ if(Math.abs(n)>=1e9)return `$${(n/1e9).toFixed(2)}B`; if(Math.abs(n)>=1e6)return `$${(n/1e6).toFixed(2)}M`; return String(Math.round(n*10000)/10000);} return String(v); }
function live(block){ return ["sosovalue-api","sodex-api"].includes(block?.source) && (block?.itemCount || 0) > 0; }
function setBadge(id,text,kind){ const el=$(id); el.textContent=text; el.className=`badge ${kind}`; }
function switchTab(id){ document.querySelectorAll(".tab").forEach(t=>t.classList.remove("show")); $(id).classList.add("show"); document.querySelectorAll(".nav").forEach(b=>b.classList.toggle("active", b.dataset.tab===id)); }
document.querySelectorAll(".nav").forEach(b=>b.addEventListener("click",()=>switchTab(b.dataset.tab)));
$("openApi").addEventListener("click",()=>switchTab("api"));
function rows(id, block, max=8){ const el=$(id), items=block?.items||[]; if(!items.length){ el.innerHTML=`<div class="row"><div><b>No live records</b><small>${esc(block?.warning || "Open API Console to inspect endpoint/key status.")}</small></div><strong>${esc(block?.status || block?.source || "")}</strong></div>`; return; } el.innerHTML=items.slice(0,max).map(item=>`<div class="row"><div><b>${esc(label(item))}</b><small>${esc(JSON.stringify(item).slice(0,190))}</small></div><strong>${esc(fmt(value(item)))}</strong></div>`).join(""); }
function signalCard(s){ return `<article class="signal"><div class="score">${esc(s.score ?? 0)}</div><h4>${esc(s.title || "Signal")}</h4><p><b>Source:</b> ${esc(s.source || "Live engine")}</p><p><b>Confidence:</b> ${esc(s.confidence || "n/a")}</p><ul>${(s.evidence||[]).map(e=>`<li>${esc(e)}</li>`).join("")}</ul><p><b>Invalidation:</b> ${esc(s.invalidation || "n/a")}</p><p><b>Action:</b> ${esc(s.action || "n/a")}</p></article>`; }
function renderDiagnostics(){ const soso=state.sosoPayload, sodex=state.sodexPayload; $("diagnostics").innerHTML=`<div class="row"><div><b>SoSoValue</b><small>${esc(soso?.keyFingerprint ? `Key: ${soso.keyFingerprint}` : "No key fingerprint")} · ${esc(soso?.baseUrl || "")}</small></div><strong>${esc(soso?.liveBlocks || 0)}/4</strong></div><div class="row"><div><b>SoDEX</b><small>${esc((sodex?.bases?.spot || []).join(" | ").slice(0,170))}</small></div><strong>${esc(sodex?.data?.liveBlocks || 0)}/6</strong></div>`; }
function render(){ const d=state.data||{}; $("sosoMarketCount").textContent=d.sosoMarket?.itemCount||0; $("sodexMarketCount").textContent=d.sodexMarket?.itemCount||0; $("etfCount").textContent=d.etf?.itemCount||0; $("newsCount").textContent=d.news?.itemCount||0; $("ssiCount").textContent=d.ssi?.itemCount||0; const count=["sosoMarket","sodexMarket","etf","news","ssi"].filter(k=>live(d[k])).length; $("liveScore").textContent=`${count}/5`; const sosoLive=live(d.sosoMarket)||live(d.etf)||live(d.news)||live(d.ssi); setBadge("sosoBadge", sosoLive ? "SoSo Live" : "SoSo Error", sosoLive ? "good" : "bad"); setBadge("sodexBadge", live(d.sodexMarket) ? "SoDEX Live" : "SoDEX Error", live(d.sodexMarket) ? "good" : "bad"); setBadge("apiBadge", count ? `${count}/5 Live` : "API Error", count ? "good" : "bad"); $("brief").textContent=state.ai?.brief || (count ? "Live records loaded." : "No live records. Open API Console."); rows("sosoMarketRows", d.sosoMarket); rows("sodexRows", d.sodexMarket, 12); rows("etfRows", d.etf); rows("newsRows", d.news); rows("ssiRows", d.ssi); renderDiagnostics(); const sig=state.ai?.signals||[]; const empty=`<p class="brief">No signals until live records are loaded.</p>`; $("topSignals").innerHTML=sig.slice(0,3).map(signalCard).join("") || empty; $("signalList").innerHTML=sig.map(signalCard).join("") || empty; const radar=state.ai?.radar||[]; $("radarList").innerHTML=radar.length ? radar.map(r=>`<div class="radar-row"><b>${esc(r.name)}</b><div class="bar"><i style="width:${Math.max(0,Math.min(100,r.heat))}%"></i></div><span>${esc(r.heat)}/100</span></div>`).join("") : `<p class="brief">No narrative radar until live data loads.</p>`; const a=state.ai?.allocation; $("allocation").innerHTML=a?.allocations?.length ? a.allocations.map(x=>`<div class="allocation-row"><b>${esc(x.name)}</b><div class="bar"><i style="width:${Math.max(0,Math.min(100,x.weight))}%"></i></div><span>${esc(x.weight)}%</span></div>`).join("") + `<p class="brief">${esc(a.note)}</p>` : `<p class="brief">${esc(a?.note || "No live SSI allocation yet.")}</p>`; const risk=state.ai?.portfolioRisk; $("riskBox").innerHTML=risk ? `<div class="risk-card"><h3>Risk Score: ${esc(risk.score)}/100</h3><p>Concentration: ${esc(risk.concentration)}</p><p>SSI Exposure: ${esc(risk.ssiExposure)}%</p><p>${esc(risk.suggestion)}</p></div>` : ""; }
function parseHoldings(){ return $("holdings").value.split("\n").map(x=>x.trim()).filter(Boolean).map(line=>{ const parts=line.split(/\s+/); const w=Number((parts.pop()||"0").replace("%","")); return { asset: parts.join(" "), weight: Number.isFinite(w) ? w : 0 }; }); }
function combine(soso, sodex){ const sd=sodex?.data||{}; return { sosoMarket: soso?.market || null, sodexMarket: { source: sd.source || "sodex-api-error", resource:"sodexMarket", updatedAt:sd.updatedAt, itemCount:sd.itemCount||0, items:sd.items||[], warning:sd.warning||"", status:sd.status||"" }, etf: soso?.etf || null, news: soso?.news || null, ssi: soso?.ssi || null }; }
async function analyze(){ const res=await fetch("/api/ai",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({data:state.data,holdings:parseHoldings(),profile:$("profile").value})}); state.ai=await res.json(); render(); }
async function refresh(){ setBadge("apiBadge","Loading","wait"); setBadge("sosoBadge","SoSo loading","wait"); setBadge("sodexBadge","SoDEX loading","wait"); try{ const [sosoRes,sodexRes]=await Promise.all([fetch("/api/soso?resource=all",{cache:"no-store"}),fetch("/api/sodex?resource=all",{cache:"no-store"})]); state.sosoPayload=await sosoRes.json(); state.sodexPayload=await sodexRes.json(); state.data=combine(state.sosoPayload,state.sodexPayload); $("apiLog").textContent=JSON.stringify({soso:state.sosoPayload,sodex:state.sodexPayload},null,2); await analyze(); const count=["sosoMarket","sodexMarket","etf","news","ssi"].filter(k=>live(state.data[k])).length; toast(count ? `Loaded ${count}/5 live modules` : "No live modules. Check API Console."); }catch(e){ setBadge("apiBadge","API Error","bad"); $("apiLog").textContent=e.message; toast(e.message); } }
$("refresh").addEventListener("click",refresh); $("profile").addEventListener("change",analyze); $("analyzePortfolio").addEventListener("click",analyze);
$("exploreSoso").addEventListener("click",async()=>{ const r=await fetch("/api/soso?resource=explore",{cache:"no-store"}); $("apiLog").textContent=JSON.stringify(await r.json(),null,2); switchTab("api"); });
$("exploreSodex").addEventListener("click",async()=>{ const r=await fetch("/api/sodex?resource=all",{cache:"no-store"}); $("apiLog").textContent=JSON.stringify(await r.json(),null,2); switchTab("api"); });
$("testSosoPath").addEventListener("click",async()=>{ const p=$("sosoPath").value.trim(); if(!p)return; const r=await fetch(`/api/soso?path=${encodeURIComponent(p)}`,{cache:"no-store"}); $("apiLog").textContent=JSON.stringify(await r.json(),null,2); });
$("testSodexPath").addEventListener("click",async()=>{ const p=$("sodexPath").value.trim(); if(!p)return; const m=$("sodexMarket").value; const r=await fetch(`/api/sodex?market=${encodeURIComponent(m)}&path=${encodeURIComponent(p)}`,{cache:"no-store"}); $("apiLog").textContent=JSON.stringify(await r.json(),null,2); });
$("exportMd").addEventListener("click",()=>{ const lines=["# SoSo Signal Copilot Research Plan","",`Generated: ${new Date().toISOString()}`,"","## Brief",state.ai?.brief||"No brief.","","## Signals",...(state.ai?.signals||[]).flatMap(s=>["",`### ${s.title}`,`Score: ${s.score}/100`,`Confidence: ${s.confidence}`,...(s.evidence||[]).map(e=>`- ${e}`),`Invalidation: ${s.invalidation}`,`Action: ${s.action}`]),"","## API Status",$("apiLog").textContent.slice(0,3000),"","Disclaimer: research only, not financial advice."]; const blob=new Blob([lines.join("\n")],{type:"text/markdown"}); const url=URL.createObjectURL(blob); const a=document.createElement("a"); a.href=url; a.download="soso-signal-copilot-research-plan.md"; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); toast("Research plan exported"); });
refresh();
'''

FILES["scripts/smoke-test.mjs"] = r'''
import fs from "node:fs";
const required = ["index.html", "styles.css", "app.js", "api/health.js", "api/soso.js", "api/sodex.js", "api/ai.js", "package.json", "vercel.json", ".env.example", "README.md", "docs/submission.md", "logo.svg"];
let ok = true;
for (const f of required) if (!fs.existsSync(f)) { console.error("Missing", f); ok = false; }
for (const f of ["package.json", "vercel.json"]) JSON.parse(fs.readFileSync(f, "utf8"));
const soso = fs.readFileSync("api/soso.js", "utf8");
const sodex = fs.readFileSync("api/sodex.js", "utf8");
const html = fs.readFileSync("index.html", "utf8");
if (!soso.includes("x-soso-api-key")) { console.error("Missing SoSoValue API key header"); ok = false; }
if (!sodex.includes("sodex")) { console.error("Missing SoDEX integration"); ok = false; }
for (const token of ["Command Center", "Market Intelligence", "Narrative Radar", "Signal Engine", "SSI Builder", "Portfolio Risk", "API Console"]) if (!html.includes(token)) { console.error("Missing UI module:", token); ok = false; }
for (const forbidden of ["Demo fallback", "fallback demo data", "CoinGecko"]) if (soso.includes(forbidden) || sodex.includes(forbidden) || html.includes(forbidden)) { console.error("Forbidden phrase:", forbidden); ok = false; }
if (!ok) process.exit(1);
console.log("Smoke test passed: FULL live SoSoValue + SoDEX project, no demo data.");
'''


def write_files():
    for rel, content in FILES.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.lstrip(), encoding="utf-8")


def validate_json():
    json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


def make_zip():
    zip_path = ROOT.parent / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    excluded = {".git", "node_modules", ".vercel"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in ROOT.rglob("*"):
            if not file.is_file():
                continue
            rel = file.relative_to(ROOT)
            parts = set(rel.parts)
            if parts & excluded:
                continue
            if file.name in {".env", ".env.local", ZIP_NAME}:
                continue
            z.write(file, arcname=f"{ROOT.name}/{rel.as_posix()}")
    return zip_path


if __name__ == "__main__":
    write_files()
    validate_json()
    zip_path = make_zip()
    print("DONE: SoSo Signal Copilot FULL generated")
    print(f"Project folder: {ROOT}")
    print(f"ZIP file: {zip_path}")
    print("Next: npm run smoke")
    print("Then: git add . && git commit -m \"Full live SoSoValue and SoDEX terminal\" && git push origin main")
