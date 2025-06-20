@echo off
title Dosya Dogrulama Araci
color 0A

echo.
echo ================================================
echo    DOSYA iMZA DOGRULAMA ARACI BASLATILIYOR
echo ================================================
echo.
echo Python betik calistiriliyor...
echo.

:: Python'un PATH'te olup olmadığını kontrol et
where python >nul 2>nul
if %errorlevel% equ 0 (
    python simple-file-verification.py
    goto end
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    python3 simple-file-verification.py
    goto end
)

:: Python bulunamazsa kullanıcıyı uyar
echo.
echo !!! UYARI !!!
echo Sisteminizde Python bulunamadi.
echo Lutfen Python'u kurun ve PATH'e ekleyin.
echo https://www.python.org/downloads/
echo.
pause
exit /b 1

:end
echo.
echo =================================================
echo    TAMAMLANDI - CIKMAK iCiN ENTER TUSUNA BASIN
echo =================================================
echo.
pause
