package com.aselens.aselcam

import android.app.Application
import android.content.Context
import android.os.Environment
import android.util.Log
import java.io.File

class AselCamApplication : Application() {

    override fun attachBaseContext(base: Context?) {
        super.attachBaseContext(base)

        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            val stack = Log.getStackTraceString(throwable)
            Log.e("AselCamFatal", "FATAL CRASH on thread ${thread.name}:", throwable)
            try {
                val dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                File(dir, "aselcam_crash_report.txt").writeText(
                    "=== AselCam Hata Raporu ===\n" +
                    "Sürüm: v${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})\n" +
                    "İş Parçacığı: ${thread.name}\n" +
                    "Hata: ${throwable.localizedMessage}\n\n" +
                    "Yığın İzi:\n$stack"
                )
            } catch (_: Throwable) {}
            try {
                File(filesDir, "last_crash.txt").writeText(stack)
            } catch (_: Throwable) {}

            defaultHandler?.uncaughtException(thread, throwable)
        }
    }
}
