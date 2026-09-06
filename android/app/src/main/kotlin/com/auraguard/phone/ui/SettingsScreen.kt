package com.auraguard.phone.ui

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.auraguard.phone.RiskPipeline
import com.auraguard.phone.sos.AlertPreferences

@Composable
fun SettingsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val preferences = remember { AlertPreferences(context) }
    var name by remember { mutableStateOf(preferences.caregiverName) }
    var phone by remember { mutableStateOf(preferences.caregiverPhone) }
    var dial by remember { mutableStateOf(preferences.primaryDialNumber) }
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { grants ->
        val granted = grants.values.count { it }
        Toast.makeText(context, "$granted permissions granted", Toast.LENGTH_SHORT).show()
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Safety settings", style = MaterialTheme.typography.titleLarge)
            TextButton(onClick = onBack) { Text("Back") }
        }
        Text(
            "Configure a caregiver before enabling real alert dispatch. Information stays on this phone.",
            style = MaterialTheme.typography.bodySmall,
        )
        HorizontalDivider()
        Text("Emergency contact", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("Caregiver name") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            label = { Text("Caregiver mobile number") },
            supportingText = { Text("Include the country code, for example +966") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = dial,
            onValueChange = { dial = it },
            label = { Text("Optional number to open in dialer") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Button(
            onClick = {
                preferences.caregiverName = name
                preferences.caregiverPhone = phone
                preferences.primaryDialNumber = dial
                Toast.makeText(context, "Safety settings saved", Toast.LENGTH_SHORT).show()
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Save contact") }

        HorizontalDivider()
        Text("Permissions", style = MaterialTheme.typography.titleMedium)
        Text(
            "SMS is used only after an uncancelled real alert. Location is included when available.",
            style = MaterialTheme.typography.bodySmall,
        )
        OutlinedButton(
            onClick = {
                permissionLauncher.launch(buildList {
                    add(Manifest.permission.SEND_SMS)
                    add(Manifest.permission.ACCESS_FINE_LOCATION)
                    add(Manifest.permission.ACCESS_COARSE_LOCATION)
                    if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
                }.toTypedArray())
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Review alert permissions") }

        HorizontalDivider()
        Text("Safe system test", style = MaterialTheme.typography.titleMedium)
        Text(
            "Runs the 15-second warning workflow. Emergency SMS and dialing are suppressed.",
            style = MaterialTheme.typography.bodySmall,
        )
        Button(
            onClick = {
                RiskPipeline.triggerTestCountdown(context)
                onBack()
            },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
        ) { Text("Run test countdown") }

        HorizontalDivider()
        Text("Research-use boundary", style = MaterialTheme.typography.titleMedium)
        Text(
            "Aura Guard is a research prototype. It is not a diagnostic device and must not replace medical care, prescribed monitoring, or emergency services.",
            style = MaterialTheme.typography.bodySmall,
        )
    }
}
