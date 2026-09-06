package com.auraguard.phone

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.auraguard.phone.ui.DashboardScreen
import com.auraguard.phone.ui.EventLogScreen
import com.auraguard.phone.ui.IntroScreen
import com.auraguard.phone.ui.SettingsScreen

private val DarkColors = darkColorScheme(
    primary          = Color(0xFF00FFD1),
    onPrimary        = Color(0xFF0D1117),
    secondary        = Color(0xFFFFBF24),
    onSecondary      = Color(0xFF0D1117),
    background       = Color(0xFF0D1117),
    onBackground     = Color(0xFFE6EDF3),
    surface          = Color(0xFF161B22),
    onSurface        = Color(0xFFE6EDF3),
    surfaceVariant   = Color(0xFF1C2128),
    onSurfaceVariant = Color(0xFF8B949E),
    error            = Color(0xFFFF2E6C),
    onError          = Color(0xFF0D1117),
    outline          = Color(0xFF30363D),
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = DarkColors) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Color(0xFF0D1117),
                ) {
                    AuraGuardApp()
                }
            }
        }
    }
}

@Composable
private fun AuraGuardApp() {
    var showIntro by rememberSaveable { mutableStateOf(true) }
    var tab by remember { mutableStateOf(Tab.Dashboard) }
    if (showIntro) {
        IntroScreen(onEnterDemo = { showIntro = false })
        return
    }
    Scaffold(
        containerColor = Color(0xFF0D1117),
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(Color(0xFF0D1117)),
        ) {
            when (tab) {
                Tab.Dashboard -> DashboardScreen(
                    onOpenLog = { tab = Tab.Log },
                    onOpenSettings = { tab = Tab.Settings },
                )
                Tab.Log       -> EventLogScreen(onBack = { tab = Tab.Dashboard })
                Tab.Settings  -> SettingsScreen(onBack = { tab = Tab.Dashboard })
            }
        }
    }
}

private enum class Tab { Dashboard, Log, Settings }
