package com.auraguard.phone.ml

import com.auraguard.shared.SensorPacket
import kotlin.math.sqrt

/** Exact feature order expected by the Aura wearable ONNX contract. */
object WearableFeatureExtractor {
    val featureNames = listOf(
        "accel_magnitude_mean",
        "accel_magnitude_std",
        "accel_magnitude_rms",
        "accel_magnitude_max",
        "accel_jerk_mean_abs",
        "accel_jerk_max_abs",
        "gyro_magnitude_mean",
        "gyro_magnitude_std",
        "gyro_magnitude_max",
        "heart_rate_mean",
        "heart_rate_std",
        "heart_rate_min",
        "heart_rate_max",
        "temperature_mean_c",
        "temperature_std_c",
        "battery_fraction",
        "accel_completeness",
        "gyro_available",
        "heart_rate_available",
        "temperature_available",
    )

    fun extract(packet: SensorPacket): FloatArray {
        val accel = magnitude(packet.accelX, packet.accelY, packet.accelZ)
        val gyro = magnitude(packet.gyroX, packet.gyroY, packet.gyroZ)
        val jerk = differences(accel).map { kotlin.math.abs(it) }.toFloatArray()

        return floatArrayOf(
            mean(accel), std(accel), rms(accel), max(accel), mean(jerk), max(jerk),
            mean(gyro), std(gyro), max(gyro),
            mean(packet.heartRate), std(packet.heartRate), min(packet.heartRate), max(packet.heartRate),
            mean(packet.temperatureC), std(packet.temperatureC),
            packet.batteryPct.coerceIn(0f, 1f).takeIf { packet.batteryPct >= 0f } ?: 0f,
            packet.accelCompleteness,
            if (packet.hasGyroscope) 1f else 0f,
            if (packet.heartRate.isNotEmpty()) 1f else 0f,
            if (packet.temperatureC.isNotEmpty()) 1f else 0f,
        )
    }

    fun motionPreview(packet: SensorPacket, points: Int = 100): FloatArray {
        val values = magnitude(packet.accelX, packet.accelY, packet.accelZ)
        if (values.isEmpty()) return FloatArray(0)
        return FloatArray(points.coerceAtMost(values.size)) { index ->
            values[(index * values.size / points).coerceAtMost(values.lastIndex)]
        }
    }

    private fun magnitude(x: FloatArray, y: FloatArray, z: FloatArray): FloatArray {
        val size = minOf(x.size, y.size, z.size)
        return FloatArray(size) { index -> sqrt(x[index] * x[index] + y[index] * y[index] + z[index] * z[index]) }
    }

    private fun differences(values: FloatArray): List<Float> =
        if (values.size < 2) emptyList() else (1 until values.size).map { values[it] - values[it - 1] }

    private fun mean(values: FloatArray): Float = if (values.isEmpty()) 0f else values.average().toFloat()
    private fun min(values: FloatArray): Float = values.minOrNull() ?: 0f
    private fun max(values: FloatArray): Float = values.maxOrNull() ?: 0f
    private fun rms(values: FloatArray): Float =
        if (values.isEmpty()) 0f else sqrt(values.sumOf { (it * it).toDouble() } / values.size).toFloat()

    private fun std(values: FloatArray): Float {
        if (values.size < 2) return 0f
        val mean = values.average()
        return sqrt(values.sumOf { (it - mean) * (it - mean) } / values.size).toFloat()
    }
}
