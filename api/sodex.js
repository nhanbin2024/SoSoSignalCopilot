const DEFAULT_SPOT = "https://mainnet-gw.sodex.dev/api/v1/spot";
const DEFAULT_PERPS = "https://mainnet-gw.sodex.dev/api/v1/perps";

const ROUTES = {
  symbols: "/markets/symbols",
  coins: "/markets/coins",
  tickers: "/markets/tickers",
  miniTickers: "/markets/miniTickers",
  bookTickers: "/markets/bookTickers",
  markPrices: "/markets/mark-prices"
};

function baseUrl(market) {
  if (market === "perps") {
    return (process.env.SODEX_PERPS_BASE || DEFAULT_PERPS).replace(/\/$/, "");
  }

  return (process.env.SODEX_SPOT_BASE || DEFAULT_SPOT).replace(/\/$/, "");
}

function extractItems(payload) {
  const raw = payload?.data ?? payload?.result ?? payload?.items ?? payload;

  if (Array.isArray(raw)) return raw;
  if (Array.isArray(raw?.list)) return raw.list;
  if (Array.isArray(raw?.items)) return raw.items;
  if (Array.isArray(raw?.records)) return raw.records;

  return [];
}

async function callSodex({ market = "spot", type = "tickers" }) {
  const path = ROUTES[type] || ROUTES.tickers;
  const url = `${baseUrl(market)}${path}`;
  const started = Date.now();

  const response = await fetch(url, {
    method: "GET",
    headers: {
      accept: "application/json"
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
    ok: response.ok && items.length > 0,
    source: response.ok && items.length > 0 ? "sodex-api" : "sodex-api-error",
    market,
    type,
    url,
    status: response.status,
    latencyMs: Date.now() - started,
    updatedAt: new Date().toISOString(),
    itemCount: items.length,
    items: items.slice(0, 80),
    rawPreview: JSON.stringify(payload, null, 2).slice(0, 5000),
    warning: response.ok && !items.length ? "SoDEX API responded but no records were found." : "",
    errorPreview: response.ok ? "" : text.slice(0, 1500)
  };
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();

  try {
    const market = String(req.query.market || "spot").toLowerCase();
    const type = String(req.query.type || "tickers");

    if (!["spot", "perps"].includes(market)) {
      return res.status(400).json({
        ok: false,
        error: "market must be spot or perps"
      });
    }

    const data = await callSodex({ market, type });

    return res.status(200).json({
      ok: data.ok,
      data
    });
  } catch (error) {
    return res.status(500).json({
      ok: false,
      error: error.message
    });
  }
}