# ====================================================================
# AselCam Production ProGuard & R8 Optimization Rules
# Preserves Jetpack Compose, Kotlin runtime, Coroutines, and App classes
# ====================================================================
# Disable aggressive bytecode optimization to ensure Compose, Coroutines, and Lifecycle runtime stability
# Full shrinking and name obfuscation remain 100% active for Google Play compliance
-dontoptimize

# Keep Kotlin metadata and annotations (CRITICAL for Jetpack Compose runtime & reflection)
-keepattributes RuntimeVisible*Annotations,RuntimeVisibleParameterAnnotations,RuntimeVisibleTypeAnnotations,AnnotationDefault,Metadata,Signature,InnerClasses,EnclosingMethod,SourceFile,LineNumberTable

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

# Keep All AselCam Application Classes and Members
-keep class com.aselens.aselcam.** { *; }
-keepclassmembers class com.aselens.aselcam.** { *; }

# Keep AndroidX Lifecycle, Fragment, Activity, and Compose
-keep class androidx.lifecycle.** { *; }
-keepclassmembers class androidx.lifecycle.** { *; }
-keep class androidx.activity.** { *; }
-keepclassmembers class androidx.activity.** { *; }
-keep class androidx.fragment.app.** { *; }
-keepclassmembers class androidx.fragment.app.** { *; }

# Jetpack Compose Essential Rules
-keep class androidx.compose.** { *; }
-keepclassmembers class androidx.compose.** { *; }
-keep class androidx.compose.runtime.State { *; }
-keep class androidx.compose.runtime.MutableState { *; }
-keep class androidx.compose.runtime.snapshots.** { *; }
-keep class androidx.compose.ui.node.** { *; }
-keepclassmembers class * {
    @androidx.compose.runtime.Composable *;
}
-dontwarn androidx.compose.**
-dontwarn kotlinx.coroutines.**
-dontwarn org.jetbrains.annotations.**

# Google Mobile Ads (AdMob)
-keep class com.google.android.gms.ads.** { *; }
-keepclassmembers class com.google.android.gms.ads.** { *; }
-dontwarn com.google.android.gms.**
