@echo off
chcp 65001 > nul
title 오늘 할 일 v1.2.2 - Windows EXE Build
echo.
echo ==========================================
echo   오늘 할 일 v1.2.2 - EXE 빌드
echo ==========================================
echo.
py -m pip install -r requirements-build.txt
if errorlevel 1 goto :error
pyinstaller "오늘할일.spec" --noconfirm --clean
if errorlevel 1 goto :error
echo.
echo [완료] dist\오늘할일.exe
echo.
explorer dist
pause
exit /b 0

:error
echo.
echo [실패] 빌드 중 오류가 발생했습니다.
echo 이 스크립트는 Windows 빌드 PC에 Python이 있을 때만 사용합니다.
pause
exit /b 1
