package com.aegislink.app.service

import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Main URL scanner that orchestrates URL detection and blocking logic.
 * Uses BrowserUrlExtractor and TextUrlExtractor for URL extraction.
 */
class UrlScanner(
    private val verificationBaseUrl: String,
    private val suspiciousPatterns: List<Regex>
) {
    companion object {
        private const val TAG = "UrlScanner"
    }
    
    // Extractors
    private val browserExtractor = BrowserUrlExtractor()
    private val textExtractor = TextUrlExtractor()
    
    // URLs that have been shown overlay (blocked)
    private val blockedUrls = mutableSetOf<String>()
    
    /**
     * Result of scanning a node tree for URLs.
     */
    data class ScanResult(
        val allUrls: List<String>,
        val browserUrl: String?,
        val suspiciousUrls: Set<String>,
        val newSuspiciousUrls: Set<String>,
        val isOnVerificationPage: Boolean
    )
    
    /**
     * Scans the node tree for URLs and returns scan result.
     */
    fun scan(rootNode: AccessibilityNodeInfo): ScanResult {
        // 1. Try to get URL from browser address bar
        val browserUrl = browserExtractor.extractBrowserUrl(rootNode)
        
        // 2. Extract URLs from all text on screen
        val textUrls = textExtractor.extractUrls(rootNode)
        
        // 3. Combine all URLs
        val allUrls = mutableSetOf<String>()
        browserUrl?.let { allUrls.add(it) }
        allUrls.addAll(textUrls)
        
        Log.d(TAG, "Found ${allUrls.size} URLs (browser: $browserUrl, text: ${textUrls.size})")
        
        // Check if on verification page
        val isOnVerificationPage = allUrls.any { it.contains(verificationBaseUrl) }
        if (isOnVerificationPage) {
            Log.d(TAG, "On verification page, clearing blocked list")
            blockedUrls.clear()
            return ScanResult(
                allUrls = allUrls.toList(),
                browserUrl = browserUrl,
                suspiciousUrls = emptySet(),
                newSuspiciousUrls = emptySet(),
                isOnVerificationPage = true
            )
        }
        
        // Find suspicious URLs
        val suspiciousUrls = allUrls.filter { isSuspicious(it) }.toSet()
        
        // If no suspicious URLs on screen, clear blocked list (user navigated to safe page)
        if (suspiciousUrls.isEmpty()) {
            if (blockedUrls.isNotEmpty()) {
                Log.d(TAG, "No suspicious URLs, clearing blocked list: $blockedUrls")
                blockedUrls.clear()
            }
            return ScanResult(
                allUrls = allUrls.toList(),
                browserUrl = browserUrl,
                suspiciousUrls = emptySet(),
                newSuspiciousUrls = emptySet(),
                isOnVerificationPage = false
            )
        }
        
        // Find NEW suspicious URLs (not yet blocked)
        val newSuspiciousUrls = suspiciousUrls.filter { it !in blockedUrls }.toSet()
        
        Log.d(TAG, "Suspicious: $suspiciousUrls, new: $newSuspiciousUrls, blocked: $blockedUrls")
        
        return ScanResult(
            allUrls = allUrls.toList(),
            browserUrl = browserUrl,
            suspiciousUrls = suspiciousUrls,
            newSuspiciousUrls = newSuspiciousUrls,
            isOnVerificationPage = false
        )
    }
    
    /**
     * Marks a URL as blocked (overlay was shown).
     */
    fun markAsBlocked(url: String) {
        blockedUrls.add(url)
        Log.d(TAG, "Marked as blocked: $url")
    }
    
    /**
     * Clears all tracking state.
     */
    fun clearAll() {
        blockedUrls.clear()
        Log.d(TAG, "Cleared all tracking")
    }
    
    /**
     * Returns list of blocked URLs.
     */
    fun getBlockedUrls(): List<String> {
        return blockedUrls.toList()
    }
    
    /**
     * Checks if URL matches any suspicious pattern.
     */
    private fun isSuspicious(url: String): Boolean {
        return suspiciousPatterns.any { it.containsMatchIn(url) }
    }
}
