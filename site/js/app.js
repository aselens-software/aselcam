/**
 * AselCam Landing Page Client Application
 * Apple HIG Compliant Interactions & Live Studio Simulation
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
        el.textContent = dict[key];
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
        file: "releases/macos/AselCam-v1.4.7-macOS.zip",
        sub: "Apple Silicon & Intel (1.4 MB)",
        icon: "🍎"
      };
    } else if (/Windows/i.test(ua)) {
      return {
        name: "Windows",
        file: "releases/windows/AselCam-v1.4.7-Windows-x64.zip",
        sub: "Windows 10 / 11 64-bit (98 MB)",
        icon: "🪟"
      };
    } else if (/Android/i.test(ua)) {
      return {
        name: "Android",
        file: "releases/android/AselCam-v1.4.7-Android.apk",
        sub: "Android 8.0 to 15+ (13 MB)",
        icon: "🤖"
      };
    } else if (/iPhone|iPad|iPod/i.test(ua)) {
      return {
        name: "iOS",
        file: "releases/ios/AselCam-v1.4.7-iOS.ipa",
        sub: "iOS 15.0+ Sideload (263 KB)",
        icon: "📱"
      };
    } else if (/Linux/i.test(ua)) {
      return {
        name: "Linux",
        file: "#downloads-linux",
        sub: "Native V4L2 & PipeWire",
        icon: "🐧"
      };
    }
    return {
      name: "Desktop",
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

  // 3. INTERACTIVE STUDIO VIEWFINDER SIMULATOR
  const simCanvas = document.getElementById("sim-canvas");
  const simTempSlider = document.getElementById("sim-temp");
  const simTintSlider = document.getElementById("sim-tint");
  const simSharpSlider = document.getElementById("sim-sharp");
  const simValTemp = document.getElementById("sim-val-temp");
  const simValTint = document.getElementById("sim-val-tint");
  const simValSharp = document.getElementById("sim-val-sharp");
  const simBokehToggle = document.getElementById("sim-bokeh-toggle");
  const simBlackoutToggle = document.getElementById("sim-blackout-toggle");
  const simResetBtn = document.getElementById("sim-reset-btn");
  
  const simStatFps = document.getElementById("sim-stat-fps");
  const simStatBitrate = document.getElementById("sim-stat-bitrate");
  const simStatPing = document.getElementById("sim-stat-ping");
  const simStatLoss = document.getElementById("sim-stat-loss");
  const simModeUsb = document.getElementById("sim-mode-usb");
  const simModeWifi = document.getElementById("sim-mode-wifi");
  const simSubject = document.getElementById("sim-subject");
  const simBackground = document.getElementById("sim-background");
  const simOverlayBlackout = document.getElementById("sim-blackout-overlay");

  let activeProfile = "natural";
  let isUsbMode = true;

  function updateSimFilters() {
    const temp = parseInt(simTempSlider?.value || 0, 10);
    const tint = parseInt(simTintSlider?.value || 0, 10);
    const sharp = parseInt(simSharpSlider?.value || 0, 10);
    const bokeh = simBokehToggle?.classList.contains("active");

    const dict = I18N_DATA[currentLang] || I18N_DATA.en;

    // Badges update
    if (simValTemp) simValTemp.textContent = temp === 0 ? dict.sim_preset_natural : (temp > 0 ? `+${temp}K` : `${temp}K`);
    if (simValTint) simValTint.textContent = tint === 0 ? dict.sim_preset_natural : (tint > 0 ? `+${tint}` : `${tint}`);
    if (simValSharp) simValSharp.textContent = sharp === 0 ? "Off" : `${sharp}%`;

    // Visual Filter calculation on preview elements
    let sepia = 0;
    let hueRotate = 0;
    let saturate = 1;
    let contrast = 1;
    let brightness = 1;

    // Temp shifts warm/cool
    if (temp > 0) {
      sepia = temp * 0.4;
      saturate += temp * 0.005;
      brightness += temp * 0.001;
    } else if (temp < 0) {
      hueRotate = temp * 0.3;
      saturate += Math.abs(temp) * 0.002;
    }

    // Tint shifts magenta/green
    if (tint > 0) {
      hueRotate += tint * 0.4;
    } else if (tint < 0) {
      hueRotate += tint * 0.4;
    }

    // Profile presets adjustments
    if (activeProfile === "cinema") {
      contrast = 1.15;
      saturate = 1.25;
      sepia += 8;
    } else if (activeProfile === "vivid") {
      saturate = 1.45;
      contrast = 1.08;
    } else if (activeProfile === "bw") {
      saturate = 0;
      contrast = 1.25;
    } else if (activeProfile === "night") {
      brightness = 1.12;
      contrast = 0.95;
    } else if (activeProfile === "portrait") {
      contrast = 1.05;
      saturate = 1.1;
    }

    // Sharpness effect via drop-shadow and contrast
    if (sharp > 0) {
      contrast += (sharp / 100) * 0.25;
    }

    const filterString = `sepia(${sepia}%) hue-rotate(${hueRotate}deg) saturate(${saturate}) contrast(${contrast}) brightness(${brightness})`;
    
    if (simSubject) {
      simSubject.style.filter = filterString;
    }

    // Background bokeh blur
    if (simBackground) {
      simBackground.style.filter = bokeh ? `blur(14px) brightness(0.85)` : `blur(0px) brightness(1)`;
      simBackground.style.transform = bokeh ? `scale(1.08)` : `scale(1)`;
      simBackground.style.transition = `filter 0.4s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)`;
    }
  }

  // Preset Chips
  document.querySelectorAll(".chip-preset").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-preset").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeProfile = chip.getAttribute("data-preset");

      if (activeProfile === "cinema") {
        simTempSlider.value = 18;
        simTintSlider.value = -6;
        simSharpSlider.value = 45;
      } else if (activeProfile === "vivid") {
        simTempSlider.value = 8;
        simTintSlider.value = 4;
        simSharpSlider.value = 60;
      } else if (activeProfile === "bw") {
        simTempSlider.value = 0;
        simTintSlider.value = 0;
        simSharpSlider.value = 50;
      } else if (activeProfile === "portrait") {
        simTempSlider.value = 12;
        simTintSlider.value = 2;
        simSharpSlider.value = 30;
        if (simBokehToggle && !simBokehToggle.classList.contains("active")) {
          simBokehToggle.classList.add("active");
        }
      } else if (activeProfile === "night") {
        simTempSlider.value = -15;
        simTintSlider.value = -8;
        simSharpSlider.value = 20;
      } else {
        // Natural
        simTempSlider.value = 0;
        simTintSlider.value = 0;
        simSharpSlider.value = 0;
      }
      updateSimFilters();
    });
  });

  if (simTempSlider) simTempSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimFilters(); });
  if (simTintSlider) simTintSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimFilters(); });
  if (simSharpSlider) simSharpSlider.addEventListener("input", () => { activeProfile = "custom"; updateSimFilters(); });

  if (simBokehToggle) {
    simBokehToggle.addEventListener("click", () => {
      simBokehToggle.classList.toggle("active");
      updateSimFilters();
    });
  }

  if (simBlackoutToggle) {
    simBlackoutToggle.addEventListener("click", () => {
      simBlackoutToggle.classList.toggle("active");
      const isBlackout = simBlackoutToggle.classList.contains("active");
      if (simOverlayBlackout) {
        simOverlayBlackout.style.opacity = isBlackout ? "0.96" : "0";
        simOverlayBlackout.style.pointerEvents = isBlackout ? "all" : "none";
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
      if (simOverlayBlackout) simOverlayBlackout.style.opacity = "0";
      document.querySelectorAll(".chip-preset").forEach(c => c.classList.remove("active"));
      const naturalChip = document.querySelector('.chip-preset[data-preset="natural"]');
      if (naturalChip) naturalChip.classList.add("active");
      activeProfile = "natural";
      updateSimFilters();
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
      if (simStatLoss) simStatLoss.textContent = "0.0%";
      if (simStatFps) simStatFps.textContent = "60.0 FPS";
    } else {
      if (simStatPing) simStatPing.textContent = "14.8 ms";
      if (simStatBitrate) simStatBitrate.textContent = "18.2 Mbps";
      if (simStatLoss) simStatLoss.textContent = "0.0%";
      if (simStatFps) simStatFps.textContent = "59.8 FPS";
    }
  }

  if (simModeUsb) simModeUsb.addEventListener("click", () => setConnMode(true));
  if (simModeWifi) simModeWifi.addEventListener("click", () => setConnMode(false));

  // Telemetry Micro Jitter (Simulating realistic live camera metrics)
  setInterval(() => {
    if (!simStatPing) return;
    if (isUsbMode) {
      const ping = (3.8 + Math.random() * 0.8).toFixed(1);
      const fps = (59.8 + Math.random() * 0.4).toFixed(1);
      simStatPing.textContent = `${ping} ms`;
      simStatFps.textContent = `${fps} FPS`;
    } else {
      const ping = (13.5 + Math.random() * 2.5).toFixed(1);
      const fps = (59.6 + Math.random() * 0.7).toFixed(1);
      simStatPing.textContent = `${ping} ms`;
      simStatFps.textContent = `${fps} FPS`;
    }
  }, 2200);

  // 4. SHA256 COPY TO CLIPBOARD
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

  // 5. STICKY NAV BLUR ON SCROLL
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
  updateSimFilters();
  setConnMode(true);
});
