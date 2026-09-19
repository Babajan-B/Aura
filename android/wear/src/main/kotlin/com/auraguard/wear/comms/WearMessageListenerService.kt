package com.auraguard.wear.comms

import android.util.Log
import com.auraguard.shared.DemoEvent
import com.auraguard.shared.SensorPacket
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.WearableListenerService
import kotlinx.serialization.json.Json

/**
 * Receives the phone's alert message ([SensorPacket.ALERT_PATH]) and hands it
 * to [WearAlertBus] so the watch UI can raise the countdown screen.
 */
class WearMessageListenerService : WearableListenerService() {

    override fun onMessageReceived(event: MessageEvent) {
        when (event.path) {
            SensorPacket.ALERT_PATH -> {
                decode(event, DemoEvent.Type.SEIZURE)?.let { demo ->
                    Log.w(TAG, "alert ${demo.eventId} received from phone -> raising countdown")
                    WearAlertBus.triggerAlert(demo)
                }
            }
            SensorPacket.DEMO_MOTION_PATH -> {
                decode(event, DemoEvent.Type.MOTION)?.let { demo ->
                    Log.i(TAG, "motion demo ${demo.eventId} received from phone")
                    WearAlertBus.triggerMotionDemo(demo)
                }
            }
        }
    }

    private fun decode(event: MessageEvent, fallbackType: DemoEvent.Type): DemoEvent? {
        if (event.data.isEmpty()) {
            val seizure = fallbackType == DemoEvent.Type.SEIZURE
            return DemoEvent(
                eventId = "LEGACY-${System.currentTimeMillis()}",
                capturedAtMs = System.currentTimeMillis(),
                type = fallbackType,
                risk = if (seizure) 0.9f else 0.42f,
                heartRate = if (seizure) 96f else 92f,
                temperatureC = if (seizure) 34f else 33.7f,
            )
        }
        return runCatching {
            Json.decodeFromString<DemoEvent>(event.data.decodeToString())
        }.onFailure { Log.e(TAG, "invalid demo event payload", it) }.getOrNull()
    }

    companion object {
        private const val TAG = "WearMessageListener"
    }
}
