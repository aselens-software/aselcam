@echo off
REM AselCam Studio - Windows Virtual Camera & Audio Driver Automated Setup
title AselCam Driver Auto-Installer

REM Check and auto-elevate to Administrator if not already elevated
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Yonetici yetkileri gerekiyor. UAC yetkilendirmesi baslatiliyor...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

pushd "%~dp0"

set "DRIVER_DIR=%~dp0_internal\aselcam\drivers\windows"
if not exist "%DRIVER_DIR%\UnityCaptureFilter64.dll" set "DRIVER_DIR=%~dp0"

echo ========================================================
echo        AselCam Studio - Automated Driver Setup
echo ========================================================

REM 1. Register Virtual Camera DirectShow Filter (64-bit and 32-bit)
echo [*] Installing AselCam DirectShow Virtual Camera (64-bit)...
if exist "%DRIVER_DIR%\UnityCaptureFilter64.dll" (
    if exist "%SystemRoot%\System32\regsvr32.exe" (
        "%SystemRoot%\System32\regsvr32.exe" /s "%DRIVER_DIR%\UnityCaptureFilter64.dll"
    ) else (
        regsvr32.exe /s "%DRIVER_DIR%\UnityCaptureFilter64.dll"
    )
)

echo [*] Installing AselCam DirectShow Virtual Camera (32-bit for Discord/Chrome)...
if exist "%DRIVER_DIR%\UnityCaptureFilter32.dll" (
    if exist "%SystemRoot%\SysWOW64\regsvr32.exe" (
        "%SystemRoot%\SysWOW64\regsvr32.exe" /s "%DRIVER_DIR%\UnityCaptureFilter32.dll"
    ) else (
        regsvr32.exe /s "%DRIVER_DIR%\UnityCaptureFilter32.dll"
    )
)

REM Set FriendlyName to "AselCam Virtual Camera" in Windows Registry
reg.exe add "HKLM\SOFTWARE\Classes\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{5C2CD55C-92AD-4999-8666-912BD3E70010}" /v FriendlyName /t REG_SZ /d "AselCam Virtual Camera" /f /reg:64 >nul 2>&1
reg.exe add "HKLM\SOFTWARE\Classes\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{5C2CD55C-92AD-4999-8666-912BD3E70010}" /v FriendlyName /t REG_SZ /d "AselCam Virtual Camera" /f /reg:32 >nul 2>&1
reg.exe add "HKCR\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{5C2CD55C-92AD-4999-8666-912BD3E70010}" /v FriendlyName /t REG_SZ /d "AselCam Virtual Camera" /f >nul 2>&1

REM 2. Install Virtual Microphone Driver (PnPUtil)
echo [*] Installing AselCam Virtual Audio Driver...
if exist "%DRIVER_DIR%\VirtualAudioDriver.inf" (
    pnputil.exe /add-driver "%DRIVER_DIR%\VirtualAudioDriver.inf" /install >nul 2>&1
)

echo.
echo ========================================================
echo  [OK] AselCam Sanal Kamera ve Mikrofon Sürücüleri Kuruldu!
echo  [*] Aygit Adi: "AselCam Virtual Camera"
echo  [*] Discord, Zoom veya Teams aciksa, cihaz listesinin
echo      yenilenmesi icin uygulamayi yeniden baslatin.
echo ========================================================
echo.
popd
exit /b 0
