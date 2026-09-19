package com.auraguard.shared

import kotlinx.serialization.Serializable

/**
 * SensorPacket — the unit of data the watch streams to the phone every
 * ~10 seconds via the Wear Data Layer.
 *
 * Structured as primitives (FloatArray / DoubleArray / Long) so it round-trips
 * cleanly through DataMap.putFloatArray / putDoubleArray.
 *
 * Layout
 *  - capturedAtMs    : System.currentTimeMillis() at the END of the window.
 *  - windowSeconds   : nominal window length, currently 10s.
 *  - accelHz         : sampling rate of accelerometer stream (50Hz target).
 *  - accelX/Y/Z      : raw accelerometer samples for the window.
 *  - heartRate       : 1Hz heart-rate samples (bpm) for the window.
 *  - skinTempC       : optional 1Hz skin temperature; empty if sensor absent.
 *  - batteryPct      : watch battery [0..1] for QoS / dropout reasoning.
 */
@Serializable
data class SensorPacket(
    val capturedAtMs: Long,
    val windowSeconds: Int = WINDOW_SECONDS,
    val accelHz: Int = ACCEL_HZ,
    val accelX: FloatArray,
    val accelY: FloatArray,
    val accelZ: FloatArray,
    val heartRate: FloatArray,
    val skinTempC: FloatArray = FloatArray(0),
    val batteryPct: Float = -1f,
) {
    /** Total samples we expect on the accel channels for a complete window. */
    val expectedAccelSamples: Int get() = windowSeconds * accelHz

    fun isComplete(): Boolean =
        accelX.size == expectedAccelSamples &&
            accelY.size == expectedAccelSamples &&
            accelZ.size == expectedAccelSamples &&
            heartRate.isNotEmpty()

    companion object {
        const val WINDOW_SECONDS = 10
        const val ACCEL_HZ = 50
        const val HR_HZ = 1

        /** Wear DataItem path used by both modules. */
        const val DATA_PATH = "/aura/sensor/window"

        // DataMap keys (kept here so phone + watch can't drift).
        const val KEY_CAPTURED_AT = "captured_at_ms"
        const val KEY_WINDOW_SEC = "window_seconds"
        const val KEY_ACCEL_HZ = "accel_hz"
        const val KEY_ACCEL_X = "accel_x"
        const val KEY_ACCEL_Y = "accel_y"
        const val KEY_ACCEL_Z = "accel_z"
        const val KEY_HR = "heart_rate"
        const val KEY_TEMP = "skin_temp_c"
        const val KEY_BATTERY = "battery_pct"
    }
}
