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
