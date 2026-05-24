from pathlib import Path
import textwrap

ROOT = Path.cwd()

def write(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip(), encoding='utf-8')
    print('wrote', path)

write('package.json', r'''
{
  "name": "soso-signal-copilot-v2",
  "version": "2.0.0",
  "private": true,
  "description": "SoSoValue-only AI Research OS for Wave 2.",
  "type": "module",
  "scripts": {
    "smoke": "node scripts/smoke-test.mjs"
  },
  "keywords": ["sosovalue", "sodex", "ssi", "ai", "crypto", "wave2"]
}
''')

write('vercel.json', r'''
{
  "version": 2,
  "cleanUrls": true,
  "trailingSlash": false
}
''')

write('.env.example', r'''
SOSO_API_KEY=your_private_sosovalue_api_key
SOSO_BASE_URL=https://openapi.sosovalue.com/openapi/v1

# Optional: comma-separated endpoint paths from official SoSoValue docs.
# Example: /your/real/path,/another/path
SOSO_MARKET_PATHS=
SOSO_ETF_PATHS=
SOSO_NEWS_PATHS=
SOSO_SSI_PATHS=
''')

write('api/soso.js', r'''
const DEFAULT_BASE_URL = "https://openapi.sosovalue.com/openapi/v1";

const DEFAULT_CANDIDATES = {
  market: [
    "/market/overview",
    "/coins/markets",
    "/crypto/market",
    "/currency/market",
    "/market/tickers",
    "/coins/list"
  ],
  etf: [
    "/etf/flow",
    "/etf/net-inflow",
    "/etf/historical",
    "/bitcoin/spot-etf",
    "/etf/bitcoin/spot",
    "/etf/eth/spot"
  ],
  news: [
    "/news",
    "/news/list",
    "/insight/news",
    "/articles",
    "/research/news"
  ],
  ssi: [
    "/ssi/assets",
    "/indices/ssi/assets",
    "/index/assets",
    "/ssi",
    "/index/list"
  ]
};

const ENV_KEYS = {
  market: ["SOSO_MARKET_PATHS", "SOSO_MARKET_PATH", "SOSOVALUE_MARKET_PATHS"],
  etf: ["SOSO_ETF_PATHS", "SOSO_ETF_PATH", "SOSOVALUE_ETF_PATHS"],
  news: ["SOSO_NEWS_PATHS", "SOSO_NEWS_PATH", "SOSOVALUE_NEWS_PATHS"],
  ssi: ["SOSO_SSI_PATHS", "SOSO_SSI_PATH", "SOSOVALUE_SSI_PATHS"]
};

function apiKey() {
  return process.env.SOSO_API_KEY || process.env.SOSOVALUE_API_KEY || "";
}

function baseUrl() {
  return (process.env.SOSO_BASE_URL || process.env.SOSOVALUE_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, "");
}

function splitPaths(value) {
  return String(value || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function pathsFor(resource) {
  const envPaths = (ENV_KEYS[resource] || [])
    .flatMap((key) => splitPaths(process.env[key]));
  return [...new Set([...envPaths, ...(DEFAULT_CANDIDATES[resource] || [])])];
}

function makeUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${baseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function extractItems(payload) {
  const seen = new Set();
  const out = [];

  function walk(value, depth = 0) {
    if (depth > 5 || value == null) return;
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item && typeof item === "object") {
          const key = JSON.stringify(item).slice(0, 300);
          if (!seen.has(key)) {
            seen.add(key);
            out.push(item);
          }
        }
      }
      return;
    }
    if (typeof value === "object") {
      for (const key of ["data", "result", "items", "list", "records", "rows", "content"]) {
        if (Array.isArray(value[key])) walk(value[key], depth + 1);
      }
      if (!out.length) {
        for (const child of Object.values(value)) walk(child, depth + 1);
      }
    }
  }

  walk(payload);
  return out.slice(0, 80);
}

function compactPreview(payload) {
  const text = JSON.stringify(payload, null, 2);
  return text.length > 4000 ? text.slice(0, 4000) + "\n...trimmed" : text;
}

async function callSoso(path) {
  const key = apiKey();
  if (!key) {
    return {
      ok: false,
      source: "sosovalue-api-error",
      status: 0,
      path,
      url: makeUrl(path),
      warning: "Missing SOSO_API_KEY in Vercel Environment Variables."
    };
  }

  const url = makeUrl(path);
  const started = Date.now();
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        accept: "application/json",
        "x-soso-api-key": key
      }
    });
    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = { text };
    }
    const items = response.ok ? extractItems(payload) : [];
    return {
      ok: response.ok,
      source: response.ok ? "sosovalue-api" : "sosovalue-api-error",
      status: response.status,
      path,
      url,
      latencyMs: Date.now() - started,
      updatedAt: new Date().toISOString(),
      itemCount: items.length,
      items,
      rawPreview: compactPreview(payload),
      errorPreview: response.ok ? "" : String(text).slice(0, 1500)
    };
  } catch (error) {
    return {
      ok: false,
      source: "sosovalue-api-error",
      status: 0,
      path,
      url,
      latencyMs: Date.now() - started,
      updatedAt: new Date().toISOString(),
      itemCount: 0,
      items: [],
      warning: error.message
    };
  }
}

async function fetchResource(resource) {
  const tried = [];
  for (const path of pathsFor(resource)) {
    const result = await callSoso(path);
    tried.push({ path, status: result.status, ok: result.ok, itemCount: result.itemCount, warning: result.warning || result.errorPreview || "" });
    if (result.ok && result.itemCount > 0) {
      return { resource, ...result, pathsTried: tried };
    }
    if (result.ok && result.itemCount === 0) {
      return { resource, ...result, pathsTried: tried, warning: "API responded successfully, but no list-like records were found." };
    }
  }
  return {
    resource,
    ok: false,
    source: "sosovalue-api-error",
    updatedAt: new Date().toISOString(),
    itemCount: 0,
    items: [],
    warning: "No SoSoValue endpoint returned live records. Set the correct *_PATHS environment variables from the official API docs.",
    pathsTried: tried
  };
}

async function explore() {
  const resources = ["market", "etf", "news", "ssi"];
  const result = {};
  for (const resource of resources) {
    result[resource] = [];
    for (const path of pathsFor(resource)) {
      result[resource].push(await callSoso(path));
    }
  }
  return result;
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();

  const resource = String(req.query.resource || "all").toLowerCase();
  const path = req.query.path ? String(req.query.path) : "";

  try {
    if (path) {
      const data = await callSoso(path);
      return res.status(200).json({ ok: data.ok, hasApiKey: Boolean(apiKey()), baseUrl: baseUrl(), custom: data });
    }

    if (resource === "explore") {
      const data = await explore();
      return res.status(200).json({ ok: true, hasApiKey: Boolean(apiKey()), baseUrl: baseUrl(), explore: data });
    }

    if (resource === "all") {
      const [market, etf, news, ssi] = await Promise.all([
        fetchResource("market"),
        fetchResource("etf"),
        fetchResource("news"),
        fetchResource("ssi")
      ]);
      const liveBlocks = [market, etf, news, ssi].filter((x) => x.ok && x.itemCount > 0).length;
      return res.status(200).json({ ok: liveBlocks > 0, hasApiKey: Boolean(apiKey()), baseUrl: baseUrl(), liveBlocks, market, etf, news, ssi });
    }

    if (!["market", "etf", "news", "ssi"].includes(resource)) {
      return res.status(400).json({ ok: false, error: "Use resource=all, market, etf, news, ssi, explore or path=/custom/endpoint" });
    }

    const data = await fetchResource(resource);
    return res.status(200).json({ ok: data.ok, hasApiKey: Boolean(apiKey()), baseUrl: baseUrl(), [resource]: data });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}
''')

