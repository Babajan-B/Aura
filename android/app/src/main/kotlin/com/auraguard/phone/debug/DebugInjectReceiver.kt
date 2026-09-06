package com.auraguard.phone.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.auraguard.phone.RiskPipeline
import com.auraguard.shared.SensorPacket
import kotlin.math.sin
import kotlin.random.Random

/**
 * Debug-only entry point so the phone pipeline can be exercised end-to-end
 * without a paired watch. Trigger via:
 *
 *   adb shell am broadcast -a com.auraguard.phone.DEBUG_INJECT \
 *       -n com.auraguard.phone/.debug.DebugInjectReceiver --es mode force --ef risk 0.9
 *
 * modes:
 *   force  --ef risk <0..1>     push a fixed risk through the gate
 *   packet --ez shaking <bool>  synthesize a seizure-like / calm motion window
 *   sos                         simulate the watch's countdown elapsing
 */
class DebugInjectReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.getStringExtra("mode")) {
            "force" -> RiskPipeline.debugForceRisk(context, intent.getFloatExtra("risk", 0.9f))
            "sos" -> RiskPipeline.onSosFromWatch(context)
            "packet" -> RiskPipeline.process(
                context,
                syntheticPacket(intent.getBooleanExtra("shaking", true)),
            )
            else -> Log.w(TAG, "unknown mode; use force | packet | sos")
        }
    }

    private fun syntheticPacket(shaking: Boolean): SensorPacket {
        val n = 500
        val ax = FloatArray(n); val ay = FloatArray(n); val az = FloatArray(n)
        val twoPi = 2f * Math.PI.toFloat()
        for (i in 0 until n) {
            val t = i / 50f
            if (shaking) {
                ax[i] = 9.8f + 6f * sin(twoPi * 5f * t) + Random.nextFloat()
                ay[i] = 5f * sin(twoPi * 6f * t)
                az[i] = 5f * sin(twoPi * 4f * t)
            } else {
                ax[i] = 9.8f + 0.05f * Random.nextFloat()
                ay[i] = 0.05f * Random.nextFloat()
                az[i] = 0.05f * Random.nextFloat()
            }
        }
        val hr = FloatArray(10) { if (shaking) 120f else 70f }
        return SensorPacket(
            capturedAtMs = System.currentTimeMillis(),
            accelX = ax, accelY = ay, accelZ = az, heartRate = hr,
        )
    }

    companion object { private const val TAG = "DebugInject" }
}
