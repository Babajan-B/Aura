package com.auraguard.phone.sos

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.CancellationSignal
import androidx.core.content.ContextCompat
import com.auraguard.phone.AuraState

class EmergencyCoordinator(private val context: Context) {
    private val app = context.applicationContext

    fun dispatch(riskScore: Float, onComplete: (String) -> Unit) {
        val preferences = AlertPreferences(app)
        val contacts = preferences.configuredContacts()
        if (contacts.isEmpty()) {
            onComplete("No caregiver phone is configured")
            return
        }

        currentLocation { location ->
            EmergencyDispatcher(
                context = app,
                contacts = contacts,
                primaryDialNumber = preferences.primaryDialNumber.takeIf { it.isNotBlank() },
            ).dispatch(
                latitude = location?.latitude,
                longitude = location?.longitude,
                riskScore = riskScore,
            )
            onComplete(if (location == null) "Alert sent without location" else "Alert sent with GPS location")
        }
    }

    private fun currentLocation(callback: (Location?) -> Unit) {
        if (ContextCompat.checkSelfPermission(app, Manifest.permission.ACCESS_FINE_LOCATION) !=
            PackageManager.PERMISSION_GRANTED &&
            ContextCompat.checkSelfPermission(app, Manifest.permission.ACCESS_COARSE_LOCATION) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            callback(null)
            return
        }

        val manager = app.getSystemService(LocationManager::class.java)
        val provider = when {
            manager.isProviderEnabled(LocationManager.GPS_PROVIDER) -> LocationManager.GPS_PROVIDER
            manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER
            else -> null
        }
        if (provider == null) {
            callback(null)
            return
        }

        runCatching {
            manager.getCurrentLocation(
                provider,
                CancellationSignal(),
                ContextCompat.getMainExecutor(app),
                callback,
            )
        }.onFailure { callback(manager.getLastKnownLocation(provider)) }
    }
}