write('api/ai.js', r'''
function asText(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(asText).join(" ");
  if (typeof value === "object") return Object.values(value).map(asText).join(" ");
  return "";
}

function num(value) {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const n = Number(value.replace(/[$,%+,]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}

function labelOf(item) {
  return item.symbol || item.ticker || item.name || item.asset || item.title || item.coin || item.currency || "SoSo item";
}

function allItems(data) {
  return ["market", "etf", "news", "ssi"].flatMap((key) => {
    const block = data?.[key];
    return Array.isArray(block?.items) ? block.items.map((item) => ({ ...item, __source: key })) : [];
  });
}

function narrativeRadar(data) {
  const dict = {
    ETF: ["etf", "inflow", "outflow", "fund", "spot etf"],
    BTC: ["btc", "bitcoin"],
    ETH: ["eth", "ethereum"],
    SOL: ["sol", "solana"],
    DeFi: ["defi", "dex", "lend", "yield", "liquidity"],
    Meme: ["meme", "doge", "shib", "pepe"],
    RWA: ["rwa", "real world", "treasury", "tokenized"],
    AI: [" ai ", "artificial intelligence", "agent"],
    Macro: ["fed", "rate", "inflation", "macro", "dollar"],
    SSI: ["ssi", "index", "basket", "mag7", "defi.ssi", "meme.ssi"],
    SoDEX: ["sodex", "spot", "orderbook", "btc_usdc"]
  };
  const textBlocks = allItems(data).map((x) => asText(x).toLowerCase());
  return Object.entries(dict).map(([name, words]) => {
    let hits = 0;
    for (const text of textBlocks) {
      for (const word of words) if (text.includes(word)) hits += 1;
    }
    const heat = Math.min(100, hits * 14 + (hits ? 25 : 0));
    return { name, heat, sentiment: heat >= 70 ? "Bullish" : heat >= 35 ? "Active" : "Quiet", hits };
  }).sort((a, b) => b.heat - a.heat);
}

function signalCards(data) {
  const items = allItems(data);
  if (!items.length) return [];

  const cards = [];
  const marketItems = items.filter((x) => x.__source === "market");
  const etfItems = items.filter((x) => x.__source === "etf");
  const newsItems = items.filter((x) => x.__source === "news");
  const ssiItems = items.filter((x) => x.__source === "ssi");

  const avgMomentum = marketItems.length
    ? marketItems.reduce((s, x) => s + Math.max(-20, Math.min(20, num(x.change24h ?? x.change ?? x.percentChange ?? x.priceChange))), 0) / marketItems.length
    : 0;

  const etfFlow = etfItems.reduce((s, x) => s + num(x.netFlow ?? x.net_inflow ?? x.flow ?? x.value ?? x.amount), 0);
  const positiveNews = newsItems.filter((x) => /positive|bull|inflow|rise|gain|surge|up/i.test(asText(x))).length;
  const topNarrative = narrativeRadar(data)[0] || { name: "Market", heat: 0 };
  const topSsi = ssiItems.sort((a, b) => num(b.change24h ?? b.change) - num(a.change24h ?? a.change))[0];

  const score1 = Math.round(Math.max(0, Math.min(100, 52 + avgMomentum * 2 + (etfFlow > 0 ? 20 : -10) + positiveNews * 5)));
  cards.push({
    title: "SoSoValue Market Momentum Signal",
    score: score1,
    confidence: score1 >= 75 ? "High" : score1 >= 55 ? "Medium" : "Low",
    evidence: [`Average market momentum: ${avgMomentum.toFixed(2)}`, `ETF flow aggregate: ${etfFlow || "n/a"}`, `Positive news hits: ${positiveNews}`],
    invalidation: "Momentum weakens or live ETF/news data turns negative.",
    action: "Create a watchlist plan and open the related SoDEX market only after confirmation."
  });

  cards.push({
    title: `${topNarrative.name} Narrative Radar Signal`,
    score: topNarrative.heat,
    confidence: topNarrative.heat >= 70 ? "High" : topNarrative.heat >= 40 ? "Medium" : "Low",
    evidence: [`Narrative heat: ${topNarrative.heat}/100`, `Keyword hits from live SoSoValue data: ${topNarrative.hits}`],
    invalidation: "Narrative heat drops below 35 or conflicting headlines dominate.",
    action: "Track related assets, export a research plan, and compare against SSI exposure."
  });

  if (topSsi) {
    cards.push({
      title: `${labelOf(topSsi)} SSI Allocation Signal`,
      score: Math.round(Math.max(10, Math.min(95, 55 + num(topSsi.change24h ?? topSsi.change) * 6))),
      confidence: "Medium",
      evidence: [`Top SSI candidate from live data: ${labelOf(topSsi)}`, `Change metric: ${topSsi.change24h ?? topSsi.change ?? "n/a"}`],
      invalidation: "SSI trend weakens or basket exposure no longer matches the user's risk profile.",
      action: "Use SSI Builder to generate a diversified research allocation."
    });
  }

  return cards;
}

function ssiAllocation(data, profile = "balanced") {
  const ssi = Array.isArray(data?.ssi?.items) ? data.ssi.items : [];
  if (!ssi.length) return { profile, allocations: [], note: "No live SSI records available from SoSoValue API." };
  const names = ssi.slice(0, 5).map(labelOf);
  const presets = {
    conservative: [45, 25, 15, 10, 5],
    balanced: [35, 25, 20, 12, 8],
    aggressive: [25, 25, 20, 18, 12],
    hunter: [20, 20, 20, 20, 20]
  };
  const weights = presets[profile] || presets.balanced;
  return {
    profile,
    allocations: names.map((name, i) => ({ name, weight: weights[i] || 0 })).filter((x) => x.weight > 0),
    note: "Allocation is computed locally from live SSI records for research only."
  };
}

function portfolioRisk(holdings = []) {
  const total = holdings.reduce((s, h) => s + num(h.weight), 0) || 1;
  const normalized = holdings.map((h) => ({ ...h, weight: (num(h.weight) / total) * 100 }));
  const maxWeight = normalized.reduce((m, h) => Math.max(m, h.weight), 0);
  const memeWeight = normalized.filter((h) => /meme|pepe|doge|shib/i.test(h.asset)).reduce((s, h) => s + h.weight, 0);
  const ssiWeight = normalized.filter((h) => /ssi|index/i.test(h.asset)).reduce((s, h) => s + h.weight, 0);
  const score = Math.round(Math.min(100, 35 + maxWeight * 0.45 + memeWeight * 0.35 - Math.min(ssiWeight, 35) * 0.2));
  return {
    score,
    concentration: maxWeight >= 50 ? "High" : maxWeight >= 30 ? "Medium" : "Low",
    ssiExposure: Math.round(ssiWeight),
    suggestion: score >= 75 ? "Reduce concentration and increase diversified SSI/index exposure." : score >= 50 ? "Keep position sizes controlled and monitor narrative concentration." : "Portfolio looks relatively diversified for a research plan."
  };
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ ok: false, error: "Method not allowed" });

  try {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
    const data = body.data || {};
    const holdings = body.holdings || [];
    const profile = body.profile || "balanced";
    const signals = signalCards(data);
    const radar = narrativeRadar(data);
    const liveBlocks = ["market", "etf", "news", "ssi"].filter((k) => data?.[k]?.source === "sosovalue-api").length;

    return res.status(200).json({
      ok: true,
      liveBlocks,
      brief: liveBlocks ? `Live SoSoValue data loaded across ${liveBlocks}/4 modules. Top narrative: ${radar[0]?.name || "n/a"}.` : "No live SoSoValue records loaded. Check API Console.",
      radar,
      signals,
      allocation: ssiAllocation(data, profile),
      portfolioRisk: portfolioRisk(holdings)
    });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}
''')

