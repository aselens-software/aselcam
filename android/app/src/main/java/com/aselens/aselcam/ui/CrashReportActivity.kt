package com.aselens.aselcam.ui

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.aselens.aselcam.BuildConfig
import com.aselens.aselcam.MainActivity

class CrashReportActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val errorMessage = intent.getStringExtra(EXTRA_ERROR_MESSAGE) ?: "Bilinmeyen Hata"
        val stackTrace = intent.getStringExtra(EXTRA_STACK_TRACE) ?: "Yığın izi bulunamadı."

        val fullReport = buildString {
            appendLine("=== AselCam Hata Raporu ===")
            appendLine("Sürüm: v${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
            appendLine("Cihaz: ${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE}, API ${Build.VERSION.SDK_INT})")
            appendLine("Zaman: ${java.util.Date()}")
            appendLine()
            appendLine("Hata Mesajı:")
            appendLine(errorMessage)
            appendLine()
            appendLine("Yığın İzi (Stack Trace):")
            appendLine(stackTrace)
        }

        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0F131D"))
            setPadding(dpToPx(16), dpToPx(32), dpToPx(16), dpToPx(16))
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        val titleView = TextView(this).apply {
            text = "AselCam Tanılama & Hata"
            setTextColor(Color.parseColor("#EF4444"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, dpToPx(4))
        }
        rootLayout.addView(titleView)

        val subtitleView = TextView(this).apply {
            text = "Uygulama beklenmeyen bir durumla karşılaştı. Bu ekran çökmenin detaylarını görmenizi sağlar."
            setTextColor(Color.parseColor("#8C909F"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setPadding(0, 0, 0, dpToPx(12))
        }
        rootLayout.addView(subtitleView)

        val versionView = TextView(this).apply {
            text = "Sürüm: v${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE}) • ${Build.MANUFACTURER} ${Build.MODEL}"
            setTextColor(Color.parseColor("#4EDEA3"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            setPadding(0, 0, 0, dpToPx(12))
        }
        rootLayout.addView(versionView)

        val scrollView = ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                0,
                1.0f
            )
            setBackgroundColor(Color.parseColor("#0A0E18"))
            setPadding(dpToPx(12), dpToPx(12), dpToPx(12), dpToPx(12))
        }

        val logView = TextView(this).apply {
            text = fullReport
            setTextColor(Color.parseColor("#DFE2F1"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
            typeface = Typeface.MONOSPACE
            setTextIsSelectable(true)
        }
        scrollView.addView(logView)
        rootLayout.addView(scrollView)

        val buttonLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dpToPx(16), 0, 0)
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }

        val copyButton = Button(this).apply {
            text = "Raporu Kopyala"
            setTextColor(Color.parseColor("#00311F"))
            setBackgroundColor(Color.parseColor("#4EDEA3"))
            layoutParams = LinearLayout.LayoutParams(0, dpToPx(48), 1.0f).apply {
                marginEnd = dpToPx(8)
            }
            setOnClickListener {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("AselCam Crash Log", fullReport)
                clipboard.setPrimaryClip(clip)
                Toast.makeText(this@CrashReportActivity, "Rapor panoya kopyalandı!", Toast.LENGTH_SHORT).show()
            }
        }
        buttonLayout.addView(copyButton)

        val restartButton = Button(this).apply {
            text = "Yeniden Başlat"
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#4D8EFF"))
            layoutParams = LinearLayout.LayoutParams(0, dpToPx(48), 1.0f).apply {
                marginStart = dpToPx(8)
            }
            setOnClickListener {
                val restartIntent = Intent(this@CrashReportActivity, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                startActivity(restartIntent)
                finish()
            }
        }
        buttonLayout.addView(restartButton)

        rootLayout.addView(buttonLayout)
        setContentView(rootLayout)
    }

    private fun dpToPx(dp: Int): Int {
        return (dp * resources.displayMetrics.density).toInt()
    }

    companion object {
        const val EXTRA_ERROR_MESSAGE = "extra_error_message"
        const val EXTRA_STACK_TRACE = "extra_stack_trace"
    }
}
