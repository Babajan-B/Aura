package com.auraguard.shared

import kotlinx.serialization.Serializable

/** One controlled presentation event shared verbatim by phone and watch. */
@Serializable
data class DemoEvent(
    val eventId: String,
    val capturedAtMs: Long,
    val type: Type,
    val risk: Float,
    val heartRate: Float,
    val temperatureC: Float,
) {
    @Serializable
    enum class Type { MOTION, SEIZURE }
}
