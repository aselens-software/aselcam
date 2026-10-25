/**
 * AselCam Apple-Design Client Application
 * - Interactive Before/After Image Comparison Slider (Modern clip-path engine)
 * - Real Video Call Portrait Studio Viewfinder
 * - Apple Segmented Control Downloads (3 Desktop + 2 Mobile)
 * - Direct GitHub Releases Links (No server storage)
 * - Privacy Policy & Terms of Service Modals
 * - 8-Language Dynamic Localization & Smart OS Detection
 * - Full Responsive Mobile Navigation Drawer & Hamburger Menu
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

  // 2. MOBILE MENU HAMBURGER & LIQUID GLASS DRAWER
  const btnMobileMenu = document.getElementById("btn-mobile-menu");
  const mobileNavDrawer = document.getElementById("mobile-nav-drawer");

  function openMobileMenu() {
    if (!btnMobileMenu || !mobileNavDrawer) return;
    btnMobileMenu.classList.add("open");
    mobileNavDrawer.classList.add("open");
    btnMobileMenu.setAttribute("aria-expanded", "true");
    mobileNavDrawer.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeMobileMenu() {
    if (!btnMobileMenu || !mobileNavDrawer) return;
    btnMobileMenu.classList.remove("open");
    mobileNavDrawer.classList.remove("open");
    btnMobileMenu.setAttribute("aria-expanded", "false");
    mobileNavDrawer.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  if (btnMobileMenu) {
    btnMobileMenu.addEventListener("click", () => {
      const isOpen = btnMobileMenu.classList.contains("open");
      if (isOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });
  }

  document.querySelectorAll(".mobile-nav-link, .btn-mobile-dl").forEach(link => {
    link.addEventListener("click", () => {
      closeMobileMenu();
    });
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && btnMobileMenu?.classList.contains("open")) {
      closeMobileMenu();
    }
  });

  // 3. PLATFORM DETECTION & SMART GITHUB DOWNLOAD CTA
  const detectedOsInfo = detectOS();
  const heroCtaBtn = document.getElementById("hero-cta-btn");
  const heroCtaSub = document.getElementById("hero-cta-sub");

  function detectOS() {
    const ua = navigator.userAgent || "";
    if (/Macintosh|Mac OS X/i.test(ua)) {
      return {
        name: "macOS",
        type: "desktop",
        file: "/releases/macos/AselCam-v1.5.2-macOS.zip?v=1.5.2",
        sub: "Apple Silicon & Intel • 1.6 MB",
        icon: "🍎"
      };
    } else if (/Windows/i.test(ua)) {
      return {
        name: "Windows",
        type: "desktop",
        file: "/releases/windows/AselCam-v1.5.2-Windows-Setup.exe?v=1.5.2",
        sub: "Windows 10 / 11 (64-bit) • 149 MB",
        icon: "🪟"
      };
    } else if (/Android/i.test(ua)) {
      return {
        name: "Android",
        type: "mobile",
        file: "/releases/android/AselCam-v1.5.2-Android.apk?v=1.5.2",
        sub: "Android 8.0 — 16 • 8.7 MB",
        icon: "🤖"
      };
    } else if (/iPhone|iPad|iPod/i.test(ua)) {
      return {
        name: "iOS",
        type: "mobile",
        file: "/releases/ios/AselCam-v1.5.2-iOS.ipa?v=1.5.2",
        sub: "iOS 15.0+ Sideload • 263 KB",
        icon: "📱"
      };
    } else if (/Linux/i.test(ua)) {
      return {
        name: "Linux",
        type: "desktop",
        file: "/releases/linux/AselCam-v1.5.2-Linux.zip?v=1.5.2",
        sub: "Universal • 33 MB",
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

  // 4. SEGMENTED DOWNLOADS CONTROLLER (DESKTOP VS MOBILE)
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

  setDownloadSegment(detectedOsInfo.type !== "mobile");

  // 5. INTERACTIVE BEFORE / AFTER IMAGE COMPARISON SLIDER (CLIP-PATH ENGINE)
  const compareContainer = document.getElementById("compare-slider-container");

  let isDraggingCompare = false;

  function updateCompareSlider(clientX) {
    if (!compareContainer) return;
    const rect = compareContainer.getBoundingClientRect();
    let x = clientX - rect.left;
    x = Math.max(0, Math.min(x, rect.width));
    const percent = ((x / rect.width) * 100).toFixed(2);
    compareContainer.style.setProperty("--slider-pos", `${percent}%`);
  }

  if (compareContainer) {
    compareContainer.addEventListener("mousedown", (e) => {
      isDraggingCompare = true;
      updateCompareSlider(e.clientX);
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDraggingCompare) return;
      updateCompareSlider(e.clientX);
    });

    window.addEventListener("mouseup", () => {
      isDraggingCompare = false;
    });

    // Touch support
    compareContainer.addEventListener("touchstart", (e) => {
      isDraggingCompare = true;
      if (e.touches[0]) updateCompareSlider(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener("touchmove", (e) => {
      if (!isDraggingCompare) return;
      if (e.touches[0]) updateCompareSlider(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener("touchend", () => {
      isDraggingCompare = false;
    });

    // Keyboard Accessibility
    compareContainer.setAttribute("tabindex", "0");
    compareContainer.setAttribute("role", "slider");
    compareContainer.setAttribute("aria-label", "Webcam vs AselCam Image Comparison");
    compareContainer.addEventListener("keydown", (e) => {
      const currentVal = parseFloat(compareContainer.style.getPropertyValue("--slider-pos")) || 50;
      if (e.key === "ArrowLeft") {
        const next = Math.max(0, currentVal - 5);
        compareContainer.style.setProperty("--slider-pos", `${next}%`);
      } else if (e.key === "ArrowRight") {
        const next = Math.min(100, currentVal + 5);
        compareContainer.style.setProperty("--slider-pos", `${next}%`);
      }
    });
  }

  // 6. REAL PHOTOGRAPHIC STUDIO VIEWFINDER
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

    let sepia = 0;
    let hue = 0;
    let saturate = 100;
    let contrast = 100;
    let brightness = 100;
    let blur = 0;

    // Temperature (Kelvin shift)
    if (temp > 0) {
      sepia += temp * 0.7;
      saturate += temp * 0.5;
    } else if (temp < 0) {
      hue += temp * 0.4;
      saturate += Math.abs(temp) * 0.2;
    }

    // Tint
    if (tint > 0) {
      hue += tint * 0.6;
    } else if (tint < 0) {
      hue -= Math.abs(tint) * 0.6;
    }

    // Sharpness effect
    if (sharp > 0) {
      contrast += sharp * 0.35;
    }

    // Color Profile Preset Modifiers
    switch (activeProfile) {
      case "vivid":
        saturate += 40;
        contrast += 15;
        brightness += 4;
        break;
      case "cinema":
        contrast += 25;
        saturate -= 10;
        sepia += 15;
        break;
      case "portrait":
        brightness += 8;
        saturate += 12;
        break;
      case "night":
        brightness += 25;
        contrast += 10;
        saturate -= 15;
        break;
      case "bw":
        saturate = 0;
        contrast += 30;
        break;
      case "natural":
      default:
        break;
    }

    if (simPhoto) {
      simPhoto.style.filter = `sepia(${sepia}%) hue-rotate(${hue}deg) saturate(${saturate}%) contrast(${contrast}%) brightness(${brightness}%) blur(${blur}px)`;
    }

    // Sync labels
    const dict = I18N_DATA[currentLang] || I18N_DATA.en;
    if (simValTemp) simValTemp.textContent = temp === 0 ? dict.sim_preset_natural : `${temp > 0 ? "+" : ""}${temp}`;
    if (simValTint) simValTint.textContent = tint === 0 ? dict.sim_preset_natural : `${tint > 0 ? "+" : ""}${tint}`;
    if (simValSharp) simValSharp.textContent = sharp === 0 ? "Off" : `${sharp}%`;
  }

  // Presets click listeners
  document.querySelectorAll(".chip-preset").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-preset").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeProfile = chip.getAttribute("data-preset");
      updateSimPhotoFilters();
    });
  });

  // Slider input listeners
  [simTempSlider, simTintSlider, simSharpSlider].forEach(slider => {
    if (slider) {
      slider.addEventListener("input", updateSimPhotoFilters);
    }
  });

  // Bokeh toggle
  if (simBokehToggle) {
    simBokehToggle.addEventListener("click", () => {
      simBokehToggle.classList.toggle("active");
      updateSimPhotoFilters();
    });
  }

  // Blackout toggle
  if (simBlackoutToggle) {
    simBlackoutToggle.addEventListener("click", () => {
      const isActive = simBlackoutToggle.classList.toggle("active");
      if (simBlackoutOverlay) {
        simBlackoutOverlay.style.opacity = isActive ? "0.96" : "0";
      }
    });
  }

  // Reset button
  if (simResetBtn) {
    simResetBtn.addEventListener("click", () => {
      if (simTempSlider) simTempSlider.value = 0;
      if (simTintSlider) simTintSlider.value = 0;
      if (simSharpSlider) simSharpSlider.value = 0;
      if (simBokehToggle) simBokehToggle.classList.remove("active");
      if (simBlackoutToggle) simBlackoutToggle.classList.remove("active");
      if (simBlackoutOverlay) simBlackoutOverlay.style.opacity = "0";
      activeProfile = "natural";
      document.querySelectorAll(".chip-preset").forEach(c => {
        c.classList.toggle("active", c.getAttribute("data-preset") === "natural");
      });
      updateSimPhotoFilters();
    });
  }

  // Connection mode toggles
  function setConnMode(usb) {
    isUsbMode = usb;
    if (simModeUsb) {
      simModeUsb.classList.toggle("active", usb);
      simModeUsb.setAttribute("aria-selected", usb ? "true" : "false");
    }
    if (simModeWifi) {
      simModeWifi.classList.toggle("active", !usb);
      simModeWifi.setAttribute("aria-selected", !usb ? "true" : "false");
    }
    if (simStatPing && simStatFps && simStatBitrate) {
      if (usb) {
        simStatPing.textContent = "4.2 ms";
        simStatFps.textContent = "60.0 FPS";
        simStatBitrate.textContent = "28.5 Mbps";
      } else {
        simStatPing.textContent = "14.8 ms";
        simStatFps.textContent = "60.0 FPS";
        simStatBitrate.textContent = "18.2 Mbps";
      }
    }
  }

  if (simModeUsb) simModeUsb.addEventListener("click", () => setConnMode(true));
  if (simModeWifi) simModeWifi.addEventListener("click", () => setConnMode(false));

  // Live telemetry pulse
  setInterval(() => {
    if (!simStatPing || !simStatFps) return;
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

  // 7. SHA256 COPY TO CLIPBOARD
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

  // 8. LEGAL MODAL SHEETS (PRIVACY & TERMS)
  function setupModal(triggerId, modalId, closeId) {
    const trigger = document.getElementById(triggerId);
    const modal = document.getElementById(modalId);
    const closeBtn = document.getElementById(closeId);
    if (!modal) return;

    function openModal(e) {
      if (e) e.preventDefault();
      modal.classList.add("open");
      document.body.style.overflow = "hidden";
    }

    function closeModal() {
      modal.classList.remove("open");
      document.body.style.overflow = "";
    }

    if (trigger) trigger.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) {
        closeModal();
      }
    });
  }

  setupModal("link-open-privacy", "modal-privacy", "btn-close-privacy");
  setupModal("link-open-terms", "modal-terms", "btn-close-terms");

  // 9. STICKY NAV SCROLL
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
});
