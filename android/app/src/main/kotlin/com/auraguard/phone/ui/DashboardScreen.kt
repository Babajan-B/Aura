package com.auraguard.phone.ui

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BatteryFull
import androidx.compose.material.icons.filled.DeviceThermostat
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Sensors
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.auraguard.phone.AuraState
import com.auraguard.phone.RiskPipeline
import com.auraguard.shared.MonitoringMode
import com.auraguard.shared.TemperatureSource
import kotlinx.coroutines.delay
import kotlin.math.max
import kotlin.math.min

private val BG = Color(0xFF0D1117)
private val SURFACE = Color(0xFF161B22)
private val CYAN = Color(0xFF00E5C2)
private val AMBER = Color(0xFFFFBF24)
private val PINK = Color(0xFFFF2E6C)
private val SUBTLE = Color(0xFF8B949E)
private val BORDER = Color(0xFF30363D)

@Composable
fun DashboardScreen(onOpenLog: () -> Unit, onOpenSettings: () -> Unit) {
    val state by AuraState.state.collectAsState()
    val context = LocalContext.current

    LaunchedEffect(state.mode, state.demoRunning) {
        while (state.mode == MonitoringMode.DEMO && state.demoRunning) {
            delay(1_000)
            RiskPipeline.tickDemo()
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().background(BG).verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Header(state)
        ModeSelector(state.mode) { RiskPipeline.setMode(it) }
        if (state.mode == MonitoringMode.DEMO) {
            DemoControls(
                state = state,
                onStart = { RiskPipeline.startDemo() },
                onPause = { RiskPipeline.pauseDemo() },
                onAlert = { RiskPipeline.triggerTestCountdown(context) },
                onReset = { RiskPipeline.resetDemo() },
            )
        }
        if (state.alertStatus != AuraState.AlertStatus.MONITORING) {
            AlertCard(
                state = state,
                onCancel = { RiskPipeline.cancelPhoneAlert(context) },
                onElapsed = { RiskPipeline.onPhoneCountdownElapsed(context) },
            )
        }
        RiskGaugeCard(state)
        SignalCard(state)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard(
                Modifier.weight(1f), "HEART RATE", state.heartRate?.let { "%.0f".format(it) } ?: "--",
                "BPM", Icons.Filled.Favorite, PINK,
            )
            MetricCard(
                Modifier.weight(1f), temperatureTitle(state.temperatureSource),
                state.temperatureC?.let { "%.1f".format(it) } ?: "--", "C",
                Icons.Filled.DeviceThermostat, AMBER,
            )
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard(
                Modifier.weight(1f), "WATCH BATTERY",
                state.batteryPct?.let { "%.0f".format(it * 100) } ?: "--", "%",
                Icons.Filled.BatteryFull, CYAN,
            )
            MetricCard(
                Modifier.weight(1f), "SIGNAL QUALITY",
                "%.0f".format(state.accelCompleteness * 100), "%",
                Icons.Filled.Sensors, qualityColor(state.accelCompleteness),
            )
        }
        TemperatureContext(state)
        ConnectionCard(state)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            ActionButton("EVENTS", Modifier.weight(1f), onOpenLog)
            ActionButton("SETTINGS", Modifier.weight(1f), onOpenSettings)
        }
        Spacer(Modifier.height(6.dp))
    }
}

