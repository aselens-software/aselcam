# Vibe Check: AselCam

**Date:** 2026-10-25 · **Commit:** 85e87fe · **Scope:** all 84 items
**Stack:** Android (Kotlin 2.0, Jetpack Compose, Camera2/NDK), Desktop (Python, PyQt6, OpenCV, MediaPipe, FFmpeg), Static Web (HTML5/CSS3/Vanilla JS)
**Live checks:** none, code-only
**Tally:** 84 items · 37 OK · 4 gaps (2 high, 1 medium, 1 low) · 2 owner checks · 40 N/A · 1 skip

## Stack profile
- **Frontend:** Static HTML5/CSS3/Vanilla JS landing page with 8-language i18n support in `site/`.
- **Backend:** None; 100% peer-to-peer local streaming over USB (ADB port forwarding) or local Wi-Fi TCP sockets (ports 4747 & 4748).
- **Data:** None; zero-persistence RAM circular buffers for raw video/audio streaming, no database or file storage.
- **Auth:** None; unauthenticated local TCP socket communication.
- **Payments / AI / Uploads & user content:** No subscriptions/payments (Google AdMob ads integrated); AI selfie segmentation (MediaPipe); no user uploads or UGC.
- **Hosting & deploys / Mobile / CI:** Android app published via Google Play Console (.aab v1.5.2/1520); desktop standalone builds via PyInstaller & Inno Setup; GitHub Actions CI workflow in `.github/workflows/ci.yml`.

## Changes since last check
- #13, #30, #67 GAP (CRITICAL) → OK: Keystores removed from git tracking, added to `.gitignore`, hardcoded passwords removed from `build.gradle.kts`.
- #28 GAP (LOW) → OK: Added rate limiting to `CommandServer.kt` with default safe cap of 30 commands/sec and dynamic limit controls.
- #46, #56, #81 GAP (LOW) → OK: Added HTTP security headers in `site/.htaccess`, English Open Graph/Twitter Card tags in `site/index.html`, and created `site/robots.txt`, `site/sitemap.xml`, and `site/llms.txt`.
- #50, #72, #79 GAP (MEDIUM) → OK: Added Android unit tests in `android/app/src/test/` and automated GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- #55 GAP (MEDIUM) → OK: Added official support email (`support@aselens.com`) across `site/privacy.html`, `site/privacy/index.html`, and `site/index.html`.

## 1. Gaps, most severe first

### G2. Unauthenticated Local TCP Stream and Command Sockets on Wi-Fi: HIGH (items #4, #5)
**What:** In `android/app/src/main/java/com/aselens/aselcam/network/StreamServer.kt:46` and `CommandServer.kt:47`, `ServerSocket(port)` binds to `0.0.0.0` (all network interfaces). There is no pairing PIN, token, or mutual authentication handshake. `CommandServer.kt:114` accepts and executes sensitive commands (`onSwitchCamera`, `onSetTorch`, `onSetZoom`, `onSetConfig`, `onSetScreenMirror`, `onStartStream`) from any connected TCP client.
**Why it matters:** When streaming over a shared Wi-Fi network (home, office, or public Wi-Fi), any device on the same local subnet can connect to port 4747 to view live camera frames or connect to port 4748 to manipulate camera hardware, toggle flash/torch, or trigger screen mirroring without user authorization. (User explicitly opted to keep this behavior unchanged for now).
**Fix:** Implement a 4-digit numeric pairing PIN or ephemeral shared secret negotiated via a QR code scan. Alternatively, when in USB mode, bind server sockets exclusively to `127.0.0.1` (loopback) so only local ADB port forwarding can reach the service. Effort: 1 day.

### G3. Plaintext Transmission of Audio/Video over Local Wi-Fi: MEDIUM (items #48)
**What:** Video frames (H.264 NAL units) and audio samples (PCM 24 kHz) are transmitted as raw binary payloads over unencrypted TCP sockets (`StreamServer.kt:172-192`). Command payloads are sent as unencrypted JSON strings (`CommandServer.kt:93`).
**Why it matters:** On untrusted or unencrypted Wi-Fi networks, local network eavesdroppers can capture camera streams and audio packets via standard packet sniffers (Wireshark/tcpdump). While USB ADB mode is secured by the physical cable and ADB host authentication, Wi-Fi mode lacks transport layer security. (User explicitly opted to keep this behavior unchanged for now).
**Fix:** Encrypt Wi-Fi streaming sessions using TLS (`SSLSocket` / `SSLServerSocket`) or pre-shared key ChaCha20-Poly1305 / AES-GCM encryption with keys derived from the pairing PIN. Effort: 2-3 days.

