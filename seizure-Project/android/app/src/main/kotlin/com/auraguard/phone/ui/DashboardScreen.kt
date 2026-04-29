package com.auraguard.phone.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.*

private val BG      = Color(0xFF0D1117)
private val SURFACE = Color(0xFF161B22)
private val CYAN    = Color(0xFF00FFD1)
private val AMBER   = Color(0xFFFFBF24)
private val PINK    = Color(0xFFFF2E6C)
private val SUBTLE  = Color(0xFF8B949E)
private val BORDER  = Color(0xFF30363D)

@Composable
fun DashboardScreen(onOpenLog: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BG)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        HeaderRow()
        RiskGaugeCard(riskScore = 0.12f)
        EegWaveformCard()
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StatCard(
                modifier = Modifier.weight(1f),
                label = "HEART RATE",
                value = "72",
                unit = "BPM",
                icon = Icons.Filled.Favorite,
                color = PINK,
            )
            StatCard(
                modifier = Modifier.weight(1f),
                label = "WATCH BATT",
                value = "81",
                unit = "%",
                icon = Icons.Filled.BatteryFull,
                color = CYAN,
            )
        }
        ConnectionStatusCard()
        Button(
            onClick = onOpenLog,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = SURFACE, contentColor = CYAN),
            shape = RoundedCornerShape(12.dp),
            border = BorderStroke(1.dp, BORDER),
        ) {
            Icon(Icons.AutoMirrored.Filled.List, contentDescription = null, modifier = Modifier.size(14.dp))
            Spacer(Modifier.width(8.dp))
            Text(
                "VIEW EVENT LOG",
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                letterSpacing = 2.sp,
            )
        }
        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun HeaderRow() {
    val pulse = rememberInfiniteTransition(label = "header_pulse")
    val dotAlpha by pulse.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "dot_a",
    )
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column {
            Text(
                "AURA GUARD",
                color = CYAN,
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 4.sp,
            )
            Text(
                "Neural Seizure Guardian",
                color = SUBTLE,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
            )
        }
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Box(
                Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(CYAN.copy(alpha = dotAlpha)),
            )
            Text(
                "LIVE",
                color = CYAN.copy(alpha = dotAlpha),
                fontSize = 9.sp,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 2.sp,
            )
        }
    }
}

