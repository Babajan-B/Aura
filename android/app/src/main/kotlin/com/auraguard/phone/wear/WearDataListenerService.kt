package com.auraguard.phone.wear

import android.util.Log
import com.auraguard.phone.RiskPipeline
import com.auraguard.shared.SensorPacket
import com.auraguard.shared.TemperatureSource
import com.google.android.gms.wearable.DataEvent
import com.google.android.gms.wearable.DataEventBuffer
import com.google.android.gms.wearable.DataMapItem
import com.google.android.gms.wearable.WearableListenerService
import com.google.android.gms.wearable.MessageEvent

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

    override fun onDataChanged(buffer: DataEventBuffer) {
        for (event in buffer) {
            if (event.type != DataEvent.TYPE_CHANGED) continue
            val item = event.dataItem
            if (!item.uri.path.orEmpty().startsWith(SensorPacket.DATA_PATH)) continue

            val packet = runCatching { decode(DataMapItem.fromDataItem(item)) }
                .onFailure { Log.e(TAG, "Bad SensorPacket", it) }
                .getOrNull() ?: continue

            Log.i(TAG, "processing packet capturedAt=${packet.capturedAtMs}")
            RiskPipeline.process(applicationContext, packet)
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
            gyroX = map.getFloatArray(SensorPacket.KEY_GYRO_X) ?: FloatArray(0),
            gyroY = map.getFloatArray(SensorPacket.KEY_GYRO_Y) ?: FloatArray(0),
            gyroZ = map.getFloatArray(SensorPacket.KEY_GYRO_Z) ?: FloatArray(0),
            heartRate = map.getFloatArray(SensorPacket.KEY_HR) ?: FloatArray(0),
            temperatureC = map.getFloatArray(SensorPacket.KEY_TEMP) ?: FloatArray(0),
            temperatureSource = runCatching {
                TemperatureSource.valueOf(
                    map.getString(SensorPacket.KEY_TEMP_SOURCE, TemperatureSource.UNAVAILABLE.name),
                )
            }.getOrDefault(TemperatureSource.UNAVAILABLE),
            batteryPct = map.getFloat(SensorPacket.KEY_BATTERY, -1f),
        )
    }

    override fun onMessageReceived(event: MessageEvent) {
        when (event.path) {
            SensorPacket.SOS_PATH -> RiskPipeline.onSosFromWatch(applicationContext)
            SensorPacket.CANCEL_PATH -> RiskPipeline.onCancelFromWatch(applicationContext)
            SensorPacket.WATCH_TEST_PATH -> RiskPipeline.triggerTestCountdown(
                applicationContext,
                notifyWatch = false,
            )
        }
    }

    companion object {
        private const val TAG = "WearDataListener"
    }
}
