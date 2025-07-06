#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB 자동 설치 및 설정 스크립트
"""

import os
import sys
import urllib.request
import zipfile
import subprocess
import shutil
from pathlib import Path

def check_adb_installed():
    """ADB가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def download_adb():
    """ADB Platform Tools 다운로드"""
    print("ADB Platform Tools를 다운로드하고 있습니다...")
    
    # Windows용 Platform Tools URL
    url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    
    # 다운로드 디렉토리 생성
    download_dir = Path("adb_tools")
    download_dir.mkdir(exist_ok=True)
    
    zip_path = download_dir / "platform-tools.zip"
    
    try:
        # 파일 다운로드
        print(f"다운로드 중: {url}")
        urllib.request.urlretrieve(url, zip_path)
        print("다운로드 완료")
        
        # 압축 해제
        print("압축 해제 중...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        
        # 압축 파일 삭제
        zip_path.unlink()
        
        # platform-tools 디렉토리 경로
        platform_tools_dir = download_dir / "platform-tools"
        
        if platform_tools_dir.exists():
            print(f"ADB가 설치되었습니다: {platform_tools_dir.absolute()}")
            return platform_tools_dir.absolute()
        else:
            print("오류: platform-tools 디렉토리를 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"다운로드 오류: {e}")
        return None

def add_to_path(adb_path):
    """ADB를 PATH에 추가 (Windows)"""
    try:
        # 현재 PATH 확인
        current_path = os.environ.get('PATH', '')
        adb_path_str = str(adb_path)
        
        if adb_path_str not in current_path:
            print("PATH에 ADB 경로를 추가하려면 관리자 권한이 필요합니다.")
            print(f"수동으로 다음 경로를 PATH에 추가해주세요: {adb_path_str}")
            print("\n방법:")
            print("1. Win + R을 누르고 'sysdm.cpl' 입력")
            print("2. '고급' 탭 → '환경 변수' 클릭")
            print("3. '시스템 변수'에서 'Path' 선택 → '편집' 클릭")
            print("4. '새로 만들기' 클릭하고 ADB 경로 추가")
            print("5. 모든 창에서 '확인' 클릭")
            
            # 배치 파일 생성으로 임시 해결
            create_batch_file(adb_path)
        else:
            print("ADB가 이미 PATH에 있습니다.")
            
    except Exception as e:
        print(f"PATH 설정 오류: {e}")

def create_batch_file(adb_path):
    """ADB 실행을 위한 배치 파일 생성"""
    batch_content = f'''@echo off
set PATH={adb_path};%PATH%
python android_tablet_controller.py
pause
'''
    
    with open("run_controller.bat", "w", encoding="utf-8") as f:
        f.write(batch_content)
    
    print("run_controller.bat 파일이 생성되었습니다.")
    print("이 파일을 더블클릭하여 프로그램을 실행할 수 있습니다.")

def main():
    print("=== Android 태블릿 제어기 설정 ===")
    
    # ADB 설치 확인
    if check_adb_installed():
        print("ADB가 이미 설치되어 있습니다.")
        return
    
    print("ADB가 설치되어 있지 않습니다.")
    response = input("ADB를 자동으로 다운로드하고 설치하시겠습니까? (y/n): ")
    
    if response.lower() in ['y', 'yes', '예']:
        adb_path = download_adb()
        if adb_path:
            add_to_path(adb_path)
            print("\n설정이 완료되었습니다.")
            print("컴퓨터를 재시작하거나 새 명령 프롬프트를 열어주세요.")
        else:
            print("ADB 설치에 실패했습니다.")
    else:
        print("수동으로 ADB를 설치해주세요:")
        print("https://developer.android.com/studio/releases/platform-tools")

if __name__ == "__main__":
    main()