package com.auraguard.phone

import com.auraguard.shared.MonitoringMode
import com.auraguard.shared.TemperatureSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.math.sin

object AuraState {
    enum class PredictionStatus { DEMO, ACTIVE, MODEL_UNAVAILABLE, INPUT_MISMATCH, WAITING_FOR_DATA }
    enum class AlertStatus { MONITORING, COUNTDOWN, CANCELLED, DISPATCHED }

    data class Snapshot(
        val mode: MonitoringMode = MonitoringMode.DEMO,
        val risk: Float? = 0.12f,
        val movingAvgRisk: Float? = 0.12f,
        val predictionStatus: PredictionStatus = PredictionStatus.DEMO,
        val modelName: String = "Controlled test",
        val heartRate: Float? = 72f,
        val temperatureC: Float? = 33.4f,
        val temperatureSource: TemperatureSource = TemperatureSource.SIMULATED,
        val temperatureBaselineC: Float? = 33.1f,
        val batteryPct: Float? = 0.81f,
        val connected: Boolean = false,
        val accelCompleteness: Float = 1f,
        val gyroAvailable: Boolean = true,
        val motionPreview: FloatArray = demoWaveform(),
        val alertStatus: AlertStatus = AlertStatus.MONITORING,
        val alertMessage: String? = null,
        val alertStartedAtMs: Long? = null,
        val alertIsTest: Boolean = false,
        val demoRunning: Boolean = false,
        val demoTick: Int = 0,
        val demoStage: String = "Ready to start",
        val replayRunning: Boolean = false,
        val replayPosition: Int = 0,
        val replayTotal: Int = 0,
        val replayDataset: String? = null,
        val replayGroundTruth: String? = null,
        val updatedAtMs: Long = System.currentTimeMillis(),
    )

    private val _state = MutableStateFlow(Snapshot())
    val state: StateFlow<Snapshot> = _state.asStateFlow()

    fun setMode(mode: MonitoringMode) {
        _state.value = when (mode) {
            MonitoringMode.DEMO -> Snapshot()
            MonitoringMode.WEARABLE -> emptyLiveSnapshot(mode, "Waiting for wearable data")
            MonitoringMode.EEG_RESEARCH -> emptyLiveSnapshot(mode, "Waiting for EEG stream")
        }
    }

    fun updateFromSensorWindow(
        risk: Float?,
        movingAvgRisk: Float?,
        predictionStatus: PredictionStatus,
        modelName: String,
        heartRate: Float?,
        temperatureC: Float?,
        temperatureSource: TemperatureSource,
        temperatureBaselineC: Float?,
        batteryPct: Float?,
        accelCompleteness: Float,
        gyroAvailable: Boolean,
        motionPreview: FloatArray,
        capturedAtMs: Long,
    ) {
        val previous = _state.value
        _state.value = previous.copy(
            mode = MonitoringMode.WEARABLE,
            risk = risk,
            movingAvgRisk = movingAvgRisk,
            predictionStatus = predictionStatus,
            modelName = modelName,
            heartRate = heartRate,
            temperatureC = temperatureC,
            temperatureSource = temperatureSource,
            temperatureBaselineC = temperatureBaselineC,
            batteryPct = batteryPct,
            connected = true,
            accelCompleteness = accelCompleteness,
            gyroAvailable = gyroAvailable,
            motionPreview = motionPreview,
            updatedAtMs = capturedAtMs,
        )
    }

    fun updateAlert(status: AlertStatus, message: String? = null, isTest: Boolean = false) {
        _state.value = _state.value.copy(
            alertStatus = status,
            alertMessage = message,
            alertStartedAtMs = if (status == AlertStatus.COUNTDOWN) System.currentTimeMillis() else null,
            alertIsTest = isTest,
        )
    }

