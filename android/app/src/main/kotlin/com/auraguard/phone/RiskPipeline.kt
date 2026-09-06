package com.auraguard.phone

import android.content.Context
import android.util.Log
import com.auraguard.phone.data.EventLogEntity
import com.auraguard.phone.data.EventLogRepository
import com.auraguard.phone.ml.InferenceEngine
import com.auraguard.phone.ml.RingBuffer
import com.auraguard.phone.ml.WearableFeatureExtractor
import com.auraguard.phone.sos.EmergencyCoordinator
import com.auraguard.shared.MonitoringMode
import com.auraguard.shared.SensorPacket
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.Wearable
import kotlin.concurrent.thread
import kotlin.math.sin

object RiskPipeline {
    private const val TAG = "RiskPipeline"
    private const val GATE_FRAMES = 6
    private const val ALERT_RESET_THRESHOLD = 0.50f

    @Volatile private var engine: InferenceEngine? = null
    private val riskGate = RingBuffer(capacity = GATE_FRAMES, slotSize = 1)
    @Volatile private var lastMovingAvg = 0f
    @Volatile private var alerting = false
    @Volatile private var temperatureBaselineC: Float? = null
    @Volatile private var demoTick = 0

    private fun engine(context: Context): InferenceEngine = engine ?: synchronized(this) {
        engine ?: InferenceEngine.create(context.applicationContext).also { engine = it }
    }

    fun setMode(mode: MonitoringMode) {
        AuraState.setMode(mode)
        alerting = false
        riskGate.clear()
        if (mode != MonitoringMode.DEMO) demoTick = 0
    }

    fun startDemo() {
        setMode(MonitoringMode.DEMO)
        demoTick = 0
        tickDemo()
    }

    fun tickDemo() {
        val current = AuraState.state.value
        if (current.mode != MonitoringMode.DEMO ||
            current.alertStatus == AuraState.AlertStatus.COUNTDOWN
        ) return

        demoTick += 1
        val phase = demoTick.toFloat()
        val risk = (0.14f + 0.025f * sin(phase / 2.4f)).coerceIn(0.08f, 0.22f)
        val heartRate = 72f + 3f * sin(phase / 3.2f)
        val temperature = 33.4f + 0.12f * sin(phase / 7f)
        val battery = (0.86f - demoTick * 0.0004f).coerceAtLeast(0.72f)
        val waveform = FloatArray(120) { index ->
            val x = index / 10f + phase * 0.2f
            (sin(x) * 0.55f + sin(x * 2.7f) * 0.18f).toFloat()
        }
        riskGate.clear()
        riskGate.push(floatArrayOf(risk))
        lastMovingAvg = risk
        AuraState.updateDemoFrame(
            risk = risk,
            movingAverage = risk,
            heartRate = heartRate,
            temperatureC = temperature,
            batteryPct = battery,
            motionPreview = waveform,
            stage = "Simulated sensors streaming",
            running = true,
            tick = demoTick,
        )
    }

    fun pauseDemo() = AuraState.stopDemo()

    fun resetDemo() {
        demoTick = 0
        alerting = false
        riskGate.clear()
        AuraState.setMode(MonitoringMode.DEMO)
    }

