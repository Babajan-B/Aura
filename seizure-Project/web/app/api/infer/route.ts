import { NextResponse } from "next/server";

interface InferRequest {
  age?: number;
  sex?: number;
  hr?: number;
  hrv?: number;
  hoursSinceSeizure?: number;
  medicationAdherence?: number;
  injectSeizure?: boolean;
}

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  let body: InferRequest = {};
  try {
    body = (await req.json()) as InferRequest;
  } catch {
    body = {};
  }

  const hr = body.hr ?? 75;
  const hrv = body.hrv ?? 50;
  const hoursSinceSeizure = body.hoursSinceSeizure ?? 24;
  const medicationAdherence = body.medicationAdherence ?? 0.9;
  const inject = Boolean(body.injectSeizure);

  let risk = 0.1;
  if (hr > 110) risk += 0.3;
  if (hrv < 30) risk += 0.2;
  if (hoursSinceSeizure < 6) risk += 0.15;
  if (medicationAdherence < 0.5) risk += 0.1;
  if (inject) risk = 0.92;

  risk = Math.max(0, Math.min(1, risk));
  const label = risk >= 0.75 ? "PRE-ICTAL — ALERT" : "Inter-ictal";
  const latency_ms = Math.floor(40 + Math.random() * 50);

  // small artificial delay so the latency badge feels real
  await new Promise((r) => setTimeout(r, latency_ms));

  return NextResponse.json({
    risk: Number(risk.toFixed(3)),
    label,
    latency_ms,
  });
}
