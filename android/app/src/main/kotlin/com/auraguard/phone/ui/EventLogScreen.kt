package com.auraguard.phone.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.auraguard.phone.data.EventLogEntity
import com.auraguard.phone.data.EventLogRepository
import kotlinx.coroutines.flow.flowOf
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun EventLogScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val events by remember { EventLogRepository.observe(context) }.collectAsState(initial = emptyList())

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Event history", style = MaterialTheme.typography.titleLarge)
            Row {
                if (events.isNotEmpty()) TextButton(onClick = { EventLogRepository.clear(context) }) { Text("Clear") }
                TextButton(onClick = onBack) { Text("Back") }
            }
        }
        Text(
            "Local audit history. A score of -- means inference was withheld.",
            style = MaterialTheme.typography.bodySmall,
        )
        HorizontalDivider(Modifier.padding(vertical = 8.dp))
        if (events.isEmpty()) {
            Text("No events recorded yet.", style = MaterialTheme.typography.bodyMedium)
        } else {
            LazyColumn {
                items(events, key = { it.id }) { event ->
                    EventRow(event)
                    HorizontalDivider()
                }
            }
        }
    }
}

@Composable
private fun EventRow(event: EventLogEntity) {
    Column(Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(formatTimestamp(event.capturedAtMs), style = MaterialTheme.typography.labelLarge)
            Text(event.mode.replace('_', ' '), style = MaterialTheme.typography.labelSmall)
        }
        Text(
            "Risk ${if (event.riskScore < 0f) "--" else "%.0f%%".format(event.riskScore * 100)} · ${event.label}",
            style = MaterialTheme.typography.bodyMedium,
        )
        Text(
            buildString {
                append(event.modelName)
                event.heartRate?.let { append(" · HR ${"%.0f".format(it)}") }
                event.temperatureC?.let { append(" · Temp ${"%.1f".format(it)} C") }
                append(" · Quality ${"%.0f".format(event.signalQuality * 100)}%")
            },
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

private fun formatTimestamp(value: Long): String =
    SimpleDateFormat("MMM d, HH:mm:ss", Locale.getDefault()).format(Date(value))
