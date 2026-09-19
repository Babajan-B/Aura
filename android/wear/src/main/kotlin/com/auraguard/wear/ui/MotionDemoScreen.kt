package com.auraguard.wear.ui

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material.Text
import kotlinx.coroutines.delay
import kotlin.math.sin
import com.auraguard.shared.DemoEvent

private val MotionBg = Color(0xFF080D12)
private val MotionCyan = Color(0xFF00FFD1)
private val MotionAmber = Color(0xFFFFBF24)

@Composable
fun MotionDemoScreen(event: DemoEvent?, onComplete: () -> Unit) {
    LaunchedEffect(Unit) {
        delay(12_000)
        onComplete()
    }
    val transition = rememberInfiniteTransition(label = "motion_demo")
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(650, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "motion_phase",
    )

    Box(Modifier.fillMaxSize().background(MotionBg), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val path = Path()
            val center = size.height * 0.50f
            for (index in 0..80) {
                val x = size.width * index / 80f
                val envelope = if (index in 15..66) 1f else 0.22f
                val y = center + envelope * sin(index * 0.78f + phase * 8f).toFloat() * size.height * 0.12f
                if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
            }
            drawPath(path, MotionCyan, style = Stroke(4f, cap = StrokeCap.Round))
            drawCircle(MotionCyan.copy(alpha = 0.15f), size.minDimension * (0.34f + phase * 0.08f), Offset(size.width / 2, center))
        }
        Column(
            modifier = Modifier.fillMaxSize().padding(vertical = 48.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("MOTION EVENT", color = MotionAmber, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    "TEST RISK ${event?.risk?.times(100)?.toInt() ?: 42}%",
                    color = MotionAmber,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                )
                Text("SIMULATED", color = MotionCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text(
                    "HR ${event?.heartRate?.toInt() ?: 92} · ${"%.1f".format(event?.temperatureC ?: 33.7f)} C",
                    color = Color.White,
                    fontSize = 7.sp,
                    fontFamily = FontFamily.Monospace,
                )
                Text("ACCELEROMETER + GYRO", color = Color.White, fontSize = 7.sp, fontFamily = FontFamily.Monospace)
            }
        }
    }
}
