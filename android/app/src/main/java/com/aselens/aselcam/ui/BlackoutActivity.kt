package com.aselens.aselcam.ui

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.GestureDetector
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView

class BlackoutActivity : Activity() {

    private lateinit var gestureDetector: GestureDetector

    private val dismissReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Keep screen alive but completely dimmed
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED)

        val lp = window.attributes
        lp.screenBrightness = 0.01f // Minimum brightness
        window.attributes = lp

        // Fullscreen immersive pure black
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            or View.SYSTEM_UI_FLAG_FULLSCREEN
            or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        )

        val root = FrameLayout(this).apply {
            setBackgroundColor(Color.BLACK)
        }

        val hintText = TextView(this).apply {
            text = "AselCam Yayında\n(Çıkmak için ekrana çift dokunun)"
            setTextColor(Color.argb(40, 255, 255, 255)) // Ultra dim 15% opacity text
            textSize = 14f
            textAlignment = View.TEXT_ALIGNMENT_CENTER
            val params = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.CENTER
            }
            layoutParams = params
        }
        root.addView(hintText)
        setContentView(root)

        gestureDetector = GestureDetector(this, object : GestureDetector.SimpleOnGestureListener() {
            override fun onDoubleTap(e: MotionEvent): Boolean {
                finish()
                return true
            }
        })

        val filter = IntentFilter(ACTION_DISMISS)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(dismissReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(dismissReceiver, filter)
        }
    }

    override fun onTouchEvent(event: MotionEvent?): Boolean {
        if (event != null && gestureDetector.onTouchEvent(event)) {
            return true
        }
        return super.onTouchEvent(event)
    }

    override fun onDestroy() {
        try {
            unregisterReceiver(dismissReceiver)
        } catch (e: Exception) {}
        super.onDestroy()
    }

    companion object {
        const val ACTION_DISMISS = "com.aselens.aselcam.DISMISS_BLACKOUT"
    }
}
