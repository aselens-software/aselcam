/**
 * AselCam Privacy Policy Client Script
 * - 8-Language Localization (Turkish & English Full Texts + Global UI)
 * - Table of Contents (TOC) Active Link Tracking (IntersectionObserver)
 * - Mobile Navigation Drawer & Hamburger Menu
 * - Sticky Header Glassmorphism Scroll Effect
 */

// Extended Localization Dictionary for Privacy Policy Page
const PRIVACY_I18N_EXT = {
  "en": {
    "privacy_page_meta_title": "Privacy Policy • AselCam",
    "privacy_page_badge": "Official Privacy & Security Notice",
    "privacy_page_main_title": "AselCam Privacy Policy",
    "privacy_page_main_subtitle": "Your video, audio, and communications belong solely to you. Zero cloud, zero external servers, zero telemetry, and 100% local closed-circuit architecture.",
    "privacy_meta_updated_label": "Last Updated:",
    "privacy_meta_updated_val": "October 19, 2026",
    "privacy_meta_version_label": "Version:",
    "privacy_meta_scope_label": "Scope:",
    "privacy_meta_scope_val": "Desktop & Mobile (Android & iOS)",
    "privacy_meta_compliance_label": "Compliance:",
    
    "pillar_1_title": "Zero Cloud Dependency",
    "pillar_1_desc": "Video and audio frames are never sent to external servers or cloud relays; they flow directly point-to-point between your devices.",
    "pillar_2_title": "Zero Telemetry & Analytics",
    "pillar_2_desc": "No user accounts, no login requirements, and no background tracking libraries. Your personal identity remains private.",
    "pillar_3_title": "Point-to-Point Connection",
    "pillar_3_desc": "Stream directly over physical USB cable or your local Wi-Fi network using encrypted or closed-circuit local socket communication.",
    "pillar_4_title": "Open Source & Transparency",
    "pillar_4_desc": "AselCam's network sockets, hardware encoders, and camera control pipelines are completely open to public inspection on GitHub.",

    "toc_heading": "Table of Contents",
    "toc_1": "1. Core Philosophy & Zero-Data",
    "toc_2": "2. Processed Data & Zero-Persistence",
    "toc_3": "3. Hardware Permissions & Purposes",
    "toc_4": "4. Network Protocols & Security",
    "toc_5": "5. Mobile Apps & Google AdMob",
    "toc_6": "6. Third-Party Integrations & Links",
    "toc_7": "7. Children's Privacy (COPPA & GDPR)",
    "toc_8": "8. Legal Rights (GDPR Compliance)",
    "toc_9": "9. Security Safeguards & Open Source",
    "toc_10": "10. Contact & Policy Updates",

    "sec1_title": "Core Philosophy and Zero-Data Collection Architecture",
    "sec1_p1": "AselCam (and its developer Aselens Software) considers user privacy not as a marketing tagline, but as the fundamental architectural cornerstone of the entire application. AselCam was engineered from scratch with a strict \"zero-data-collection\" policy to eliminate the privacy risks associated with traditional webcams and cloud-mediated video streaming services.",
    "sec1_p2": "None of our components contain a centralized user database, account management system, authentication server, or external relay (STUN/TURN) cloud. To use AselCam, you never have to provide your name, email address, phone number, or any personal identifying information.",
    "sec1_callout_title": "Aselens Software Fundamental Pledge:",
    "sec1_callout_text": "Not a single video frame, pixel, or audio waveform passing through your camera or microphone is ever transmitted, replicated, or stored on Aselens Software servers or any external cloud infrastructure.",

    "sec2_title": "Processed Data Types and Zero-Persistence Architecture",
    "sec2_p1": "AselCam processes strictly the transient hardware signals necessary to transform your mobile device into a high-performance desktop webcam:",
    "sec2_item1_title": "Video Stream (Camera Feed):",
    "sec2_item1_desc": "Raw camera sensor frames (YUV420/NV21 or CVPixelBuffer) are hardware-encoded on-device (Android MediaCodec or Apple VideoToolbox) directly into H.264 video packets and dispatched straight into the local socket.",
    "sec2_item2_title": "Audio Stream (Microphone Feed):",
    "sec2_item2_desc": "Raw 24 kHz mono/stereo PCM audio samples captured from the device microphone are encoded in real-time without latency and streamed directly to the desktop virtual audio receiver.",
    "sec2_item3_title": "Camera Control Parameters:",
    "sec2_item3_desc": "JSON-RPC adjustments such as color temperature (Kelvin), brightness, contrast, saturation, zoom, autofocus, and flashlight controls are executed instantaneously between both devices.",
    "sec2_p2": "Zero-Persistence: None of these audio or video buffers are ever written to your phone's storage, SD card, or desktop hard drive. Data exists solely in volatile RAM circular buffers for mere milliseconds and is discarded immediately after being delivered to the desktop virtual camera pipeline. When the session ends, zero residual traces remain.",

    "sec3_title": "Hardware Permissions and Operational Purposes",
    "sec3_p1": "The AselCam mobile app (Android and iOS) requests strictly the minimum essential hardware permissions required for operation:",
    "th_perm": "Permission / API",
    "th_platform": "Platform",
    "th_purpose": "Operational Purpose",
    "th_storage": "Persistent Storage?",
    "perm_camera_desc": "Opens the phone camera sensor to provide real-time video streaming to your desktop.",
    "perm_mic_desc": "Transfers microphone input to your PC for wireless studio microphone functionality.",
    "perm_fg_desc": "Prevents video interruption when the app runs in the background or during screen blackout.",
    "perm_net_desc": "Discovers the desktop client on your local Wi-Fi network and binds local communication sockets.",
    "perm_wake_desc": "Prevents device sleep during live streaming and activates the LED torch for studio lighting.",
    "tag_no_storage": "NO STORAGE (Zero)",
    "tag_service_only": "SERVICE ONLY",
    "tag_runtime": "RUNTIME ONLY",
    "sec3_p2": "AselCam never requests or accesses Location (GPS), Contacts, SMS, Files/Photo Gallery, or Biometric authentication.",

    "sec4_title": "Communication Protocols and Network Security",
    "sec4_p1": "Data transfer between the AselCam desktop client and mobile transmitter occurs over two physical channels:",
    "sec4_item1_title": "Direct USB Cable Connection (Recommended):",
    "sec4_item1_desc": "Uses ADB port forwarding on Android or usbmuxd local socket bridging on iOS. Traffic does not touch any network interface; it travels directly across the motherboard USB 3.0/3.2 bus, completely isolated from external eavesdropping.",
    "sec4_item2_title": "Local Wi-Fi Network (LAN) Connection:",
    "sec4_item2_desc": "Your phone listens on TCP port 4747 (video/audio streaming) and TCP port 4748 (camera control JSON-RPC) within your local subnet (e.g. 192.168.1.X). Packets never leave your local router and never access the public internet (WAN).",
    "sec4_callout_title": "Security Recommendation:",
    "sec4_callout_text": "When connected to public or untrusted Wi-Fi networks (hotels, cafes), we strongly recommend using the direct USB cable mode for absolute physical isolation.",

    "sec5_title": "Mobile Applications and Advertising Policy (Google AdMob SDK)",
    "sec5_p1": "AselCam is a free and open-source project. To support ongoing maintenance, continuous development, and infrastructure costs of the mobile apps, Google AdMob SDK is integrated into the Android and iOS apps.",
    "sec5_p2": "Our Google AdMob integration operates under clear, transparent guidelines:",
    "sec5_item1_title": "Banner Ads:",
    "sec5_item1_desc": "A standard advertisement banner displayed at the bottom of the mobile main screen. It never interferes with streaming controls or camera settings.",
    "sec5_item2_title": "Interstitial Ads:",
    "sec5_item2_desc": "A full-screen ad shown when the user taps \"Start Stream\". No unexpected ads ever interrupt an ongoing live broadcast.",
    "sec5_item3_title": "Ad Data Processed by Google:",
    "sec5_item3_desc": "Google AdMob may process your device's Advertising ID (Google Advertising ID - GAID or iOS IDFA), IP address, and general device model for fraud prevention and ad delivery. This information is never transmitted to Aselens Software servers.",
    "sec5_p3": "You can restrict personalized ads or reset your advertising ID at any time via your device settings (Android: Settings ➔ Google ➔ Ads; iOS: Settings ➔ Privacy & Security ➔ Tracking). For details, visit Google Privacy & Terms.",

    "sec6_title": "Third-Party Integrations and External Links",
    "sec6_p1": "AselCam desktop and website contain zero third-party trackers or cookies. Our ecosystem includes only these transparent external links:",
    "sec6_item1_title": "GitHub Releases:",
    "sec6_item1_desc": "Download buttons direct you to official binary release packages hosted on GitHub infrastructure.",
    "sec6_item2_title": "Buy Me a Coffee:",
    "sec6_item2_desc": "An optional external link for users who wish to support development with voluntary tips.",

    "sec7_title": "Children's Privacy (COPPA & GDPR Compliance)",
    "sec7_p1": "AselCam is a general-audience utility. We do not knowingly collect any personal data from children under 13 (or under 16 in the European Union). Because our software requires no registration and uses no central database, we hold no personal data belonging to children.",
    "sec7_p2": "If you believe your child has shared information via third-party ad networks, please contact us immediately.",

    "sec8_title": "Your Legal Rights (GDPR & International Protections)",
    "sec8_p1": "Under European GDPR and international privacy frameworks, we fully uphold your fundamental data rights:",
    "sec8_item1": "Right to Information & Access: AselCam holds no centralized user records.",
    "sec8_item2": "Right to Erasure (To Be Forgotten): Since no data is retained on servers, there are zero databases to purge.",
    "sec8_item3": "Data Portability: Uninstalling the app permanently purges all local runtime configurations on your device.",

    "sec9_title": "Security Safeguards and Open Source Auditing",
    "sec9_p1": "The ultimate guarantee of security is transparency. The desktop client and mobile application source code are publicly available on GitHub under the permissive MIT license.",
    "sec9_p2": "Security researchers, developers, and users can independently inspect network socket listeners, verify the absence of telemetry, and compile their own binaries directly from source.",

    "sec10_title": "Contact, Support, and Policy Amendments",
    "sec10_p1": "Aselens Software reserves the right to update this policy to reflect changes in legal regulations or platform operating systems. Updates will be published on this page with an updated effective date.",
    "sec10_p2": "For any inquiries, feedback, or security reports, please reach out via our official channels:",
    "btn_back_home": "Back to AselCam Home",
    "btn_scroll_top": "Back to Top ↑"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  // 1. MERGE EXTENDED DICTIONARIES INTO I18N_DATA
  if (typeof I18N_DATA !== "undefined") {
    for (const lang in PRIVACY_I18N_EXT) {
      if (I18N_DATA[lang]) {
        Object.assign(I18N_DATA[lang], PRIVACY_I18N_EXT[lang]);
      }
    }
  }

  // 2. LANGUAGE ENGINE
  const langSelector = document.getElementById("lang-select");
  const storedLang = localStorage.getItem("aselcam_lang");
  const systemLang = (navigator.language || "en").substring(0, 2).toLowerCase();
  
  let currentLang = storedLang || (I18N_DATA[systemLang] ? systemLang : "tr");

  function applyLanguage(lang) {
    if (!I18N_DATA[lang]) lang = "tr";
    currentLang = lang;
    localStorage.setItem("aselcam_lang", lang);

    const isRtl = lang === "ar";
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = lang;

    const dict = I18N_DATA[lang] || I18N_DATA.tr;
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

    if (langSelector) {
      langSelector.value = lang;
    }
  }

  if (langSelector) {
    langSelector.addEventListener("change", (e) => {
      applyLanguage(e.target.value);
    });
  }

  // 3. MOBILE MENU HAMBURGER & LIQUID GLASS DRAWER
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
    link.addEventListener("click", closeMobileMenu);
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && btnMobileMenu?.classList.contains("open")) {
      closeMobileMenu();
    }
  });

  // 4. STICKY NAV SCROLL
  const navHeader = document.querySelector(".nav-header");
  window.addEventListener("scroll", () => {
    if (window.scrollY > 20) {
      navHeader?.classList.add("scrolled");
    } else {
      navHeader?.classList.remove("scrolled");
    }
  }, { passive: true });

  // 5. TABLE OF CONTENTS ACTIVE HIGHLIGHTING (IntersectionObserver)
  const tocLinks = document.querySelectorAll(".toc-link");
  const sections = document.querySelectorAll(".privacy-section-block");

  if ("IntersectionObserver" in window && sections.length > 0) {
    const observerOptions = {
      root: null,
      rootMargin: "-80px 0px -60% 0px",
      threshold: 0
    };

    const sectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          tocLinks.forEach(link => {
            const href = link.getAttribute("href");
            if (href === `#${id}`) {
              link.classList.add("active");
            } else {
              link.classList.remove("active");
            }
          });
        }
      });
    }, observerOptions);

    sections.forEach(section => sectionObserver.observe(section));
  }

  // Initialize
  applyLanguage(currentLang);
});