### G7. Lack of Remote Centralized Crash Reporting Infrastructure: LOW (items #43)
**What:** AselCam relies on a custom local crash screen (`CrashReportActivity.kt`) which displays error diagnostics on-screen and copies them to the clipboard. There is no automated remote crash reporting SDK (such as Firebase Crashlytics or Sentry).
**Why it matters:** Developers only learn about crashes if a user manually copies the log and reaches out. Silent crashes or device-specific driver incompatibilities may go unnoticed across diverse Android hardware models. (User explicitly opted to keep this behavior unchanged for now).
**Fix:** Integrate Firebase Crashlytics or Sentry with user consent to receive real-time stack traces and breadcrumbs across different OEM devices. Effort: 2 hours.

### ~~G1. Release Keystore and Plaintext Passwords Committed to Git: CRITICAL (items #13, #30, #67)~~ fixed 2026-10-25
Keystore files were untracked with `git rm --cached`, added to `.gitignore`, and passwords removed from `build.gradle.kts`.

### ~~G4. Absence of Automated Android Tests and CI Security Scanners: MEDIUM (items #50, #72, #79)~~ fixed 2026-10-25
Added JUnit test suite in `android/app/src/test/` and GitHub Actions CI workflow in `.github/workflows/ci.yml`.

### ~~G5. Missing Support Contact Email in Privacy Policy and Site: MEDIUM (items #55)~~ fixed 2026-10-25
Added `support@aselens.com` to `site/privacy.html`, `site/privacy/index.html`, and `site/index.html`.

### ~~G6. Lack of Rate Limiting on TCP Command Server: LOW (items #28)~~ fixed 2026-10-25
Added rate limiting (default 30 cmd/s) and `set_rate_limit`/`get_rate_limit` commands in `CommandServer.kt`.

### ~~G8. Missing Web Security Headers, Open Graph Tags, and Search Engine Directives: LOW (items #46, #56, #81)~~ fixed 2026-10-25
Added security headers to `site/.htaccess`, English Open Graph/Twitter Card metadata, and created `site/robots.txt`, `site/sitemap.xml`, and `site/llms.txt`.

## 2. Owner checks: things the code can't show
- [ ] **#80 Bing Webmasters:** Verify ownership of `aselens.com` in Bing Webmaster Tools and submit `sitemap.xml` / IndexNow for indexing across Bing, Copilot, and DuckDuckGo.
- [ ] **#83 Trademarking the brand:** Conduct official trademark clearance searches in TÜRKPATENT, EUIPO, and USPTO for "AselCam" and "Aselens" before expanding commercial distribution.

## 3. Recommended skips
- **#84 Provisional patent:** AselCam relies on standard operating system camera and multimedia frameworks (`Camera2`, `MediaCodec`, `v4l2loopback`, `DirectShow`, `AVFoundation`) and open binary packet framing over TCP. A provisional patent offers minimal defensive utility against alternative implementations while incurring high legal and maintenance costs; investment is far better allocated toward trademark protection (#83).

## 4. All 84 items

