package com.aegislink.app.service

import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Universal Link Interceptor - intercepts ALL link clicks and redirects to verification URL.
 * 
 * Unlike UrlScanner which only blocks suspicious URLs, this interceptor redirects
 * ALL detected URLs to the verification server for analysis before allowing access.
 * 
 * Features:
 * - Debouncing: Same URL won't trigger within cooldown period
 * - URL change detection: Only triggers on actual navigation
 * - Browser edit mode skip: Ignores URL bar editing
 * 
 * Usage:
 * - Enable universalInterceptMode in AegisLinkAccessibilityService
 * - All link clicks will be redirected to: {VERIFICATION_BASE_URL}?url={original_url}
 */
class UniversalLinkInterceptor(
    private val verificationBaseUrl: String
) {
    companion object {
        private const val TAG = "UniversalLinkInterceptor"
        
        // Cooldown period in milliseconds (prevent rapid re-triggers)
        private const val INTERCEPT_COOLDOWN_MS = 3000L
        
        // Minimum URL length to consider for interception
        private const val MIN_URL_LENGTH = 10
        
        // Unicode control characters to remove from URLs
        // These are often used in phishing to hide the real URL
        private val INVISIBLE_CHARS_REGEX = Regex("[\u200E\u200F\u200B\u200C\u200D\u2060\uFEFF]")
        
        // Verification grace period (allow redirects within this time)
        private const val VERIFICATION_GRACE_PERIOD_MS = 10000L
        
        // TTL for processed URLs (re-verify after this time)
        private const val PROCESSED_URL_TTL_MS = 5000L // 5 seconds
        
        /**
         * Removes invisible/control Unicode characters from URL.
         * Samsung Internet and other browsers sometimes include these.
         */
        fun sanitizeUrl(url: String): String {
            return url.replace(INVISIBLE_CHARS_REGEX, "").trim()
        }
    }
    
    // Extractors (reuse existing)
    private val browserExtractor = BrowserUrlExtractor()
    // Disabled TextUrlExtractor as per request - only intercept browser address bar
    // private val textExtractor = TextUrlExtractor()
    
    // URLs already processed with their expiration time
    private val processedUrls = mutableMapOf<String, Long>()
    
    // Last intercepted URL and timestamp for debouncing
    private var lastInterceptedUrl: String? = null
    private var lastInterceptTime: Long = 0
    
    // Track the current stable URL (to detect actual navigation)
    private var currentStableUrl: String? = null
    private var urlStableCount: Int = 0
    
    // Time when user last visited the verification page
    private var lastVerificationVisitTime: Long = 0
    
    // Time when verification page log was last printed (to prevent spam)
    private var lastVerificationLogTime: Long = 0
    
    /**
     * Result of interception check.
     */
    data class InterceptResult(
        val shouldIntercept: Boolean,
        val originalUrl: String?,
        val redirectUrl: String?,
        val isOnVerificationPage: Boolean,
        val skipReason: String? = null
    )
    
    /**
     * Checks if any URL should be intercepted and returns redirect info.
     * 
     * @param rootNode The accessibility node to scan for URLs
     * @return InterceptResult with interception details
     */
    fun checkForIntercept(rootNode: AccessibilityNodeInfo): InterceptResult {
        // 1. Try to get URL from browser address bar (most accurate)
        val rawBrowserUrl = browserExtractor.extractBrowserUrl(rootNode)
        
        // 2. If no browser URL, extract from screen text (DISABLED)
        val textUrls = emptyList<String>() 
        
        // Use browser URL first, then first text URL (currently only browser URL)
        val rawUrl = rawBrowserUrl ?: textUrls.firstOrNull()
        
        // Sanitize URL - remove invisible Unicode characters
        val targetUrl = rawUrl?.let { sanitizeUrl(it) }
        
        if (targetUrl == null) {
            Log.d(TAG, "No URL detected")
            resetStableUrl()
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = null,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "no_url"
            )
        }
        
        // Skip if URL is too short (likely partial/editing)
        if (targetUrl.length < MIN_URL_LENGTH) {
            Log.d(TAG, "URL too short, likely editing: $targetUrl")
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "url_too_short"
            )
        }
        
        // Skip if URL doesn't look complete (no scheme or domain)
        if (!isCompleteUrl(targetUrl)) {
            Log.d(TAG, "URL looks incomplete: $targetUrl")
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "incomplete_url"
            )
        }
        
        Log.d(TAG, "Detected URL: $targetUrl")
        
        // Skip if already on verification page
        if (isVerificationUrl(targetUrl)) {
            // Update last visit time ONLY if enough time has passed since last update
            val now = System.currentTimeMillis()
            if (now - lastVerificationVisitTime > 2000) {
                 lastVerificationVisitTime = now
                 Log.d(TAG, "On verification page, enabling/refreshing grace period")
            }
            
            // Clear processed URLs when on verification page
            processedUrls.clear()
            lastInterceptedUrl = null // Reset cooldown to allow immediate re-interception
            resetStableUrl()
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = true
            )
        }
        
        // Skip if within verification grace period (user just came from verification page)
        // This handles cases where redirect parameters are stripped
        if (System.currentTimeMillis() - lastVerificationVisitTime < VERIFICATION_GRACE_PERIOD_MS) {
            Log.i(TAG, "Within verification grace period, allowing: $targetUrl")
            markAsProcessed(targetUrl)
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "grace_period"
            )
        }
        
        // Check if URL is stable (same URL detected multiple times = actual navigation)
        if (!isUrlStable(targetUrl)) {
            Log.d(TAG, "URL not stable yet, waiting: $targetUrl (count: $urlStableCount)")
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "url_not_stable"
            )
        }
        
        // Check if URL was already processed and still valid
        val expiryTime = processedUrls[targetUrl]
        if (expiryTime != null) {
            if (System.currentTimeMillis() < expiryTime) {
                Log.d(TAG, "URL already processed (valid until ${expiryTime}): $targetUrl")
                return InterceptResult(
                    shouldIntercept = false,
                    originalUrl = targetUrl,
                    redirectUrl = null,
                    isOnVerificationPage = false,
                    skipReason = "already_processed"
                )
            } else {
                // Expired, remove from processed list
                processedUrls.remove(targetUrl)
                Log.d(TAG, "Processed URL expired, re-verifying: $targetUrl")
            }
        }
        
        // Skip if URL has verification parameter (server-side pass)
        if (hasVerificationParameter(targetUrl)) {
            Log.i(TAG, "URL verified by server parameter, skipping: $targetUrl")
            // Clear processed URLs and COOLDOWN when on verification page
            // This ensures that if the user goes back to the suspicious page,
            // we intercept it immediately (no 3s delay).
            processedUrls.clear()
            lastInterceptedUrl = null 
            resetStableUrl()
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = true,
                skipReason = "verified_param"
            )
        }
        
        // Check debounce cooldown
        val now = System.currentTimeMillis()
        if (targetUrl == lastInterceptedUrl && (now - lastInterceptTime) < INTERCEPT_COOLDOWN_MS) {
            Log.d(TAG, "Within cooldown period for: $targetUrl")
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "cooldown"
            )
        }
        
        // Skip internal/safe URLs
        if (isSafeUrl(targetUrl)) {
            Log.d(TAG, "Safe URL, skipping: $targetUrl")
            return InterceptResult(
                shouldIntercept = false,
                originalUrl = targetUrl,
                redirectUrl = null,
                isOnVerificationPage = false,
                skipReason = "safe_url"
            )
        }
        
        // Build redirect URL
        val encodedUrl = android.net.Uri.encode(targetUrl)
        val redirectUrl = "${verificationBaseUrl}?url=$encodedUrl"
        
        Log.i(TAG, "Intercepting URL: $targetUrl -> $redirectUrl")
        
        return InterceptResult(
            shouldIntercept = true,
            originalUrl = targetUrl,
            redirectUrl = redirectUrl,
            isOnVerificationPage = false
        )
    }
    
    /**
     * Checks if URL is stable (detected consistently).
     * Requires the same URL to be detected multiple times before triggering.
     */
    private fun isUrlStable(url: String): Boolean {
        if (url == currentStableUrl) {
            urlStableCount++
        } else {
            currentStableUrl = url
            urlStableCount = 1
        }
        
        // Require URL to be seen at least 2 times consecutively
        return urlStableCount >= 2
    }
    
    /**
     * Resets the stable URL tracking.
     */
    private fun resetStableUrl() {
        currentStableUrl = null
        urlStableCount = 0
    }
    
    /**
     * Checks if URL looks complete (has scheme and domain).
     */
    private fun isCompleteUrl(url: String): Boolean {
        // Must start with http:// or https://
        if (!url.startsWith("http://", ignoreCase = true) && 
            !url.startsWith("https://", ignoreCase = true)) {
            return false
        }
        
        // Must have a domain (at least one dot after scheme)
        val afterScheme = url.substringAfter("://")
        if (!afterScheme.contains(".") || afterScheme.startsWith(".")) {
            return false
        }
        
        return true
    }
    
    /**
     * Marks URL as processed with TTL.
     */
    fun markAsProcessed(url: String) {
        processedUrls[url] = System.currentTimeMillis() + PROCESSED_URL_TTL_MS
        lastInterceptedUrl = url
        lastInterceptTime = System.currentTimeMillis()
        Log.d(TAG, "Marked as processed (expires in 60s): $url")
    }
    
    /**
     * Clears all tracking state.
     */
    fun clearAll() {
        processedUrls.clear()
        lastInterceptedUrl = null
        lastInterceptTime = 0
        resetStableUrl()
        Log.d(TAG, "Cleared all tracking")
    }
    
    /**
     * Gets the last intercepted URL.
     */
    fun getLastInterceptedUrl(): String? = lastInterceptedUrl
    
    /**
     * Gets all currently valid processed URLs.
     */
    fun getProcessedUrls(): Set<String> {
        val now = System.currentTimeMillis()
        // Filter out expired URLs
        val validUrls = processedUrls.filterValues { it > now }.keys
        // Clean up map
        if (processedUrls.size > validUrls.size + 10) { // Cleanup only when many expired
             val expired = processedUrls.filterValues { it <= now }.keys
             expired.forEach { processedUrls.remove(it) }
        }
        return validUrls
    }
    
    /**
     * Checks if URL has the verification parameter (e.g. verified=true).
     * This allows the server to whitelist a URL after user approval.
     */
    private fun hasVerificationParameter(url: String): Boolean {
        return try {
            val uri = android.net.Uri.parse(url)
            val isVerified = uri.getQueryParameter("aegis_verified") == "true"
            if (isVerified) {
                Log.d(TAG, "Updates: found aegis_verified=true in URL")
            }
            isVerified
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Checks if URL is the verification page.
     * Handles both with and without trailing slash.
     */
    private fun isVerificationUrl(url: String): Boolean {
        // Remove trailing slash for comparison
        val baseWithoutSlash = verificationBaseUrl.trimEnd('/')
        val urlHost = try {
            android.net.Uri.parse(url).host ?: ""
        } catch (e: Exception) {
            ""
        }
        val baseHost = try {
            android.net.Uri.parse(baseWithoutSlash).host ?: ""
        } catch (e: Exception) {
            ""
        }
        
        // Check by host (most reliable)
        if (urlHost.isNotEmpty() && baseHost.isNotEmpty() && 
            urlHost.equals(baseHost, ignoreCase = true)) {
            return true
        }
        
        // Fallback: check if URL starts with or contains verification base
        return url.startsWith(baseWithoutSlash, ignoreCase = true) ||
               url.contains(baseWithoutSlash, ignoreCase = true)
    }
    
    /**
     * Checks if URL is considered safe and should not be intercepted.
     * 
     * Safe URLs:
     * - localhost / 127.0.0.1
     * - about: protocol
     * - chrome:// internal pages
     * - file:// local files
     * - Google search, common portals
     */
    private fun isSafeUrl(url: String): Boolean {
        val safePrefixes = listOf(
            "about:",
            "chrome://",
            "file://",
            "chrome-extension://",
            "moz-extension://"
        )
        
        val safeHosts = listOf(
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "www.google.com",
            "google.com",
            "www.naver.com",
            "naver.com",
            "m.naver.com"
        )
        
        // Check safe prefixes
        if (safePrefixes.any { url.startsWith(it, ignoreCase = true) }) {
            return true
        }
        
        // Check safe hosts
        try {
            val uri = android.net.Uri.parse(url)
            val host = uri.host ?: return false
            if (safeHosts.any { host.equals(it, ignoreCase = true) }) {
                return true
            }
        } catch (e: Exception) {
            Log.w(TAG, "Failed to parse URL: $url", e)
        }
        
        return false
    }
}
