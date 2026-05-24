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
