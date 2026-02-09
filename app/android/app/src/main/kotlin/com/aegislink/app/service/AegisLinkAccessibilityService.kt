package com.aegislink.app.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.graphics.PixelFormat
import android.os.Build
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.TextView
import com.aegislink.app.R
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

import com.aegislink.app.BuildConfig

/**
 * Core AccessibilityService for Aegis Link smishing prevention app.
 * Detects URLs from screen content and displays blocking overlay for suspicious URLs.
 */
class AegisLinkAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "AegisLinkService"
        const val CHANNEL_NAME = "com.aegislink.app/blocker"
        private const val VERIFICATION_BASE_URL = BuildConfig.VERIFICATION_BASE_URL

        // Packages to monitor (messaging apps, browsers)
        private val MONITORED_PACKAGES = setOf(
            "com.samsung.android.messaging",
            "com.google.android.apps.messaging",
            "com.kakao.talk",
            "com.android.chrome",
            "org.mozilla.firefox",
            "com.sec.android.app.sbrowser",
            "com.sec.android.app.sbrowser.beta",
            "com.naver.whale"
        )

        // Suspicious smishing URL patterns
        private val SUSPICIOUS_PATTERNS = listOf(
            Regex("""https://forms.gle/P2F8fFdYoMMRWDq19""", RegexOption.IGNORE_CASE),
            Regex("""https://l.wl.co/l\?u=https://qr-codes.io/kXK7z3""", RegexOption.IGNORE_CASE),
            Regex("""https://qr-codes.io/.*""", RegexOption.IGNORE_CASE),
            Regex("""https://templat65sldh.myfreesites.net""", RegexOption.IGNORE_CASE),
            Regex("""https://serviceorange7.godaddysites.com""", RegexOption.IGNORE_CASE),
            Regex("""https://unam.myfreesites.net""", RegexOption.IGNORE_CASE),
            Regex("""https://creditiperhabbogratissicuro100.blogspot.it.*""", RegexOption.IGNORE_CASE),
            Regex("""https://vtxmail2018.myfreesites.net""", RegexOption.IGNORE_CASE),
            Regex("""https://qr-codes.io/kXK7z3""", RegexOption.IGNORE_CASE)
        )
        // Service instance for Flutter access
        var instance: AegisLinkAccessibilityService? = null
            private set

        /**
         * Mode flag: When true, ALL links are redirected to verification URL.
         * When false, only suspicious URLs trigger the blocking overlay.
         * Default: true (universal intercept mode)
         */
        var universalInterceptMode: Boolean = true
    }

    private var windowManager: WindowManager? = null
    private var overlayView: View? = null
    private var methodChannel: MethodChannel? = null
    private var currentBlockedUrl: String? = null

    // URL Scanner handles suspicious URL detection (legacy mode)
    private val urlScanner = UrlScanner(VERIFICATION_BASE_URL, SUSPICIOUS_PATTERNS)

    // Universal Link Interceptor handles ALL URL redirection (new mode)
    private val universalInterceptor = UniversalLinkInterceptor(VERIFICATION_BASE_URL)

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        // Configure service
        serviceInfo = serviceInfo?.apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED  // For external app launches
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
            notificationTimeout = 100
        }

        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager

        Log.i(TAG, "AegisLink AccessibilityService connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return

        // Package filtering
        val packageName = event.packageName?.toString() ?: return
        if (packageName !in MONITORED_PACKAGES) return

        // Check for URLs on relevant events
        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED,
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                Log.d(TAG, "Event: ${getEventTypeName(event.eventType)} from $packageName")

                // Choose mode: universal intercept vs suspicious-only blocking
                if (universalInterceptMode) {
                    handleUniversalIntercept(packageName)
                } else {
                    checkForSuspiciousUrls(packageName)
                }
            }
        }
    }

    private fun getEventTypeName(eventType: Int): String {
        return when (eventType) {
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> "CONTENT_CHANGED"
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> "STATE_CHANGED"
            AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED -> "TEXT_CHANGED"
            else -> "UNKNOWN($eventType)"
        }
    }

    /**
     * Handles Universal Intercept mode - redirects ALL links to verification URL.
     * This is the NEW behavior: every link click goes through verification.
     */
    private fun handleUniversalIntercept(packageName: String) {
        val rootNode = rootInActiveWindow ?: return

        try {
            val result = universalInterceptor.checkForIntercept(rootNode)

            // Skip if on verification page or no interception needed
            if (result.isOnVerificationPage || !result.shouldIntercept) {
                return
            }

            val originalUrl = result.originalUrl ?: return
            val redirectUrl = result.redirectUrl ?: return

            Log.i(TAG, "[Universal] Intercepting: $originalUrl from $packageName")

            // Redirect to verification URL
            try {
                val intent = android.content.Intent(
                    android.content.Intent.ACTION_VIEW,
                    android.net.Uri.parse(redirectUrl)
                )
                intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)

                // Mark as processed to prevent re-interception
                universalInterceptor.markAsProcessed(originalUrl)

                // Notify Flutter about the interception
                notifyFlutterIntercept(originalUrl, redirectUrl, packageName)

            } catch (e: Exception) {
                Log.e(TAG, "Failed to redirect to verification URL", e)
            }

        } finally {
            rootNode.recycle()
        }
    }

    /**
     * Checks current window for suspicious URLs using UrlScanner.
     * This is the LEGACY behavior: only suspicious URLs trigger overlay.
     */
    private fun checkForSuspiciousUrls(packageName: String) {
        val rootNode = rootInActiveWindow ?: return

        try {
            val result = urlScanner.scan(rootNode)

            // Skip if on verification page
            if (result.isOnVerificationPage) {
                Log.d(TAG, "On verification page, skipping")
                return
            }

            // Only show overlay for NEW suspicious URLs
            if (result.newSuspiciousUrls.isNotEmpty()) {
                val url = result.newSuspiciousUrls.first()
                Log.w(TAG, "NEW suspicious URL detected: $url from $packageName")
                showBlockingOverlay(url, packageName)
                notifyFlutter(url, packageName)
                urlScanner.markAsBlocked(url)  // Prevent re-triggering
            }
        } finally {
            rootNode.recycle()
        }
    }

    override fun onInterrupt() {
        Log.w(TAG, "AegisLink AccessibilityService interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        dismissOverlay()
        Log.i(TAG, "AegisLink AccessibilityService destroyed")
    }

    /**
     * Displays blocking overlay at the top of the screen.
     */
    private fun showBlockingOverlay(url: String, packageName: String) {
        if (overlayView != null) return // Already displayed

        currentBlockedUrl = url  // Track the URL being blocked

        val layoutParams = WindowManager.LayoutParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            } else {
                @Suppress("DEPRECATION")
                WindowManager.LayoutParams.TYPE_PHONE
            }
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
            format = PixelFormat.TRANSLUCENT
            gravity = Gravity.CENTER
        }

        overlayView = LayoutInflater.from(this)
            .inflate(R.layout.overlay_blocking, null)?.apply {

                findViewById<TextView>(R.id.tvWarningMessage)?.text =
                    "⚠️ Suspicious URL detected!\n\n$url"

                findViewById<Button>(R.id.btnDismiss)?.setOnClickListener {

                    try {
                        val verificationUrl = "${VERIFICATION_BASE_URL}?url=$url"
                        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(verificationUrl))
                        intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                        startActivity(intent)
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to open verification URL", e)
                    }

                    dismissOverlay()
                }

                findViewById<Button>(R.id.btnProceed)?.setOnClickListener {
                    // User chose to proceed with risk
                    Log.w(TAG, "User chose to proceed with suspicious URL: $url")
                    dismissOverlay()
                }
            }

        try {
            windowManager?.addView(overlayView, layoutParams)
            Log.i(TAG, "Blocking overlay displayed for: $url")

            // Attempt to navigate back to close the malicious page/popup
            performGlobalAction(GLOBAL_ACTION_BACK)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to show overlay", e)
        }
    }

    /**
     * Removes overlay from screen.
     */
    private fun dismissOverlay() {
        overlayView?.let { view ->
            try {
                windowManager?.removeView(view)
            } catch (e: Exception) {
                Log.e(TAG, "Failed to remove overlay", e)
            }
        }
        overlayView = null

        currentBlockedUrl = null
    }

    /**
     * Notifies Flutter about blocked URL event (legacy mode).
     */
    private fun notifyFlutter(url: String, packageName: String) {
        methodChannel?.invokeMethod("onUrlBlocked", mapOf(
            "url" to url,
            "app" to packageName,
            "timestamp" to System.currentTimeMillis()
        ))
    }

    /**
     * Notifies Flutter about intercepted URL event (universal mode).
     */
    private fun notifyFlutterIntercept(originalUrl: String, redirectUrl: String, packageName: String) {
        methodChannel?.invokeMethod("onUrlIntercepted", mapOf(
            "originalUrl" to originalUrl,
            "redirectUrl" to redirectUrl,
            "app" to packageName,
            "timestamp" to System.currentTimeMillis()
        ))
    }

    /**
     * Returns list of processed/blocked URLs for Flutter access.
     */
    fun getIgnoredUrls(): List<String> {
        return if (universalInterceptMode) {
            universalInterceptor.getProcessedUrls().toList()
        } else {
            urlScanner.getBlockedUrls()
        }
    }

    /**
     * Attaches Flutter MethodChannel.
     * Called from MainActivity when FlutterEngine is initialized.
     */
    fun attachFlutterEngine(flutterEngine: FlutterEngine) {
        methodChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL_NAME
        )
        Log.i(TAG, "Flutter MethodChannel attached")
    }
}
