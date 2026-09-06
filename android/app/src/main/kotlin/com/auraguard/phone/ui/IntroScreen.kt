package com.auraguard.phone.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val IntroBackground = Color(0xFF0D1117)
private val IntroSurface = Color(0xFF161B22)
private val IntroCyan = Color(0xFF00E5C2)
private val IntroMuted = Color(0xFF8B949E)
private val IntroBorder = Color(0xFF30363D)

@Composable
fun IntroScreen(onEnterDemo: () -> Unit) {
    val transition = rememberInfiniteTransition(label = "intro_pulse")
    val pulse by transition.animateFloat(
        initialValue = 0.82f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1_300), RepeatMode.Reverse),
        label = "intro_pulse_value",
    )

    Box(
        modifier = Modifier.fillMaxSize().background(IntroBackground).padding(28.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Box(Modifier.size(210.dp), contentAlignment = Alignment.Center) {
                Canvas(Modifier.fillMaxSize()) {
                    val stroke = 7.dp.toPx()
                    val inset = stroke / 2
                    val diameter = size.minDimension - stroke
                    drawArc(
                        color = IntroBorder,
                        startAngle = -90f,
                        sweepAngle = 360f,
                        useCenter = false,
                        topLeft = Offset(inset, inset),
                        size = Size(diameter, diameter),
                        style = Stroke(stroke, cap = StrokeCap.Round),
                    )
                    drawArc(
                        color = IntroCyan.copy(alpha = pulse),
                        startAngle = -90f,
                        sweepAngle = 292f,
                        useCenter = false,
                        topLeft = Offset(inset, inset),
                        size = Size(diameter, diameter),
                        style = Stroke(stroke, cap = StrokeCap.Round),
                    )
                }
                Surface(
                    modifier = Modifier.size(112.dp),
                    shape = CircleShape,
                    color = IntroSurface,
                    border = BorderStroke(1.dp, IntroBorder),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Filled.Favorite,
                            contentDescription = null,
                            tint = IntroCyan,
                            modifier = Modifier.size(48.dp),
                        )
                    }
                }
            }

            Spacer(Modifier.height(30.dp))
            Text(
                "AURA GUARD",
                color = IntroCyan,
                fontSize = 34.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 4.sp,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "WEARABLE SEIZURE-SAFETY PROTOTYPE",
                color = IntroMuted,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp,
            )
            Spacer(Modifier.height(28.dp))
            PulseLine(modifier = Modifier.fillMaxWidth().height(72.dp))
            Spacer(Modifier.height(18.dp))
            Text(
                "SENSE   •   ASSESS   •   ALERT",
                color = IntroCyan,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 2.sp,
            )
            Spacer(Modifier.height(46.dp))
            Button(
                onClick = onEnterDemo,
                modifier = Modifier.fillMaxWidth().height(54.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = IntroCyan,
                    contentColor = IntroBackground,
                ),
            ) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null)
                Text(
                    "ENTER DEMO",
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                )
            }
        }
    }
}

@Composable
private fun PulseLine(modifier: Modifier = Modifier) {
    Canvas(modifier) {
        val middle = size.height / 2f
        drawLine(
            color = IntroBorder,
            start = Offset(0f, middle),
            end = Offset(size.width, middle),
            strokeWidth = 2f,
        )
        val points = listOf(
            0.00f to 0.00f,
            0.12f to 0.00f,
            0.18f to -0.14f,
            0.23f to 0.10f,
            0.29f to 0.00f,
            0.38f to 0.00f,
            0.43f to -0.22f,
            0.48f to 0.72f,
            0.53f to -0.46f,
            0.59f to 0.12f,
            0.65f to 0.00f,
            0.76f to 0.00f,
            0.82f to -0.14f,
            0.87f to 0.10f,
            0.92f to 0.00f,
            1.00f to 0.00f,
        )
        val path = Path()
        points.forEachIndexed { index, (x, amplitude) ->
            val px = size.width * x
            val py = middle - amplitude * size.height * 0.48f
            if (index == 0) path.moveTo(px, py) else path.lineTo(px, py)
        }
        drawPath(
            path = path,
            color = IntroCyan,
            style = Stroke(width = 4f, cap = StrokeCap.Round),
        )
    }
}
