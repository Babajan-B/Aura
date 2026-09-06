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
    private val loadedAsset: String?,
) {

    enum class ModelKind { WEARABLE, EEG, NONE }

    sealed interface ScoreResult {
        data class Prediction(val probability: Float) : ScoreResult
        data class Unavailable(val reason: String) : ScoreResult
    }

    val modelKind: ModelKind = when (loadedAsset) {
        AURA_SIGNAL_MODEL_ASSET -> ModelKind.WEARABLE
        RGF_MODEL_ASSET -> ModelKind.EEG
        else -> ModelKind.NONE
    }

    val modelName: String = loadedAsset ?: "No compatible model"

    val expectedInputSize: Int? = runCatching {
        val info = session?.inputInfo?.values?.firstOrNull()?.info as? ai.onnxruntime.TensorInfo
        info?.shape?.lastOrNull()?.toInt()?.takeIf { it > 0 }
    }.getOrNull()

    fun scoreWearable(input: FloatArray): ScoreResult {
        if (modelKind != ModelKind.WEARABLE) {
            return ScoreResult.Unavailable("Wearable ONNX model is not installed")
        }
        if (expectedInputSize != null && expectedInputSize != input.size) {
            return ScoreResult.Unavailable("Model expects $expectedInputSize features; app produced ${input.size}")
        }
        return ScoreResult.Prediction(score(input))
    }

    /** Run a single forward pass. Thread-safe via synchronized block. */
    @Synchronized
    fun score(input: FloatArray): Float {
        if (env == null || session == null) return STUB_SCORE

        return try {
            if (session.inputNames.size == 1) {
                scoreSingleInputModel(input)
            } else {
                scoreRgfModel(input)
            }
        } catch (t: Throwable) {
            Log.e(TAG, "ONNX inference failed for $loadedAsset; falling back to stub", t)
            STUB_SCORE
        }
    }

    private fun scoreSingleInputModel(input: FloatArray): Float {
        val session = requireNotNull(session)
        val env = requireNotNull(env)
        val inputName = session.inputNames.first()
        val tensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(input), longArrayOf(1, input.size.toLong()))
        try {
            session.run(mapOf(inputName to tensor)).use { results ->
                return extractProbability(results).coerceIn(0f, 1f)
            }
        } finally {
            tensor.close()
        }
    }

    private fun scoreRgfModel(input: FloatArray): Float {
        require(input.size == INPUT_SIZE) {
            "InferenceEngine expected $INPUT_SIZE features for $RGF_MODEL_ASSET, got ${input.size}"
        }
        val session = requireNotNull(session)
        val env = requireNotNull(env)

        // Split flat input -> EEG tensor (1,19,1280) + biometric tensor (1,6).
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
        try {
            session.run(mapOf("eeg_input" to eegTensor, "biometric_cond" to condTensor)).use { results ->
                return extractProbability(results).coerceIn(0f, 1f)
            }
        } finally {
            eegTensor.close()
            condTensor.close()
        }
    }

    private fun extractProbability(results: OrtSession.Result): Float {
        val logits = results.get("logits")
        if (logits.isPresent) {
            @Suppress("UNCHECKED_CAST")
            val values = logits.get().value as Array<FloatArray>
            return softmaxPositive(values[0])
        }

        for (index in 0 until results.size()) {
            val value = results[index].value
            when (value) {
                is Array<*> -> {
                    val first = value.firstOrNull()
                    if (first is FloatArray && first.isNotEmpty()) {
                        return if (first.size > 1) first[1] else first[0]
                    }
                    if (first is DoubleArray && first.isNotEmpty()) {
                        return (if (first.size > 1) first[1] else first[0]).toFloat()
                    }
                }
                is FloatArray -> if (value.isNotEmpty()) return if (value.size > 1) value[1] else value[0]
                is DoubleArray -> if (value.isNotEmpty()) return (if (value.size > 1) value[1] else value[0]).toFloat()
            }
        }

        Log.w(TAG, "Could not identify probability output; using stub")
        return STUB_SCORE
    }

    private fun softmaxPositive(logits: FloatArray): Float {
        if (logits.size < 2) return logits.firstOrNull() ?: STUB_SCORE
        val expPre = Math.exp(logits[1].toDouble())
        val expInter = Math.exp(logits[0].toDouble())
        return (expPre / (expPre + expInter)).toFloat()
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
        const val AURA_SIGNAL_MODEL_ASSET = "aura_watch_signal_model.onnx"
        const val RGF_MODEL_ASSET = "rgf_net.onnx"
        const val RISK_THRESHOLD = 0.75f
        private const val STUB_SCORE = 0.05f

        fun create(context: Context): InferenceEngine {
            val assets = listOf(AURA_SIGNAL_MODEL_ASSET, RGF_MODEL_ASSET)
            for (asset in assets) {
                try {
                    val bytes = context.assets.open(asset).readBytes()
                    val env = OrtEnvironment.getEnvironment()
                    val opts = OrtSession.SessionOptions().apply {
                        setIntraOpNumThreads(2)
                    }
                    val session = env.createSession(bytes, opts)
                    Log.i(TAG, "ONNX Runtime session created from $asset — inputs: ${session.inputNames}")
                    return InferenceEngine(env, session, asset)
                } catch (t: Throwable) {
                    Log.w(TAG, "$asset not found or failed to load", t)
                }
            }
            Log.w(TAG, "No ONNX model asset loaded; using stub")
            return InferenceEngine(null, null, null)
        }
    }
}