    /** Process a real wearable window. Prediction fails closed if the model contract does not match. */
    fun process(context: Context, packet: SensorPacket) {
        val app = context.applicationContext
        val inference = engine(app)
        val features = WearableFeatureExtractor.extract(packet)
        val result = inference.scoreWearable(features)
        val risk = (result as? InferenceEngine.ScoreResult.Prediction)?.probability
        val status = when (result) {
            is InferenceEngine.ScoreResult.Prediction -> AuraState.PredictionStatus.ACTIVE
            is InferenceEngine.ScoreResult.Unavailable -> if (result.reason.contains("expects")) {
                AuraState.PredictionStatus.INPUT_MISMATCH
            } else {
                AuraState.PredictionStatus.MODEL_UNAVAILABLE
            }
        }
        val modelName = when (result) {
            is InferenceEngine.ScoreResult.Prediction -> inference.modelName
            is InferenceEngine.ScoreResult.Unavailable -> result.reason
        }

        val avg = risk?.let { updateGate(it) }
        updateTemperatureBaseline(packet.temperatureC.lastOrNull())
        AuraState.updateFromSensorWindow(
            risk = risk,
            movingAvgRisk = avg,
            predictionStatus = status,
            modelName = modelName,
            heartRate = packet.heartRate.lastOrNull(),
            temperatureC = packet.temperatureC.lastOrNull(),
            temperatureSource = packet.temperatureSource,
            temperatureBaselineC = temperatureBaselineC,
            batteryPct = packet.batteryPct.takeIf { it >= 0f },
            accelCompleteness = packet.accelCompleteness,
            gyroAvailable = packet.hasGyroscope,
            motionPreview = WearableFeatureExtractor.motionPreview(packet),
            capturedAtMs = packet.capturedAtMs,
        )

        EventLogRepository.record(
            app,
            EventLogEntity(
                capturedAtMs = packet.capturedAtMs,
                riskScore = risk ?: -1f,
                label = when (status) {
                    AuraState.PredictionStatus.ACTIVE -> riskLabel(avg ?: risk ?: 0f)
                    else -> modelName
                },
                mode = MonitoringMode.WEARABLE.name,
                modelName = inference.modelName,
                heartRate = packet.heartRate.lastOrNull(),
                temperatureC = packet.temperatureC.lastOrNull(),
                temperatureSource = packet.temperatureSource.name,
                signalQuality = packet.accelCompleteness,
            ),
        )

        if (avg != null) evaluateGate(app, avg)
    }

    /** Presentation-only deterministic path. It is always labelled Demo in the UI and log. */
    fun debugForceRisk(context: Context, risk: Float, hr: Float = 88f) {
        val safeRisk = risk.coerceIn(0f, 1f)
        val avg = updateGate(safeRisk)
        AuraState.updateDemoFrame(
            risk = safeRisk,
            movingAverage = avg,
            heartRate = hr,
            temperatureC = 33.8f,
            batteryPct = 0.84f,
            motionPreview = FloatArray(120) { index ->
                (sin(index * 0.9) * 0.9 + sin(index * 2.2) * 0.35).toFloat()
            },
            stage = "Controlled high-risk test",
            running = false,
            tick = demoTick,
        )
        EventLogRepository.record(
            context.applicationContext,
            EventLogEntity(
                capturedAtMs = System.currentTimeMillis(),
                riskScore = safeRisk,
                label = "Demo: ${riskLabel(avg)}",
                mode = MonitoringMode.DEMO.name,
                modelName = "Controlled demo",
                heartRate = hr,
                temperatureC = AuraState.state.value.temperatureC,
                temperatureSource = AuraState.state.value.temperatureSource.name,
                signalQuality = 1f,
            ),
        )
        evaluateGate(context.applicationContext, avg)
    }

    fun triggerTestCountdown(context: Context) {
        alerting = true
        riskGate.clear()
        AuraState.setMode(MonitoringMode.DEMO)
        AuraState.updateDemoFrame(
            risk = 0.9f,
            movingAverage = 0.9f,
            heartRate = 96f,
            temperatureC = 34.0f,
            batteryPct = 0.84f,
            motionPreview = FloatArray(120) { index ->
                (sin(index * 0.9) * 0.9 + sin(index * 2.2) * 0.35).toFloat()
            },
            stage = "High-risk event simulated",
            running = false,
            tick = demoTick,
        )
        AuraState.updateAlert(
            AuraState.AlertStatus.COUNTDOWN,
            "Test countdown only; no SMS will be sent",
            isTest = true,
        )
        sendToWatch(context.applicationContext, SensorPacket.ALERT_PATH)
    }

    fun cancelPhoneAlert(context: Context) = onCancelFromWatch(context)

    fun onPhoneCountdownElapsed(context: Context) = onSosFromWatch(context)

