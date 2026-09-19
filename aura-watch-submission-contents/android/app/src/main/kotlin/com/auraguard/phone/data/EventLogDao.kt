package com.auraguard.phone.data

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/**
 * Persistent event log for the phone module. One row per inference round
 * that produced a notable change — baseline, elevated, alert, recovered, etc.
 *
 * The Room database itself isn't built here yet (hackathon scope); we only
 * declare the entity + DAO so UI code can compile against the contract and
 * we can swap in a real Database during day 2.
 */
@Entity(tableName = "event_log")
data class EventLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "captured_at_ms") val capturedAtMs: Long,
    @ColumnInfo(name = "risk_score") val riskScore: Float,
    @ColumnInfo(name = "label") val label: String,
    @ColumnInfo(name = "dispatched_sos") val dispatchedSos: Boolean = false,
    @ColumnInfo(name = "user_marked_false") val userMarkedFalse: Boolean = false,
)

@Dao
interface EventLogDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(event: EventLogEntity): Long

    @Query("SELECT * FROM event_log ORDER BY captured_at_ms DESC LIMIT :limit")
    fun observeRecent(limit: Int = 50): Flow<List<EventLogEntity>>

    @Query("SELECT COUNT(*) FROM event_log WHERE captured_at_ms >= :sinceMs")
    suspend fun countSince(sinceMs: Long): Int

    @Query("UPDATE event_log SET user_marked_false = 1 WHERE id = :id")
    suspend fun markFalsePositive(id: Long)

    @Query("DELETE FROM event_log")
    suspend fun clear()
}
