# Aura Guard Android Prototype

Aura Guard is a phone and Wear OS research prototype for wearable seizure-risk monitoring and caregiver alerting. It is not a diagnostic device and does not replace medical care or emergency services.

## Operating modes

| Mode | Input | Prediction behavior |
| --- | --- | --- |
| Demo | Controlled values | Clearly labelled presentation workflow; SMS is suppressed during tests |
| Wearable | Watch accelerometer, gyroscope, heart rate, optional temperature, battery | Runs only when a compatible wearable ONNX model is installed |
| EEG research | Validated external EEG stream plus contextual sensors | Reserved for the EEG model integration; no simulated EEG is shown as live data |

## Modules

| Module | Purpose |
| --- | --- |
| `:app` | Live dashboard, ONNX inference guard, risk smoothing, local event history, caregiver settings, GPS/SMS coordination |
| `:wear` | Foreground sensor collection, capability reporting, phone transport, alert countdown and cancellation |
| `:shared` | Versioned sensor packet, paths, monitoring modes and temperature-source definitions |

## Sensor contract

The watch sends ten-second windows containing:

- Accelerometer at a target of 50 Hz.
- Gyroscope when available.
- Heart rate at the cadence supplied by the device.
- Temperature when available, with an explicit source: wrist skin, ambient, external, simulated or unavailable.
- Watch battery fraction and capture timestamp.

Ambient measurements are never labelled as skin temperature. Temperature is optional and cannot trigger an alert by itself.

## Model installation

Place the trained wearable model at:

```text
app/src/main/assets/aura_watch_signal_model.onnx
```

The model must use the exact feature order in:

```text
app/src/main/assets/aura_watch_model_contract.json
```

If the model is absent or its input size differs from the 20-feature contract, inference fails closed and the dashboard displays `Unavailable`. The bundled `rgf_net.onnx` is an EEG model and is not applied to watch motion.

## Run

```bash
./gradlew :app:assembleDebug :wear:assembleDebug
```

Phone APK:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Wear APK:

```text
wear/build/outputs/apk/debug/wear-debug.apk
```

Configure the caregiver phone and review SMS/location permissions from **Settings**. Use **Run test countdown** to test the interface safely; test mode never dispatches an emergency message.

## Offline presentation demo

The presentation workflow runs entirely on the Android phone and does not require the HPC server, internet access, a paired watch or the unpublished wearable model.

1. Open the app in **Demo** mode and tap **Start**. The waveform, heart rate, demonstration temperature, battery, signal quality and stable risk score update once per second.
2. Tap **Test alert**. A controlled 90% demonstration score and a 15-second warning appear. The screen explicitly states that SMS and emergency calls are disabled.
3. Tap **I'm OK** to demonstrate wearer cancellation. The application records the test outcome locally and returns the score to the stable state.

All values in this workflow are visibly marked `SIMULATED` or `DEMO`. They are not patient measurements and are not outputs from the HPC-trained model.

The app opens on a presentation intro screen. Tap **Enter demo** to reveal the dashboard.

## Implemented safeguards

- Separate Demo, Wearable and EEG Research modes.
- Per-sensor availability and quality indicators.
- Source-labelled temperature and a slowly established personal baseline.
- Six-window moving-average alert gate.
- Fifteen-second wearer cancellation window.
- Compatible-model and input-size checks before inference.
- Local SQLite audit history with model, mode, sensor context and alert outcome.
- Configurable caregiver instead of a hardcoded destination.
- GPS included only when permission and a location provider are available.
- Foreground watch monitoring notification.

## Verification

```bash
./gradlew :app:testDebugUnitTest
./gradlew :app:compileDebugKotlin :wear:compileDebugKotlin
```

The tests verify the 20-feature order and missing-sensor masks. Hardware validation is still required on the selected watch and temperature sensor because Wear OS devices expose different health capabilities and sampling cadences.