    fun updateDemoFrame(
        risk: Float,
        movingAverage: Float,
        heartRate: Float,
        temperatureC: Float,
        batteryPct: Float,
        motionPreview: FloatArray,
        stage: String,
        running: Boolean,
        tick: Int,
    ) {
        if (_state.value.mode != MonitoringMode.DEMO) setMode(MonitoringMode.DEMO)
        _state.value = _state.value.copy(
            risk = risk,
            movingAvgRisk = movingAverage,
            heartRate = heartRate,
            temperatureC = temperatureC,
            temperatureSource = TemperatureSource.SIMULATED,
            temperatureBaselineC = 33.1f,
            batteryPct = batteryPct,
            connected = false,
            accelCompleteness = 0.98f,
            gyroAvailable = true,
            motionPreview = motionPreview,
            predictionStatus = PredictionStatus.DEMO,
            modelName = "Test signal generator - no clinical model",
            demoRunning = running,
            demoTick = tick,
            demoStage = stage,
            updatedAtMs = System.currentTimeMillis(),
        )
    }

    fun updateWearableTestFrame(
        risk: Float,
        heartRate: Float,
        temperatureC: Float,
        motionPreview: FloatArray,
        stage: String,
    ) {
        _state.value = _state.value.copy(
            mode = MonitoringMode.WEARABLE,
            risk = risk,
            movingAvgRisk = risk,
            predictionStatus = PredictionStatus.DEMO,
            modelName = "Wearable test scenario - no clinical model",
            heartRate = heartRate,
            temperatureC = temperatureC,
            temperatureSource = TemperatureSource.SIMULATED,
            temperatureBaselineC = 33.1f,
            batteryPct = 0.84f,
            connected = true,
            accelCompleteness = 1f,
            gyroAvailable = true,
            motionPreview = motionPreview,
            demoRunning = false,
            demoStage = stage,
            updatedAtMs = System.currentTimeMillis(),
        )
    }

    fun stopDemo(stage: String = "Paused") {
        _state.value = _state.value.copy(demoRunning = false, demoStage = stage)
    }

    fun updateFromEegReplay(
        risk: Float?,
        movingAvgRisk: Float?,
        predictionStatus: PredictionStatus,
        modelName: String,
        replayPosition: Int,
        replayTotal: Int,
        replayDataset: String,
        replayGroundTruth: String,
        riskHistory: FloatArray,
        running: Boolean,
    ) {
        _state.value = _state.value.copy(
            mode = MonitoringMode.EEG_RESEARCH,
            risk = risk,
            movingAvgRisk = movingAvgRisk,
            predictionStatus = predictionStatus,
            modelName = modelName,
            connected = true,
            accelCompleteness = 1f,
            gyroAvailable = false,
            motionPreview = riskHistory,
            replayRunning = running,
            replayPosition = replayPosition,
            replayTotal = replayTotal,
            replayDataset = replayDataset,
            replayGroundTruth = replayGroundTruth,
            updatedAtMs = System.currentTimeMillis(),
        )
    }

    fun stopEegReplay(message: String) {
        _state.value = _state.value.copy(replayRunning = false, modelName = message)
    }

    private fun emptyLiveSnapshot(mode: MonitoringMode, modelName: String) = Snapshot(
        mode = mode,
        risk = null,
        movingAvgRisk = null,
        predictionStatus = PredictionStatus.WAITING_FOR_DATA,
        modelName = modelName,
        heartRate = null,
        temperatureC = null,
        temperatureSource = TemperatureSource.UNAVAILABLE,
        temperatureBaselineC = null,
        batteryPct = null,
        connected = false,
        accelCompleteness = 0f,
        gyroAvailable = false,
        motionPreview = FloatArray(0),
    )

    private fun demoWaveform(): FloatArray = FloatArray(100) { index ->
        val x = index / 100f
        (sin(x * Math.PI * 5).toFloat() * 0.65f) +
            (sin(x * Math.PI * 11).toFloat() * 0.25f)
    }
}
