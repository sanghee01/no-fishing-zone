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
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Button
import android.widget.TextView
import com.aegislink.app.R
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Core AccessibilityService for Aegis Link smishing prevention app.
 * Detects URLs from screen content and displays blocking overlay for suspicious URLs.
 */
class AegisLinkAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "AegisLinkService"
        const val CHANNEL_NAME = "com.aegislink.app/blocker"
        private const val VERIFICATION_BASE_URL = "https://check.com"
        
        // Packages to monitor (messaging apps, browsers)
        private val MONITORED_PACKAGES = setOf(
            "com.samsung.android.messaging",
            "com.google.android.apps.messaging",
            "com.kakao.talk",
            "com.android.chrome",
            "org.mozilla.firefox",
            "com.sec.android.app.sbrowser",
            "com.naver.whale"
        )
        
        // Suspicious smishing URL patterns
        private val SUSPICIOUS_PATTERNS = listOf(
            Regex("""https?://bit\.ly/\w+""", RegexOption.IGNORE_CASE),
            Regex("""https?://tinyurl\.com/\w+""", RegexOption.IGNORE_CASE),
            Regex("""https?://.*\.xyz/.*""", RegexOption.IGNORE_CASE),
            Regex("""https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*"""),
            Regex("""https?://.*택배.*"""),
            Regex("""https?://.*delivery.*\.kr""", RegexOption.IGNORE_CASE),
            Regex("""https?://.*국민지원.*"""),
            Regex("""https?://.*정부24.*"""),
            Regex("""https?://.*naver.*"""),
            Regex("""https?://.*blog.*""")
        )
        
        // Service instance for Flutter access
        var instance: AegisLinkAccessibilityService? = null
            private set
    }

    private var windowManager: WindowManager? = null
    private var overlayView: View? = null
    private var methodChannel: MethodChannel? = null
    private val ignoredUrls = mutableSetOf<String>()
    private var currentBlockedUrl: String? = null  // Track currently displayed URL
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        
        // Configure service
        serviceInfo = serviceInfo?.apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                         AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED
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
        
        // Debug log for event type
        Log.d(TAG, "Event received: type=${event.eventType}, package=$packageName")
        
        // Handle all event types - check for URLs on any monitored event
        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_CLICKED -> {
                Log.d(TAG, "VIEW_CLICKED event")
                checkForSuspiciousUrls(packageName)
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                Log.d(TAG, "WINDOW_STATE_CHANGED event")
                checkForSuspiciousUrls(packageName)
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                Log.d(TAG, "WINDOW_CONTENT_CHANGED event")
                checkForSuspiciousUrls(packageName)
            }
            AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED -> {
                Log.d(TAG, "VIEW_TEXT_CHANGED event")
                checkForSuspiciousUrls(packageName)
            }
            AccessibilityEvent.TYPE_VIEW_FOCUSED -> {
                Log.d(TAG, "VIEW_FOCUSED event")
                checkForSuspiciousUrls(packageName)
            }
            else -> {
                // Also check on other events to catch edge cases
                Log.d(TAG, "OTHER event: ${event.eventType}")
                checkForSuspiciousUrls(packageName)
            }
        }
    }
    
    /**
     * Checks current window for suspicious URLs.
     */
    private fun checkForSuspiciousUrls(packageName: String) {
        val rootNode = rootInActiveWindow ?: run {
            Log.d(TAG, "rootInActiveWindow is null")
            return
        }
        val urls = extractUrlsFromNode(rootNode)
        
        Log.d(TAG, "Found ${urls.size} URLs: $urls")
        
        // Check for suspicious URLs
        for (url in urls) {
            val isSuspicious = isSuspiciousUrl(url)
            val isIgnored = url in ignoredUrls
            Log.d(TAG, "URL check: $url, suspicious=$isSuspicious, ignored=$isIgnored")
            
            if (isSuspicious && !isIgnored) {
                Log.w(TAG, "Suspicious URL detected: $url from $packageName")
                showBlockingOverlay(url, packageName)
                notifyFlutter(url, packageName)
                break
            }
        }
        
        rootNode.recycle()
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
     * Recursively traverses the node tree to extract URLs.
     */
    private fun extractUrlsFromNode(node: AccessibilityNodeInfo): List<String> {
        val urls = mutableSetOf<String>()  // Use Set to avoid duplicates
        val urlPattern = Regex("""https?://[^\s<>"{}|\\^`\[\]]+""")
        
        // Check current node text
        node.text?.let { text ->
            urlPattern.findAll(text.toString()).forEach { match ->
                urls.add(match.value)
            }
        }
        
        // Recursively traverse child nodes
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                urls.addAll(extractUrlsFromNode(child))
                child.recycle()
            }
        }
        
        return urls.toList()
    }
    
    /**
     * Checks if a URL matches suspicious smishing patterns.
     */
    private fun isSuspiciousUrl(url: String): Boolean {
        return SUSPICIOUS_PATTERNS.any { pattern ->
            pattern.containsMatchIn(url)
        }
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
                    ignoredUrls.add(url)
                    
                    try {
                        val verificationUrl = "$VERIFICATION_BASE_URL?t=$url"
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
     * Notifies Flutter about blocked URL event.
     */
    private fun notifyFlutter(url: String, packageName: String) {
        methodChannel?.invokeMethod("onUrlBlocked", mapOf(
            "url" to url,
            "app" to packageName,
            "timestamp" to System.currentTimeMillis()
        ))
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
    
    /**
     * Returns list of ignored URLs.
     */
    fun getIgnoredUrls(): List<String> = ignoredUrls.toList()
}
