package com.aegislink.app.service

import android.annotation.TargetApi
import android.os.Build
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Extracts URLs from screen text content.
 * Recursively scans all text nodes for URL patterns.
 */
class TextUrlExtractor {
    
    private val urlPattern = Regex("""https?://[^\s<>"{}|\\^`\[\]]+""")
    
    /**
     * Extracts all URLs found in text content of the node tree.
     */
    fun extractUrls(rootNode: AccessibilityNodeInfo): Set<String> {
        val urls = mutableSetOf<String>()
        extractUrlsRecursively(rootNode, urls)
        return urls
    }
    
    /**
     * Recursively traverses node tree and extracts URLs from text.
     */
    @TargetApi(Build.VERSION_CODES.ICE_CREAM_SANDWICH)
    private fun extractUrlsRecursively(node: AccessibilityNodeInfo, urls: MutableSet<String>) {
        // Extract from current node's text
        node.text?.let { text ->
            urlPattern.findAll(text.toString()).forEach { match ->
                urls.add(match.value)
            }
        }
        
        // Process children
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                extractUrlsRecursively(child, urls)
                child.recycle()
            }
        }
    }
}
