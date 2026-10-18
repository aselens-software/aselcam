"""
ASELCAM OBSIDIAN STREAM STUDIO THEME
Extracted & Synchronized from Google Stitch AI Design System
Theme: Obsidian Stream Studio (Virtual Cam UI Redesign)
Aesthetic: Deep Slate Minimalism, Low-Latency Hardware Controls & Glassmorphic Telemetry
"""

DARK_STYLE = """
/* ==========================================================================
   GLOBAL CANVAS & BASE TYPOGRAPHY
   Tokens: bg-canvas #080C14, surface-base #0F172A, text-primary #DFE2F1
   ========================================================================== */
QMainWindow, QWidget#central_widget, QWidget#body_widget {
    background-color: #080c14;
    color: #dfe2f1;
    font-family: "Space Grotesk", "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
}

/* ==========================================================================
   LABELS & TEXT (Strictly Transparent Backgrounds)
   ========================================================================== */
QLabel {
    background: transparent;
    background-color: transparent;
    color: #cbd5e1;
    font-size: 13px;
}

/* Studio Digital Telemetry & Value Readout Badge */
QLabel#lbl_value_badge, QLineEdit#lbl_value_badge {
    background-color: #0b0f19;
    color: #38bdf8;
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 6px;
    padding: 2px 6px;
    font-weight: 700;
    font-size: 11px;
    font-family: "JetBrains Mono", "SF Mono", "Fira Code", monospace, "Segoe UI";
    min-width: 48px;
    qproperty-alignment: AlignCenter;
}

QLineEdit#lbl_value_badge:focus {
    border: 1px solid #38bdf8;
    background-color: #050811;
    color: #ffffff;
}

/* Studio Telemetry Chip Card */
QFrame#telemetry_card {
    background-color: #171b26;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 10px;
}

/* Top Connection Strip Container */
QFrame#connection_strip {
    background-color: #171b26;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    border-top: none;
    border-left: none;
    border-right: none;
}

/* Bottom Controls Dock Under Viewport */
QFrame#video_control_dock {
    background-color: #171b26;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 4px;
}

/* Right Panel Inspector Shell */
QWidget#inspector_shell {
    background-color: #171b26;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
}

/* ==========================================================================
   STUDIO ELEVATED CARDS / GROUPBOXES
   Tokens: surface-container #1C1F2A, border-subtle rgba(255, 255, 255, 0.08)
   ========================================================================== */
QGroupBox {
    background-color: #1c1f2a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    margin-top: 22px;
    margin-bottom: 12px;
    font-weight: 700;
    color: #94a3b8;
    padding-top: 22px;
    padding-bottom: 14px;
    padding-left: 14px;
    padding-right: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 3px;
    padding: 0 8px;
    color: #4cd7f6;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: transparent;
}

/* ==========================================================================
   PRECISION STUDIO BUTTONS
   Tokens: surface-elevated #1E293B, surface-hover #283548, radius 8px
   ========================================================================== */
QPushButton {
    background: #1e293b;
    color: #dfe2f1;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background: #283548;
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #ffffff;
}

QPushButton:pressed {
    background: #0f131d;
    border: 1px solid rgba(0, 0, 0, 0.4);
}

QPushButton:disabled {
    background: #111827;
    color: #475569;
    border: 1px solid rgba(255, 255, 255, 0.04);
}

/* Primary Connect & Launch Button (Cyber Emerald: #00A572 -> #4EDEA3) */
QPushButton#btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00a572, stop:1 #4edea3);
    color: #003824;
    border: 1px solid #4edea3;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    padding: 7px 18px;
}

QPushButton#btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #6ffbbe);
    border: 1px solid #6ffbbe;
    color: #002113;
}

QPushButton#btn_primary:pressed {
    background: #00875c;
    color: #ffffff;
}

/* Danger / Disconnect Button (Radiant Coral: #EF4444 -> #DC2626) */
QPushButton#btn_danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #dc2626);
    color: #ffffff;
    border: 1px solid #f87171;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    padding: 7px 18px;
}

QPushButton#btn_danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f87171, stop:1 #ef4444);
    border: 1px solid #fca5a5;
}

QPushButton#btn_danger:pressed {
    background: #991b1b;
}

/* Primary Action / Camera Flip / Apply Settings Button (Electric Blue / Primary Container) */
QPushButton#btn_action {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d8eff, stop:1 #2563eb);
    color: #ffffff;
    border: 1px solid #60a5fa;
    border-radius: 8px;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
}

QPushButton#btn_action:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 #3b82f6);
    border: 1px solid #93c5fd;
}

QPushButton#btn_action:pressed {
    background: #1d4ed8;
}

/* Screen Mirroring Action Button (Electric Cyan Glow) */
QPushButton#btn_screen_mirror {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 16px;
}

QPushButton#btn_screen_mirror:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #0284c7);
    border: 1px solid #7dd3fc;
}

QPushButton#btn_screen_mirror:pressed {
    background: #075985;
}

/* Preset Quick Pill Buttons (e.g. Zoom 0.6x, 1.0x, 2.0x, 5.0x) */
QPushButton#btn_preset_chip {
    background: #262a35;
    color: #8c909f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
    font-weight: 600;
    font-family: "JetBrains Mono", monospace;
}

QPushButton#btn_preset_chip:hover {
    background: #313540;
    color: #dfe2f1;
    border-color: rgba(77, 142, 255, 0.4);
}

QPushButton#btn_preset_chip:checked, QPushButton#btn_preset_chip:pressed {
    background: #4d8eff;
    color: #00285d;
    border: 1px solid #adc6ff;
    font-weight: 700;
}

/* Segment Switcher Buttons (USB / Wi-Fi Strip) */
QPushButton#btn_mode_active {
    background-color: #4d8eff !important;
    background: #4d8eff !important;
    color: #00285d !important;
    border: none !important;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 700;
    font-size: 12px;
}

QPushButton#btn_mode_inactive {
    background-color: transparent !important;
    background: transparent !important;
    color: #c2c6d6 !important;
    border: none !important;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton#btn_mode_inactive:hover {
    background-color: #262a35 !important;
    color: #dfe2f1 !important;
}

/* ==========================================================================
   RECESSED INSET INPUTS & COMBOBOXES
   Tokens: background #0A0E18, border-subtle rgba(255, 255, 255, 0.1)
   ========================================================================== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #0a0e18;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 10px;
    color: #dfe2f1;
    font-size: 12px;
    font-family: "JetBrains Mono", monospace, "Segoe UI";
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #4d8eff;
    background-color: #070a11;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #4cd7f6;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #171b26;
    border: 1px solid #313540;
    border-radius: 8px;
    selection-background-color: #262a35;
    selection-color: #4cd7f6;
    color: #dfe2f1;
    padding: 4px;
}

/* ==========================================================================
   STUDIO TAB SYSTEM (Inspector Tabs)
   ========================================================================== */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    background-color: #171b26;
    top: -1px;
}

QTabBar::tab {
    background-color: #0a0e18;
    color: #8c909f;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 7px 14px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 11px;
}

QTabBar::tab:hover {
    background-color: #1c1f2a;
    color: #dfe2f1;
}

QTabBar::tab:selected {
    background-color: #262a35;
    color: #4d8eff;
    border: 1px solid rgba(77, 142, 255, 0.5);
    border-bottom: 2px solid #4d8eff;
    font-weight: 700;
}

/* ==========================================================================
   STUDIO SLIDERS (Distinct recessed track with visible boundaries)
   ========================================================================== */
QSlider::groove:horizontal {
    border: 1px solid rgba(255, 255, 255, 0.12);
    height: 6px;
    background: #0d121d;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #38bdf8);
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 3px;
}

QSlider::add-page:horizontal {
    background: #0d121d;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 3px solid #38bdf8;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    border: 3px solid #7dd3fc;
    background: #f0f9ff;
}

QSlider::handle:horizontal:pressed {
    background: #bae6fd;
    border: 3px solid #0284c7;
}

/* ==========================================================================
   CHECKBOXES
   ========================================================================== */
QCheckBox {
    spacing: 8px;
    color: #dfe2f1;
    font-weight: 500;
    background: transparent;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    background-color: #0a0e18;
}

QCheckBox::indicator:hover {
    border-color: #4d8eff;
}

QCheckBox::indicator:checked {
    background: #4d8eff;
    border: 1px solid #adc6ff;
}

/* ==========================================================================
   VU METER & AUDIO PROGRESS BAR
   ========================================================================== */
QProgressBar {
    background-color: #0a0e18;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    text-align: center;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4edea3, stop:0.7 #00a572, stop:0.88 #eab308, stop:1 #ef4444);
    border-radius: 3px;
}

/* ==========================================================================
   STATUS BAR & BADGES
   ========================================================================== */
QStatusBar {
    background-color: #0a0e18;
    color: #8c909f;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
    min-height: 28px;
}

QLabel#status_badge {
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* ==========================================================================
   STUDIO TITLE BAR & WINDOW CONTROLS
   ========================================================================== */
QWidget#custom_title_bar {
    background-color: #0a0e18;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QPushButton#btn_win_control {
    background-color: transparent;
    color: #8c909f;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    padding: 0;
}

QPushButton#btn_win_control:hover {
    background: #262a35;
    color: #dfe2f1;
}

QPushButton#btn_win_close {
    background-color: transparent;
    color: #8c909f;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    padding: 0;
}

QPushButton#btn_win_close:hover {
    background: #ef4444;
    color: #ffffff;
}

QPushButton#btn_collapse_hub {
    background-color: #262a35;
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    padding: 0px !important;
    margin: 0px !important;
    text-align: center;
}

QPushButton#btn_collapse_hub:hover {
    background-color: #334155;
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.25);
}

/* ==========================================================================
   SCROLL AREA & MINIMAL SCROLLBAR
   ========================================================================== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background-color: #0a0e18;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #262a35;
    min-height: 25px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #424754;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Outer Window Bevel for Frameless Mode */
QMainWindow#main_window {
    border: 1px solid #262a35;
}
"""
