package com.auraguard.wear.comms

import android.util.Log
import com.auraguard.shared.SensorPacket
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.WearableListenerService

/**
 * Receives the phone's alert message ([SensorPacket.ALERT_PATH]) and hands it
 * to [WearAlertBus] so the watch UI can raise the countdown screen.
 */
class WearMessageListenerService : WearableListenerService() {

    override fun onMessageReceived(event: MessageEvent) {
        if (event.path == SensorPacket.ALERT_PATH) {
            Log.w(TAG, "alert received from phone → raising countdown")
            WearAlertBus.triggerAlert()
        }
    }

    companion object {
        private const val TAG = "WearMessageListener"
    }
}
