package com.auraguard.wear.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material.*
import com.auraguard.shared.TemperatureSource
import com.auraguard.wear.WearState

private val BG     = Color(0xFF080D12)
private val CYAN   = Color(0xFF00FFD1)
private val SUBTLE = Color(0xFF3D5566)
private val TRACK  = Color(0xFF162130)

@Composable
fun MonitoringScreen(onSimulateAlert: () -> Unit) {
    val state by WearState.state.collectAsState()
    val heartTrans = rememberInfiniteTransition(label = "heartbeat")
    val heartScale by heartTrans.animateFloat(
        initialValue = 1f,
        targetValue = 1.30f,
        animationSpec = infiniteRepeatable(
            keyframes {
                durationMillis = 1200
                1f    at 0
                1.30f at 140
                1f    at 310
                1.12f at 450
                1f    at 600
            },
            RepeatMode.Restart,
        ),
        label = "heart_scale",
    )

    val monitoringFraction = if (state.monitoring) 1f else 0.15f

    Scaffold(
        timeText = {
            TimeText(timeTextStyle = TimeTextDefaults.timeTextStyle(color = SUBTLE, fontSize = 11.sp))
        },
        vignette = { Vignette(vignettePosition = VignettePosition.TopAndBottom) },
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(BG),
            contentAlignment = Alignment.Center,
        ) {
            // Risk arc ring painted behind content
            Canvas(modifier = Modifier.fillMaxSize()) {
                val sw  = 7.dp.toPx()
                val pad = sw / 2f + 3.dp.toPx()
                val arcSize = Size(size.width - pad * 2, size.height - pad * 2)
                val tl = Offset(pad, pad)

                drawArc(TRACK, -90f, 360f, false, tl, arcSize, style = Stroke(sw, cap = StrokeCap.Round))

                if (monitoringFraction > 0.01f) {
                    // Glow halo
                    drawArc(
                        CYAN.copy(alpha = 0.20f), -90f, 360f * monitoringFraction, false,
                        Offset(pad - 4f, pad - 4f),
                        Size(arcSize.width + 8f, arcSize.height + 8f),
                        style = Stroke(sw + 8f, cap = StrokeCap.Round),
                    )
                    // Arc fill
                    drawArc(CYAN, -90f, 360f * monitoringFraction, false, tl, arcSize,
                        style = Stroke(sw, cap = StrokeCap.Round))
                }
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.fillMaxSize(0.66f),
            ) {
                // Pulsing heart — size() * heartScale avoids graphicsLayer import
                Icon(
                    imageVector = Icons.Filled.Favorite,
                    contentDescription = "Heart rate",
                    tint = CYAN,
                    modifier = Modifier.size(18.dp * heartScale),
                )

                Spacer(Modifier.height(3.dp))

                Text(
                    state.heartRate?.let { "%.0f".format(it) } ?: "--",
                    color = Color.White,
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                )
                Text(
                    "BPM",
                    color = CYAN,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 2.sp,
                )

                Spacer(Modifier.height(4.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(3.dp),
                ) {
                    Box(Modifier.size(4.dp).clip(CircleShape).background(if (state.monitoring) CYAN else SUBTLE))
                    Text(
                        if (state.monitoring) "SENSORS ACTIVE" else "STARTING",
                        color = if (state.monitoring) CYAN else SUBTLE,
                        fontSize = 7.sp,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 1.sp,
                    )
                }

                Spacer(Modifier.height(5.dp))

                Text(
                    temperatureLabel(state.temperatureC, state.temperatureSource),
                    color = if (state.temperatureC != null) Color.White else SUBTLE,
                    fontSize = 7.sp,
                    fontFamily = FontFamily.Monospace,
                )

                Text(
                    buildString {
                        append(if (state.gyroAvailable) "GYRO" else "NO GYRO")
                        state.batteryPct?.let { append(" · ${"%.0f".format(it * 100)}%") }
                    },
                    color = SUBTLE,
                    fontSize = 6.sp,
                    fontFamily = FontFamily.Monospace,
                )

                Spacer(Modifier.height(5.dp))

                Chip(
                    onClick = onSimulateAlert,
                    colors = ChipDefaults.chipColors(
                        backgroundColor = Color(0xFF162130),
                        contentColor = CYAN,
                    ),
                    label = {
                        Text(
                            "TEST ALERT",
                            fontSize = 8.sp,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp,
                        )
                    },
                    modifier = Modifier
                        .width(82.dp)
                        .height(24.dp),
                )
            }
        }
    }
}

private fun temperatureLabel(value: Float?, source: TemperatureSource): String {
    if (value == null) return "TEMP UNAVAILABLE"
    val label = when (source) {
        TemperatureSource.WRIST_SKIN -> "SKIN"
        TemperatureSource.AMBIENT -> "AMBIENT"
        TemperatureSource.EXTERNAL -> "EXTERNAL"
        TemperatureSource.SIMULATED -> "TEST"
        TemperatureSource.UNAVAILABLE -> "TEMP"
    }
    return "$label ${"%.1f".format(value)} C"
}
