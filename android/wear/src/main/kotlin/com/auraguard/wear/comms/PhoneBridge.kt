package com.auraguard.wear.comms

import android.content.Context
import android.util.Log
import com.auraguard.shared.SensorPacket
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

    private val appContext = context.applicationContext
    private val dataClient: DataClient = Wearable.getDataClient(appContext)

    fun sendPacket(packet: SensorPacket) {
        if (!packet.isUsable()) {
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
            dataMap.putFloatArray(SensorPacket.KEY_GYRO_X, packet.gyroX)
            dataMap.putFloatArray(SensorPacket.KEY_GYRO_Y, packet.gyroY)
            dataMap.putFloatArray(SensorPacket.KEY_GYRO_Z, packet.gyroZ)
            dataMap.putFloatArray(SensorPacket.KEY_HR, packet.heartRate)
            dataMap.putFloatArray(SensorPacket.KEY_TEMP, packet.temperatureC)
            dataMap.putString(SensorPacket.KEY_TEMP_SOURCE, packet.temperatureSource.name)
            dataMap.putFloat(SensorPacket.KEY_BATTERY, packet.batteryPct)
        }.asPutDataRequest().setUrgent()

        dataClient.putDataItem(req)
            .addOnSuccessListener { Log.d(TAG, "packet sent capturedAt=${packet.capturedAtMs}") }
            .addOnFailureListener { Log.e(TAG, "putDataItem failed", it) }
    }

    fun confirmSos() = sendMessage(SensorPacket.SOS_PATH)

    fun cancelAlert() = sendMessage(SensorPacket.CANCEL_PATH)

    fun requestSeizureTest() = sendMessage(SensorPacket.WATCH_TEST_PATH)

    private fun sendMessage(path: String) {
        Wearable.getNodeClient(appContext).connectedNodes
            .addOnSuccessListener { nodes ->
                val client = Wearable.getMessageClient(appContext)
                nodes.forEach { node -> client.sendMessage(node.id, path, ByteArray(0)) }
            }
            .addOnFailureListener { Log.e(TAG, "node lookup failed for $path", it) }
    }

    companion object { private const val TAG = "PhoneBridge" }
}
