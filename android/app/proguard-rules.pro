# ====================================================================
# AselCam Production ProGuard & R8 Configuration
# Prevents crashes by preserving Jetpack Compose, Kotlin runtime, Coroutines,
# and all AselCam entry points while safely obfuscating libraries for Google Play.
# ====================================================================

# Disable aggressive bytecode inlining/rewriting to guarantee Compose runtime stability
-dontoptimize

# Keep Kotlin runtime metadata and annotations (CRITICAL for Jetpack Compose)
-keepattributes RuntimeVisible*Annotations,RuntimeVisibleParameterAnnotations,RuntimeVisibleTypeAnnotations,AnnotationDefault,Metadata,InnerClasses,EnclosingMethod,SourceFile,LineNumberTable

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

-keepclassmembers class * implements android.os.Parcelable {
    public static final ** CREATOR;
}

# Keep Kotlin Standard Library & Coroutines
-keep class kotlin.** { *; }
-keepclassmembers class kotlin.** { *; }
-keep class kotlin.jvm.functions.** { *; }
-keep class kotlin.jvm.internal.** { *; }
-keep class kotlin.coroutines.** { *; }
-keep class kotlinx.coroutines.** { *; }
-keepclassmembers class kotlinx.coroutines.** { *; }

# Keep AndroidX Lifecycle, Fragment, Activity, and Startup
-keep class androidx.lifecycle.** { *; }
-keepclassmembers class androidx.lifecycle.** { *; }
-keep class androidx.activity.** { *; }
-keepclassmembers class androidx.activity.** { *; }
-keep class androidx.fragment.app.** { *; }
-keepclassmembers class androidx.fragment.app.** { *; }
-keep class androidx.startup.** { *; }
-keep class androidx.emoji2.** { *; }
-keep class androidx.profileinstaller.** { *; }

# Jetpack Compose Essential Rules
-keep class androidx.compose.runtime.** { *; }
-keepclassmembers class androidx.compose.runtime.** { *; }
-keep class androidx.compose.ui.** { *; }
-keepclassmembers class androidx.compose.ui.** { *; }
-keep class androidx.compose.foundation.** { *; }
-keep class androidx.compose.material3.** { *; }
-keep class androidx.compose.animation.** { *; }
-keep class androidx.compose.runtime.State { *; }
-keep class androidx.compose.runtime.MutableState { *; }
-keep class androidx.compose.runtime.snapshots.** { *; }
-keep class androidx.compose.ui.node.** { *; }
-keepclassmembers class * {
    @androidx.compose.runtime.Composable *;
}

# Keep ALL AselCam Application Classes, Composables, Singletons, and Top-level facades
-keep class com.aselens.aselcam.** { *; }
-keepclassmembers class com.aselens.aselcam.** { *; }

# Google Mobile Ads (AdMob)
-keep class com.google.android.gms.ads.** { *; }
-keepclassmembers class com.google.android.gms.ads.** { *; }

# Suppress harmless warnings for non-critical classes
-dontwarn com.google.android.gms.**
-dontwarn androidx.compose.**
-dontwarn kotlinx.coroutines.**
-dontwarn org.jetbrains.annotations.**
