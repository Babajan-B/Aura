# Aura Watch

**A wearable seizure-safety research prototype for monitoring, user confirmation and caregiver-alert workflows.**

Aura Watch combines an Android application, a Wear OS application, a controlled web demonstration and a separately evaluated EEG machine-learning pipeline. It is a research prototype, not a diagnostic or clinically approved medical device.

## Current status

### Completed

- Android and Wear OS prototype applications
- Controlled sensor-state and risk-display demonstrations
- Repeated high-risk confirmation and 15-second cancellation workflow
- Proposed SMS, GPS and caregiver escalation flow
- Offline EEG feature extraction and evaluation of three classical models
- Vercel-ready Next.js demonstration website

### Scientific boundary

The applications currently use controlled simulated wearable inputs. The offline EEG classifier is not integrated into the mobile or watch applications. EEG-derived performance cannot be transferred directly to accelerometer, gyroscope, PPG or temperature signals. A separate model trained on synchronized wearable sensor and seizure-event data is required.

## Stage 13 EEG evaluation

The signal-only evaluation used 23 features and excluded identifiers, dataset labels, file paths, timing fields and target-derived columns from the model inputs.

Held-out test set: **1,295 windows** consisting of 1,071 seizure and 224 non-seizure windows.

| Model | ROC-AUC | PR-AUC | Sensitivity | Specificity | F1 |
|---|---:|---:|---:|---:|---:|
| Histogram Gradient Boosting | 0.926 | 0.981 | 93.4% | 71.4% | 0.937 |
| Extra Trees | 0.918 | 0.978 | 94.5% | 70.1% | 0.941 |
| Random Forest | **0.932** | **0.982** | **94.3%** | **73.7%** | **0.944** |

Random Forest confusion matrix: TN 165, FP 59, FN 61 and TP 1,010. Its Brier score was 0.072 and 10-bin ECE was 0.092. Cross-dataset ROC-AUC varied from 0.971 on CHB-MIT to 0.780 on TUSZ, demonstrating the need for stronger patient-independent, external and prospective validation.

## Proposed wearable workflow

1. Collect accelerometer, gyroscope and PPG/heart-rate signals; temperature is optional.
2. Preprocess windows on the Android/edge layer and apply a future validated wearable model.
3. Confirm repeated high-risk readings and start a 15-second cancellation window.
4. If the user does not respond, the phone attempts to send an SMS containing GPS location, event time and risk information.

## Repository structure

```text
android/   Android phone, Wear OS and shared Kotlin modules
web/       Next.js web demonstration for Vercel
ml/        EEG model-development scripts and research artifacts
docs/      Architecture, model-card and demonstration documentation
```

## Run the website

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

For Vercel, import this repository and set **Root Directory** to `web`.

## Build the Android applications

```bash
cd android
./gradlew :app:assembleDebug :wear:assembleDebug
```

## Intended use

Aura Watch is intended for research, education and prototype evaluation. It must not be used for diagnosis, treatment decisions or as the sole mechanism for emergency assistance.
