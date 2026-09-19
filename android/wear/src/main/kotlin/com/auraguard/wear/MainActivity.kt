package com.auraguard.wear

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.wear.compose.material.MaterialTheme
import com.auraguard.wear.comms.WearAlertBus
import com.auraguard.wear.comms.PhoneBridge
import com.auraguard.wear.sensors.SensorService
import com.auraguard.wear.ui.AlertConfirmedScreen
import com.auraguard.wear.ui.CountdownScreen
import com.auraguard.wear.ui.MonitoringScreen
import com.auraguard.wear.ui.MotionDemoScreen
import com.auraguard.shared.DemoEvent
import kotlinx.coroutines.flow.drop

/**
 * Watch entry point. Hosts the three-state demo flow that mirrors the web
 * dashboard's WatchFace component:
 *
 *   Monitoring ──(pre-ictal)──▶ Countdown ──(15s elapses)──▶ Alert confirmed
 *        ▲                          │  "I'M OK"                    │ (auto)
 *        └──────────────────────────┴──────────────────────────────┘
 *
 * In production this graduates to wear navigation + a ViewModel driven by
 * risk updates pushed from [com.auraguard.wear.comms.PhoneBridge].
 */
class MainActivity : ComponentActivity() {

    private lateinit var phoneBridge: PhoneBridge

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { startMonitoringService() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        phoneBridge = PhoneBridge(applicationContext)
        ensurePermissionsAndStart()
        setContent {
            MaterialTheme {
                AuraWatchApp(phoneBridge)
            }
        }
    }

    private fun ensurePermissionsAndStart() {
        val permissions = buildList {
            add(Manifest.permission.BODY_SENSORS)
            add(Manifest.permission.ACTIVITY_RECOGNITION)
            if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isEmpty()) startMonitoringService() else permissionLauncher.launch(missing.toTypedArray())
    }

    private fun startMonitoringService() {
        ContextCompat.startForegroundService(this, Intent(this, SensorService::class.java))
    }
}

@Composable
private fun AuraWatchApp(phoneBridge: PhoneBridge) {
    var screen by remember { mutableStateOf<Screen>(Screen.Monitoring) }
    var alertEvent by remember { mutableStateOf<DemoEvent?>(null) }
    var motionEvent by remember { mutableStateOf<DemoEvent?>(null) }

    // Phone gate tripped → /aura/alert message → raise the countdown.
    // drop(1) skips the initial flow value so we only react to real alerts.
    LaunchedEffect(Unit) {
        WearAlertBus.alerts.drop(1).collect { event ->
            if (event != null) {
                alertEvent = event
                screen = Screen.Countdown
            }
        }
    }
    LaunchedEffect(Unit) {
        WearAlertBus.motionDemos.drop(1).collect { event ->
            if (event != null) {
                motionEvent = event
                screen = Screen.MotionDemo
            }
        }
    }

    AnimatedContent(
        targetState = screen,
        transitionSpec = { fadeIn() togetherWith fadeOut() },
        label = "screen",
    ) { s ->
        when (s) {
            Screen.Monitoring -> MonitoringScreen(
                onSimulateAlert = {
                    phoneBridge.requestSeizureTest()
                    screen = Screen.Countdown
                },
            )
            Screen.Countdown -> CountdownScreen(
                event = alertEvent,
                onDismiss = {
                    phoneBridge.cancelAlert()
                    screen = Screen.Monitoring
                },
                onElapsed = {
                    phoneBridge.confirmSos()
                    screen = Screen.Alert
                },
            )
            Screen.Alert -> AlertConfirmedScreen(
                onReset = { screen = Screen.Monitoring },
            )
            Screen.MotionDemo -> MotionDemoScreen(
                event = motionEvent,
                onComplete = { screen = Screen.Monitoring },
            )
        }
    }
}

private sealed interface Screen {
    data object Monitoring : Screen
    data object Countdown : Screen
    data object Alert : Screen
    data object MotionDemo : Screen
}
