//
//  AdMobManager.swift
//  AselCam iOS
//
//  Google AdMob Integration for iOS:
//  - Banner Ads (UIViewRepresentable for SwiftUI)
//  - Interstitial Ads (Triggered on 'Start Stream' button with preload & cooldown)
//

import SwiftUI
import UIKit
#if canImport(GoogleMobileAds)
import GoogleMobileAds
#endif

public final class AdMobManager: NSObject {
    public static let shared = AdMobManager()
    
    // Live AdMob Identifiers
    public static let liveBannerAdUnitId = "ca-app-pub-3011996181892691/3349588537"
    public static let liveInterstitialAdUnitId = "ca-app-pub-3011996181892691/5905178693"
    
    // Official Google Test Ad Unit Identifiers (for Debug / Simulator)
    public static let testBannerAdUnitId = "ca-app-pub-3940256099942544/2934735716"
    public static let testInterstitialAdUnitId = "ca-app-pub-3940256099942544/4411468910"
    
    #if canImport(GoogleMobileAds)
    private var interstitialAd: GADInterstitialAd?
    #endif
    
    private var isAdLoading = false
    private var lastAdShowTime: Date = .distantPast
    private let minCooldownSeconds: TimeInterval = 45.0 // 45 seconds cooldown
    
    private override init() {
        super.init()
    }
    
    public func initialize() {
        #if canImport(GoogleMobileAds)
        GADMobileAds.sharedInstance().start { [weak self] status in
            print("[AdMob iOS] SDK initialized successfully.")
            self?.loadInterstitial()
        }
        #else
        print("[AdMob iOS] GoogleMobileAds framework not linked. Running in ad-free fallback mode.")
        #endif
    }
    
    private var currentBannerId: String {
        #if DEBUG
        return AdMobManager.testBannerAdUnitId
        #else
        return AdMobManager.liveBannerAdUnitId
        #endif
    }
    
    private var currentInterstitialId: String {
        #if DEBUG
        return AdMobManager.testInterstitialAdUnitId
        #else
        return AdMobManager.liveInterstitialAdUnitId
        #endif
    }
    
    public func loadInterstitial() {
        #if canImport(GoogleMobileAds)
        guard interstitialAd == nil, !isAdLoading else { return }
        isAdLoading = true
        
        let request = GADRequest()
        GADInterstitialAd.load(withAdUnitID: currentInterstitialId, request: request) { [weak self] ad, error in
            guard let self = self else { return }
            self.isAdLoading = false
            if let error = error {
                print("[AdMob iOS] Interstitial load failed: \(error.localizedDescription)")
                self.interstitialAd = nil
                return
            }
            self.interstitialAd = ad
            self.interstitialAd?.fullScreenContentDelegate = self
            print("[AdMob iOS] Interstitial ad preloaded successfully.")
        }
        #endif
    }
    
    private var pendingAction: (() -> Void)?
    
    /// Shows the interstitial ad if ready and cooldown has passed.
    /// Runs onActionToRun immediately when dismissed or if no ad is ready.
    public func showInterstitialThen(onActionToRun: @escaping () -> Void) {
        let now = Date()
        let timeSinceLastAd = now.timeIntervalSince(lastAdShowTime)
        
        #if canImport(GoogleMobileAds)
        guard let ad = interstitialAd, timeSinceLastAd >= minCooldownSeconds else {
            print("[AdMob iOS] No cached ad ready or cooldown active (\(Int(timeSinceLastAd))s). Running action immediately.")
            onActionToRun()
            loadInterstitial()
            return
        }
        
        guard let rootVC = topViewController() else {
            onActionToRun()
            return
        }
        
        self.pendingAction = onActionToRun
        ad.present(fromRootViewController: rootVC)
        #else
        onActionToRun()
        #endif
    }
    
    private func topViewController(base: UIViewController? = nil) -> UIViewController? {
        let baseVC = base ?? UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
        
        if let nav = baseVC as? UINavigationController {
            return topViewController(base: nav.visibleViewController)
        }
        if let tab = baseVC as? UITabBarController {
            return topViewController(base: tab.selectedViewController)
        }
        if let presented = baseVC?.presentedViewController {
            return topViewController(base: presented)
        }
        return baseVC
    }
}

#if canImport(GoogleMobileAds)
extension AdMobManager: GADFullScreenContentDelegate {
    public func adDidDismissFullScreenContent(_ ad: GADFullScreenPresentingAd) {
        print("[AdMob iOS] Interstitial ad dismissed. Starting stream...")
        interstitialAd = nil
        lastAdShowTime = Date()
        let action = pendingAction
        pendingAction = nil
        action?()
        loadInterstitial()
    }
    
    public func ad(_ ad: GADFullScreenPresentingAd, didFailToPresentFullScreenContentWithError error: Error) {
        print("[AdMob iOS] Interstitial failed to present: \(error.localizedDescription)")
        interstitialAd = nil
        let action = pendingAction
        pendingAction = nil
        action?()
        loadInterstitial()
    }
}
#endif

// MARK: - SwiftUI Banner View
public struct AdmobBannerView: View {
    public init() {}
    
    public var body: some View {
        #if canImport(GoogleMobileAds)
        AdmobBannerRepresentable()
            .frame(width: 320, height: 50)
        #else
        EmptyView()
        #endif
    }
}

#if canImport(GoogleMobileAds)
struct AdmobBannerRepresentable: UIViewRepresentable {
    func makeUIView(context: Context) -> GADBannerView {
        let banner = GADBannerView(adSize: GADAdSizeBanner)
        #if DEBUG
        banner.adUnitID = AdMobManager.testBannerAdUnitId
        #else
        banner.adUnitID = AdMobManager.liveBannerAdUnitId
        #endif
        
        banner.rootViewController = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
        
        banner.load(GADRequest())
        return banner
    }
    
    func updateUIView(_ uiView: GADBannerView, context: Context) {}
}
#endif
