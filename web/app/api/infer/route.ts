import { NextResponse } from "next/server";

interface DemoRequest { heartRate?: number; movement?: number; temperature?: number; repeatedPattern?: boolean; }

export async function POST(req: Request) {
  let body: DemoRequest = {};
  try { body = (await req.json()) as DemoRequest; } catch { return NextResponse.json({ error: "Invalid JSON request" }, { status: 400 }); }
  const heartRate = Math.min(180, Math.max(40, body.heartRate ?? 76));
  const movement = Math.min(100, Math.max(0, body.movement ?? 20));
  const temperature = Math.min(42, Math.max(30, body.temperature ?? 36.8));
  const repeatedPattern = Boolean(body.repeatedPattern);
  const score = Math.min(0.99, 0.06 + Math.max(0, (heartRate - 75) / 105) * 0.28 + (movement / 100) * 0.42 + Math.max(0, Math.abs(temperature - 36.8) - 0.5) * 0.05 + (repeatedPattern ? 0.24 : 0));
  return NextResponse.json({ score: Number(score.toFixed(3)), state: score >= 0.75 ? "DEMO HIGH-RISK STATE" : score >= 0.45 ? "DEMO ELEVATED STATE" : "DEMO MONITORING STATE", demo: true, disclaimer: "Controlled interface simulation; not a clinical prediction." });
}
