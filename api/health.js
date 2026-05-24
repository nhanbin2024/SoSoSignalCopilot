export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  return res.status(200).json({
    ok: true,
    service: "SoSo Signal Copilot FULL",
    mode: "live APIs only, no demo data",
    time: new Date().toISOString()
  });
}
