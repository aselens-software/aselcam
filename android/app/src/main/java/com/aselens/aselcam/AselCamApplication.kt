package com.aselens.aselcam

import android.app.Application
import android.content.Intent
import android.util.Log
import com.aselens.aselcam.ui.CrashReportActivity
import java.io.File

class AselCamApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e("AselCamCrash", "FATAL CRASH on thread ${thread.name}", throwable)
            try {
                val crashFile = File(filesDir, "crash_log.txt")
                crashFile.writeText("Sürüm: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})\nİş Parçacığı: ${thread.name}\nHata: ${throwable.message}\n\nStack:\n${throwable.stackTraceToString()}")

                val intent = Intent(this, CrashReportActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                    putExtra(CrashReportActivity.EXTRA_ERROR_MESSAGE, throwable.message ?: throwable.javaClass.simpleName)
                    putExtra(CrashReportActivity.EXTRA_STACK_TRACE, throwable.stackTraceToString())
                }
                startActivity(intent)
                android.os.Process.killProcess(android.os.Process.myPid())
                System.exit(10)
            } catch (e: Throwable) {
                defaultHandler?.uncaughtException(thread, throwable)
            }
        }
    }
}
