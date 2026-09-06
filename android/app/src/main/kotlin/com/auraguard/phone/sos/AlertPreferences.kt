package com.auraguard.phone.sos

import android.content.Context

class AlertPreferences(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    var caregiverName: String
        get() = prefs.getString(KEY_NAME, "Caregiver") ?: "Caregiver"
        set(value) { prefs.edit().putString(KEY_NAME, value.trim()).apply() }

    var caregiverPhone: String
        get() = prefs.getString(KEY_PHONE, "") ?: ""
        set(value) { prefs.edit().putString(KEY_PHONE, value.trim()).apply() }

    var primaryDialNumber: String
        get() = prefs.getString(KEY_DIAL, "") ?: ""
        set(value) { prefs.edit().putString(KEY_DIAL, value.trim()).apply() }

    fun configuredContacts(): List<EmergencyDispatcher.EmergencyContact> =
        caregiverPhone.takeIf { it.isNotBlank() }
            ?.let { listOf(EmergencyDispatcher.EmergencyContact(caregiverName, it)) }
            .orEmpty()

    companion object {
        private const val FILE = "aura_alert_preferences"
        private const val KEY_NAME = "caregiver_name"
        private const val KEY_PHONE = "caregiver_phone"
        private const val KEY_DIAL = "primary_dial_number"
    }
}
