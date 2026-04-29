package com.auraguard.phone.ml

import android.content.Context
import android.util.Log
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer

/**
 * Loads `assets/rgf_net.onnx` and runs RGF-Net inference via ONNX Runtime.
 *
 * Input layout (flat FloatArray of length INPUT_SIZE = 19*1280 + 6 = 24326):
 *   [0 .. 24319]  — EEG signal  (19 channels × 1280 samples @ 256 Hz / 5s)
 *   [24320..24325] — biometrics [age_norm, sex, resting_hr, hrv_sdnn,
 *                                hours_since_seizure, medication_adherence]
 *
 * Output: pre-ictal probability in [0, 1]. Threshold 0.75 triggers alert.
 *
 * Falls back to a deterministic stub (0.05) if the model asset is absent,
 * so the UI works on a fresh emulator before the .onnx is placed in assets/.
 */
class InferenceEngine private constructor(
    private val env: OrtEnvironment?,
    private val session: OrtSession?,
) {

    /** Run a single forward pass. Thread-safe via synchronized block. */
    @Synchronized
    fun score(input: FloatArray): Float {
        require(input.size == INPUT_SIZE) {
            "InferenceEngine expected $INPUT_SIZE features, got ${input.size}"
        }
        if (env == null || session == null) return STUB_SCORE

        return try {
            // Split flat input → EEG tensor (1,19,1280) + cond tensor (1,6)
            val eegFlat = input.copyOfRange(0, EEG_SAMPLES)
            val condFlat = input.copyOfRange(EEG_SAMPLES, INPUT_SIZE)

            val eegTensor = OnnxTensor.createTensor(
                env,
                FloatBuffer.wrap(eegFlat),
                longArrayOf(1, N_CHANNELS.toLong(), WINDOW_SAMPLES.toLong()),
            )
            val condTensor = OnnxTensor.createTensor(
                env,
                FloatBuffer.wrap(condFlat),
                longArrayOf(1, BIOMETRIC_FEATURES.toLong()),
            )
            val inputs = mapOf("eeg_input" to eegTensor, "biometric_cond" to condTensor)
            // Close input tensors after inference regardless of outcome.
            try {
                // OrtSession.Result is AutoCloseable; use() closes it after the block.
                session.run(inputs).use { results ->
                    // results.get(name) returns Java Optional<OnnxValue> — must call .get() to unwrap.
                    @Suppress("UNCHECKED_CAST")
                    val logits = (results.get("logits").get().value as Array<FloatArray>)[0]
                    val preIctalLogit   = logits[1]
                    val interIctalLogit = logits[0]
                    // Manual softmax → P(pre-ictal)
                    val expPre   = Math.exp(preIctalLogit.toDouble())
                    val expInter = Math.exp(interIctalLogit.toDouble())
                    (expPre / (expPre + expInter)).toFloat().coerceIn(0f, 1f)
                }
            } finally {
                eegTensor.close()
                condTensor.close()
            }
        } catch (t: Throwable) {
            Log.e(TAG, "ONNX inference failed; falling back to stub", t)
            STUB_SCORE
        }
    }

    fun close() {
        session?.close()
        env?.close()
    }

    companion object {
        private const val TAG = "InferenceEngine"
        const val N_CHANNELS = 19
        const val WINDOW_SAMPLES = 1280          // 5s @ 256 Hz
        const val EEG_SAMPLES = N_CHANNELS * WINDOW_SAMPLES   // 24320
        const val BIOMETRIC_FEATURES = 6
        const val INPUT_SIZE = EEG_SAMPLES + BIOMETRIC_FEATURES  // 24326
        const val MODEL_ASSET = "rgf_net.onnx"
        const val RISK_THRESHOLD = 0.75f
        private const val STUB_SCORE = 0.05f

        fun create(context: Context): InferenceEngine {
            return try {
                val bytes = context.assets.open(MODEL_ASSET).readBytes()
                val env = OrtEnvironment.getEnvironment()
                val opts = OrtSession.SessionOptions().apply {
                    setIntraOpNumThreads(2)
                }
                val session = env.createSession(bytes, opts)
                Log.i(TAG, "ONNX Runtime session created — inputs: ${session.inputNames}")
                InferenceEngine(env, session)
            } catch (t: Throwable) {
                Log.w(TAG, "$MODEL_ASSET not found or failed to load; using stub", t)
                InferenceEngine(null, null)
            }
        }
    }
}
