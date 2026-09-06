package com.auraguard.phone.ml

import com.auraguard.shared.SensorPacket
import com.auraguard.shared.TemperatureSource
import org.junit.Assert.assertEquals
import org.junit.Test

class WearableFeatureExtractorTest {
    @Test
    fun `feature vector follows published twenty-feature contract`() {
        val packet = SensorPacket(
            capturedAtMs = 1L,
            accelX = FloatArray(500) { 1f },
            accelY = FloatArray(500) { 2f },
            accelZ = FloatArray(500) { 3f },
            gyroX = FloatArray(500) { 0.1f },
            gyroY = FloatArray(500) { 0.2f },
            gyroZ = FloatArray(500) { 0.3f },
            heartRate = floatArrayOf(70f, 72f),
            temperatureC = floatArrayOf(33.1f, 33.3f),
            temperatureSource = TemperatureSource.WRIST_SKIN,
            batteryPct = 0.8f,
        )

        val features = WearableFeatureExtractor.extract(packet)

        assertEquals(WearableFeatureExtractor.featureNames.size, features.size)
        assertEquals(20, features.size)
        assertEquals(1f, features[16], 0.0001f)
        assertEquals(1f, features[17], 0.0001f)
        assertEquals(1f, features[18], 0.0001f)
        assertEquals(1f, features[19], 0.0001f)
    }

    @Test
    fun `missing optional sensors are represented by masks`() {
        val packet = SensorPacket(
            capturedAtMs = 1L,
            accelX = FloatArray(500),
            accelY = FloatArray(500),
            accelZ = FloatArray(500),
            heartRate = FloatArray(0),
        )

        val features = WearableFeatureExtractor.extract(packet)

        assertEquals(0f, features[17], 0.0001f)
        assertEquals(0f, features[18], 0.0001f)
        assertEquals(0f, features[19], 0.0001f)
    }
}
