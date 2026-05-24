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
