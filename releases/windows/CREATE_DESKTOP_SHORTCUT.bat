@echo off
REM Creates a desktop shortcut for AselCam on Windows
echo [AselCam] Creating desktop shortcut...
set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%_create_shortcut.vbs"
set APP_PATH=%~dp0AselCam.exe
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\AselCam.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%APP_PATH%" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.IconLocation = "%~dp0AselCam.ico,0" >> %SCRIPT%
echo oLink.Description = "AselCam Virtual Camera Studio" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo [AselCam] Shortcut created on your Desktop! You can now launch AselCam directly from your Desktop.
pause
