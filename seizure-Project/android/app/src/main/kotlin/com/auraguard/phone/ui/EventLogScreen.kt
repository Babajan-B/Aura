package com.auraguard.phone.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Static event log placeholder. Replace [SAMPLE] with rows from
 * [com.auraguard.phone.data.EventLogDao] once Room is wired up.
 */
@Composable
fun EventLogScreen(onBack: () -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("Event log", style = MaterialTheme.typography.titleLarge)
            TextButton(onClick = onBack) { Text("Back") }
        }
        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        LazyColumn {
            items(SAMPLE) { row ->
                EventRow(row)
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun EventRow(row: EventRow) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
        Text(row.timestamp, style = MaterialTheme.typography.labelLarge)
        Text("Risk ${"%.2f".format(row.risk)} - ${row.label}", style = MaterialTheme.typography.bodyMedium)
    }
}

private data class EventRow(val timestamp: String, val risk: Float, val label: String)

private val SAMPLE = listOf(
    EventRow("12:04:11", 0.08f, "Baseline"),
    EventRow("12:09:47", 0.21f, "Elevated HR"),
    EventRow("12:13:02", 0.74f, "Pre-ictal warning (dismissed by user)"),
    EventRow("12:18:22", 0.10f, "Recovered"),
)
