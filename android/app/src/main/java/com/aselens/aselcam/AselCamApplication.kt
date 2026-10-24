package com.aselens.aselcam

import android.app.Application
import android.content.Intent
import android.util.Log
import com.aselens.aselcam.ui.CrashReportActivity
import kotlin.system.exitProcess

class AselCamApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            try {
                Log.e("AselCamFatal", "FATAL CRASH on thread ${thread.name}:", throwable)
                val intent = Intent(this, CrashReportActivity::class.java).apply {
                    putExtra(CrashReportActivity.EXTRA_ERROR_MESSAGE, throwable.localizedMessage ?: throwable.toString())
                    putExtra(CrashReportActivity.EXTRA_STACK_TRACE, Log.getStackTraceString(throwable))
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                startActivity(intent)
            } catch (t: Throwable) {
                Log.e("AselCamFatal", "Failed to launch crash reporter", t)
                defaultHandler?.uncaughtException(thread, throwable)
            } finally {
                android.os.Process.killProcess(android.os.Process.myPid())
                exitProcess(10)
            }
        }
    }
}