@Composable
private fun DemoControls(
    state: AuraState.Snapshot,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onAlert: () -> Unit,
    onReset: () -> Unit,
) {
    NeonCard(border = AMBER) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(Modifier.weight(1f)) {
                    Text("LIVE DEMO CONTROLS", color = AMBER, fontSize = 10.sp,
                        fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    Text(state.demoStage, color = SUBTLE, fontSize = 9.sp)
                }
                Text("SIMULATED", color = AMBER, fontSize = 8.sp, fontWeight = FontWeight.Bold)
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Button(
                    onClick = if (state.demoRunning) onPause else onStart,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = if (state.demoRunning) SURFACE else CYAN),
                    border = if (state.demoRunning) BorderStroke(1.dp, BORDER) else null,
                ) {
                    Icon(if (state.demoRunning) Icons.Filled.Pause else Icons.Filled.PlayArrow, null,
                        modifier = Modifier.size(15.dp), tint = if (state.demoRunning) CYAN else BG)
                    Spacer(Modifier.width(4.dp))
                    Text(if (state.demoRunning) "PAUSE" else "START", color = if (state.demoRunning) CYAN else BG,
                        fontSize = 9.sp)
                }
                Button(
                    onClick = onAlert,
                    enabled = state.alertStatus != AuraState.AlertStatus.COUNTDOWN,
                    modifier = Modifier.weight(1.35f),
                    colors = ButtonDefaults.buttonColors(containerColor = AMBER, disabledContainerColor = BORDER),
                ) {
                    Icon(Icons.Filled.Warning, null, modifier = Modifier.size(15.dp), tint = BG)
                    Spacer(Modifier.width(4.dp))
                    Text("TEST ALERT", color = BG, fontSize = 9.sp)
                }
                Button(
                    onClick = onReset,
                    modifier = Modifier.weight(0.8f),
                    colors = ButtonDefaults.buttonColors(containerColor = SURFACE),
                    border = BorderStroke(1.dp, BORDER),
                ) { Text("RESET", color = SUBTLE, fontSize = 9.sp) }
            }
            Text("Presentation simulation only. No patient data, diagnosis, SMS, or emergency call.",
                color = SUBTLE, fontSize = 8.sp)
        }
    }
}

@Composable
private fun Header(state: AuraState.Snapshot) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween) {
        Column {
            Text("AURA GUARD", color = CYAN, fontSize = 22.sp, fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace, letterSpacing = 3.sp)
            Text("Wearable seizure-safety research prototype", color = SUBTLE, fontSize = 10.sp)
        }
        val label = if (state.mode == MonitoringMode.DEMO) "TEST" else if (state.connected) "LIVE" else "WAIT"
        Text(label, color = if (state.mode == MonitoringMode.DEMO) AMBER else CYAN,
            fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
    }
}

@Composable
private fun ModeSelector(selected: MonitoringMode, onSelect: (MonitoringMode) -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        listOf(
            MonitoringMode.DEMO to "Demo",
            MonitoringMode.WEARABLE to "Wearable",
            MonitoringMode.EEG_RESEARCH to "EEG research",
        ).forEach { (mode, label) ->
            FilterChip(
                selected = selected == mode,
                onClick = { onSelect(mode) },
                label = { Text(label, fontSize = 10.sp) },
                modifier = Modifier.weight(1f),
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = CYAN.copy(alpha = 0.16f),
                    selectedLabelColor = CYAN,
                    containerColor = SURFACE,
                    labelColor = SUBTLE,
                ),
                border = FilterChipDefaults.filterChipBorder(
                    enabled = true,
                    selected = selected == mode,
                    borderColor = BORDER,
                    selectedBorderColor = CYAN,
                ),
            )
        }
    }
}

@Composable
private fun AlertCard(state: AuraState.Snapshot, onCancel: () -> Unit, onElapsed: () -> Unit) {
    var remaining by remember(state.alertStartedAtMs) { mutableIntStateOf(15) }
    LaunchedEffect(state.alertStartedAtMs) {
        if (state.alertStatus != AuraState.AlertStatus.COUNTDOWN) return@LaunchedEffect
        while (remaining > 0) {
            delay(1_000)
            remaining--
        }
        onElapsed()
    }
    NeonCard(border = if (state.alertStatus == AuraState.AlertStatus.COUNTDOWN) AMBER else BORDER) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(if (state.alertIsTest) "TEST ALERT" else "SAFETY ALERT", color = AMBER,
                    fontWeight = FontWeight.Bold, fontSize = 12.sp)
                Text(state.alertMessage ?: state.alertStatus.name, color = SUBTLE, fontSize = 10.sp)
            }
            if (state.alertStatus == AuraState.AlertStatus.COUNTDOWN) {
                Text("$remaining", color = AMBER, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.width(8.dp))
                Button(onClick = onCancel, colors = ButtonDefaults.buttonColors(containerColor = AMBER)) {
                    Text("I'M OK", color = BG, fontSize = 10.sp)
                }
            }
        }
    }
}

