package com.auraguard.wear.comms

import com.auraguard.shared.DemoEvent
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
    private val _alerts = MutableStateFlow<DemoEvent?>(null)
    val alerts: StateFlow<DemoEvent?> = _alerts.asStateFlow()
    private val _motionDemos = MutableStateFlow<DemoEvent?>(null)
    val motionDemos: StateFlow<DemoEvent?> = _motionDemos.asStateFlow()

    fun triggerAlert(event: DemoEvent) {
        _alerts.value = event
    }

    fun triggerMotionDemo(event: DemoEvent) {
        _motionDemos.value = event
    }
}
