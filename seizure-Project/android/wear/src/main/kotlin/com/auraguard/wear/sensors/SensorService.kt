package com.auraguard.wear.sensors

import android.app.Service
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.IBinder
import android.util.Log
import com.auraguard.shared.SensorPacket
import com.auraguard.wear.comms.PhoneBridge

/**
 * Foreground service on the watch that:
 *   - subscribes to the accelerometer at ~50Hz and HR at ~1Hz,
 *   - batches samples into a 10-second window,
 *   - hands a [SensorPacket] off to [PhoneBridge] every window.
 *
 * The class deliberately keeps zero coroutines for the skeleton — sensor
 * callbacks already run on a dedicated SensorManager thread, and we can
 * promote to a structured pipeline once the inference path is live.
 */
class SensorService : Service(), SensorEventListener {

    private lateinit var sensorManager: SensorManager
    private lateinit var bridge: PhoneBridge

    private val accelX = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val accelY = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val accelZ = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val hr = ArrayList<Float>(SensorPacket.WINDOW_SECONDS)
    private var windowStartMs = 0L

    override fun onCreate() {
        super.onCreate()
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        bridge = PhoneBridge(applicationContext)
        registerSensors()
        windowStartMs = System.currentTimeMillis()
        // TODO: startForeground(...) with a health-type notification for production builds.
    }

    private fun registerSensors() {
        sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.let {
            // 20_000us == 50Hz — sensor framework treats this as a hint.
            sensorManager.registerListener(this, it, 20_000)
        }
        sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE)?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL)
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                accelX.add(event.values[0])
                accelY.add(event.values[1])
                accelZ.add(event.values[2])
            }
            Sensor.TYPE_HEART_RATE -> hr.add(event.values[0])
        }
        if (System.currentTimeMillis() - windowStartMs >= SensorPacket.WINDOW_SECONDS * 1000L) {
            flushWindow()
        }
    }

    private fun flushWindow() {
        val packet = SensorPacket(
            capturedAtMs = System.currentTimeMillis(),
            accelX = accelX.toFloatArray(),
            accelY = accelY.toFloatArray(),
            accelZ = accelZ.toFloatArray(),
            heartRate = hr.toFloatArray(),
        )
        Log.i(TAG, "flush window samples=${packet.accelX.size} hr=${packet.heartRate.size}")
        bridge.sendPacket(packet)
        accelX.clear(); accelY.clear(); accelZ.clear(); hr.clear()
        windowStartMs = System.currentTimeMillis()
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        sensorManager.unregisterListener(this)
        super.onDestroy()
    }

    companion object {
        private const val TAG = "SensorService"
        private const val WINDOW_ACCEL_SAMPLES =
            SensorPacket.WINDOW_SECONDS * SensorPacket.ACCEL_HZ
    }
}
