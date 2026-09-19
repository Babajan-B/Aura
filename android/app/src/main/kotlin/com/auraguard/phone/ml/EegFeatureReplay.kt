package com.auraguard.phone.ml

import android.content.Context

data class EegReplayWindow(
    val replayId: String,
    val dataset: String,
    val groundTruth: String,
    val referenceProbability: Float,
    val features: FloatArray,
)

object EegFeatureReplay {
    private const val ASSET = "eeg_heldout_replay.csv"
    const val FEATURE_COUNT = 23

    fun load(context: Context): List<EegReplayWindow> =
        context.assets.open(ASSET).bufferedReader().useLines { lines ->
            lines.drop(1).filter { it.isNotBlank() }.mapIndexed { index, line ->
                val fields = line.split(',')
                require(fields.size == 4 + FEATURE_COUNT) {
                    "Replay row ${index + 1} has ${fields.size} columns"
                }
                EegReplayWindow(
                    replayId = fields[0],
                    dataset = fields[1],
                    groundTruth = fields[2],
                    referenceProbability = fields[3].toFloat(),
                    features = fields.drop(4).map(String::toFloat).toFloatArray(),
                )
            }.toList()
        }
}