    fun onCancelFromWatch(context: Context) {
        val wasTest = AuraState.state.value.alertIsTest
        alerting = false
        if (wasTest) resetDemo()
        val message = if (wasTest) "Test cancelled; emergency dispatch was suppressed" else "Alert cancelled by wearer"
        AuraState.updateAlert(AuraState.AlertStatus.CANCELLED, message, isTest = wasTest)
        recordAlertEvent(context, message, dispatched = false)
    }

    fun onSosFromWatch(context: Context) {
        val app = context.applicationContext
        if (AuraState.state.value.alertIsTest) {
            alerting = false
            resetDemo()
            AuraState.updateAlert(
                AuraState.AlertStatus.CANCELLED,
                "Test completed; emergency dispatch was suppressed",
                isTest = true,
            )
            recordAlertEvent(app, "Test countdown completed", dispatched = false)
            return
        }
        EmergencyCoordinator(app).dispatch(lastMovingAvg) { outcome ->
            AuraState.updateAlert(AuraState.AlertStatus.DISPATCHED, outcome)
            recordAlertEvent(app, outcome, dispatched = true)
        }
    }

    private fun updateGate(risk: Float): Float {
        riskGate.push(floatArrayOf(risk))
        val avg = riskGate.snapshot().map { it[0] }.average().toFloat()
        lastMovingAvg = avg
        return avg
    }

    private fun evaluateGate(context: Context, avg: Float) {
        if (avg >= InferenceEngine.RISK_THRESHOLD && !alerting) {
            alerting = true
            AuraState.updateAlert(AuraState.AlertStatus.COUNTDOWN, "High risk confirmed across multiple windows")
            sendToWatch(context, SensorPacket.ALERT_PATH)
            recordAlertEvent(context, "Countdown requested", dispatched = false)
        } else if (avg < ALERT_RESET_THRESHOLD) {
            alerting = false
            if (AuraState.state.value.alertStatus == AuraState.AlertStatus.COUNTDOWN) {
                AuraState.updateAlert(AuraState.AlertStatus.MONITORING)
            }
        }
    }

    private fun sendToWatch(context: Context, path: String) {
        thread(name = "aura-to-watch") {
            try {
                val nodes = Tasks.await(Wearable.getNodeClient(context).connectedNodes)
                val client = Wearable.getMessageClient(context)
                for (node in nodes) Tasks.await(client.sendMessage(node.id, path, ByteArray(0)))
                Log.i(TAG, "sent $path to ${nodes.size} node(s)")
            } catch (t: Throwable) {
                Log.e(TAG, "sendToWatch $path failed", t)
                val isTest = AuraState.state.value.alertIsTest
                AuraState.updateAlert(
                    AuraState.AlertStatus.COUNTDOWN,
                    if (isTest) {
                        "Safe test countdown; SMS and emergency calls are disabled"
                    } else {
                        "Phone alert active; watch unavailable"
                    },
                    isTest = isTest,
                )
            }
        }
    }

    private fun updateTemperatureBaseline(value: Float?) {
        if (value == null) return
        temperatureBaselineC = temperatureBaselineC?.let { old -> old * 0.98f + value * 0.02f } ?: value
    }

    private fun riskLabel(risk: Float): String = when {
        risk >= InferenceEngine.RISK_THRESHOLD -> "High risk"
        risk >= 0.50f -> "Elevated risk"
        else -> "Stable"
    }

    private fun recordAlertEvent(context: Context, label: String, dispatched: Boolean) {
        val state = AuraState.state.value
        EventLogRepository.record(
            context.applicationContext,
            EventLogEntity(
                capturedAtMs = System.currentTimeMillis(),
                riskScore = state.movingAvgRisk ?: -1f,
                label = label,
                mode = state.mode.name,
                modelName = state.modelName,
                heartRate = state.heartRate,
                temperatureC = state.temperatureC,
                temperatureSource = state.temperatureSource.name,
                signalQuality = state.accelCompleteness,
                dispatchedSos = dispatched,
            ),
        )
    }
}
