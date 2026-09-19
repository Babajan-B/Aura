# Aura Watch — Hardware Data-Collection Plan

> **Status:** Revised after technical review (2026-06-03). See **§0 Reviewer Feedback** for what
> changed and why. This plan integrates a real hardware sensor stream into the existing Aura Watch
> Android architecture (`android/wear` + `android/app`) and the RGF-Net TFLite inference path.

---

## 0. Reviewer Feedback (read this first)

The original plan proposed a **Seeed XIAO ESP32-S3 + Grove Shield + Ultrasonic Distance Sensor + OLED**.
Three issues had to be fixed before it could feed the seizure pipeline:

| # | Problem in original plan | Why it fails | Fix |
|---|--------------------------|--------------|-----|
| 1 | **Ultrasonic distance sensor** as the sensing element | A rangefinder measures distance to an object. It produces **no physiological signal** — no EEG, HR, HRV, accel, SpO₂, or temp. It cannot feed *any* model input. | Replace with real biometric sensors (PPG + IMU + temp). See §1. |
| 2 | No source for the model's **primary input (19-ch EEG)** | `eeg_input` = `(B, 19, 1280)` = 5 s @ 256 Hz. No Grove sensor produces EEG; that needs an ADS1299 analog front-end + scalp electrodes. | Choose a path (§1): **A)** keep EEG *simulated* (as the code already does) and make biometrics real, or **B)** add a real EEG front-end (OpenBCI) in Phase 1. |
| 3 | Wrong integration target & latency claim | `SensorService.kt` is in the **wear** module and streams over the **Wear Data Layer**, not BLE GATT. The "~22 ms" figure is *model inference* latency, not BLE transport latency. | Corrected file paths in §3; separated latency budgets in §4. |

**Key fact about the current codebase:** the watch's `SensorPacket` carries **accel X/Y/Z @ 50 Hz, HR @ 1 Hz,
optional skin temp, battery** — and the 19-channel EEG is **synthesized on the phone** from biometrics
(`Sensor19ChEegSimulator`). So the realistic hardware job is to make the **biometric stream real**, not to
capture EEG. (Model file: `eeg_input (B,19,1280)` + `biometric_cond (B,6)`; only resting-HR and HRV of those
6 fields come from a sensor — age, sex, hours-since-seizure, and medication-adherence are user/app metadata.)

---

## Choose Your Path

| | **Path A — Real Biometrics (recommended for hackathon)** | **Path B — Real EEG (Phase 1)** |
|---|---|---|
| **What's real** | HR, HRV, SpO₂, accel/gyro, skin temp | True 4–8 channel EEG |
| **EEG** | Simulated on phone (existing `Sensor19ChEegSimulator`) | Real, but model retrained for fewer channels |
| **Sensors** | MAX30102 (PPG) + MPU6050/LSM6DS3 (IMU) + temp | OpenBCI Ganglion (4-ch) or Cyton (8-ch) + dry electrodes |
| **Cost** | ~$25–40 | ~$200–500+ |
| **Effort** | Weekend; matches existing `SensorPacket` 1:1 | Weeks; model retrain + electrode rig |
| **Scientific basis** | Empatica's FDA-cleared seizure watch uses **EDA + accelerometer**, not EEG — biometric-only seizure *detection* is defensible | EEG is the gold standard for *pre-ictal prediction* but 19-ch clinical montage is unrealistic on this budget |

> **Recommendation:** Build **Path A** for the hackathon demo. It is honest (real sensors → real biometrics),
> consistent with the code, and cheap. Position **Path B** (real EEG) explicitly as the Phase-1 roadmap item,
> which already matches `docs/ROADMAP.md`.

---

## Path A — Bill of Materials

| Component | Purpose | Maps to model input | Notes |
|-----------|---------|---------------------|-------|
| Seeed XIAO ESP32-S3 | MCU + BLE | — | Good choice; BLE 5.0, low power. **No built-in IMU** even on "Sense". |
| Grove Shield for XIAO | Sensor breakout | — | Confirm it has a JST-PH battery port; the XIAO **Expansion Board** does. |
| **MAX30102 / MAX30105 (PPG)** | Heart rate, HRV, SpO₂ | `biometric_cond`: resting HR, HRV | I²C. The real workhorse — replaces the ultrasonic sensor. |
| **MPU6050 or LSM6DS3 (6-axis IMU)** | Accel + gyro (motion/convulsion) | `SensorPacket.accelX/Y/Z` @ 50 Hz | I²C. Drives motion-artifact + fall/convulsion signal. |
| Skin-temp sensor (MAX30205 or MLX90614) | Skin temperature | `SensorPacket.skinTempC` (optional) | Optional but already supported by the packet. |
| *(Optional)* Grove GSR / EDA sensor | Electrodermal activity | (new biometric channel) | EDA is what Empatica uses for seizure detection — scientifically strong addition. |
| OLED Display (Grove) | On-device status/risk readout | — | Fine to keep; shows "Monitoring / Risk %". |
| 3.7 V LiPo + JST-PH 2.0 | Power | — | Verify shield battery port polarity before connecting. |
| Project box + armband + Velcro | Non-destructive wearable enclosure | — | As in original plan. |