@Composable
private fun RiskGaugeCard(state: AuraState.Snapshot) {
    val risk = state.movingAvgRisk
    val gaugeColor = when {
        risk == null -> SUBTLE
        risk >= 0.75f -> PINK
        risk >= 0.50f -> AMBER
        else -> CYAN
    }
    val status = when {
        risk == null -> "UNAVAILABLE"
        risk >= 0.75f -> "HIGH RISK"
        risk >= 0.50f -> "ELEVATED"
        else -> "STABLE"
    }
    val animated by animateFloatAsState(risk ?: 0f, tween(900, easing = FastOutSlowInEasing), label = "risk")
    NeonCard {
        Column(Modifier.fillMaxWidth().padding(18.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            SectionLabel("SEIZURE-RISK SCORE")
            Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(vertical = 8.dp)) {
                Canvas(Modifier.size(164.dp)) {
                    val stroke = 14.dp.toPx()
                    val inset = stroke / 2
                    val arcSize = Size(size.width - stroke, size.height - stroke)
                    drawArc(BORDER, 135f, 270f, false, Offset(inset, inset), arcSize,
                        style = Stroke(stroke, cap = StrokeCap.Round))
                    if (risk != null) drawArc(gaugeColor, 135f, 270f * animated, false,
                        Offset(inset, inset), arcSize, style = Stroke(stroke, cap = StrokeCap.Round))
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(risk?.let { "%.0f%%".format(it * 100) } ?: "--", color = gaugeColor,
                        fontSize = 44.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    Text(status, color = gaugeColor, fontSize = 9.sp, letterSpacing = 2.sp)
                }
            }
            Text(state.modelName, color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
            if (state.predictionStatus != AuraState.PredictionStatus.ACTIVE &&
                state.predictionStatus != AuraState.PredictionStatus.DEMO) {
                Text("No alert decisions are made without a compatible model.", color = AMBER,
                    fontSize = 9.sp, modifier = Modifier.padding(top = 4.dp))
            }
        }
    }
}

@Composable
private fun SignalCard(state: AuraState.Snapshot) {
    val title = when (state.mode) {
        MonitoringMode.DEMO -> "DEMO SIGNAL PREVIEW"
        MonitoringMode.WEARABLE -> "WATCH MOTION"
        MonitoringMode.EEG_RESEARCH -> "EEG STREAM"
    }
    NeonCard {
        Column(Modifier.fillMaxWidth().padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                SectionLabel(title)
                Spacer(Modifier.width(8.dp))
                Text(if (state.motionPreview.isEmpty()) "NO DATA" else "AVAILABLE", color = CYAN, fontSize = 8.sp)
            }
            Canvas(Modifier.fillMaxWidth().height(70.dp).padding(top = 8.dp)) {
                val values = state.motionPreview
                if (values.size < 2) {
                    drawLine(BORDER, Offset(0f, size.height / 2), Offset(size.width, size.height / 2), 2f)
                    return@Canvas
                }
                val low = values.minOrNull() ?: 0f
                val high = values.maxOrNull() ?: 1f
                val range = max(high - low, 0.001f)
                val path = Path()
                values.forEachIndexed { index, value ->
                    val x = size.width * index / (values.size - 1)
                    val y = size.height - ((value - low) / range * size.height)
                    if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
                }
                drawPath(path, CYAN, style = Stroke(2f, cap = StrokeCap.Round))
            }
            val detail = when (state.mode) {
                MonitoringMode.DEMO -> "Controlled presentation input; not a patient recording"
                MonitoringMode.WEARABLE -> "10 s window · accelerometer${if (state.gyroAvailable) " + gyroscope" else ""}"
                MonitoringMode.EEG_RESEARCH -> "Connect a validated EEG stream to enable this mode"
            }
            Text(detail, color = SUBTLE, fontSize = 9.sp)
        }
    }
}

@Composable
private fun MetricCard(modifier: Modifier, label: String, value: String, unit: String,
    icon: ImageVector, color: Color) {
    NeonCard(modifier) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(icon, null, tint = color, modifier = Modifier.size(15.dp))
                Spacer(Modifier.width(6.dp))
                Text(label, color = SUBTLE, fontSize = 8.sp)
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Text(value, color = color, fontSize = 30.sp, fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace)
                Spacer(Modifier.width(3.dp))
                Text(unit, color = color.copy(alpha = 0.7f), fontSize = 10.sp,
                    modifier = Modifier.padding(bottom = 4.dp))
            }
        }
    }
}

