package com.aegislink.app.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
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
 * 군인 스미싱 방지 앱의 핵심 AccessibilityService.
 * 화면의 텍스트에서 URL을 감지하고, 의심스러운 URL 발견 시 차단 오버레이를 표시합니다.
 */
class AegisLinkAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "AegisLinkService"
        const val CHANNEL_NAME = "com.aegislink.app/blocker"
        private const val VERIFICATION_BASE_URL = "https://check.com"
        
        // 모니터링 대상 패키지 (문자, 카카오톡, 주요 브라우저)
        private val MONITORED_PACKAGES = setOf(
            "com.samsung.android.messaging",
            "com.google.android.apps.messaging",
            "com.kakao.talk",
            "com.android.chrome",
            "org.mozilla.firefox",
            "com.sec.android.app.sbrowser"
        )
        
        // 스미싱 의심 URL 패턴
        private val SUSPICIOUS_PATTERNS = listOf(
            Regex("""https?://bit\.ly/\w+""", RegexOption.IGNORE_CASE),
            Regex("""https?://.*\.xyz/.*""", RegexOption.IGNORE_CASE),
            Regex("""https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*"""),
            Regex("""https?://.*택배.*\.kr"""),
            Regex("""https?://.*국민지원.*"""),
            Regex("""https?://.*정부24.*"""),
        )
        
        // 서비스 인스턴스 (Flutter에서 접근용)
        var instance: AegisLinkAccessibilityService? = null
            private set
    }
    
    private var windowManager: WindowManager? = null
    private var overlayView: View? = null
    private var methodChannel: MethodChannel? = null
    private val ignoredUrls = mutableSetOf<String>()
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        
        // 서비스 설정
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
        
        // 패키지 필터링
        val packageName = event.packageName?.toString() ?: return
        if (packageName !in MONITORED_PACKAGES) return
        
        // 화면 텍스트에서 URL 추출
        val rootNode = rootInActiveWindow ?: return
        val urls = extractUrlsFromNode(rootNode)
        
        // 의심 URL 검사
        for (url in urls) {
            if (url in ignoredUrls) continue
            
            if (isSuspiciousUrl(url)) {
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
     * 노드 트리를 재귀적으로 탐색하여 URL을 추출합니다.
     */
    private fun extractUrlsFromNode(node: AccessibilityNodeInfo): List<String> {
        val urls = mutableListOf<String>()
        val urlPattern = Regex("""https?://[^\s<>"{}|\\^`\[\]]+""")
        
        // 현재 노드의 텍스트 검사
        node.text?.let { text ->
            urlPattern.findAll(text.toString()).forEach { match ->
                urls.add(match.value)
            }
        }
        
        // 자식 노드 재귀 탐색
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                urls.addAll(extractUrlsFromNode(child))
                child.recycle()
            }
        }
        
        return urls
    }
    
    /**
     * URL이 스미싱 의심 패턴에 해당하는지 검사합니다.
     */
    private fun isSuspiciousUrl(url: String): Boolean {
        return SUSPICIOUS_PATTERNS.any { pattern ->
            pattern.containsMatchIn(url)
        }
    }
    
    /**
     * 차단 오버레이를 화면 최상단에 표시합니다.
     */
    private fun showBlockingOverlay(url: String, packageName: String) {
        if (overlayView != null) return // 이미 표시 중
        
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
                    "⚠️ 스미싱 의심 URL이 감지되었습니다!\n\n$url"
                
                findViewById<Button>(R.id.btnDismiss)?.setOnClickListener {
                    ignoredUrls.add(url)
                    
                    try {
                        val verificationUrl = "$VERIFICATION_BASE_URL?t=$url"
                        val intent = Intent(Intent.ACTION_VIEW, android.net.Uri.parse(verificationUrl))
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        startActivity(intent)
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to open verification URL", e)
                    }
                    
                    dismissOverlay()
                }
                
                findViewById<Button>(R.id.btnProceed)?.setOnClickListener {
                    // 사용자가 위험을 감수하고 진행
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
     * 오버레이를 화면에서 제거합니다.
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
    }
    
    /**
     * Flutter에 차단 이벤트를 알립니다.
     */
    private fun notifyFlutter(url: String, packageName: String) {
        methodChannel?.invokeMethod("onUrlBlocked", mapOf(
            "url" to url,
            "app" to packageName,
            "timestamp" to System.currentTimeMillis()
        ))
    }
    
    /**
     * Flutter MethodChannel을 연결합니다.
     * MainActivity에서 FlutterEngine 초기화 시 호출됩니다.
     */
    fun attachFlutterEngine(flutterEngine: FlutterEngine) {
        methodChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL_NAME
        )
        Log.i(TAG, "Flutter MethodChannel attached")
    }
}
