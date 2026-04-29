package com.auraguard.wear

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.wear.compose.material.MaterialTheme
import com.auraguard.wear.ui.AlertCountdownScreen
import com.auraguard.wear.ui.MonitoringScreen

/**
 * Watch entry point. Hosts a tiny in-memory state machine that flips
 * between the steady-state monitoring screen and the alert countdown.
 *
 * In the real app this graduates to wear navigation + ViewModel that
 * listens for risk updates pushed from [com.auraguard.wear.comms.PhoneBridge].
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                AuraWatchApp()
            }
        }
    }
}

@Composable
private fun AuraWatchApp() {
    var screen by remember { mutableStateOf<Screen>(Screen.Monitoring) }
    when (val s = screen) {
        Screen.Monitoring -> MonitoringScreen(
            onSimulateAlert = { screen = Screen.Alert },
        )
        Screen.Alert -> AlertCountdownScreen(
            onDismiss = { screen = Screen.Monitoring },
            onConfirm = { screen = Screen.Monitoring /* TODO: trigger SOS via PhoneBridge */ },
        )
    }
}

private sealed interface Screen {
    data object Monitoring : Screen
    data object Alert : Screen
}
