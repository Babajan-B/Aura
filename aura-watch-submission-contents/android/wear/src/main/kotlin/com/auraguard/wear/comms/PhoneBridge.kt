package com.auraguard.wear.comms

import android.content.Context
import android.util.Log
import com.auraguard.shared.SensorPacket
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.DataClient
import com.google.android.gms.wearable.PutDataMapRequest
import com.google.android.gms.wearable.Wearable

/**
 * Thin wrapper over [DataClient] that converts a [SensorPacket] to a
 * DataMap and pushes it under [SensorPacket.DATA_PATH].
 *
 * We deliberately use putDataItem rather than sendMessage so that:
 *   - the OS coalesces back-to-back updates,
 *   - the phone can wake from doze with the latest payload only,
 *   - the API surface is symmetrical with WearDataListenerService.
 */
class PhoneBridge(context: Context) {

    private val dataClient: DataClient = Wearable.getDataClient(context.applicationContext)

    fun sendPacket(packet: SensorPacket) {
        if (!packet.isComplete()) {
            Log.w(TAG, "skipping incomplete packet samples=${packet.accelX.size}")
            return
        }
        val req = PutDataMapRequest.create(SensorPacket.DATA_PATH).apply {
            dataMap.putLong(SensorPacket.KEY_CAPTURED_AT, packet.capturedAtMs)
            dataMap.putInt(SensorPacket.KEY_WINDOW_SEC, packet.windowSeconds)
            dataMap.putInt(SensorPacket.KEY_ACCEL_HZ, packet.accelHz)
            dataMap.putFloatArray(SensorPacket.KEY_ACCEL_X, packet.accelX)
            dataMap.putFloatArray(SensorPacket.KEY_ACCEL_Y, packet.accelY)
            dataMap.putFloatArray(SensorPacket.KEY_ACCEL_Z, packet.accelZ)
            dataMap.putFloatArray(SensorPacket.KEY_HR, packet.heartRate)
            dataMap.putFloatArray(SensorPacket.KEY_TEMP, packet.skinTempC)
            dataMap.putFloat(SensorPacket.KEY_BATTERY, packet.batteryPct)
        }.asPutDataRequest().setUrgent()

        try {
            // Fire-and-forget: callers run on the SensorService thread already.
            Tasks.await(dataClient.putDataItem(req))
            Log.d(TAG, "packet sent capturedAt=${packet.capturedAtMs}")
        } catch (t: Throwable) {
            Log.e(TAG, "putDataItem failed", t)
        }
    }

    companion object { private const val TAG = "PhoneBridge" }
}
