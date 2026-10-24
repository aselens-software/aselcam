# ====================================================================
# AselCam ProGuard & R8 Optimization Rules
# Ensures high DEX obfuscation while preserving 100% runtime stability
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

# Keep All AselCam Application Classes and Members
# Prevents stripping/mangling of MainActivity, Services, UI, i18n, encoders, etc.
-keep class com.aselens.aselcam.** { *; }
-keepclassmembers class com.aselens.aselcam.** { *; }

# Keep AndroidX Lifecycle, Fragment, and Activity internals (required for runtime lifecycle injection)
-keep class androidx.lifecycle.** { *; }
-keepclassmembers class androidx.lifecycle.** { *; }
-keep class androidx.activity.** { *; }
-keepclassmembers class androidx.activity.** { *; }
-keep class androidx.fragment.app.** { *; }
-keepclassmembers class androidx.fragment.app.** { *; }

# Jetpack Compose
-keep class androidx.compose.** { *; }
-keepclassmembers class * {
    @androidx.compose.runtime.Composable *;
}
-dontwarn androidx.compose.**
-dontwarn kotlinx.coroutines.**
-dontwarn org.jetbrains.annotations.**

# Google Mobile Ads (AdMob)
-keep public class com.google.android.gms.ads.** {
    public *;
}
-keep public class com.google.ads.** {
    public *;
}
-keep class com.google.android.gms.internal.ads.** { *; }
-dontwarn com.google.android.gms.**
