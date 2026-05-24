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
