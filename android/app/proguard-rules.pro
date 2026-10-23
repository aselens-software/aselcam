# ====================================================================
# AselCam ProGuard & R8 Optimization Rules
# Ensures high DEX obfuscation while preserving runtime stability
# ====================================================================

# Attributes preservation for Compose, Reflection, and Stacktraces
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod,SourceFile,LineNumberTable

# Standard Android & JNI rules
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

-keepclassmembers class * {
    @androidx.annotation.Keep *;
}

-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep Application Entry Points & Activities
-keep class com.aselens.aselcam.MainActivity { *; }
-keep class com.aselens.aselcam.ui.BlackoutActivity { *; }

# Keep Foreground Service and Binder for IPC / ServiceConnection
-keep class com.aselens.aselcam.service.CameraStreamService { *; }
-keep class com.aselens.aselcam.service.CameraStreamService$LocalBinder { *; }

# Keep Google Mobile Ads (AdMob)
-keep public class com.google.android.gms.ads.** {
    public *;
}
-keep public class com.google.ads.** {
    public *;
}
-keep class com.google.android.gms.internal.ads.** { *; }
-dontwarn com.google.android.gms.ads.**

# Keep AdMob Manager
-keep class com.aselens.aselcam.ads.AdMobManager { *; }

# Keep Camera and Encoding Pipelines
-keep class com.aselens.aselcam.camera.** { *; }
-keep class com.aselens.aselcam.encoder.** { *; }
-keep class com.aselens.aselcam.network.** { *; }
-keep class com.aselens.aselcam.screen.** { *; }

# Jetpack Compose and Coroutines
-dontwarn androidx.compose.**
-dontwarn kotlinx.coroutines.**
-dontwarn org.jetbrains.annotations.**

# Repackage non-kept classes for aggressive obfuscation
-repackageclasses ''
-allowaccessmodification
