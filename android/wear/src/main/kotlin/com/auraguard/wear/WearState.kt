package com.auraguard.wear

import com.auraguard.shared.TemperatureSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object WearState {
    data class Snapshot(
        val monitoring: Boolean = false,
        val heartRate: Float? = null,
        val temperatureC: Float? = null,
        val temperatureSource: TemperatureSource = TemperatureSource.UNAVAILABLE,
        val batteryPct: Float? = null,
        val accelAvailable: Boolean = false,
        val gyroAvailable: Boolean = false,
        val heartRateAvailable: Boolean = false,
        val updatedAtMs: Long = 0L,
    )

    private val _state = MutableStateFlow(Snapshot())
    val state: StateFlow<Snapshot> = _state.asStateFlow()

    fun capabilities(accel: Boolean, gyro: Boolean, heartRate: Boolean, tempSource: TemperatureSource) {
        _state.value = _state.value.copy(
            monitoring = true,
            accelAvailable = accel,
            gyroAvailable = gyro,
            heartRateAvailable = heartRate,
            temperatureSource = tempSource,
        )
    }

    fun readings(
        heartRate: Float?,
        temperatureC: Float?,
        temperatureSource: TemperatureSource,
        batteryPct: Float?,
        updatedAtMs: Long,
    ) {
        _state.value = _state.value.copy(
            monitoring = true,
            heartRate = heartRate,
            temperatureC = temperatureC,
            temperatureSource = temperatureSource,
            batteryPct = batteryPct,
            updatedAtMs = updatedAtMs,
        )
    }
}
