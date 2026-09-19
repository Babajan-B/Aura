package com.auraguard.wear.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material.*
import kotlinx.coroutines.delay

private val ALERT_BG = Color(0xFF100309)
private val PINK     = Color(0xFFFF2E6C)
private val PINK_DIM = Color(0xFF3D0E1F)

@Composable
fun AlertCountdownScreen(
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    var remaining by remember { mutableIntStateOf(COUNTDOWN_SECONDS) }

    LaunchedEffect(Unit) {
        while (remaining > 0) {
            delay(1_000)
            remaining -= 1
        }
        onConfirm()
    }

    val flashTrans = rememberInfiniteTransition(label = "flash")
    val flashAlpha by flashTrans.animateFloat(
        initialValue = 0.12f,
        targetValue = 0.42f,
        animationSpec = infiniteRepeatable(tween(550), RepeatMode.Reverse),
        label = "flash_a",
    )

    Scaffold {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(ALERT_BG),
            contentAlignment = Alignment.Center,
        ) {
            // Radial glow flash
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(PINK.copy(alpha = flashAlpha), Color.Transparent),
                        center = center,
                        radius = size.minDimension * 0.62f,
                    ),
                )
            }

            // Depleting countdown arc
            Canvas(Modifier.fillMaxSize()) {
                val sw  = 9.dp.toPx()
                val pad = sw / 2f + 2.dp.toPx()
                val arcSize = Size(size.width - pad * 2, size.height - pad * 2)
                val tl = Offset(pad, pad)
                val fraction = remaining.toFloat() / COUNTDOWN_SECONDS.toFloat()

                drawArc(PINK_DIM, -90f, 360f, false, tl, arcSize, style = Stroke(sw, cap = StrokeCap.Round))

                if (fraction > 0f) {
                    drawArc(
                        PINK.copy(alpha = 0.22f), -90f, 360f * fraction, false,
                        Offset(pad - 4f, pad - 4f),
                        Size(arcSize.width + 8f, arcSize.height + 8f),
                        style = Stroke(sw + 8f, cap = StrokeCap.Round),
                    )
                    drawArc(PINK, -90f, 360f * fraction, false, tl, arcSize,
                        style = Stroke(sw, cap = StrokeCap.Round))
                }
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    "SEIZURE",
                    color = PINK,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 3.sp,
                )
                Text(
                    "ALERT",
                    color = PINK,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 3.sp,
                )

                Spacer(Modifier.height(4.dp))

                Text(
                    "$remaining",
                    color = Color.White,
                    fontSize = 46.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                )
                Text(
                    "SOS IN ${remaining}s",
                    color = PINK.copy(alpha = 0.75f),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 1.sp,
                )

                Spacer(Modifier.height(10.dp))

                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF2A0E18),
                        contentColor = PINK,
                    ),
                    modifier = Modifier
                        .width(80.dp)
                        .height(32.dp),
                ) {
                    Text(
                        "I'M OK",
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

private const val COUNTDOWN_SECONDS = 15
