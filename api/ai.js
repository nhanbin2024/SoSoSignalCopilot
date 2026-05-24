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
