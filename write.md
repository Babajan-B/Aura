# Aura Watch — How It Works (Simple Write-Up)

## 1. What the system does

Aura Watch predicts a seizure **30+ seconds before it happens**, using only a
watch and a phone — no internet, no cloud, no hospital equipment.

```
Watch (sensors) → Phone (AI model) → Risk score → Alert → SMS/GPS to caregiver
```

1. The **watch** continuously records body signals (heart rate, accelerometer,
   gyroscope, skin temperature).
2. The **phone** feeds those signals into a small AI model (RGF-Net) every
   few seconds.
3. The model outputs a **risk score (0–100%)** for "seizure coming soon."
4. If the risk stays high for 3 readings in a row (~30 seconds), the watch
   shows a **15-second countdown**. The patient can tap "I'm OK" to cancel.
5. If the countdown finishes, the phone **automatically sends an SMS with
   GPS location** to an emergency contact and sounds an alarm on the watch.

Everything runs **on the device itself** — no data ever leaves the phone
unless an actual alert is triggered.

---

## 2. Synthetic data — what we used for the test

Real patient EEG data takes weeks/months to get approved and access (see
Section 3). To build and demo a working model in the hackathon timeframe, we
generated **synthetic EEG signals** instead:

- A script (`SyntheticEEGDataset`) creates fake 19-channel EEG windows that
  mimic the *shape* of real brain signals (sine waves + noise + simulated
  "pre-seizure" patterns).
- 500 synthetic samples were generated, with ~30% labeled "pre-ictal" (about
  to seizure) and the rest "inter-ictal" (normal).
- The model trained on this data learns the **correct input/output format
  and architecture** — but it has **not** learned to recognize a real human
  seizure. It would perform close to random guessing on real EEG.

**Why this matters:** the synthetic data proves the *pipeline* works
end-to-end (watch → phone → AI → alert → SMS/GPS), but the *intelligence*
of the model is not clinically real yet.

---

## 3. Real data — what we are getting (in progress)

We have identified and planned access to several public, research-grade
seizure EEG databases used by every major lab in this field:

| Dataset | Source | Status | What it gives us |
|---|---|---|---|
| **TUH EEG Seizure Corpus (TUSZ)** | Temple University Hospital (isip.piconepress.com) | Application submitted / planned | 10,000+ patients, ~3,500 labeled seizures — the largest public seizure EEG corpus in the world |
| **CHB-MIT Scalp EEG** | PhysioNet (physionet.org) | Open access — no approval needed | 23 pediatric patients, 198 seizures, gold-standard benchmark since 2010 |
| **Siena Scalp EEG** | PhysioNet | Open access | 14 adult patients, 47 seizures |
| **EPILEPSIAE** | epilepsiae.eu | Registration required, planned | 30 adult patients, 277 seizures, high channel count |

**"Accession" process** (how we get the real data):
1. Register/apply on the dataset's data-use portal (TUH and EPILEPSIAE
   require a signed data-use agreement; CHB-MIT/Siena are open).
2. Once approved, download the raw EDF (European Data Format) files —
   these contain real recorded brain signals from real patients during
   actual seizures, with timestamps marked by neurologists.
3. Replace `SyntheticEEGDataset` in our pipeline with a real-data loader
   that reads these EDF files, cleans them (filtering noise, resampling to
   256 Hz, fixing channel counts), and feeds them into the same model
   architecture we already built.
4. Retrain the model on this real data and measure real performance
   (sensitivity, false-alarm rate) using patient-independent testing —
   i.e., never test on a patient the model was trained on.

Once this step is done, the model moves from "demo prototype" to
"clinically validated prototype."

---

## 4. What it takes to monitor seizures on the band + send GPS alerts

To make the **watch/band** actually detect a seizure in real time and notify
someone, three things have to work together:

### A. Sensing on the band
- **Accelerometer + gyroscope** (50 Hz) — catch the rhythmic shaking motion
  of a tonic-clonic seizure.
- **Heart rate / PPG sensor** (1 Hz) — seizures usually cause a sudden HR
  spike (>150% of baseline).
- **EEG headband (future upgrade)** — for *predicting* a seizure before it
  starts (pre-ictal), as opposed to detecting it once it's already
  happening. This requires an external EEG device (e.g., Muse 2, OpenBCI)
  since standard smartwatches cannot read brainwaves.

### B. On-device analysis
- The band streams a rolling 5–10 second window of sensor data to the phone
  over Bluetooth.
- The phone's AI model scores that window for "seizure risk" in real time
  (~22ms per inference on a Pixel-class phone).
- A **smoothing gate** (moving average over multiple windows) prevents
  one noisy reading from triggering a false alarm.

### C. Alert + GPS dispatch
- Once risk crosses the threshold and stays there, the phone:
  1. Sends a message back to the watch to show the 15-second countdown.
  2. If not cancelled, pulls the phone's **last known GPS location**.
  3. Sends an **SMS** to pre-registered emergency contacts containing the
     risk event and a Google Maps link to the GPS coordinates.
  4. Optionally pushes the same event to a **caregiver dashboard** (the
     Next.js web app) for remote family/clinician monitoring.

### What's still needed to make this real (not just demo)
| Requirement | Why |
|---|---|
| Real EEG/motion training data (Section 3) | Model needs to learn real seizure patterns, not synthetic ones |
| Foreground service + persistent BLE connection | So the watch keeps streaming even when the screen is off |
| Battery optimization | Continuous sensing + BLE drains battery fast — needs duty-cycling |
| Location permission handling | GPS must be fetched reliably even if the app is backgrounded |
| Carrier SMS fallback / offline alerting | In case there's no cell signal, fallback options (e.g., local alarm, Bluetooth mesh to a nearby phone) need to be considered |
| Clinical validation | Before trusting this for real patients, it needs testing against real seizure events (sensitivity/specificity), per Section 3 |

---

## Summary

- **Today:** Working end-to-end demo (watch → phone → AI → alert → GPS/SMS)
  trained on **synthetic** data — proves the engineering works.
- **Next step:** Swap in **real EEG data** (TUH, CHB-MIT, and others we're
  getting accession for) to make the AI model actually clinically accurate.
- **After that:** Validate on real seizure events, then consider real
  EEG-capable hardware for true pre-ictal (before-seizure) prediction.
