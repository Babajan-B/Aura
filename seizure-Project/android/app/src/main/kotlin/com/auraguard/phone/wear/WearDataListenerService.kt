package com.auraguard.phone.wear

import android.content.Intent
import android.util.Log
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import com.auraguard.phone.ml.InferenceEngine
import com.auraguard.shared.SensorPacket
import com.google.android.gms.wearable.DataEvent
import com.google.android.gms.wearable.DataEventBuffer
import com.google.android.gms.wearable.DataMapItem
import com.google.android.gms.wearable.WearableListenerService

/**
 * Bridges incoming SensorPacket DataItems from the watch into the inference
 * pipeline.
 *
 * Lifecycle:
 *   1. Watch's PhoneBridge writes a DataItem at [SensorPacket.DATA_PATH].
 *   2. Android wakes this service; we decode the DataMap.
 *   3. We construct a feature vector and call [InferenceEngine.score].
 *   4. We rebroadcast the resulting risk score so the foreground UI / alert
 *      pipeline can react.
 */
class WearDataListenerService : WearableListenerService() {

    private val engine by lazy { InferenceEngine.create(applicationContext) }

    override fun onDataChanged(buffer: DataEventBuffer) {
        for (event in buffer) {
            if (event.type != DataEvent.TYPE_CHANGED) continue
            val item = event.dataItem
            if (!item.uri.path.orEmpty().startsWith(SensorPacket.DATA_PATH)) continue

            val packet = runCatching { decode(DataMapItem.fromDataItem(item)) }
                .onFailure { Log.e(TAG, "Bad SensorPacket", it) }
                .getOrNull() ?: continue

            val features = buildFeatureVector(packet)
            val risk = engine.score(features)
            Log.i(TAG, "risk=$risk capturedAt=${packet.capturedAtMs}")
            broadcastRisk(risk, packet.capturedAtMs)
            // TODO: persist event via EventLogDao + trigger SOS if risk > 0.85
        }
    }

    private fun decode(item: DataMapItem): SensorPacket {
        val map = item.dataMap
        return SensorPacket(
            capturedAtMs = map.getLong(SensorPacket.KEY_CAPTURED_AT),
            windowSeconds = map.getInt(SensorPacket.KEY_WINDOW_SEC, SensorPacket.WINDOW_SECONDS),
            accelHz = map.getInt(SensorPacket.KEY_ACCEL_HZ, SensorPacket.ACCEL_HZ),
            accelX = map.getFloatArray(SensorPacket.KEY_ACCEL_X) ?: FloatArray(0),
            accelY = map.getFloatArray(SensorPacket.KEY_ACCEL_Y) ?: FloatArray(0),
            accelZ = map.getFloatArray(SensorPacket.KEY_ACCEL_Z) ?: FloatArray(0),
            heartRate = map.getFloatArray(SensorPacket.KEY_HR) ?: FloatArray(0),
            skinTempC = map.getFloatArray(SensorPacket.KEY_TEMP) ?: FloatArray(0),
            batteryPct = map.getFloat(SensorPacket.KEY_BATTERY, -1f),
        )
    }

    private fun buildFeatureVector(packet: SensorPacket): FloatArray {
        // TODO: replace with real feature extractor (FFT bands, HRV, etc.).
        val out = FloatArray(InferenceEngine.INPUT_SIZE)
        val n = minOf(out.size, packet.accelX.size)
        for (i in 0 until n) out[i] = packet.accelX[i]
        return out
    }

    private fun broadcastRisk(risk: Float, capturedAtMs: Long) {
        val intent = Intent(ACTION_RISK_UPDATE).apply {
            putExtra(EXTRA_RISK, risk)
            putExtra(EXTRA_CAPTURED_AT, capturedAtMs)
        }
        LocalBroadcastManager.getInstance(applicationContext).sendBroadcast(intent)
    }

    companion object {
        private const val TAG = "WearDataListener"
        const val ACTION_RISK_UPDATE = "com.auraguard.phone.RISK_UPDATE"
        const val EXTRA_RISK = "risk"
        const val EXTRA_CAPTURED_AT = "captured_at"
    }
}
