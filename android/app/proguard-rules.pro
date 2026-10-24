# Proguard & R8 Optimization Rules for AselCam
# Optimizes DEX bytecode, obfuscates class/method names, and preserves necessary runtime members.

# Keep Kotlin Coroutines internal volatile fields
-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}

# Keep Android Service lifecycles and binder methods
-keepclassmembers class * extends android.app.Service {
    public <methods>;
}

# Google Play Services & AdMob SDK rules
-keep public class com.google.android.gms.ads.** { *; }
-keep public class com.google.ads.** { *; }
-dontwarn com.google.android.gms.ads.**

# Keep AselCam internal streaming components accessible to Service & Activity
-keep class com.aselens.aselcam.service.** { *; }
-keep class com.aselens.aselcam.network.** { *; }
-keep class com.aselens.aselcam.camera.** { *; }
-keep class com.aselens.aselcam.encoder.** { *; }
-keep class com.aselens.aselcam.ads.** { *; }

# Keep data models and JSON serialization helpers intact
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Allow R8 to aggressively obfuscate and optimize UI composables and internal logic
