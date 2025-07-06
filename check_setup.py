#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 태블릿 제어기 설정 검증 스크립트
설치 및 설정이 올바르게 되었는지 확인합니다.
"""

import subprocess
import sys
import socket
import importlib.util
import platform

def print_header(title):
    """섹션 헤더 출력"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)

def print_result(check_name, result, details=""):
    """검사 결과 출력"""
    status = "✅ 성공" if result else "❌ 실패"
    print(f"{check_name:<30} {status}")
    if details:
        print(f"   → {details}")

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 7
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    return is_valid, f"Python {version_str} {'(권장)' if is_valid else '(Python 3.7+ 필요)'}"

def check_python_packages():
    """필요한 Python 패키지 확인"""
    packages = ['tkinter', 'subprocess', 'threading', 'json', 'socket']
    results = []
    
    for package in packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'subprocess':
                import subprocess
            elif package == 'threading':
                import threading
            elif package == 'json':
                import json
            elif package == 'socket':
                import socket
            
            results.append((package, True, "사용 가능"))
        except ImportError:
            results.append((package, False, "설치 필요"))
    
    return results

def check_adb_installation():
    """ADB 설치 확인"""
    try:
        result = subprocess.run(['adb', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return True, f"설치됨 - {version_line}"
        else:
            return False, "ADB 실행 실패"
    except subprocess.TimeoutExpired:
        return False, "ADB 응답 시간 초과"
    except FileNotFoundError:
        return False, "ADB를 찾을 수 없음 (PATH 확인 필요)"

def check_adb_server():
    """ADB 서버 상태 확인"""
    try:
        result = subprocess.run(['adb', 'start-server'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 연결된 기기 확인
            devices_result = subprocess.run(['adb', 'devices'], 
                                          capture_output=True, text=True, timeout=5)
            devices = [line for line in devices_result.stdout.split('\n') 
                      if '\tdevice' in line]
            device_count = len(devices)
            return True, f"서버 실행 중 (연결된 기기: {device_count}개)"
        else:
            return False, "서버 시작 실패"
    except Exception as e:
        return False, f"서버 확인 오류: {str(e)}"

def check_network_connectivity():
    """네트워크 연결 확인"""
    try:
        # 로컬 네트워크 확인
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # 네트워크 대역 확인
        network_class = "알 수 없음"
        if local_ip.startswith("192.168"):
            network_class = "가정용/사무용 네트워크"
        elif local_ip.startswith("10."):
            network_class = "사설 네트워크"
        elif local_ip.startswith("172."):
            network_class = "기업용 네트워크"
        
        return True, f"IP: {local_ip} ({network_class})"
    except Exception:
        return False, "네트워크 연결 확인 불가"

def check_firewall_ports():
    """방화벽 포트 확인 (간접적)"""
    try:
        # 5555 포트로 소켓 생성 테스트
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 5555))
        s.close()
        return True, "ADB 포트(5555) 사용 가능"
    except socket.error as e:
        if e.errno == 98 or e.errno == 10048:  # Address already in use
            return True, "ADB 포트(5555) 이미 사용 중 (정상)"
        else:
            return False, f"포트 확인 실패: {e}"

def check_config_files():
    """설정 파일 확인"""
    import os
    
    files = {
        'android_tablet_controller.py': '메인 프로그램',
        'requirements.txt': '패키지 의존성',
        'README.md': '사용 설명서',
        'android_setup_guide.md': '안드로이드 설정 가이드'
    }
    
    results = []
    for filename, description in files.items():
        exists = os.path.exists(filename)
        results.append((f"{filename} ({description})", exists, 
                       "존재함" if exists else "파일 없음"))
    
    return results

def suggest_fixes():
    """문제 해결 제안"""
    print_header("문제 해결 제안")
    
    suggestions = [
        "❌ Python 버전 문제:",
        "   → Python 3.7 이상을 설치하세요: https://www.python.org/downloads/",
        "",
        "❌ ADB 설치 문제:",
        "   → setup_adb.py를 실행하여 자동 설치하세요",
        "   → 또는 수동으로 Platform Tools를 다운로드하세요",
        "   → https://developer.android.com/studio/releases/platform-tools",
        "",
        "❌ 패키지 설치 문제:",
        "   → pip install -r requirements.txt",
        "",
        "❌ 네트워크 문제:",
        "   → PC와 안드로이드 기기가 같은 Wi-Fi에 연결되었는지 확인",
        "   → 방화벽에서 ADB 포트(5555) 허용",
        "",
        "❌ 안드로이드 설정 문제:",
        "   → android_setup_guide.md 문서를 참조하세요",
        "   → USB 디버깅 및 무선 디버깅 활성화 확인"
    ]
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    print("Android 태블릿 제어기 설정 검증")
    print("="*50)
    
    # 시스템 정보
    print_header("시스템 정보")
    print(f"운영체제: {platform.system()} {platform.release()}")
    print(f"아키텍처: {platform.machine()}")
    
    # Python 환경 검사
    print_header("Python 환경 검사")
    python_ok, python_details = check_python_version()
    print_result("Python 버전", python_ok, python_details)
    
    # 패키지 검사
    print_header("Python 패키지 검사")
    package_results = check_python_packages()
    all_packages_ok = True
    for package, ok, details in package_results:
        print_result(f"{package} 패키지", ok, details)
        if not ok:
            all_packages_ok = False
    
    # ADB 검사
    print_header("ADB 환경 검사")
    adb_ok, adb_details = check_adb_installation()
    print_result("ADB 설치", adb_ok, adb_details)
    
    if adb_ok:
        server_ok, server_details = check_adb_server()
        print_result("ADB 서버", server_ok, server_details)
    
    # 네트워크 검사
    print_header("네트워크 환경 검사")
    network_ok, network_details = check_network_connectivity()
    print_result("네트워크 연결", network_ok, network_details)
    
    port_ok, port_details = check_firewall_ports()
    print_result("방화벽/포트", port_ok, port_details)
    
    # 파일 검사
    print_header("프로젝트 파일 검사")
    file_results = check_config_files()
    all_files_ok = True
    for filename, ok, details in file_results:
        print_result(filename, ok, details)
        if not ok:
            all_files_ok = False
    
    # 종합 결과
    print_header("종합 결과")
    
    total_checks = 0
    passed_checks = 0
    
    checks = [
        ("Python 환경", python_ok),
        ("Python 패키지", all_packages_ok),
        ("ADB 설치", adb_ok),
        ("네트워크 연결", network_ok),
        ("프로젝트 파일", all_files_ok)
    ]
    
    for check_name, result in checks:
        total_checks += 1
        if result:
            passed_checks += 1
        print_result(check_name, result)
    
    print(f"\n전체 검사 결과: {passed_checks}/{total_checks} 통과")
    
    if passed_checks == total_checks:
        print("\n🎉 모든 설정이 완료되었습니다!")
        print("android_tablet_controller.py를 실행하여 프로그램을 시작할 수 있습니다.")
    else:
        print(f"\n⚠️  {total_checks - passed_checks}개의 문제가 발견되었습니다.")
        suggest_fixes()

if __name__ == "__main__":
    main()