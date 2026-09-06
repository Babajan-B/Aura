package com.auraguard.phone.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

object EventLogRepository {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val events = MutableStateFlow<List<EventLogEntity>>(emptyList())
    @Volatile private var helper: EventDbHelper? = null

    fun observe(context: Context): StateFlow<List<EventLogEntity>> {
        ensureLoaded(context.applicationContext)
        return events
    }

    fun record(context: Context, event: EventLogEntity) {
        val app = context.applicationContext
        scope.launch {
            database(app).writableDatabase.insert(TABLE, null, event.toValues())
            refresh(app)
        }
    }

    fun clear(context: Context) {
        val app = context.applicationContext
        scope.launch {
            database(app).writableDatabase.delete(TABLE, null, null)
            events.value = emptyList()
        }
    }

    private fun ensureLoaded(context: Context) {
        if (helper == null) scope.launch { refresh(context) }
    }

    private fun refresh(context: Context) {
        val rows = mutableListOf<EventLogEntity>()
        database(context).readableDatabase.query(
            TABLE,
            null,
            null,
            null,
            null,
            null,
            "captured_at_ms DESC",
            "50",
        ).use { cursor ->
            while (cursor.moveToNext()) {
                fun index(name: String) = cursor.getColumnIndexOrThrow(name)
                fun nullableFloat(name: String): Float? {
                    val column = index(name)
                    return if (cursor.isNull(column)) null else cursor.getFloat(column)
                }
                rows += EventLogEntity(
                    id = cursor.getLong(index("id")),
                    capturedAtMs = cursor.getLong(index("captured_at_ms")),
                    riskScore = cursor.getFloat(index("risk_score")),
                    label = cursor.getString(index("label")),
                    mode = cursor.getString(index("mode")),
                    modelName = cursor.getString(index("model_name")),
                    heartRate = nullableFloat("heart_rate"),
                    temperatureC = nullableFloat("temperature_c"),
                    temperatureSource = cursor.getString(index("temperature_source")),
                    signalQuality = cursor.getFloat(index("signal_quality")),
                    dispatchedSos = cursor.getInt(index("dispatched_sos")) == 1,
                    userMarkedFalse = cursor.getInt(index("user_marked_false")) == 1,
                )
            }
        }
        events.value = rows
    }

    private fun database(context: Context): EventDbHelper = helper ?: synchronized(this) {
        helper ?: EventDbHelper(context).also { helper = it }
    }

    private fun EventLogEntity.toValues() = ContentValues().apply {
        put("captured_at_ms", capturedAtMs)
        put("risk_score", riskScore)
        put("label", label)
        put("mode", mode)
        put("model_name", modelName)
        heartRate?.let { put("heart_rate", it) }
        temperatureC?.let { put("temperature_c", it) }
        put("temperature_source", temperatureSource)
        put("signal_quality", signalQuality)
        put("dispatched_sos", if (dispatchedSos) 1 else 0)
        put("user_marked_false", if (userMarkedFalse) 1 else 0)
    }

    private class EventDbHelper(context: Context) :
        SQLiteOpenHelper(context, "aura_guard.db", null, 1) {
        override fun onCreate(db: SQLiteDatabase) {
            db.execSQL(
                """
                CREATE TABLE $TABLE (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at_ms INTEGER NOT NULL,
                    risk_score REAL NOT NULL,
                    label TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    heart_rate REAL,
                    temperature_c REAL,
                    temperature_source TEXT,
                    signal_quality REAL NOT NULL,
                    dispatched_sos INTEGER NOT NULL,
                    user_marked_false INTEGER NOT NULL
                )
                """.trimIndent(),
            )
        }

        override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit
    }

    private const val TABLE = "event_log"
}