write('index.html', r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SoSo Signal Copilot v2</title>
  <meta name="description" content="SoSoValue-only AI Research OS for Wave 2" />
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <div class="bg-layer l1"></div><div class="bg-layer l2"></div><div class="bg-grid"></div>
  <aside class="side glass">
    <div class="brand"><div class="bot">◉</div><div><small>SoSoValue Only</small><h1>Signal Copilot v2</h1></div></div>
    <button class="nav active" data-tab="command">Command Center</button>
    <button class="nav" data-tab="radar">Narrative Radar</button>
    <button class="nav" data-tab="signals">Signal Engine</button>
    <button class="nav" data-tab="ssi">SSI Builder</button>
    <button class="nav" data-tab="portfolio">Portfolio Risk</button>
    <button class="nav" data-tab="api">API Console</button>
    <div class="side-links">
      <a href="https://sosovalue.com/join/9RZ4FYNK" target="_blank">SoSoValue</a>
      <a href="https://sodex.com/" target="_blank">SoDEX</a>
      <a href="https://sodex.com/trade/spot/BTC_USDC" target="_blank">BTC/USDC</a>
      <a href="https://ssi.sosovalue.com/vi/assets" target="_blank">SSI Assets</a>
    </div>
  </aside>

  <main class="app">
    <header class="hero glass">
      <div><p class="eyebrow">AI × On-Chain Finance × SoSoValue API</p><h2>Research OS powered only by live SoSoValue data.</h2><p>No demo data. No external market API. If SoSoValue API fails, this tool shows the real error.</p><div class="actions"><button id="refresh" class="primary">Refresh Live API</button><button id="exportMd">Export Research Plan</button><button id="openApi">Inspect API</button></div></div>
      <div class="status-orb"><div class="ring"></div><span id="liveScore">0/4</span><small>Live Modules</small></div>
    </header>

    <section class="cards four"><div class="stat"><small>Market</small><b id="marketCount">0</b></div><div class="stat"><small>ETF</small><b id="etfCount">0</b></div><div class="stat"><small>News</small><b id="newsCount">0</b></div><div class="stat"><small>SSI</small><b id="ssiCount">0</b></div></section>

    <section id="command" class="tab show"><div class="panel glass"><div class="head"><div><p class="eyebrow">Command Center</p><h3>Daily Research Brief</h3></div><span id="apiBadge" class="badge bad">Checking</span></div><p id="brief" class="brief">Loading live SoSoValue API...</p><div id="topSignals" class="signal-grid"></div></div></section>

    <section id="radar" class="tab"><div class="panel glass"><p class="eyebrow">Narrative Radar</p><h3>Heatmap from live SoSoValue records</h3><div id="radarList" class="radar"></div></div></section>

    <section id="signals" class="tab"><div class="panel glass"><p class="eyebrow">Signal Engine</p><h3>Scored Research Cards</h3><div id="signalList" class="signal-grid"></div></div></section>

    <section id="ssi" class="tab"><div class="panel glass"><p class="eyebrow">SSI Builder</p><h3>Allocation from live SSI records</h3><select id="profile"><option value="conservative">Conservative</option><option value="balanced" selected>Balanced</option><option value="aggressive">Aggressive</option><option value="hunter">Narrative Hunter</option></select><div id="allocation" class="alloc"></div></div></section>

    <section id="portfolio" class="tab"><div class="panel glass"><p class="eyebrow">Portfolio Risk</p><h3>Manual holdings, SoSo-style research scoring</h3><textarea id="holdings" placeholder="BTC 40\nETH 25\nMAG7.ssi 25\nMEME.ssi 10"></textarea><button id="analyzePortfolio" class="primary">Analyze Risk</button><div id="riskBox" class="risk-box"></div></div></section>

    <section id="api" class="tab"><div class="panel glass"><div class="head"><div><p class="eyebrow">API Console</p><h3>Real SoSoValue API status</h3></div><button id="explore">Explore Endpoints</button></div><p class="brief">Set SOSO_API_KEY in Vercel. For exact docs endpoints, set SOSO_MARKET_PATHS / SOSO_ETF_PATHS / SOSO_NEWS_PATHS / SOSO_SSI_PATHS.</p><input id="customPath" placeholder="/paste/real/soso/endpoint/path" /><button id="testPath">Test Custom Path</button><pre id="apiLog">Waiting...</pre></div></section>

    <section class="data-grid"><div class="panel glass"><p class="eyebrow">Market Records</p><div id="marketRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">ETF Records</p><div id="etfRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">News Records</p><div id="newsRows" class="rows"></div></div><div class="panel glass"><p class="eyebrow">SSI Records</p><div id="ssiRows" class="rows"></div></div></section>
  </main>
<script src="/app.js" type="module"></script>
</body>
</html>
''')

write('styles.css', r'''
:root{--bg:#050712;--card:rgba(16,24,48,.72);--card2:rgba(31,42,82,.54);--line:rgba(255,255,255,.13);--text:#f7fbff;--muted:#9aa8ce;--cyan:#38e8ff;--violet:#9d72ff;--green:#78ffb7;--red:#ff6d8d;--gold:#ffd166}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 15% 15%,rgba(56,232,255,.18),transparent 26%),radial-gradient(circle at 80% 10%,rgba(157,114,255,.22),transparent 28%),linear-gradient(135deg,#060814,#0b1028 55%,#12173a);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,Segoe UI,sans-serif}.bg-layer{position:fixed;inset:auto;border-radius:999px;filter:blur(28px);pointer-events:none;animation:float 12s infinite}.l1{width:360px;height:360px;left:-120px;top:20%;background:rgba(56,232,255,.16)}.l2{width:460px;height:460px;right:-140px;bottom:0;background:rgba(157,114,255,.15);animation-delay:-4s}.bg-grid{position:fixed;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,black,transparent 85%);pointer-events:none}@keyframes float{50%{transform:translateY(-30px) scale(1.05)}}.glass{background:var(--card);border:1px solid var(--line);box-shadow:0 30px 100px rgba(0,0,0,.34);backdrop-filter:blur(18px)}.side{position:fixed;left:16px;top:16px;bottom:16px;width:280px;border-radius:30px;padding:20px;display:flex;flex-direction:column;gap:12px}.brand{display:flex;gap:14px;align-items:center;margin-bottom:12px}.brand small,.eyebrow{color:var(--cyan);text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:900}.brand h1{font-size:20px;margin:3px 0 0}.bot{width:58px;height:58px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(135deg,var(--cyan),var(--violet));box-shadow:0 0 30px rgba(56,232,255,.35);animation:pulse 2s infinite}@keyframes pulse{50%{filter:brightness(1.3);transform:translateY(-2px)}}button,.nav,select,input,textarea{font:inherit}.nav,button{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);border-radius:16px;padding:12px 14px;cursor:pointer;transition:.2s}.nav{text-align:left}.nav:hover,.nav.active,button:hover{transform:translateY(-1px);border-color:rgba(56,232,255,.45);background:rgba(56,232,255,.12)}.primary{background:linear-gradient(135deg,var(--cyan),var(--violet));font-weight:900;color:white}.side-links{margin-top:auto;display:grid;gap:8px}.side-links a{color:var(--muted);text-decoration:none;border:1px solid var(--line);padding:10px;border-radius:14px}.app{margin-left:320px;padding:16px;display:grid;gap:18px}.hero{border-radius:32px;padding:34px;display:grid;grid-template-columns:1fr 260px;gap:20px;align-items:center;overflow:hidden;position:relative}.hero:before{content:"";position:absolute;inset:-2px;background:linear-gradient(120deg,rgba(56,232,255,.12),transparent,rgba(157,114,255,.14));pointer-events:none}.hero h2{font-size:clamp(34px,5vw,68px);line-height:.94;letter-spacing:-.06em;margin:4px 0}.hero p{color:var(--muted);max-width:780px}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}.status-orb{height:210px;border-radius:28px;background:rgba(255,255,255,.05);display:grid;place-items:center;position:relative}.ring{position:absolute;width:140px;height:140px;border-radius:50%;border:1px solid rgba(56,232,255,.45);border-top-color:var(--violet);animation:spin 7s linear infinite}.status-orb span{font-size:42px;font-weight:1000}.status-orb small{color:var(--muted);margin-top:64px}@keyframes spin{to{transform:rotate(360deg)}}.cards.four{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat{background:var(--card2);border:1px solid var(--line);border-radius:24px;padding:18px}.stat small{color:var(--muted)}.stat b{display:block;font-size:32px;margin-top:10px}.tab{display:none}.tab.show{display:block}.panel{border-radius:28px;padding:22px}.head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.badge{border:1px solid var(--line);border-radius:999px;padding:8px 12px;font-size:13px}.badge.good{color:var(--green);background:rgba(120,255,183,.1)}.badge.bad{color:var(--red);background:rgba(255,109,141,.1)}.brief{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:18px;padding:16px;color:var(--muted);line-height:1.6}.signal-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.signal{border:1px solid var(--line);background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.035));border-radius:22px;padding:16px;min-height:245px;animation:rise .45s ease both}.score{font-size:32px;font-weight:1000;color:var(--green)}.signal h4{margin:8px 0}.signal p,.signal li{color:var(--muted);font-size:13px;line-height:1.55}.radar{display:grid;gap:12px}.bar{height:14px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--violet),var(--green));border-radius:999px}.radar-row,.alloc-row,.row{border:1px solid var(--line);background:rgba(255,255,255,.045);border-radius:16px;padding:12px}.radar-row{display:grid;grid-template-columns:140px 1fr 90px;gap:12px;align-items:center}.data-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.rows{display:grid;gap:10px}.row{display:grid;grid-template-columns:1fr auto;gap:10px}.row small{display:block;color:var(--muted);margin-top:3px}input,select,textarea{width:100%;border:1px solid var(--line);background:rgba(255,255,255,.07);color:var(--text);border-radius:16px;padding:12px;margin:8px 0 12px}textarea{min-height:170px}pre{white-space:pre-wrap;max-height:520px;overflow:auto;background:#050813;border:1px solid var(--line);border-radius:18px;padding:16px;color:#c9d7ff}.alloc{display:grid;gap:10px}.risk-box{margin-top:14px}@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}@media(max-width:1100px){.side{position:relative;width:auto}.app{margin-left:0}.hero,.cards.four,.signal-grid,.data-grid{grid-template-columns:1fr}}
''')

write('app.js', r'''
const $ = (id) => document.getElementById(id);
const state = { data: null, ai: null, holdings: [] };

function toast(msg){ console.log(msg); }
function esc(v){return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function label(item){return item.symbol || item.ticker || item.name || item.asset || item.title || item.coin || item.currency || 'SoSo record';}
function value(item){return item.price ?? item.change24h ?? item.change ?? item.netFlow ?? item.net_inflow ?? item.sentiment ?? item.status ?? item.date ?? '';}
function fmt(v){ if(typeof v==='number'){ if(Math.abs(v)>=1e9)return `$${(v/1e9).toFixed(2)}B`; if(Math.abs(v)>=1e6)return `$${(v/1e6).toFixed(2)}M`; return String(Math.round(v*100)/100);} return String(v ?? '');}
function live(block){return block?.source === 'sosovalue-api' && (block?.itemCount || 0) > 0;}

function switchTab(id){ document.querySelectorAll('.tab').forEach(x=>x.classList.remove('show')); $(id).classList.add('show'); document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active', x.dataset.tab===id)); }
document.querySelectorAll('.nav').forEach(btn=>btn.onclick=()=>switchTab(btn.dataset.tab));
$('openApi').onclick=()=>switchTab('api');

function rows(id, block){
  const el=$(id); const items=block?.items || [];
  el.innerHTML = items.slice(0,8).map(item=>`<div class="row"><div><b>${esc(label(item))}</b><small>${esc(JSON.stringify(item).slice(0,130))}</small></div><strong>${esc(fmt(value(item)))}</strong></div>`).join('') || `<div class="row"><div><b>No live records</b><small>${esc(block?.warning || 'Check API Console')}</small></div><strong>${esc(block?.status || '')}</strong></div>`;
}

function signalCard(s){
  return `<article class="signal"><div class="score">${esc(s.score ?? 0)}</div><h4>${esc(s.title)}</h4><p><b>Confidence:</b> ${esc(s.confidence)}</p><ul>${(s.evidence||[]).map(e=>`<li>${esc(e)}</li>`).join('')}</ul><p><b>Invalidation:</b> ${esc(s.invalidation)}</p><p><b>Action:</b> ${esc(s.action)}</p></article>`;
}

function render(){
  const d=state.data || {};
  $('marketCount').textContent=d.market?.itemCount || 0; $('etfCount').textContent=d.etf?.itemCount || 0; $('newsCount').textContent=d.news?.itemCount || 0; $('ssiCount').textContent=d.ssi?.itemCount || 0;
  const count=['market','etf','news','ssi'].filter(k=>live(d[k])).length;
  $('liveScore').textContent=`${count}/4`;
  $('apiBadge').textContent=count ? 'Live SoSo API' : 'API Error'; $('apiBadge').className=`badge ${count?'good':'bad'}`;
  $('brief').textContent=state.ai?.brief || (count ? 'Live data loaded.' : 'No live SoSoValue records. Open API Console to inspect exact errors.');
  rows('marketRows',d.market); rows('etfRows',d.etf); rows('newsRows',d.news); rows('ssiRows',d.ssi);
  const signals=state.ai?.signals || [];
  $('topSignals').innerHTML=signals.slice(0,3).map(signalCard).join('') || '<p class="brief">No signals until live SoSoValue records are loaded.</p>';
  $('signalList').innerHTML=signals.map(signalCard).join('') || '<p class="brief">No signals until live SoSoValue records are loaded.</p>';
  $('radarList').innerHTML=(state.ai?.radar || []).map(r=>`<div class="radar-row"><b>${esc(r.name)}</b><div class="bar"><i style="width:${Math.max(0,Math.min(100,r.heat))}%"></i></div><span>${esc(r.heat)}/100</span></div>`).join('') || '<p class="brief">No radar until live data loads.</p>';
  const a=state.ai?.allocation;
  $('allocation').innerHTML=a?.allocations?.length ? a.allocations.map(x=>`<div class="alloc-row"><b>${esc(x.name)}</b><div class="bar"><i style="width:${x.weight}%"></i></div><span>${x.weight}%</span></div>`).join('') + `<p class="brief">${esc(a.note)}</p>` : `<p class="brief">${esc(a?.note || 'No live SSI allocation yet.')}</p>`;
  const pr=state.ai?.portfolioRisk;
  $('riskBox').innerHTML=pr ? `<div class="brief"><h3>Risk Score: ${esc(pr.score)}/100</h3><p>Concentration: ${esc(pr.concentration)}</p><p>SSI Exposure: ${esc(pr.ssiExposure)}%</p><p>${esc(pr.suggestion)}</p></div>` : '';
}

function parseHoldings(){
  return $('holdings').value.split('\n').map(line=>line.trim()).filter(Boolean).map(line=>{const parts=line.split(/\s+/); const weight=Number(parts.pop().replace('%','')); return {asset:parts.join(' '), weight:Number.isFinite(weight)?weight:0};});
}

async function analyze(){
  const res=await fetch('/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:state.data, holdings:parseHoldings(), profile:$('profile').value})});
  state.ai=await res.json(); render();
}

async function refresh(){
  $('apiBadge').textContent='Loading';
  const res=await fetch('/api/soso?resource=all',{cache:'no-store'});
  const json=await res.json();
  state.data={market:json.market,etf:json.etf,news:json.news,ssi:json.ssi};
  $('apiLog').textContent=JSON.stringify(json,null,2);
  await analyze();
}

$('refresh').onclick=refresh;
$('profile').onchange=analyze;
$('analyzePortfolio').onclick=analyze;
$('explore').onclick=async()=>{const r=await fetch('/api/soso?resource=explore',{cache:'no-store'}); $('apiLog').textContent=JSON.stringify(await r.json(),null,2); switchTab('api');};
$('testPath').onclick=async()=>{const p=$('customPath').value.trim(); if(!p)return; const r=await fetch('/api/soso?path='+encodeURIComponent(p),{cache:'no-store'}); $('apiLog').textContent=JSON.stringify(await r.json(),null,2);};
$('exportMd').onclick=()=>{
  const md=[`# SoSo Signal Copilot v2 Research Plan`, '', `Generated: ${new Date().toISOString()}`, '', `## Brief`, state.ai?.brief || '', '', `## Signals`, ...(state.ai?.signals||[]).flatMap(s=>[`### ${s.title}`,`Score: ${s.score}/100`, `Confidence: ${s.confidence}`, ...(s.evidence||[]).map(e=>`- ${e}`), `Invalidation: ${s.invalidation}`, `Action: ${s.action}`, '']), '', 'Disclaimer: research only, not financial advice.'].join('\n');
  const blob=new Blob([md],{type:'text/markdown'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='soso-signal-plan.md'; a.click(); URL.revokeObjectURL(a.href);
};
refresh();
''')

write('scripts/smoke-test.mjs', r'''
import fs from 'node:fs';
const files=['index.html','styles.css','app.js','api/soso.js','api/ai.js','package.json','vercel.json'];
let ok=true;
for(const f of files){if(!fs.existsSync(f)){console.error('missing',f);ok=false;}}
for(const f of ['package.json','vercel.json']) JSON.parse(fs.readFileSync(f,'utf8'));
for(const f of ['api/soso.js','api/ai.js','app.js']){
  const s=fs.readFileSync(f,'utf8');
  if(f==='api/soso.js' && !s.includes('x-soso-api-key')){console.error('missing api key header'); ok=false;}
  if(s.includes('demo-fallback') || s.includes('DEMO')){console.error('demo fallback found in',f); ok=false;}
}
if(!ok) process.exit(1);
console.log('Smoke test passed: live SoSoValue only, no demo fallback.');
''')

print('\nDONE. Next commands:')
print('npm run smoke')
print('git add . && git commit -m "Upgrade to live SoSoValue v2" && git push origin main')
