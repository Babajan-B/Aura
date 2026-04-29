# Aura Watch — Dashboard

Dark, neon, sci-fi medical dashboard for the **Aura Watch — On-Device Seizure Pre-Ictal Guardian** hackathon project. Replaces the Gradio demo with a Next.js 15 single-page experience showcasing RGF-Net (37,554 params, 36.7 KB, <500 ms on-device).

## Stack

- Next.js 15 (App Router) + React 19
- TypeScript (strict)
- Tailwind CSS 3.4
- framer-motion · recharts · lucide-react · @radix-ui/react-slider

## Run it

```bash
npm install
npm run dev
```

Then visit [http://localhost:3000](http://localhost:3000).

## Sections

1. **Hero** — animated brain SVG + key stats
2. **Monitor** — live mock EEG + pre-ictal risk gauge
3. **Architecture** — Teacher → Student knowledge distillation
4. **Watch** — Wear OS face mockup with monitoring / countdown / alert states
5. **Simulator** — six biometric sliders, POSTs to `/api/infer`
6. **Footprint** — log-scale model size comparison

## Inference API

`POST /api/infer` accepts `{age, sex, hr, hrv, hoursSinceSeizure, medicationAdherence, injectSeizure?}` and returns `{risk, label, latency_ms}`. Heuristic shape mirrors the deployed RGF-Net pre-ictal threshold of 0.75.
