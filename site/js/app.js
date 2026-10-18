/**
 * AselCam Apple-Design Client Application
 * - Real Photographic Studio Viewfinder Engine
 * - Interactive Webcam vs AselCam Comparison
 * - Apple Segmented Control Downloads (3 Desktop + 2 Mobile)
 * - 8-Language Dynamic Localization & Smart OS Detection
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. LANGUAGE ENGINE
  const langSelector = document.getElementById("lang-select");
  const storedLang = localStorage.getItem("aselcam_lang");
  const systemLang = (navigator.language || "en").substring(0, 2).toLowerCase();
  
  let currentLang = storedLang || (I18N_DATA[systemLang] ? systemLang : "tr");
  
  function applyLanguage(lang) {
    if (!I18N_DATA[lang]) lang = "tr";
    currentLang = lang;
    localStorage.setItem("aselcam_lang", lang);
    
    // Set RTL / LTR
    const isRtl = lang === "ar";
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = lang;

    // Retranslate all data-i18n elements
    const dict = I18N_DATA[lang];
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        // preserve line breaks if in titles
        if (dict[key].includes("\n")) {
          el.innerHTML = dict[key].replace(/\n/g, "<br>");
        } else {
          el.textContent = dict[key];
        }
      }
    });

    // Update detected hero download button label
    updateHeroCtaText();

    // Sync select dropdown
    if (langSelector) {
      langSelector.value = lang;
    }
  }

  if (langSelector) {
    langSelector.addEventListener("change", (e) => {
      applyLanguage(e.target.value);
    });
  }

  // 2. PLATFORM DETECTION & SMART DOWNLOAD CTA
  const detectedOsInfo = detectOS();
  const heroCtaBtn = document.getElementById("hero-cta-btn");
  const heroCtaSub = document.getElementById("hero-cta-sub");

  function detectOS() {
    const ua = navigator.userAgent || "";
    if (/Macintosh|Mac OS X/i.test(ua)) {
      return {
        name: "macOS",
        type: "desktop",
        file: "releases/macos/AselCam-v1.4.7-macOS.zip",
        sub: "Apple Silicon & Intel • 1.4 MB",
        icon: "🍎"
      };
    } else if (/Windows/i.test(ua)) {
      return {
        name: "Windows",
        type: "desktop",
        file: "releases/windows/AselCam-v1.4.7-Windows-x64.zip",
        sub: "Windows 10 / 11 (64-bit) • 98 MB",
        icon: "🪟"
      };
    } else if (/Android/i.test(ua)) {
      return {
        name: "Android",
        type: "mobile",
        file: "releases/android/AselCam-v1.4.7-Android.apk",
        sub: "Android 8.0 — 15+ • 13 MB",
        icon: "🤖"
      };
    } else if (/iPhone|iPad|iPod/i.test(ua)) {
      return {
        name: "iOS",
        type: "mobile",
        file: "releases/ios/AselCam-v1.4.7-iOS.ipa",
        sub: "iOS 15.0+ Sideload • 263 KB",
        icon: "📱"
      };
    } else if (/Linux/i.test(ua)) {
      return {
        name: "Linux",
        type: "desktop",
        file: "#downloads",
        sub: "Arch, Ubuntu, Fedora, Debian",
        icon: "🐧"
      };
    }
    return {
      name: "Desktop",
      type: "desktop",
      file: "#downloads",
      sub: "macOS, Windows, Linux",
      icon: "⚡"
    };
  }

  function updateHeroCtaText() {
    if (!heroCtaBtn) return;
    const dict = I18N_DATA[currentLang] || I18N_DATA.en;
    const prefix = dict.hero_cta_detect || "Download for ";
    heroCtaBtn.innerHTML = `<span class="os-icon">${detectedOsInfo.icon}</span> ${prefix}${detectedOsInfo.name}`;
    heroCtaBtn.setAttribute("href", detectedOsInfo.file);
    if (heroCtaSub) {
      heroCtaSub.textContent = detectedOsInfo.sub;
    }
  }

  // 3. SEGMENTED DOWNLOADS CONTROLLER (DESKTOP VS MOBILE)
  const tabDesktop = document.getElementById("tab-dl-desktop");
  const tabMobile = document.getElementById("tab-dl-mobile");
  const panelDesktop = document.getElementById("dl-panel-desktop");
  const panelMobile = document.getElementById("dl-panel-mobile");

  function setDownloadSegment(isDesktop) {
    if (tabDesktop && tabMobile && panelDesktop && panelMobile) {
      tabDesktop.classList.toggle("active", isDesktop);
      tabMobile.classList.toggle("active", !isDesktop);
      tabDesktop.setAttribute("aria-selected", isDesktop ? "true" : "false");
      tabMobile.setAttribute("aria-selected", !isDesktop ? "true" : "false");

      panelDesktop.style.display = isDesktop ? "grid" : "none";
      panelMobile.style.display = !isDesktop ? "grid" : "none";
    }
  }

  if (tabDesktop) tabDesktop.addEventListener("click", () => setDownloadSegment(true));
  if (tabMobile) tabMobile.addEventListener("click", () => setDownloadSegment(false));

  // Initialize downloads tab based on detected visitor platform
  setDownloadSegment(detectedOsInfo.type !== "mobile");

  // 4. REAL PHOTOGRAPHIC STUDIO VIEWFINDER
  const simPhoto = document.getElementById("sim-photo-subject");
  const simTempSlider = document.getElementById("sim-temp");
  const simTintSlider = document.getElementById("sim-tint");
  const simSharpSlider = document.getElementById("sim-sharp");
  const simValTemp = document.getElementById("sim-val-temp");
  const simValTint = document.getElementById("sim-val-tint");
  const simValSharp = document.getElementById("sim-val-sharp");
  const simBokehToggle = document.getElementById("sim-bokeh-toggle");
  const simBlackoutToggle = document.getElementById("sim-blackout-toggle");
  const simResetBtn = document.getElementById("sim-reset-btn");
  const simBlackoutOverlay = document.getElementById("sim-blackout-overlay");

  const simStatFps = document.getElementById("sim-stat-fps");
  const simStatBitrate = document.getElementById("sim-stat-bitrate");
  const simStatPing = document.getElementById("sim-stat-ping");
  const simModeUsb = document.getElementById("sim-mode-usb");
  const simModeWifi = document.getElementById("sim-mode-wifi");

  let activeProfile = "natural";
  let isUsbMode = true;

  function updateSimPhotoFilters() {
    const temp = parseInt(simTempSlider?.value || 0, 10);
    const tint = parseInt(simTintSlider?.value || 0, 10);
    const sharp = parseInt(simSharpSlider?.value || 0, 10);
    const bokeh = simBokehToggle?.classList.contains("active");

    const dict = I18N_DATA[currentLang] || I18N_DATA.en;

    // Numeric badge updates
    if (simValTemp) simValTemp.textContent = temp === 0 ? dict.sim_preset_natural : (temp > 0 ? `+${temp}K` : `${temp}K`);
    if (simValTint) simValTint.textContent = tint === 0 ? dict.sim_preset_natural : (tint > 0 ? `+${tint}` : `${tint}`);
    if (simValSharp) simValSharp.textContent = sharp === 0 ? "Off" : `${sharp}%`;

    // Photographic color calculations
    let sepia = 0;
    let hueRotate = 0;
    let saturate = 1;
    let contrast = 1;
    let brightness = 1;

    // Kelvin temperature shift
    if (temp > 0) {
      sepia = temp * 0.35;
      saturate += temp * 0.004;
      brightness += temp * 0.001;
    } else if (temp < 0) {
      hueRotate = temp * 0.25;
      saturate += Math.abs(temp) * 0.002;
    }

    // Tint shift
    if (tint !== 0) {
      hueRotate += tint * 0.35;
    }

    // Preset LUT profiles
    if (activeProfile === "cinema") {
      contrast = 1.18;
      saturate = 1.25;
      sepia += 10;
    } else if (activeProfile === "vivid") {
      saturate = 1.45;
      contrast = 1.1;
    } else if (activeProfile === "bw") {
      saturate = 0;
      contrast = 1.28;
    } else if (activeProfile === "night") {
      brightness = 1.15;
      contrast = 0.95;
      sepia += 5;
    } else if (activeProfile === "portrait") {
      contrast = 1.06;
      saturate = 1.12;
      sepia += 4;
    }

    // Sharpness effect via high-frequency contrast
    if (sharp > 0) {
      contrast += (sharp / 100) * 0.22;
    }

    if (simPhoto) {
      simPhoto.style.filter = `sepia(${sepia}%) hue-rotate(${hueRotate}deg) saturate(${saturate}) contrast(${contrast}) brightness(${brightness})`;
      simPhoto.style.transform = bokeh ? `scale(1.04)` : `scale(1)`;
      simPhoto.style.transition = "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), filter 0.2s ease";
    }
  }

  // Preset Chips
  document.querySelectorAll(".chip-preset").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-preset").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeProfile = chip.getAttribute("data-preset");

      if (activeProfile === "cinema") {
        if (simTempSlider) simTempSlider.value = 16;
        if (simTintSlider) simTintSlider.value = -6;
        if (simSharpSlider) simSharpSlider.value = 45;
      } else if (activeProfile === "vivid") {
        if (simTempSlider) simTempSlider.value = 8;
        if (simTintSlider) simTintSlider.value = 4;
        if (simSharpSlider) simSharpSlider.value = 60;
      } else if (activeProfile === "bw") {
        if (simTempSlider) simTempSlider.value = 0;
        if (simTintSlider) simTintSlider.value = 0;
        if (simSharpSlider) simSharpSlider.value = 50;
      } else if (activeProfile === "portrait") {
        if (simTempSlider) simTempSlider.value = 12;
        if (simTintSlider) simTintSlider.value = 2;
        if (simSharpSlider) simSharpSlider.value = 35;
        if (simBokehToggle && !simBokehToggle.classList.contains("active")) {
          simBokehToggle.classList.add("active");
        }
      } else if (activeProfile === "night") {
        if (simTempSlider) simTempSlider.value = -12;
        if (simTintSlider) simTintSlider.value = -6;
        if (simSharpSlider) simSharpSlider.value = 20;
      } else {
        // Natural
        if (simTempSlider) simTempSlider.value = 0;
        if (simTintSlider) simTintSlider.value = 0;
        if (simSharpSlider) simSharpSlider.value = 0;
      }
      updateSimPhotoFilters();
    });
  });

  if (simTempSlider) simTempSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimPhotoFilters(); });
  if (simTintSlider) simTintSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimPhotoFilters(); });
  if (simSharpSlider) simSharpSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimPhotoFilters(); });

  if (simBokehToggle) {
    simBokehToggle.addEventListener("click", () => {
      simBokehToggle.classList.toggle("active");
      updateSimPhotoFilters();
    });
  }

  if (simBlackoutToggle) {
    simBlackoutToggle.addEventListener("click", () => {
      simBlackoutToggle.classList.toggle("active");
      const isBlackout = simBlackoutToggle.classList.contains("active");
      if (simBlackoutOverlay) {
        simBlackoutOverlay.style.opacity = isBlackout ? "0.96" : "0";
        simBlackoutOverlay.style.pointerEvents = isBlackout ? "all" : "none";
      }
    });
  }

  if (simResetBtn) {
    simResetBtn.addEventListener("click", () => {
      if (simTempSlider) simTempSlider.value = 0;
      if (simTintSlider) simTintSlider.value = 0;
      if (simSharpSlider) simSharpSlider.value = 0;
      if (simBokehToggle) simBokehToggle.classList.remove("active");
      if (simBlackoutToggle) simBlackoutToggle.classList.remove("active");
      if (simBlackoutOverlay) simBlackoutOverlay.style.opacity = "0";
      document.querySelectorAll(".chip-preset").forEach(c => c.classList.remove("active"));
      const naturalChip = document.querySelector('.chip-preset[data-preset="natural"]');
      if (naturalChip) naturalChip.classList.add("active");
      activeProfile = "natural";
      updateSimPhotoFilters();
    });
  }

  // USB vs Wi-Fi Modes
  function setConnMode(usb) {
    isUsbMode = usb;
    if (simModeUsb) simModeUsb.classList.toggle("active", usb);
    if (simModeWifi) simModeWifi.classList.toggle("active", !usb);

    if (usb) {
      if (simStatPing) simStatPing.textContent = "4.2 ms";
      if (simStatBitrate) simStatBitrate.textContent = "28.5 Mbps";
      if (simStatFps) simStatFps.textContent = "60.0 FPS";
    } else {
      if (simStatPing) simStatPing.textContent = "14.2 ms";
      if (simStatBitrate) simStatBitrate.textContent = "18.0 Mbps";
      if (simStatFps) simStatFps.textContent = "59.8 FPS";
    }
  }

  if (simModeUsb) simModeUsb.addEventListener("click", () => setConnMode(true));
  if (simModeWifi) simModeWifi.addEventListener("click", () => setConnMode(false));

  // Telemetry Micro Jitter
  setInterval(() => {
    if (!simStatPing) return;
    if (isUsbMode) {
      const ping = (3.8 + Math.random() * 0.8).toFixed(1);
      const fps = (59.8 + Math.random() * 0.4).toFixed(1);
      simStatPing.textContent = `${ping} ms`;
      simStatFps.textContent = `${fps} FPS`;
    } else {
      const ping = (13.5 + Math.random() * 2.2).toFixed(1);
      const fps = (59.6 + Math.random() * 0.7).toFixed(1);
      simStatPing.textContent = `${ping} ms`;
      simStatFps.textContent = `${fps} FPS`;
    }
  }, 2400);

  // 5. INTERACTIVE WEBCAM VS ASELCAM COMPARISON
  const btnCompareWebcam = document.getElementById("btn-compare-webcam");
  const btnCompareAselcam = document.getElementById("btn-compare-aselcam");
  const comparePhoto = document.getElementById("compare-photo");
  const compareTag = document.getElementById("compare-status-tag");

  function setComparison(isAselcam) {
    if (btnCompareWebcam && btnCompareAselcam && comparePhoto && compareTag) {
      btnCompareWebcam.classList.toggle("active", !isAselcam);
      btnCompareAselcam.classList.toggle("active", isAselcam);

      const dict = I18N_DATA[currentLang] || I18N_DATA.en;

      if (isAselcam) {
        comparePhoto.style.filter = "none";
        compareTag.textContent = dict.compare_aselcam_tag;
        compareTag.className = "compare-badge aselcam";
      } else {
        // Simulate grainy low-light webcam
        comparePhoto.style.filter = "blur(1.6px) contrast(0.82) saturate(0.7) brightness(0.9) grayscale(0.2)";
        compareTag.textContent = dict.compare_webcam_tag;
        compareTag.className = "compare-badge webcam";
      }
    }
  }

  if (btnCompareWebcam) btnCompareWebcam.addEventListener("click", () => setComparison(false));
  if (btnCompareAselcam) btnCompareAselcam.addEventListener("click", () => setComparison(true));

  // 6. SHA256 COPY TO CLIPBOARD
  document.querySelectorAll(".btn-copy-checksum").forEach(btn => {
    btn.addEventListener("click", async () => {
      const checksum = btn.getAttribute("data-checksum");
      if (!checksum) return;
      try {
        await navigator.clipboard.writeText(checksum);
        const originalText = btn.innerHTML;
        btn.innerHTML = `<span class="check-icon">✓</span> <span data-i18n="dl_copied">${(I18N_DATA[currentLang] || I18N_DATA.en).dl_copied}</span>`;
        btn.classList.add("copied");
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove("copied");
        }, 2000);
      } catch (err) {
        console.error("Copy failed", err);
      }
    });
  });

  // 7. STICKY NAV BLUR ON SCROLL
  const navHeader = document.querySelector(".nav-header");
  window.addEventListener("scroll", () => {
    if (window.scrollY > 20) {
      navHeader?.classList.add("scrolled");
    } else {
      navHeader?.classList.remove("scrolled");
    }
  }, { passive: true });

  // Initialize
  applyLanguage(currentLang);
  updateSimPhotoFilters();
  setConnMode(true);
  setComparison(true);
});
