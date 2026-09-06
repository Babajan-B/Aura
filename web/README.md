# Aura Watch web demonstration

Vercel-ready Next.js interface for the Aura Watch wearable seizure-safety research prototype.

## Scientific boundary

- The interactive website uses controlled deterministic wearable inputs to demonstrate interface and alert states.
- It does not run a clinical model and does not produce a medical prediction.
- The separately evaluated Stage 13 EEG pipeline used 23 signal-only features and a held-out set of 1,295 windows.
- Random Forest test results: ROC-AUC 0.932, PR-AUC 0.982, sensitivity 94.3%, specificity 73.7%, and F1 0.944.
- The EEG model has not been integrated into the Android or Wear OS applications.
- A separate model trained on synchronized wearable signals and seizure-event labels is required before wearable inference can be evaluated.

## Local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Vercel deployment

Import the GitHub repository into Vercel and set **Root Directory** to `web`. Vercel detects Next.js automatically; no environment variables are required.

## Main sections

1. Project scope and evidence boundary
2. Controlled signal visualization
3. Proposed wearable safety workflow
4. Interactive Wear OS states
5. Deterministic prototype simulator
6. Stage 13 held-out model validation

## Prototype API

`POST /api/infer` accepts:

```json
{
  "heartRate": 76,
  "movement": 20,
  "temperature": 36.8,
  "repeatedPattern": false
}
```

The endpoint returns a controlled demonstration score and an explicit non-clinical disclaimer.
