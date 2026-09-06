package com.auraguard.phone.data

data class EventLogEntity(
    val id: Long = 0,
    val capturedAtMs: Long,
    val riskScore: Float,
    val label: String,
    val mode: String,
    val modelName: String,
    val heartRate: Float? = null,
    val temperatureC: Float? = null,
    val temperatureSource: String? = null,
    val signalQuality: Float = 0f,
    val dispatchedSos: Boolean = false,
    val userMarkedFalse: Boolean = false,
)