---

---

## Solder-Free Shopping List (Path A)

> **Goal: zero soldering.** Everything below connects via Grove plug-in cables, pre-soldered header
> pins + Dupont jumpers, or JST connectors. The two ⚠️ items are the only ones that can *accidentally*
> require a soldering iron — buy the **pre-soldered-header** variant and you're fine.

### Core (required)

| # | Item | Qty | Why | Connection | Solder-free? |
|---|------|-----|-----|------------|--------------|
| 1 | **Seeed XIAO ESP32-S3 — *with pre-soldered headers*** | 1 | BLE MCU, runs firmware | Seats into Grove shield socket | ⚠️ **Pick the headers-included SKU** |
| 2 | **Grove Shield / Expansion Board for XIAO** | 1 | Breakout for plug-in sensors + LiPo port | XIAO plugs in on top | ✅ |
| 3 | **MAX30102 / MAX30105 PPG module — *pre-soldered headers*** | 1 | HR, HRV, SpO₂ | I²C (Grove-to-female cable) | ⚠️ **Pick the pre-soldered SKU** |
| 4 | **6-axis IMU (MPU6050 or LSM6DS3)** — Grove version *or* pre-soldered breakout | 1 | accel + gyro | I²C | ✅ (Grove) / ⚠️ (breakout) |
| 5 | **Grove I²C Hub (6-port)** | 1 | Fan one I²C port out to 4 devices (shield has too few) | Grove plug-in | ✅ |
| 6 | **Grove OLED Display 0.96″ (SSD1315, I²C)** | 1 | On-watch status / risk % | Grove plug-in | ✅ |
| 7 | **3.7 V LiPo battery, JST-PH 2.0** (≥400 mAh) | 1 | Power | JST into shield | ✅ |
| 8 | **USB-C cable** | 1 | Flashing + charging | USB-C | ✅ |

### Cables & connectivity (required — these are what keep it solder-free)

| # | Item | Qty | Why |
|---|------|-----|-----|
| 9 | **Grove 4-pin cables** | 3–4 | Connect Grove-native modules + hub |
| 10 | **Grove-to-female-Dupont conversion cables** | 2 | Connect non-Grove breakouts (MAX30102, IMU) to Grove ports with no soldering |
| 11 | **Female-female Dupont jumper assortment** | 1 pack | Fallback wiring for any header-pin module |

### Optional (nice to have)

| # | Item | Qty | Why | Connection |
|---|------|-----|-----|------------|
| 12 | **Skin-temp sensor (MAX30205 I²C, or MLX90614 IR)** | 1 | Real skin temp → `SensorPacket.skinTempC` | I²C via hub |
| 13 | **Grove GSR / EDA sensor** | 1 | Electrodermal activity — the signal Empatica's seizure watch actually uses | Analog Grove port |
| 14 | **Project box + sports armband + Velcro** | 1 | Non-destructive wearable enclosure | — |
| 15 | **Power switch (inline JST) or Grove switch** | 1 | Cut battery without unplugging | JST / Grove |

### Tools (no soldering iron needed)

