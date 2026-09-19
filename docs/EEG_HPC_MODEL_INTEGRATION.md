# HPC EEG Model Integration

## Implemented Path

```text
Held-out EEG-derived feature window
                 |
                 v
23-feature Stage 13 contract
                 |
                 v
HPC-exported ONNX HGB classifier
                 |
                 v
Saved threshold + repeated-window gate
                 |
                 v
Phone countdown -> Wear OS alert request
```

The Android `EEG research` mode runs the actual Stage 13 Histogram Gradient Boosting model exported from Aziz HPC. It is separate from the wearable mode so EEG features can never be confused with accelerometer, gyroscope, PPG or temperature inputs.

## Model Artifact

- Android asset: `app/src/main/assets/aura_watch_eeg_hgb.onnx`
- Size: 801,466 bytes
- SHA-256: `bf2ef1b5e35c0d8d0cc6fd022b00f6e41c22fd1e648ae9743e01daaf023a3c1f`
- Input: one `float32[batch, 23]` tensor named `float_input`
- Saved decision threshold: `0.3029289829079926`
- Original HPC path: `/ddn/data/generic/bbabajan/aura_watch/processed/stage13_exact_signal_model`

HPC conversion and parity validation used 256 held-out rows. Maximum absolute probability error between scikit-learn and ONNX was `1.1322e-07`; mean error was `2.9387e-08`.

## Replay Data

`eeg_heldout_replay.csv` contains 12 de-identified derived feature rows from the held-out CHB-MIT and Siena sets: six non-seizure windows followed by six seizure windows. TUH-derived rows are intentionally not packaged in the public app. Subject identifiers, filenames and raw EEG samples are not included.

The replay is curated to demonstrate model execution and the safety workflow. It is not an unbiased performance evaluation. Aggregate results remain in the original Stage 13 metrics file.

## Runtime Safety

- Wearable mode loads only `aura_watch_signal_model.onnx`; it remains unavailable until a compatible wearable model exists.
- EEG research mode loads only `aura_watch_eeg_hgb.onnx`.
- Replay alerts are always marked as tests.
- SMS and emergency dispatch are suppressed for replay alerts.
- The 15-second cancellation and Wear OS notification path remain active for demonstration.

## Reproduce the Export

The exporter, pinned dependencies, offline Linux wheels and PBS job are in the local `aura_watch_model_export` package and on HPC under:

`/ddn/data/generic/bbabajan/aura_watch/deploy/aura_watch_model_export`

The HPC output is stored under:

`/ddn/data/generic/bbabajan/aura_watch/processed/stage13_exact_signal_model/android_onnx_export`

## Remaining Work

The current implementation validates retrospective model execution and app integration. It does not establish prospective, patient-independent clinical performance. A standalone watch model requires synchronized seizure-labelled IMU, PPG and optional temperature data and a separately validated feature/model contract.
