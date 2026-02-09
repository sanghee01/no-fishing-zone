package com.aegislink.app.service

import android.annotation.TargetApi
import android.os.Build
import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Extracts URL from browser address bars.
 * Supports Chrome, Samsung Internet, Firefox, and other major browsers.
 */
class BrowserUrlExtractor {
    companion object {
        private const val TAG = "BrowserUrlExtractor"
        
        // Include invisible/control Unicode characters to remove
        private val INVISIBLE_CHARS_REGEX = Regex("[\u200E\u200F\u200B\u200C\u200D\u2060\uFEFF]")
        
        // Known browser URL bar IDs
        private val BROWSER_URL_BAR_IDS = listOf(
            // Chrome
            "com.android.chrome:id/url_bar",
            "com.android.chrome:id/omnibox_url_text",
            "com.android.chrome:id/location_bar",
            // Samsung Internet
            "com.sec.android.app.sbrowser:id/url_bar",
            "com.sec.android.app.sbrowser:id/location_bar_edit_text",
            // Firefox
            "org.mozilla.firefox:id/url_bar",
            "org.mozilla.firefox:id/mozac_browser_toolbar_url_view",
            // Naver Whale
            "com.naver.whale:id/url_bar",
            // Opera
            "com.opera.browser:id/url_field"
        )
    }
    
    private val urlPattern = Regex("""https?://[^\s<>"{}|\\^`\[\]]+""")
    
    /**
     * Attempts to extract URL from browser's address bar.
     * Returns null if no browser URL bar is found.
     */
    @TargetApi(Build.VERSION_CODES.JELLY_BEAN_MR2)
    fun extractBrowserUrl(rootNode: AccessibilityNodeInfo): String? {
        for (urlBarId in BROWSER_URL_BAR_IDS) {
            try {
                val nodes = rootNode.findAccessibilityNodeInfosByViewId(urlBarId)
                if (nodes.isNotEmpty()) {
                    val urlBarNode = nodes[0]
                    val urlText = urlBarNode.text?.toString()
                    
                    // Recycle all nodes
                    nodes.forEach { it.recycle() }
                    
                    if (!urlText.isNullOrBlank()) {
                        val normalizedUrl = normalizeUrl(urlText)
                        Log.d(TAG, "Found browser URL: $normalizedUrl (from $urlBarId)")
                        return normalizedUrl
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Error finding URL bar $urlBarId", e)
            }
        }
        return null
    }
    
    /**
     * Normalizes URL text from address bar.
     * - Removes invisible characters
     * - Extracts full URL if present
     * - Adds https:// if no protocol
     */
    private fun normalizeUrl(urlText: String): String {
        // Sanitize first
        val cleanText = urlText.replace(INVISIBLE_CHARS_REGEX, "").trim()
        
        // Try to extract full URL pattern
        val match = urlPattern.find(cleanText)
        if (match != null) {
            return match.value
        }
        
        // If no protocol, assume https
        return if (!cleanText.startsWith("http")) {
            "https://$cleanText"
        } else {
            cleanText
        }
    }
}