@Composable
private fun RiskGaugeCard(riskScore: Float) {
    val gaugeColor = when {
        riskScore >= 0.75f -> PINK
        riskScore >= 0.50f -> AMBER
        else               -> CYAN
    }
    val statusLabel = when {
        riskScore >= 0.75f -> "ALERT"
        riskScore >= 0.50f -> "CAUTION"
        else               -> "STABLE"
    }
    val animScore by animateFloatAsState(
        targetValue = riskScore,
        animationSpec = tween(1400, easing = FastOutSlowInEasing),
        label = "gauge_anim",
    )

    NeonCard {
        Column(
            modifier = Modifier.fillMaxWidth().padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            SectionLabel("PRE-ICTAL RISK SCORE")
            Spacer(Modifier.height(16.dp))
            Box(contentAlignment = Alignment.Center) {
                Canvas(Modifier.size(190.dp)) {
                    val sw = 16.dp.toPx()
                    val inset = sw / 2f
                    val arcRect = Size(size.width - sw, size.height - sw)
                    val tl = Offset(inset, inset)
                    // Background track
                    drawArc(BORDER, 135f, 270f, false, tl, arcRect, style = Stroke(sw, cap = StrokeCap.Round))
                    // Risk fill + glow
                    if (animScore > 0.005f) {
                        drawArc(
                            gaugeColor.copy(alpha = 0.18f), 135f, 270f * animScore, false,
                            Offset(inset - 6f, inset - 6f),
                            Size(arcRect.width + 12f, arcRect.height + 12f),
                            style = Stroke(sw + 12f, cap = StrokeCap.Round),
                        )
                        drawArc(gaugeColor, 135f, 270f * animScore, false, tl, arcRect,
                            style = Stroke(sw, cap = StrokeCap.Round))
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        "%.0f%%".format(animScore * 100),
                        color = gaugeColor,
                        fontSize = 52.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                    )
                    Text(
                        statusLabel,
                        color = gaugeColor,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 4.sp,
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("RGF-Net · 37KB INT8", color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text("Updated 4s ago", color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
            }
        }
    }
}

@Composable
private fun EegWaveformCard() {
    val anim = rememberInfiniteTransition(label = "eeg_anim")
    val phase by anim.animateFloat(
        initialValue = 0f,
        targetValue = 2f * PI.toFloat(),
        animationSpec = infiniteRepeatable(tween(2200, easing = LinearEasing)),
        label = "eeg_phase",
    )
    NeonCard {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                SectionLabel("EEG SIGNAL")
                Box(Modifier.size(5.dp).clip(CircleShape).background(CYAN))
                Text("LIVE", color = CYAN, fontSize = 8.sp, fontFamily = FontFamily.Monospace, letterSpacing = 2.sp)
            }
            Spacer(Modifier.height(10.dp))
            Canvas(Modifier.fillMaxWidth().height(76.dp)) {
                val w = size.width
                val h = size.height
                val mid = h / 2f
                listOf(
                    Triple(CYAN.copy(alpha = 0.95f), 0.28f, 1.00f),
                    Triple(CYAN.copy(alpha = 0.55f), 0.18f, 1.75f),
                    Triple(CYAN.copy(alpha = 0.28f), 0.12f, 0.60f),
                ).forEach { (color, amp, freq) ->
                    val path = Path()
                    val steps = 240
                    for (i in 0..steps) {
                        val t = i.toFloat() / steps
                        val x = w * t
                        val y = mid - h * amp *
                            sin(t * 4f * PI.toFloat() * freq + phase * freq) *
                            (0.6f + 0.4f * sin(t * PI.toFloat() * 2.5f))
                        if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, color, style = Stroke(1.8f, cap = StrokeCap.Round))
                }
                // Vertical scan cursor
                val scanX = ((phase / (2f * PI.toFloat())) * w).coerceIn(0f, w)
                drawLine(CYAN.copy(alpha = 0.35f), Offset(scanX, 0f), Offset(scanX, h), strokeWidth = 1.5f)
            }
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("19ch · 256 Hz · 5 s window", color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text("Fp1 Fp2 Cz …", color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
            }
        }
    }
}

@Composable
private fun StatCard(
    modifier: Modifier,
    label: String,
    value: String,
    unit: String,
    icon: ImageVector,
    color: Color,
) {
    NeonCard(modifier = modifier) {
        Column(Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(14.dp))
                Text(label, color = SUBTLE, fontSize = 8.sp, fontFamily = FontFamily.Monospace, letterSpacing = 1.sp)
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    value,
                    color = color,
                    fontSize = 34.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                )
                Spacer(Modifier.width(3.dp))
                Text(
                    unit,
                    color = color.copy(alpha = 0.6f),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
            }
        }
    }
}

@Composable
private fun ConnectionStatusCard() {
    val pulse = rememberInfiniteTransition(label = "conn_pulse")
    val dotAlpha by pulse.animateFloat(
        initialValue = 0.25f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1100), RepeatMode.Reverse),
        label = "conn_dot",
    )
    NeonCard {
        Row(
            Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Box(Modifier.size(9.dp).clip(CircleShape).background(CYAN.copy(alpha = dotAlpha)))
            Column(Modifier.weight(1f)) {
                Text(
                    "WATCH CONNECTED",
                    color = CYAN,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    "Pixel Watch · BLE · 81% batt.",
                    color = SUBTLE,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                )
            }
            Icon(Icons.Filled.Watch, contentDescription = null, tint = CYAN.copy(alpha = 0.7f), modifier = Modifier.size(20.dp))
        }
    }
}

@Composable
private fun NeonCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = SURFACE),
        border = BorderStroke(1.dp, BORDER),
        content = { content() },
    )
}

@Composable
private fun SectionLabel(text: String) {
    Text(text, color = SUBTLE, fontSize = 9.sp, fontFamily = FontFamily.Monospace, letterSpacing = 3.sp)
}
