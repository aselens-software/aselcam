package com.aselens.aselcam.ads

import android.app.Activity
import android.content.Context
import android.util.Log
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.aselens.aselcam.BuildConfig
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.interstitial.InterstitialAd
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

object AdMobManager {
    private const val TAG = "AdMobManager"

    // Canlı AdMob Reklam Birimi Kimlikleri (Ad Unit IDs)
    const val LIVE_BANNER_AD_UNIT_ID = "ca-app-pub-3011996181892691/3349588537"
    
    // Geçiş Reklamı (Interstitial) Birim Kimliği:
    var liveInterstitialAdUnitId = "ca-app-pub-3011996181892691/5905178693"

    // Google Resmi Test Reklam Birimi Kimlikleri (Geliştirme / Debug sırasında hesap güvenliği için zorunlu)
    private const val TEST_BANNER_AD_UNIT_ID = "ca-app-pub-3940256099942544/6300978111"
    private const val TEST_INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712"

    private var interstitialAd: InterstitialAd? = null
    private var isAdLoading = false
    private var lastAdShowTimeMs: Long = 0L

    // İki tam ekran reklam arasındaki minimum bekleme süresi (Cooldown): 45 saniye
    // Kullanıcının ardışık tıklamalarında rahatsız olmasını ve AdMob politika ihlalini önler
    private const val MIN_COOLDOWN_MS = 45_000L

    /**
     * AdMob SDK'sını güvenle Main thread üzerinde ilklendirir.
     */
    fun initialize(context: Context) {
        CoroutineScope(Dispatchers.Main).launch {
            try {
                MobileAds.initialize(context) { status ->
                    Log.d(TAG, "AdMob SDK Initialized successfully")
                }
                // Uygulama açılışında ilk geçiş reklamını önceden yükle (Preload)
                loadInterstitial(context.applicationContext)
            } catch (t: Throwable) {
                Log.e(TAG, "AdMob init error", t)
            }
        }
    }

    private fun getBannerAdUnitId(): String {
        return if (BuildConfig.DEBUG) {
            TEST_BANNER_AD_UNIT_ID
        } else {
            LIVE_BANNER_AD_UNIT_ID
        }
    }

    private fun getInterstitialAdUnitId(): String {
        return if (BuildConfig.DEBUG || liveInterstitialAdUnitId.contains("XXXX")) {
            TEST_INTERSTITIAL_AD_UNIT_ID
        } else {
            liveInterstitialAdUnitId
        }
    }

    /**
     * Geçiş reklamını önbelleğe alır (Preload).
     * Main thread üzerinde güvenli şekilde çağrılır.
     */
    fun loadInterstitial(context: Context) {
        if (interstitialAd != null || isAdLoading) return

        CoroutineScope(Dispatchers.Main).launch {
            try {
                if (interstitialAd != null || isAdLoading) return@launch
                isAdLoading = true
                val adRequest = AdRequest.Builder().build()
                val adUnitId = getInterstitialAdUnitId()

                InterstitialAd.load(
                    context,
                    adUnitId,
                    adRequest,
                    object : InterstitialAdLoadCallback() {
                        override fun onAdLoaded(ad: InterstitialAd) {
                            interstitialAd = ad
                            isAdLoading = false
                            Log.d(TAG, "Interstitial ad loaded and cached successfully.")
                        }

                        override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                            interstitialAd = null
                            isAdLoading = false
                            Log.w(TAG, "Interstitial ad failed to load: ${loadAdError.message}")
                        }
                    }
                )
            } catch (t: Throwable) {
                isAdLoading = false
                Log.e(TAG, "Error initiating InterstitialAd.load", t)
            }
        }
    }

    /**
     * "Yayını Başlat" butonuna tıklandığında çağrılır.
     * Reklam varsa gösterir; reklam kapatıldığında veya yoksa onActionToRun() ile yayını hemen başlatır.
     * Kullanıcı asla engellenmez veya kilitlenmez!
     */
    fun showInterstitialThen(activity: Activity, onActionToRun: () -> Unit) {
        try {
            val now = System.currentTimeMillis()
            val ad = interstitialAd

            // Cooldown süresi dolmamışsa veya reklam henüz yüklenmediyse doğrudan yayını başlat
            if (ad == null || (now - lastAdShowTimeMs < MIN_COOLDOWN_MS)) {
                Log.d(TAG, "No cached ad or cooldown active. Running stream immediately.")
                onActionToRun()
                loadInterstitial(activity.applicationContext)
                return
            }

            ad.fullScreenContentCallback = object : FullScreenContentCallback() {
                override fun onAdDismissedFullScreenContent() {
                    Log.d(TAG, "Interstitial dismissed by user. Starting stream...")
                    interstitialAd = null
                    lastAdShowTimeMs = System.currentTimeMillis()
                    onActionToRun()
                    loadInterstitial(activity.applicationContext)
                }

                override fun onAdFailedToShowFullScreenContent(adError: AdError) {
                    Log.w(TAG, "Interstitial failed to show: ${adError.message}. Starting stream...")
                    interstitialAd = null
                    onActionToRun()
                    loadInterstitial(activity.applicationContext)
                }

                override fun onAdShowedFullScreenContent() {
                    Log.d(TAG, "Interstitial ad is currently displaying.")
                }
            }

            ad.show(activity)
        } catch (t: Throwable) {
            Log.e(TAG, "Failed to show interstitial ad", t)
            interstitialAd = null
            onActionToRun()
        }
    }

    /**
     * Jetpack Compose Banner Bileşeni.
     * Güvenli hata koruması içerir; WebView veya AdView arızasında çökmez.
     */
    @Composable
    fun BannerAdView(
        modifier: Modifier = Modifier
    ) {
        AndroidView(
            modifier = modifier
                .fillMaxWidth()
                .height(50.dp),
            factory = { ctx ->
                try {
                    AdView(ctx).apply {
                        setAdSize(AdSize.BANNER)
                        adUnitId = getBannerAdUnitId()
                        loadAd(AdRequest.Builder().build())
                    }
                } catch (t: Throwable) {
                    Log.e(TAG, "BannerAdView creation error", t)
                    android.view.View(ctx)
                }
            }
        )
    }
}
