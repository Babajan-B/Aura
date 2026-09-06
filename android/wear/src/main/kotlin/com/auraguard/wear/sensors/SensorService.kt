package com.auraguard.wear.sensors

import android.app.Service
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.IntentFilter
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.BatteryManager
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.auraguard.shared.SensorPacket
import com.auraguard.shared.TemperatureSource
import com.auraguard.wear.MainActivity
import com.auraguard.wear.WearState
import com.auraguard.wear.comms.PhoneBridge
import androidx.core.app.NotificationCompat

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
    private val gyroX = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val gyroY = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val gyroZ = ArrayList<Float>(WINDOW_ACCEL_SAMPLES)
    private val hr = ArrayList<Float>(SensorPacket.WINDOW_SECONDS)
    private val temperature = ArrayList<Float>(SensorPacket.WINDOW_SECONDS)
    private var temperatureSource = TemperatureSource.UNAVAILABLE
    private var windowStartMs = 0L

    override fun onCreate() {
        super.onCreate()
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        bridge = PhoneBridge(applicationContext)
        startForeground(NOTIFICATION_ID, buildNotification())
        registerSensors()
        windowStartMs = System.currentTimeMillis()
    }

    private fun registerSensors() {
        val accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val gyro = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        val heart = sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE)
        val ambient = sensorManager.getDefaultSensor(Sensor.TYPE_AMBIENT_TEMPERATURE)

        accel?.let {
            // 20_000us == 50Hz — sensor framework treats this as a hint.
            sensorManager.registerListener(this, it, 20_000)
        }
        gyro?.let { sensorManager.registerListener(this, it, 20_000) }
        heart?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL)
        }
        ambient?.let {
            temperatureSource = TemperatureSource.AMBIENT
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL)
        }
        WearState.capabilities(
            accel = accel != null,
            gyro = gyro != null,
            heartRate = heart != null,
            tempSource = temperatureSource,
        )
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                accelX.add(event.values[0])
                accelY.add(event.values[1])
                accelZ.add(event.values[2])
            }
            Sensor.TYPE_HEART_RATE -> hr.add(event.values[0])
            Sensor.TYPE_GYROSCOPE -> {
                gyroX.add(event.values[0])
                gyroY.add(event.values[1])
                gyroZ.add(event.values[2])
            }
            Sensor.TYPE_AMBIENT_TEMPERATURE -> temperature.add(event.values[0])
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
            gyroX = gyroX.toFloatArray(),
            gyroY = gyroY.toFloatArray(),
            gyroZ = gyroZ.toFloatArray(),
            heartRate = hr.toFloatArray(),
            temperatureC = temperature.toFloatArray(),
            temperatureSource = temperatureSource,
            batteryPct = readBatteryPct(),
        )
        Log.i(TAG, "flush window samples=${packet.accelX.size} hr=${packet.heartRate.size}")
        bridge.sendPacket(packet)
        WearState.readings(
            heartRate = packet.heartRate.lastOrNull(),
            temperatureC = packet.temperatureC.lastOrNull(),
            temperatureSource = packet.temperatureSource,
            batteryPct = packet.batteryPct.takeIf { it >= 0f },
            updatedAtMs = packet.capturedAtMs,
        )
        accelX.clear(); accelY.clear(); accelZ.clear()
        gyroX.clear(); gyroY.clear(); gyroZ.clear()
        hr.clear(); temperature.clear()
        windowStartMs = System.currentTimeMillis()
    }

    private fun readBatteryPct(): Float {
        val status = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED)) ?: return -1f
        val level = status.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = status.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        return if (level >= 0 && scale > 0) level.toFloat() / scale else -1f
    }

    private fun buildNotification(): android.app.Notification {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Aura monitoring", NotificationManager.IMPORTANCE_LOW),
            )
        }
        val intent = Intent(this, MainActivity::class.java)
        val pending = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentTitle("Aura Guard monitoring")
            .setContentText("Movement and available health sensors are active")
            .setContentIntent(pending)
            .setOngoing(true)
            .setSilent(true)
            .build()
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
        private const val CHANNEL_ID = "aura_monitoring"
        private const val NOTIFICATION_ID = 1001
        private const val WINDOW_ACCEL_SAMPLES =
            SensorPacket.WINDOW_SECONDS * SensorPacket.ACCEL_HZ
    }
}