@Composable
private fun TemperatureContext(state: AuraState.Snapshot) {
    NeonCard {
        Column(Modifier.padding(14.dp)) {
            SectionLabel("TEMPERATURE CONTEXT")
            Spacer(Modifier.height(5.dp))
            val message = when {
                state.temperatureC == null -> "No compatible temperature source is available."
                state.temperatureSource == TemperatureSource.AMBIENT ->
                    "Ambient measurement; it is not labelled or interpreted as skin temperature."
                state.temperatureBaselineC != null -> {
                    val delta = state.temperatureC - state.temperatureBaselineC
                    "Personal baseline ${"%.1f".format(state.temperatureBaselineC)} C · change ${"%+.1f".format(delta)} C"
                }
                else -> "Baseline is being established; temperature cannot trigger an alert alone."
            }
            Text(message, color = SUBTLE, fontSize = 10.sp)
        }
    }
}

@Composable
private fun ConnectionCard(state: AuraState.Snapshot) {
    NeonCard {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(9.dp).background(
                if (state.connected) CYAN else if (state.mode == MonitoringMode.DEMO) AMBER else SUBTLE,
                CircleShape,
            ))
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(when {
                    state.mode == MonitoringMode.DEMO && state.demoRunning -> "SIMULATED STREAM ACTIVE"
                    state.mode == MonitoringMode.DEMO -> "DEMO MODE READY"
                    state.connected -> "WATCH DATA RECEIVED"
                    else -> "WAITING FOR WATCH"
                }, color = if (state.connected) CYAN else SUBTLE, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                Text("Gyroscope ${if (state.gyroAvailable) "available" else "unavailable"} · ${ageLabel(state.updatedAtMs)}",
                    color = SUBTLE, fontSize = 9.sp)
            }
        }
    }
}

@Composable
private fun ActionButton(label: String, modifier: Modifier, onClick: () -> Unit) {
    Button(onClick = onClick, modifier = modifier, shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(containerColor = SURFACE, contentColor = CYAN),
        border = BorderStroke(1.dp, BORDER)) {
        Text(label, fontFamily = FontFamily.Monospace, fontSize = 10.sp, letterSpacing = 1.sp)
    }
}

@Composable
private fun NeonCard(modifier: Modifier = Modifier, border: Color = BORDER, content: @Composable () -> Unit) {
    Card(modifier = modifier.fillMaxWidth(), shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = SURFACE), border = BorderStroke(1.dp, border)) {
        content()
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(text, color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace, letterSpacing = 2.sp)
}

private fun temperatureTitle(source: TemperatureSource): String = when (source) {
    TemperatureSource.WRIST_SKIN -> "SKIN TEMP"
    TemperatureSource.AMBIENT -> "AMBIENT TEMP"
    TemperatureSource.EXTERNAL -> "EXTERNAL TEMP"
    TemperatureSource.SIMULATED -> "DEMO TEMP"
    TemperatureSource.UNAVAILABLE -> "TEMPERATURE"
}

private fun qualityColor(value: Float): Color = when {
    value >= 0.8f -> CYAN
    value >= 0.5f -> AMBER
    else -> PINK
}

private fun ageLabel(updatedAtMs: Long): String {
    if (updatedAtMs <= 0) return "no recent reading"
    val seconds = ((System.currentTimeMillis() - updatedAtMs) / 1_000).coerceAtLeast(0)
    return if (seconds < 60) "updated ${seconds}s ago" else "updated ${seconds / 60}m ago"
}
