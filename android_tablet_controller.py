#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 태블릿 원격 제어 프로그램
Windows PC에서 네트워크를 통해 여러 Android 태블릿을 제어합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import json
import os
from datetime import datetime
import socket

class AndroidTabletController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Android 태블릿 원격 제어기")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 설정 파일 경로
        self.config_file = "tablet_config.json"
        
        # 태블릿 목록
        self.tablets = {}
        
        # GUI 초기화
        self.setup_gui()
        
        # 설정 로드
        self.load_config()
        
        # ADB 경로 확인
        self.check_adb()
    
    def check_adb(self):
        """ADB 설치 확인"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.log_message("ADB가 정상적으로 설치되어 있습니다.")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_message("경고: ADB를 찾을 수 없습니다. Android SDK Platform Tools를 설치해주세요.")
            messagebox.showwarning("ADB 없음", 
                "ADB를 찾을 수 없습니다.\n"
                "Android SDK Platform Tools를 설치하고 PATH에 추가해주세요.\n"
                "다운로드: https://developer.android.com/studio/releases/platform-tools")
            return False
    
    def setup_gui(self):
        """GUI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 태블릿 관리 섹션
        tablet_frame = ttk.LabelFrame(main_frame, text="태블릿 관리", padding="5")
        tablet_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 태블릿 추가
        ttk.Label(tablet_frame, text="IP 주소:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ip_entry = ttk.Entry(tablet_frame, width=15)
        self.ip_entry.grid(row=0, column=1, padx=(0, 5))
        
        ttk.Label(tablet_frame, text="포트:").grid(row=0, column=2, sticky=tk.W, padx=(5, 5))
        self.port_entry = ttk.Entry(tablet_frame, width=8)
        self.port_entry.insert(0, "5555")
        self.port_entry.grid(row=0, column=3, padx=(0, 5))
        
        ttk.Label(tablet_frame, text="이름:").grid(row=0, column=4, sticky=tk.W, padx=(5, 5))
        self.name_entry = ttk.Entry(tablet_frame, width=15)
        self.name_entry.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Button(tablet_frame, text="태블릿 추가", command=self.add_tablet).grid(row=0, column=6)
        
        # 태블릿 목록
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 트리뷰 생성
        columns = ('name', 'ip', 'port', 'status')
        self.tablet_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # 컬럼 헤더 설정
        self.tablet_tree.heading('name', text='이름')
        self.tablet_tree.heading('ip', text='IP 주소')
        self.tablet_tree.heading('port', text='포트')
        self.tablet_tree.heading('status', text='상태')
        
        # 컬럼 너비 설정
        self.tablet_tree.column('name', width=150)
        self.tablet_tree.column('ip', width=120)
        self.tablet_tree.column('port', width=80)
        self.tablet_tree.column('status', width=100)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tablet_tree.yview)
        self.tablet_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tablet_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 컨텍스트 메뉴
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="삭제", command=self.remove_tablet)
        self.tablet_tree.bind("<Button-3>", self.show_context_menu)
        
        # 제어 버튼들
        control_frame = ttk.LabelFrame(main_frame, text="태블릿 제어", padding="5")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 연결 관리
        connection_frame = ttk.Frame(control_frame)
        connection_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(connection_frame, text="연결", command=self.connect_selected).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(connection_frame, text="연결 해제", command=self.disconnect_selected).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(connection_frame, text="모두 연결", command=self.connect_all).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(connection_frame, text="상태 확인", command=self.check_status).grid(row=0, column=3, padx=(0, 5))
        
        # 전원 제어
        power_frame = ttk.Frame(control_frame)
        power_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(power_frame, text="화면 켜기", command=lambda: self.send_command("input keyevent KEYCODE_WAKEUP")).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(power_frame, text="화면 끄기", command=lambda: self.send_command("input keyevent KEYCODE_POWER")).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(power_frame, text="재부팅", command=self.reboot_tablets).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(power_frame, text="절전모드", command=lambda: self.send_command("input keyevent KEYCODE_SLEEP")).grid(row=0, column=3)
        
        # 추가 제어
        extra_frame = ttk.Frame(control_frame)
        extra_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(extra_frame, text="홈 버튼", command=lambda: self.send_command("input keyevent KEYCODE_HOME")).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(extra_frame, text="뒤로 가기", command=lambda: self.send_command("input keyevent KEYCODE_BACK")).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(extra_frame, text="메뉴", command=lambda: self.send_command("input keyevent KEYCODE_MENU")).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(extra_frame, text="사용자 명령", command=self.custom_command).grid(row=0, column=3)
        
        # 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 웨이트 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def add_tablet(self):
        """태블릿 추가"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        name = self.name_entry.get().strip()
        
        if not ip or not port or not name:
            messagebox.showerror("오류", "모든 필드를 입력해주세요.")
            return
        
        if not self.is_valid_ip(ip):
            messagebox.showerror("오류", "올바른 IP 주소를 입력해주세요.")
            return
        
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("오류", "올바른 포트 번호를 입력해주세요 (1-65535).")
            return
        
        tablet_id = f"{ip}:{port}"
        if tablet_id in self.tablets:
            messagebox.showerror("오류", "이미 추가된 태블릿입니다.")
            return
        
        self.tablets[tablet_id] = {
            'name': name,
            'ip': ip,
            'port': port,
            'status': '연결 안됨'
        }
        
        self.tablet_tree.insert('', 'end', iid=tablet_id, values=(name, ip, port, '연결 안됨'))
        
        # 입력 필드 초기화
        self.ip_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        
        self.save_config()
        self.log_message(f"태블릿 추가됨: {name} ({tablet_id})")
    
    def is_valid_ip(self, ip):
        """IP 주소 유효성 검사"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    def remove_tablet(self):
        """선택된 태블릿 삭제"""
        selected = self.tablet_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 태블릿을 선택해주세요.")
            return
        
        tablet_id = selected[0]
        tablet_name = self.tablets[tablet_id]['name']
        
        if messagebox.askyesno("확인", f"'{tablet_name}' 태블릿을 삭제하시겠습니까?"):
            del self.tablets[tablet_id]
            self.tablet_tree.delete(tablet_id)
            self.save_config()
            self.log_message(f"태블릿 삭제됨: {tablet_name}")
    
    def show_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        item = self.tablet_tree.selection()
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def connect_selected(self):
        """선택된 태블릿 연결"""
        selected = self.tablet_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "연결할 태블릿을 선택해주세요.")
            return
        
        for tablet_id in selected:
            self.connect_tablet(tablet_id)
    
    def disconnect_selected(self):
        """선택된 태블릿 연결 해제"""
        selected = self.tablet_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "연결 해제할 태블릿을 선택해주세요.")
            return
        
        for tablet_id in selected:
            self.disconnect_tablet(tablet_id)
    
    def connect_all(self):
        """모든 태블릿 연결"""
        for tablet_id in self.tablets:
            self.connect_tablet(tablet_id)
    
    def connect_tablet(self, tablet_id):
        """개별 태블릿 연결"""
        def connect():
            try:
                tablet = self.tablets[tablet_id]
                cmd = f"adb connect {tablet['ip']}:{tablet['port']}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if "connected" in result.stdout or "already connected" in result.stdout:
                    tablet['status'] = '연결됨'
                    self.log_message(f"연결 성공: {tablet['name']} ({tablet_id})")
                else:
                    tablet['status'] = '연결 실패'
                    self.log_message(f"연결 실패: {tablet['name']} ({tablet_id}) - {result.stdout.strip()}")
                
                # UI 업데이트
                self.root.after(0, lambda: self.update_tablet_status(tablet_id, tablet['status']))
                
            except subprocess.TimeoutExpired:
                tablet['status'] = '연결 실패'
                self.log_message(f"연결 타임아웃: {tablet['name']} ({tablet_id})")
                self.root.after(0, lambda: self.update_tablet_status(tablet_id, tablet['status']))
            except Exception as e:
                tablet['status'] = '연결 실패'
                self.log_message(f"연결 오류: {tablet['name']} ({tablet_id}) - {str(e)}")
                self.root.after(0, lambda: self.update_tablet_status(tablet_id, tablet['status']))
        
        threading.Thread(target=connect, daemon=True).start()
    
    def disconnect_tablet(self, tablet_id):
        """개별 태블릿 연결 해제"""
        try:
            tablet = self.tablets[tablet_id]
            cmd = f"adb disconnect {tablet['ip']}:{tablet['port']}"
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            tablet['status'] = '연결 해제됨'
            self.update_tablet_status(tablet_id, tablet['status'])
            self.log_message(f"연결 해제: {tablet['name']} ({tablet_id})")
            
        except Exception as e:
            self.log_message(f"연결 해제 오류: {tablet['name']} ({tablet_id}) - {str(e)}")
    
    def update_tablet_status(self, tablet_id, status):
        """태블릿 상태 업데이트"""
        tablet = self.tablets[tablet_id]
        self.tablet_tree.item(tablet_id, values=(tablet['name'], tablet['ip'], tablet['port'], status))
    
    def check_status(self):
        """모든 태블릿 상태 확인"""
        def check():
            try:
                result = subprocess.run("adb devices", shell=True, capture_output=True, text=True, timeout=10)
                connected_devices = set()
                
                for line in result.stdout.split('\n'):
                    if '\tdevice' in line:
                        device_id = line.split('\t')[0]
                        connected_devices.add(device_id)
                
                for tablet_id, tablet in self.tablets.items():
                    device_addr = f"{tablet['ip']}:{tablet['port']}"
                    if device_addr in connected_devices:
                        tablet['status'] = '연결됨'
                    else:
                        tablet['status'] = '연결 안됨'
                    
                    self.root.after(0, lambda tid=tablet_id, status=tablet['status']: 
                                  self.update_tablet_status(tid, status))
                
                self.root.after(0, lambda: self.log_message("상태 확인 완료"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"상태 확인 오류: {str(e)}"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def send_command(self, command):
        """선택된 태블릿에 명령 전송"""
        selected = self.tablet_tree.selection()
        if not selected:
            # 선택된 것이 없으면 연결된 모든 태블릿에 전송
            connected_tablets = [tid for tid, tablet in self.tablets.items() if tablet['status'] == '연결됨']
            if not connected_tablets:
                messagebox.showwarning("경고", "연결된 태블릿이 없습니다.")
                return
            selected = connected_tablets
        
        def execute():
            for tablet_id in selected:
                try:
                    tablet = self.tablets[tablet_id]
                    if tablet['status'] != '연결됨':
                        continue
                    
                    cmd = f"adb -s {tablet['ip']}:{tablet['port']} shell {command}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        self.root.after(0, lambda name=tablet['name'], cmd=command: 
                                      self.log_message(f"명령 실행 성공: {name} - {cmd}"))
                    else:
                        self.root.after(0, lambda name=tablet['name'], cmd=command, err=result.stderr: 
                                      self.log_message(f"명령 실행 실패: {name} - {cmd} - {err.strip()}"))
                
                except Exception as e:
                    tablet_name = self.tablets[tablet_id]['name']
                    self.root.after(0, lambda name=tablet_name, cmd=command, err=str(e): 
                                  self.log_message(f"명령 실행 오류: {name} - {cmd} - {err}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def reboot_tablets(self):
        """선택된 태블릿 재부팅"""
        selected = self.tablet_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "재부팅할 태블릿을 선택해주세요.")
            return
        
        if not messagebox.askyesno("확인", "선택된 태블릿을 재부팅하시겠습니까?"):
            return
        
        self.send_command("reboot")
    
    def custom_command(self):
        """사용자 정의 명령"""
        command = tk.simpledialog.askstring("사용자 명령", "실행할 ADB shell 명령을 입력하세요:")
        if command:
            self.send_command(command)
    
    def log_message(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def save_config(self):
        """설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.tablets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"설정 저장 실패: {str(e)}")
    
    def load_config(self):
        """설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.tablets = json.load(f)
                
                # 트리뷰에 로드
                for tablet_id, tablet in self.tablets.items():
                    self.tablet_tree.insert('', 'end', iid=tablet_id, 
                                          values=(tablet['name'], tablet['ip'], tablet['port'], tablet.get('status', '연결 안됨')))
                
                self.log_message(f"{len(self.tablets)}개 태블릿 설정을 로드했습니다.")
        except Exception as e:
            self.log_message(f"설정 로드 실패: {str(e)}")
    
    def run(self):
        """프로그램 실행"""
        self.log_message("Android 태블릿 제어기가 시작되었습니다.")
        self.log_message("사용하기 전에 태블릿에서 USB 디버깅을 활성화하고 무선 디버깅을 설정해주세요.")
        self.root.mainloop()

if __name__ == "__main__":
    import tkinter.simpledialog
    app = AndroidTabletController()
    app.run()