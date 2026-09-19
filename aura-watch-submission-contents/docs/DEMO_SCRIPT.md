# 🎬 Aura Watch — 3-Minute Live Demo Runbook

> **Goal**: take a judge from "what is this?" to "I'd hand this to my grandmother" in 180 seconds.

## 🎯 Demo Pre-Flight (do BEFORE judges arrive)

| ✅ | Item | Where |
|---|---|---|
| ☐ | Phone charged > 80%, airplane mode + Wi-Fi (not cellular) | Pixel 7 |
| ☐ | Wear OS emulator running, paired & visible in `adb devices` | laptop |
| ☐ | `pnpm dev` running on `http://localhost:3000` | laptop browser tab 1 |
| ☐ | HF Space pre-loaded as fallback in browser tab 2 | tab 2 |
| ☐ | Phone screen mirrored via `scrcpy` to projector | laptop |
| ☐ | "Fake seizure" CSV staged at `/sdcard/Download/preictal_clip.csv` | phone storage |
| ☐ | Backup MP4 of a successful run on desktop | `~/demo/aura_backup.mp4` |
| ☐ | Volume up — alarm tone is the showpiece | hardware |

---

## ⏱️ Minute-by-Minute Script

### 0:00 – 0:30 — The Hook 🎣

**On screen**: dashboard idle, watch face showing green "Monitoring" tile.

**Say**:
> "65 million people live with epilepsy. 1-in-1000 die every year from a seizure no one saw coming. Today I'll show you a 37 kilobyte neural network — smaller than this slide — that gives you a 30-second head start. Fully on the wrist. Zero cloud."

**Action**: hold the watch up to camera, point to the green tile.

---

### 0:30 – 1:00 — The Architecture Slide 🏗️

**On screen**: switch to the architecture diagram in `README.md` (rendered) OR slide 2 of the deck.

**Say**:
> "We trained a 661,000-parameter Transformer teacher on EEG seizure data, then distilled it into RGF-Net — a Ring-Buffer GRU with FiLM conditioning. INT8 quantization gets us to 37 KB. It runs on a phone in 22 milliseconds. The watch streams biometrics over BLE; the phone synthesizes the EEG channels and runs inference; everything stays on-device."

**Point at**: Teacher box → Student box → "37 KB" badge → "no cloud" arrow.

---

### 1:00 – 2:00 — The Live Run 🚨

**On screen**: split — phone mirror left, dashboard right.

**Steps**:

1. **Tap "Start monitoring"** on the phone app. Dashboard probability line begins flat near 0.05.
2. **Inject the fake seizure**:
   ```
   adb shell am broadcast \
     -a com.aura.DEMO_INJECT_PREICTAL \
     --es file /sdcard/Download/preictal_clip.csv
   ```
   *(have this command in a `~/demo/inject.sh` one-liner ready to paste)*
3. **Watch the line climb** on the dashboard. Narrate:
   > "Probability is rising. We're now seeing the pre-ictal signature — the FiLM layer is amplifying because heart rate variability is collapsing."
4. **At ~0.78 the watch buzzes**. The countdown screen appears.
5. **Let it expire** (don't tap "I'm OK"). Loud alarm fires, phone shows the SOS dialer screen with last-known GPS.
6. **Show the dashboard** — episode card has appeared with timestamp, peak probability, and a "Replay" button.

---

### 2:00 – 2:30 — The Replay 🔄

**On screen**: dashboard "Replay" view.

**Say**:
> "Every episode is logged locally as JSON. Caregivers can scrub through the exact 5-second window the model fired on. No data left the device — but families finally get to *see* what happened."

**Action**: scrub the timeline cursor across the spike. Show the 19-channel EEG synth panel light up.

---

### 2:30 – 3:00 — The Close 🎤

**On screen**: roadmap slide ([`ROADMAP.md`](ROADMAP.md) Phase 1–4).

**Say**:
> "Today: simulated EEG from biometrics. Phase 1: real headband integration with OpenBCI. Phase 2: FDA pre-cert pathway. Phase 3: clinical pilot at a children's hospital. The model is open-source MIT. The mission is simple — nobody should die alone in a seizure when the warning signal was already in their wrist."

**End**: silent slide with [QR to GitHub repo] + [QR to HF Space].

---

## 🛟 Fallback Tree (if something dies on stage)

```
Watch emulator crashes
   └─▶ Switch to "Phone-only mode" toggle in settings
       └─▶ Continue demo, narrate the absence as "watch disconnected fallback"

Phone app force-closes
   └─▶ Open browser tab 2 → run the same flow on the HF Space
       └─▶ Say: "This is the reference deployment we benchmark against"

ADB inject command fails
   └─▶ Use the in-app "Demo → Trigger Pre-Ictal" debug button
       (long-press the version number 5x to unlock)

Both apps fail
   └─▶ Play backup MP4 (~/demo/aura_backup.mp4) full-screen, narrate live
```

---

## 🗣️ Anticipated Q&A (rehearsed)

| Question | 1-sentence answer |
|---|---|
| "Watches don't have EEG — how does this work?" | We synthesize the 19 channels from biometrics for the demo; Phase 1 plugs in a real OpenBCI headband over BLE. |
| "What's your false-positive rate?" | Target is < 1/week; on the HF reference clip set we match the teacher within 3 percentage points — full clinical numbers require an IRB study. |
| "Why not cloud inference?" | 500 ms latency budget, privacy of medical data, and the system has to work in a basement with no signal. |
| "Why GRU not Transformer on-device?" | Constant-memory streaming. A Transformer would re-attend every step; the ring-buffer GRU is O(1) per frame. |
| "Is this a medical device?" | No. Research prototype. We do not claim FDA clearance — see the disclaimer in the README. |

---

## 🎒 Demo Backpack Checklist

- [ ] Phone (Pixel 7) + USB-C cable
- [ ] Wear OS emulator on laptop (Pixel Watch image)
- [ ] HDMI dongle + 2 m HDMI cable
- [ ] Backup phone with the APK pre-installed
- [ ] Printed one-pager from `HACKATHON_SUBMISSION.md` (10 copies)
- [ ] Bluetooth speaker (the alarm is the moment — don't lose it to room noise)
- [ ] Sticky note with the inject command on the laptop bezel

---

> **Rule of three**: rehearse the demo three full run-throughs the night before. The fourth time, do it with the laptop on battery only — that's how you find out the dashboard renders weirdly under power-save.
