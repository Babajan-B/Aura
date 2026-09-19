package com.auraguard.phone.sos

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.telephony.SmsManager
import android.util.Log
import androidx.core.content.ContextCompat

/**
 * Dispatches a two-pronged alert when the model crosses the SOS threshold:
 *
 *  1. SMS text to every contact in [contacts] containing the location and
 *     a templated warning ("Possible seizure detected ...").
 *  2. ACTION_DIAL intent for the user's primary emergency number — we use
 *     DIAL not CALL to avoid the runtime CALL_PHONE permission for v0.
 *
 * The class is intentionally side-effect light so it can be unit-tested by
 * passing fakes for the system services. The hackathon-day TODOs are
 * marked inline.
 */
class EmergencyDispatcher(
    private val context: Context,
    private val contacts: List<EmergencyContact>,
    private val primaryDialNumber: String? = null,
) {

    fun dispatch(latitude: Double?, longitude: Double?, riskScore: Float) {
        val message = buildMessage(latitude, longitude, riskScore)
        sendSms(message)
        primaryDialNumber?.let(::launchDial)
    }

    private fun buildMessage(lat: Double?, lon: Double?, risk: Float): String {
        val location = if (lat != null && lon != null) {
            "https://maps.google.com/?q=$lat,$lon"
        } else {
            "(location unavailable)"
        }
        return "Aura Guard: possible seizure detected (risk=${"%.2f".format(risk)}). " +
            "Owner location: $location. Reply OK if false alarm."
    }

    private fun sendSms(message: String) {
        if (!hasPermission(Manifest.permission.SEND_SMS)) {
            Log.w(TAG, "SEND_SMS not granted; skipping SMS dispatch")
            return
        }
        val sms = SmsManager.getDefault()
        contacts.forEach { contact ->
            try {
                sms.sendTextMessage(contact.phone, null, message, null, null)
                Log.i(TAG, "SOS SMS queued -> ${contact.label}")
            } catch (t: Throwable) {
                Log.e(TAG, "SMS to ${contact.label} failed", t)
            }
        }
    }

    private fun launchDial(number: String) {
        val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$number"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        runCatching { context.startActivity(intent) }
            .onFailure { Log.e(TAG, "DIAL intent failed", it) }
    }

    private fun hasPermission(perm: String): Boolean =
        ContextCompat.checkSelfPermission(context, perm) == PackageManager.PERMISSION_GRANTED

    data class EmergencyContact(val label: String, val phone: String)

    companion object { private const val TAG = "EmergencyDispatcher" }
}
