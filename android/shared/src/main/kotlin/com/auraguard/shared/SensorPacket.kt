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
 *  - gyroX/Y/Z       : optional gyroscope samples in rad/s.
 *  - heartRate       : heart-rate samples (bpm); cadence varies by device.
 *  - temperatureC    : optional temperature samples; empty if unavailable.
 *  - temperatureSource: identifies skin, ambient, external, or simulated data.
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
    val gyroX: FloatArray = FloatArray(0),
    val gyroY: FloatArray = FloatArray(0),
    val gyroZ: FloatArray = FloatArray(0),
    val heartRate: FloatArray,
    val temperatureC: FloatArray = FloatArray(0),
    val temperatureSource: TemperatureSource = TemperatureSource.UNAVAILABLE,
    val batteryPct: Float = -1f,
) {
    /** Total samples we expect on the accel channels for a complete window. */
    val expectedAccelSamples: Int get() = windowSeconds * accelHz

    val accelCompleteness: Float
        get() = (minOf(accelX.size, accelY.size, accelZ.size).toFloat() /
            expectedAccelSamples.coerceAtLeast(1)).coerceIn(0f, 1f)

    val hasGyroscope: Boolean
        get() = gyroX.isNotEmpty() && gyroY.isNotEmpty() && gyroZ.isNotEmpty()

    /** Motion is the minimum required modality; all health sensors are optional. */
    fun isUsable(): Boolean =
        minOf(accelX.size, accelY.size, accelZ.size) >= expectedAccelSamples / 2

    companion object {
        const val WINDOW_SECONDS = 10
        const val ACCEL_HZ = 50
        const val HR_HZ = 1

        /** Wear DataItem path used by both modules. */
        const val DATA_PATH = "/aura/sensor/window"

        /** MessageClient path: phone → watch, asking it to raise the countdown. */
        const val ALERT_PATH = "/aura/alert"
        const val SOS_PATH = "/aura/sos"
        const val CANCEL_PATH = "/aura/cancel"

        // DataMap keys (kept here so phone + watch can't drift).
        const val KEY_CAPTURED_AT = "captured_at_ms"
        const val KEY_WINDOW_SEC = "window_seconds"
        const val KEY_ACCEL_HZ = "accel_hz"
        const val KEY_ACCEL_X = "accel_x"
        const val KEY_ACCEL_Y = "accel_y"
        const val KEY_ACCEL_Z = "accel_z"
        const val KEY_GYRO_X = "gyro_x"
        const val KEY_GYRO_Y = "gyro_y"
        const val KEY_GYRO_Z = "gyro_z"
        const val KEY_HR = "heart_rate"
        const val KEY_TEMP = "temperature_c"
        const val KEY_TEMP_SOURCE = "temperature_source"
        const val KEY_BATTERY = "battery_pct"
    }
}

@Serializable
enum class MonitoringMode {
    DEMO,
    WEARABLE,
    EEG_RESEARCH,
}

@Serializable
enum class TemperatureSource {
    WRIST_SKIN,
    AMBIENT,
    EXTERNAL,
    SIMULATED,
    UNAVAILABLE,
}
