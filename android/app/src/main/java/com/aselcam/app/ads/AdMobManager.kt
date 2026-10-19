package com.aselcam.app.ads

import android.app.Activity
import android.content.Context
import android.util.Log
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.aselcam.app.BuildConfig
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
    // AdMob panelinizden 'Geçiş Reklamı (Interstitial)' oluşturduğunuzda aldığınız ID'yi buraya yazabilirsiniz.
    var liveInterstitialAdUnitId = "ca-app-pub-3011996181892691/XXXXXXXXXX"

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
     * AdMob SDK'sını arka planda asenkron olarak ilklendirir.
     */
    fun initialize(context: Context) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                MobileAds.initialize(context) { status ->
                    Log.d(TAG, "AdMob SDK Initialized successfully")
                }
                // Uygulama açılışında ilk geçiş reklamını arka planda önceden yükle (Preload)
                loadInterstitial(context.applicationContext)
            } catch (e: Exception) {
                Log.e(TAG, "AdMob init error", e)
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
     * Arka planda geçiş reklamını önbelleğe alır (Preload).
     * Böylece kullanıcı 'Yayını Başlat' butonuna bastığında reklam sıfır gecikmeyle açılır.
     */
    fun loadInterstitial(context: Context) {
        if (interstitialAd != null || isAdLoading) return

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
    }

    /**
     * "Yayını Başlat" butonuna tıklandığında çağrılır.
     * Reklam varsa gösterir; reklam kapatıldığında veya yoksa onActionToRun() ile yayını hemen başlatır.
     * Kullanıcı asla engellenmez veya kilitlenmez!
     */
    fun showInterstitialThen(activity: Activity, onActionToRun: () -> Unit) {
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
                // Reklam kapatıldı -> Asıl işlemi (yayını başlatmayı) çalıştır
                onActionToRun()
                // Bir sonraki başlatma için arka planda yeni reklam yükle
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
    }

    /**
     * Jetpack Compose Banner Bileşeni
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
                AdView(ctx).apply {
                    setAdSize(AdSize.BANNER)
                    adUnitId = getBannerAdUnitId()
                    loadAd(AdRequest.Builder().build())
                }
            }
        )
    }
}
