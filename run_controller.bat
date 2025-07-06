@echo off
chcp 65001
echo ======================================
echo Android 태블릿 원격 제어기
echo ======================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치한 후 다시 실행해주세요.
    echo 다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 의존성 설치 확인
if not exist "requirements.txt" (
    echo requirements.txt 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo Python 패키지 설치 중...
pip install -r requirements.txt

echo.
echo 프로그램을 시작합니다...
echo.

REM 프로그램 실행
python android_tablet_controller.py

echo.
echo 프로그램이 종료되었습니다.
pause