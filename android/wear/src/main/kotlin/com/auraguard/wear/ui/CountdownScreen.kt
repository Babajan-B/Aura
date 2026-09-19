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
import com.auraguard.shared.DemoEvent

private val BG       = Color(0xFF120A02)
private val AMBER     = Color(0xFFFBBF24)
private val AMBER_DIM = Color(0xFF3D2E0E)

/**
 * Amber controlled high-risk countdown used by the prototype demonstration.
 * mode. A depleting ring + large seconds counter. Tapping "I'M OK" cancels;
 * letting it reach zero escalates to [AlertConfirmedScreen] via [onElapsed].
 */
@Composable
fun CountdownScreen(
    event: DemoEvent?,
    onDismiss: () -> Unit,
    onElapsed: () -> Unit,
) {
    var remaining by remember { mutableIntStateOf(COUNTDOWN_SECONDS) }

    LaunchedEffect(Unit) {
        while (remaining > 0) {
            delay(1_000)
            remaining -= 1
        }
        onElapsed()
    }

    // Smoothly animate the ring between whole-second ticks.
    val fraction by animateFloatAsState(
        targetValue = remaining.toFloat() / COUNTDOWN_SECONDS.toFloat(),
        animationSpec = tween(1_000, easing = LinearEasing),
        label = "ring",
    )

    Scaffold {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(BG),
            contentAlignment = Alignment.Center,
        ) {
            Canvas(Modifier.fillMaxSize()) {
                val sw  = 9.dp.toPx()
                val pad = sw / 2f + 4.dp.toPx()
                val arcSize = Size(size.width - pad * 2, size.height - pad * 2)
                val tl = Offset(pad, pad)

                drawArc(AMBER_DIM, -90f, 360f, false, tl, arcSize, style = Stroke(sw, cap = StrokeCap.Round))
                if (fraction > 0f) {
                    drawArc(
                        AMBER.copy(alpha = 0.20f), -90f, 360f * fraction, false,
                        Offset(pad - 5f, pad - 5f),
                        Size(arcSize.width + 10f, arcSize.height + 10f),
                        style = Stroke(sw + 10f, cap = StrokeCap.Round),
                    )
                    drawArc(AMBER, -90f, 360f * fraction, false, tl, arcSize,
                        style = Stroke(sw, cap = StrokeCap.Round))
                }
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.fillMaxSize(0.62f),
            ) {
                Text(
                    "TEST SEIZURE RISK ${event?.risk?.times(100)?.toInt() ?: 90}%",
                    color = AMBER,
                    fontSize = 7.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 2.sp,
                )

                Text(
                    "$remaining",
                    color = Color.White,
                    fontSize = 40.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                )

                Text(
                    "ALERTING CAREGIVER",
                    color = AMBER.copy(alpha = 0.75f),
                    fontSize = 7.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 1.sp,
                )

                Text(
                    "HR ${event?.heartRate?.toInt() ?: 96} · ${"%.1f".format(event?.temperatureC ?: 34f)} C",
                    color = Color.White.copy(alpha = 0.85f),
                    fontSize = 7.sp,
                    fontFamily = FontFamily.Monospace,
                )

                Spacer(Modifier.height(7.dp))

                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = AMBER,
                        contentColor = Color(0xFF120A02),
                    ),
                    modifier = Modifier
                        .width(80.dp)
                        .height(30.dp),
                ) {
                    Text(
                        "I'M OK",
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

private const val COUNTDOWN_SECONDS = 15