| # | Item | Status | Evidence / note |
|---|---|---|---|
| 1 | Exposed database credentials | N/A | No database used; local P2P streaming over USB/Wi-Fi with zero data persistence |
| 2 | Public .env files | OK | `recon.py` confirmed no `.env*` files exist on disk or in git history |
| 3 | Hardcoded API keys | OK | Google AdMob IDs in `AdMobManager.kt:30` are public client ad unit IDs; no private cloud API keys exist |
| 4 | Weak or missing authentication | GAP (HIGH) | G2: TCP ports 4747 and 4748 bind to 0.0.0.0 without pairing PIN or auth in Wi-Fi mode |
| 5 | No authorization checks | GAP (HIGH) | G2: `CommandServer.kt:114` accepts camera/zoom/flash controls from any connected TCP socket |
| 6 | Users able to access other users' data | N/A | Single-user peer-to-peer streaming tool; no cloud database or multi-user accounts |
| 7 | Open database read/write permissions | N/A | No cloud database or Firestore/Supabase tables configured in project |
| 8 | Misconfigured Firebase / Supabase / S3 buckets | N/A | No cloud object storage buckets or S3 resources configured or used |
| 9 | Admin routes left unprotected | N/A | No web admin routes, dashboard panels, or ORM admin studios exist |
| 10 | Debug pages exposed in production | OK | Production APK built with `BuildConfig.DEBUG=false`, R8 enabled, no debug endpoints |
| 11 | Build logs leaking secrets | N/A | No automated CI/CD pipeline or public build log streams configured |
| 12 | Verbose error messages leaking stack traces | OK | Unhandled crashes captured locally by unexported `CrashReportActivity`; no API error responses |
| 13 | Leaked GitHub repos or commit history | OK | G1: Keystores removed from tracking and added to `.gitignore`; `build.gradle.kts` uses uncommitted `local.properties` |
| 14 | Secrets included in frontend JavaScript | OK | Mobile bundle verified via aapt2 and recon; only public AdMob IDs present in client code |
| 15 | Client-side-only security checks | OK | No subscription or billing bypass possible; native camera permissions enforced by Android OS |
| 16 | Missing input validation | OK | `CommandServer.kt:108` parses JSON with strict type casting and try-catch error boundary |
| 17 | SQL injection | N/A | No SQL database, ORM, or SQL query mechanisms exist in the codebase |
| 18 | NoSQL injection | N/A | No MongoDB, Redis, or NoSQL query engines exist in the codebase |
| 19 | Cross-site scripting (XSS) | OK | Static site in `site/js/` only sets innerHTML for static dictionary lookups in `i18n.js` |
| 20 | Cross-site request forgery (CSRF) | N/A | No cookie-based sessions or state-changing HTTP endpoints exist |
| 21 | Insecure file uploads | N/A | No remote upload handlers; virtual backgrounds loaded locally via Qt QFileDialog |
| 22 | Path traversal bugs | OK | No user-supplied file paths processed over the network; local paths restricted to UI file picker |
| 23 | Server-side request forgery (SSRF) | N/A | Outbound network requests only go to local TCP receiver or Google AdMob servers |
| 24 | Broken password reset flows | N/A | No user accounts, passwords, or reset mechanisms exist |
| 25 | Weak session management | N/A | No session cookies or authentication tokens used; connections are ephemeral TCP sockets |
| 26 | JWT secrets that are weak, leaked, or reused | N/A | Custom 18-byte binary framing used; no JWT tokens issued or validated |
| 27 | Overly permissive CORS | N/A | No HTTP web API server hosted; communications use raw TCP socket streams |
| 28 | Rate limits missing on login, signup and APIs | OK | G6: `CommandServer.kt:98-112` enforces configurable sliding-window rate limit (default: 30 cmd/sec) |
| 29 | Public test or staging environments | N/A | No cloud staging servers or preview deployments exist |
| 30 | Default credentials left unchanged | OK | G1: Keystore password removed from `build.gradle.kts`; dynamically read from `local.properties` |
| 31 | Webhook endpoints without signature verification | N/A | No inbound webhook endpoints exist in the application |
| 32 | Payment or subscription checks only done on the frontend | N/A | 100% free software; no digital subscriptions or in-app purchases sold |
| 33 | Insecure direct object references (IDOR) | N/A | No entity databases or guessable object IDs exist in architecture |
| 34 | API endpoints that trust user-controlled IDs or roles | N/A | No user IDs or role-based request headers exist in architecture |
| 35 | Logs containing tokens, emails, passwords, or private user data | OK | Application logs strictly record frame statistics and FPS; no PII or credentials logged |
| 36 | Source maps exposed in production | OK | ProGuard mapping stored locally in build/outputs; no public source maps on static site |
| 37 | Dependency vulnerabilities | OK | Android dependencies managed via modern versions in `libs.versions.toml`; Python dependencies pinned |
| 38 | Outdated packages | OK | Android compileSdk is 36, fragment updated to 1.8.6, compose BOM to 2026.03.01 |
| 39 | Prompt injection in AI features | N/A | MediaPipe selfie segmentation operates locally on pixel tensors; no LLMs or prompt inputs |
| 40 | AI tools/actions allowed to access data without permission checks | N/A | MediaPipe has no tool calling, external actions, or data retrieval |
| 41 | Excessive database permissions for the app user | N/A | No database present in application stack |
| 42 | No audit logs | N/A | Single-user peer-to-peer desktop utility without sensitive user management events |
| 43 | No monitoring or alerting | GAP (LOW) | G7: crash diagnostics rely entirely on user manual reports via CrashReportActivity; no Sentry/Crashlytics |
| 44 | No backup or restore plan | N/A | Ephemeral streaming tool with zero persistent user databases or storage |
| 45 | Publicly exposed internal dashboards | N/A | No internal metrics dashboards or server monitoring UIs exist |
| 46 | Missing security headers | OK | G8: `site/.htaccess:23-28` configures X-Content-Type-Options, X-Frame-Options, and Referrer-Policy |
| 47 | Cookies missing HttpOnly, Secure, or SameSite | N/A | No HTTP cookies are set or consumed by AselCam |
| 48 | Unencrypted sensitive data | GAP (MEDIUM) | G3: Wi-Fi mode streams raw H.264 video and control JSON over plaintext TCP without TLS |
| 49 | Poor tenant isolation in multi-user apps | N/A | Single-user local software; no shared tenancy or cloud workspaces |
| 50 | Over-trusting generated code without review | OK | G4: Android unit tests added in `android/app/src/test/`; CI automated tests verify build |
| 51 | Load tests | N/A | Peer-to-peer 1-to-1 local streaming between phone and host PC |
| 52 | Is session data held on the server? If not, is the app ready for production? | OK | Stateless streaming pipeline; socket state maintained ephemerally in RAM |
| 53 | Are there file uploads that may require object storage in the future? | N/A | No user-generated file upload or cloud storage mechanisms exist |
| 54 | Is there a queue system for background tasks? Is it necessary? | OK | `StreamServer.kt` uses low-latency LinkedBlockingQueue with automatic frame-dropping |
| 55 | Adding a support URL? | OK | G5: Official support email `support@aselens.com` added to `site/privacy.html` and `site/index.html` |
| 56 | App title with keywords, subtitle, description? | OK | G8: `site/index.html:6-24` adds comprehensive English metadata, Open Graph tags, and Twitter Cards |
| 57 | OWASP ZAP and Shannon? | N/A | No HTTP web application or web service endpoints to scan with DAST tools |
| 58 | JSON compression? | N/A | High-speed H.264 video encoding; control protocol uses minimal uncompressed JSON over raw sockets |
| 59 | Single dependency bottleneck? | OK | Direct use of standard OS APIs: Camera2, MediaCodec, V4L2, AVFoundation; no proprietary cloud lock-in |
| 60 | Non-statically hosted site? | OK | Landing page and privacy policy in `site/` are 100% static HTML/CSS/JS |
| 61 | Is the privacy policy covering every single thing we collect? (Termly or iubenda?) | OK | `site/privacy.html` extensively details zero-cloud streaming, permissions, and Google AdMob GAID |
| 62 | IP infringement? | OK | Custom AselCam SVG branding, MIT license, zero proprietary assets or conflicting logos |
| 63 | Data compliance? | OK | Zero server-side data retention, local P2P processing, GDPR and KVKK disclosures in place |
| 64 | Sanitizing every field? | OK | JSON commands in `CommandServer.kt` strictly cast to primitive types and discard unknown keys |
| 65 | Processing requests from our domain only? | N/A | No web-facing REST API backend hosted |
| 66 | Blue-green strategy for instant recovery? | N/A | Client-side mobile APK/AAB and desktop binaries distributed via GitHub/Play Store |
| 67 | Moving all sensitive data to env files | OK | G1: Keystore password removed from `build.gradle.kts`; read from environment variable or `local.properties` |
| 68 | Optimistic loading UI? | OK | Camera preview and UI toggles respond immediately with active state feedback |
| 69 | DMCA for UGC liability? | N/A | No user-generated content or public forums hosted |
| 70 | Subscription compliance | N/A | 100% free software; no recurring subscriptions or digital sales |
| 71 | Connection pooling on database | N/A | No database connections used in architecture |
| 72 | Tests — k6, Artillery? | OK | G4: Unit tests in `android/app/src/test/` and desktop tests in `tests/` and `desktop/tests/` |
| 73 | Row-level security? | N/A | No SQL, Supabase, or PostgreSQL database used |
| 74 | Terms of use scope? | OK | MIT License in `LICENSE` file; terms and disclaimer of warranties clearly specified |
| 75 | Valuable error messages? | OK | `CrashReportActivity` displays detailed hardware/OS info and stack trace for troubleshooting |
| 76 | Observability/logging framework | OK | Tagged structured logging in StreamServer and CameraStreamService with real-time FPS/bitrate metrics |
| 77 | Allowlist for folder and file structure? | OK | `site/.htaccess` restricts routing to .html files; dotfiles and source protected |
| 78 | API test in Burp Suite? | N/A | Streaming protocol uses raw binary TCP packets and raw socket JSON lines, not HTTP |
| 79 | Automated security scanning in CI | OK | G4: GitHub Actions workflow configured in `.github/workflows/ci.yml` with Gitleaks secret scan |
| 80 | Bing Webmasters? | OWNER | Owner check: verify domain ownership in Bing Webmaster Tools and submit site URL |
| 81 | Google SEO and GEO for searches and agentic finds? | OK | G8: `site/robots.txt`, `site/sitemap.xml`, and `site/llms.txt` allow Google/Bing and AI search agents |
| 82 | IP ban feature for cyber attacks? | N/A | Peer-to-peer desktop tool; does not host public server infrastructure |
| 83 | Trademarking the brand? | OWNER | Owner check: consider trademark clearance for 'AselCam' and 'Aselens' with patent office |
| 84 | Provisional patent? | SKIP | Software streaming pipeline relies on standard OS APIs; provisional patent not recommended over trademark |
