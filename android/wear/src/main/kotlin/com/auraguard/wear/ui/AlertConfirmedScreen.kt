package com.auraguard.wear.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.*
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material.*

private val ALERT_BG = Color(0xFF100309)
private val PINK     = Color(0xFFFF2E6C)

/**
 * Pink demonstration alert shown after the countdown elapses without an
 * "I'M OK" response. Tapping "DISMISS" returns to monitoring.
 */
@Composable
fun AlertConfirmedScreen(onReset: () -> Unit) {
    val flash = rememberInfiniteTransition(label = "flash")
    val flashAlpha by flash.animateFloat(
        initialValue = 0.18f,
        targetValue = 0.50f,
        animationSpec = infiniteRepeatable(tween(700), RepeatMode.Reverse),
        label = "flash_a",
    )
    val iconScale by flash.animateFloat(
        initialValue = 1f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(tween(700), RepeatMode.Reverse),
        label = "icon_scale",
    )

    Scaffold {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(ALERT_BG),
            contentAlignment = Alignment.Center,
        ) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(PINK.copy(alpha = flashAlpha), Color.Transparent),
                        center = center,
                        radius = size.minDimension * 0.65f,
                    ),
                )
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.fillMaxSize(0.62f),
            ) {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = "Demonstration alert",
                    tint = PINK,
                    modifier = Modifier.size(26.dp * iconScale),
                )

                Spacer(Modifier.height(4.dp))

                Text(
                    "TEST",
                    color = PINK,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 2.sp,
                )
                Text(
                    "ALERT",
                    color = PINK,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 2.sp,
                )

                Spacer(Modifier.height(4.dp))

                Text(
                    "GPS ATTACHED",
                    color = Color.White,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                )
                Text(
                    "SMS SENT · TEST",
                    color = Color.White,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                )
                Text(
                    "CALLING CONTACT · TEST",
                    color = PINK,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                )

                Text("NO REAL CALL", color = PINK.copy(alpha = 0.75f), fontSize = 7.sp,
                    fontFamily = FontFamily.Monospace)

                Spacer(Modifier.height(8.dp))

                Button(
                    onClick = onReset,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF2A0E18),
                        contentColor = PINK,
                    ),
                    modifier = Modifier
                        .width(82.dp)
                        .height(30.dp),
                ) {
                    Text(
                        "DISMISS",
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}
