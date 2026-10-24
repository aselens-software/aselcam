package com.aselens.aselcam.ui

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.aselens.aselcam.MainActivity

class CrashReportActivity : Activity() {

    companion object {
        const val EXTRA_ERROR_MESSAGE = "extra_error_message"
        const val EXTRA_STACK_TRACE = "extra_stack_trace"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val errorMessage = intent?.getStringExtra(EXTRA_ERROR_MESSAGE) ?: "Bilinmeyen bir hata oluştu"
        val stackTrace = intent?.getStringExtra(EXTRA_STACK_TRACE) ?: ""

        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0F172A"))
            setPadding(40, 60, 40, 40)
        }

        val titleView = TextView(this).apply {
            text = "AselCam Bir Sorunla Karşılaştı"
            setTextColor(Color.parseColor("#EF4444"))
            textSize = 20f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 30)
        }
        rootLayout.addView(titleView)

        val descView = TextView(this).apply {
            text = "Uygulama bir hata nedeniyle durduruldu. Hata detayı aşağıdadır:"
            setTextColor(Color.parseColor("#94A3B8"))
            textSize = 14f
            setPadding(0, 0, 0, 20)
        }
        rootLayout.addView(descView)

        val scrollView = ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1.0f
            )
            setBackgroundColor(Color.parseColor("#1E293B"))
            setPadding(24, 24, 24, 24)
        }

        val errorContent = TextView(this).apply {
            text = "$errorMessage\n\n$stackTrace"
            setTextColor(Color.parseColor("#F1F5F9"))
            textSize = 12f
            typeface = Typeface.MONOSPACE
            setTextIsSelectable(true)
        }
        scrollView.addView(errorContent)
        rootLayout.addView(scrollView)

        val restartButton = Button(this).apply {
            text = "Uygulamayı Yeniden Başlat"
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#3B82F6"))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(0, 30, 0, 0)
            }
            setOnClickListener {
                val launchIntent = Intent(this@CrashReportActivity, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                startActivity(launchIntent)
                finish()
            }
        }
        rootLayout.addView(restartButton)

        setContentView(rootLayout)
    }
}