* Small Phillips screwdriver (enclosure), scissors/Velcro, and a computer with **Arduino IDE** for flashing.
* *(That's it — no iron, no solder, no flux.)*

### Buying notes that prevent a soldering surprise

* **#1 and #3/#4 are the only traps.** Generic breakouts often ship with header pins *in the bag, unsoldered*. On the product page, confirm the photo shows pins **already attached**, or the listing says "pre-soldered / plug and play."
* All I²C devices (PPG, IMU, OLED, temp) share one bus — default addresses differ, so **no conflict**, but you need the **Grove I²C Hub (#5)** because the shield's 1–2 I²C ports won't fit four devices.
* GSR (#13) is **analog**, so it goes to the shield's analog Grove port (A0), not the I²C hub.

### Is this enough? — verdict

* ✅ **Enough for Path A** (real biometric loop + simulated EEG + full SOS/dashboard demo). Covers every
  field in `SensorPacket` and the sensor-derived fields of `biometric_cond` (HR, HRV).
* ❌ **Not enough for Path B** (real EEG prediction) — that needs an EEG front-end (OpenBCI Ganglion/Cyton),
  which is the Phase-1 roadmap item, not a solder-free Grove build.

---

## Phase 1: Hardware Assembly & Power

* Snap the **XIAO ESP32-S3** onto the **Grove Shield**.
* Connect **MAX30102 (PPG)** and **MPU6050/LSM6DS3 (IMU)** to Grove **I²C** ports (both are I²C — they share the bus; confirm distinct addresses). Connect the **OLED** to a second I²C port.
* *(Optional)* Add the skin-temp and/or GSR sensor to remaining Grove ports.
* Attach the **3.7 V LiPo** to the shield/board battery port (**verify polarity** first).
* Enclose in a small project box; mount to a sports armband with Velcro.

## Phase 2: Firmware (ESP32, Arduino C++)

* Install **Arduino IDE**, add the **ESP32** board package, select XIAO ESP32-S3.
* Libraries: **SparkFun MAX3010x** (PPG/HR/SpO₂), **MPU6050** or **Adafruit LSM6DS** (IMU), **U8g2** (OLED).
  *(Drop NewPing — it was for the ultrasonic sensor.)*
* **Derive HR & HRV** on-device from the PPG waveform (peak-to-peak intervals → RMSSD/SDNN for HRV).
* **Mirror the real `SensorPacket` layout** so the phone needs no new parser:
  accel X/Y/Z @ 50 Hz, HR @ 1 Hz, optional skin temp @ 1 Hz, battery %.
* **BLE GATT server** with a custom service + notify characteristic. Batch into the same **10 s window**
  the phone expects (`SensorPacket.WINDOW_SECONDS = 10`), or stream per-sample and let the phone window.
* **Backpressure:** keep only the freshest window on the MCU (ring buffer, drop-oldest) so a BLE stutter
  drops stale data instead of queuing it — mirrors the phone's `Channel(capacity=1, DROP_OLDEST)` policy.
* **Raise BLE MTU** (request ~185–247 bytes) so a window's accel array fits in few notifications.

## Phase 3: Android Integration (correct paths)

* **New BLE client path.** The watch currently streams over the **Wear Data Layer**, not BLE. Add a
  `BleSensorClient` (in `android/app/.../sensors/`) that connects to the ESP32 GATT server and emits the
  same `SensorPacket` the existing pipeline consumes. Reuse `com.auraguard.shared.SensorPacket`.
  * Real `SensorService.kt` path (for reference): `android/wear/src/main/kotlin/com/auraguard/wear/sensors/SensorService.kt`.
* **Feed the existing pipeline.** Route decoded packets into `RiskPipeline.kt` →
  `app/.../ml/InferenceEngine.kt` (`RingBuffer.kt` is already there). The phone's
  `Sensor19ChEegSimulator` still synthesizes the EEG tensor from the now-**real** biometrics (Path A).
* **Threading:** keep BLE reads on `Dispatchers.IO`; never block the single inference thread or the UI.
* **Permissions (Android 12+):** `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT` (with `neverForLocation` if you
  don't derive location), plus existing `BODY_SENSORS`/`POST_NOTIFICATIONS`.

## Phase 4: Testing & Calibration

* **Separate latency budgets:** (a) BLE transport (connection interval ~15–30 ms + MTU), (b) feature
  extraction, (c) model inference (~22 ms on Pixel 7). Validate each; don't conflate them.
* **HR/HRV sanity:** compare MAX30102-derived HR against a reference (fingertip oximeter or chest strap).
* **False-positive test:** exercise `PreIctalGate.kt` (3 consecutive frames > 0.75) with real sensor noise
  — motion artifacts from the IMU/PPG are the realistic trigger source now, not "environmental noise."
* **End-to-end demo:** confirm the **Next.js dashboard** renders live biometrics relayed phone→console.

---

## Implementation Resource Table

| Task | Tool/Resource | Goal |
|------|---------------|------|
| Firmware | Arduino IDE / C++, SparkFun MAX3010x, MPU6050/LSM6DS, U8g2 | Read PPG+IMU+temp, compute HR/HRV, stream via BLE |
| BLE link | ESP32 GATT server ↔ Android `BleSensorClient` | Deliver real `SensorPacket` to the phone |
| Android | Kotlin, `RiskPipeline.kt`, `InferenceEngine.kt`, `RingBuffer.kt` | Ingest hardware data into existing inference path |
| Validation | Aura web dashboard + `PreIctalGate.kt` | Verify data flow, latency budgets, and false-positive behavior |

---

## Honest Limitations

* **Path A does not capture EEG.** The model's dominant input stays simulated; you are demonstrating a real
  **biometric** seizure-monitoring loop, not real pre-ictal EEG prediction. State this plainly in the demo.
* **Real seizure prediction requires real EEG (Path B)** + retraining on labeled clinical data (CHB-MIT/TUH),
  which is the documented Phase-1 goal in `docs/ROADMAP.md`.
* **HRV from wrist PPG is motion-sensitive;** expect noise during movement — exactly what `PreIctalGate.kt`'s
  hysteresis is meant to absorb.

---

*Next step options:* (1) ESP32 firmware skeleton that reads MAX30102 + MPU6050 and streams a
`SensorPacket`-shaped BLE payload, or (2) the Android `BleSensorClient` + manifest BLE permissions. Say which.
