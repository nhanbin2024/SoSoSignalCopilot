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
