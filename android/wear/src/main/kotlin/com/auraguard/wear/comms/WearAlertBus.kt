package com.auraguard.wear.comms

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Process-wide bus that lets [WearMessageListenerService] (which receives the
 * phone's /aura/alert message on a background thread) signal the Compose UI in
 * [com.auraguard.wear.MainActivity] to show the countdown.
 *
 * The value is a monotonically increasing timestamp; the UI reacts to changes.
 */
object WearAlertBus {
    private val _alerts = MutableStateFlow(0L)
    val alerts: StateFlow<Long> = _alerts.asStateFlow()

    fun triggerAlert() {
        _alerts.value = System.currentTimeMillis()
    }
}
