import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import time
import sys
from pystray import MenuItem as item, Icon
from PIL import Image
import os
import argparse
import textwrap
import platform

class SystemMonitor:
    def __init__(self, mode='gui'):
        self.mode = mode
        self.running = True
        
        # Common configuration
        self.cpu_threshold = 80
        self.ram_threshold = 80
        self.disk_threshold = 80
        self.check_interval = 5
        self.email_enabled = False
        self.last_alert_time = {}
        self.alert_cooldown = 300
        
        if self.mode == 'gui':
            self.root = tk.Tk()
            self.root.title("System Monitor")
            self.root.geometry("800x600")
            self.root.protocol("WM_DELETE_WINDOW", self.quit)
            self.setup_gui()
            self.setup_tray_icon()
        elif self.mode == 'cli':
            self.setup_cli()
            
        self.monitor_thread = Thread(target=self.monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        if self.mode == 'gui':
            self.root.mainloop()
        elif self.mode == 'cli':
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.quit()

    def setup_gui(self):
        # Main frames
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mode switch button
        self.mode_switch = ttk.Button(self.main_frame, text="Switch to CLI Mode", 
                                    command=self.switch_to_cli)
        self.mode_switch.pack(side=tk.TOP, anchor=tk.NE, pady=5)
        
        # Resource indicators
        self.resource_frame = ttk.LabelFrame(self.main_frame, text="Resource Usage", padding="10")
        self.resource_frame.pack(fill=tk.X, pady=5)
        
        self.cpu_label = ttk.Label(self.resource_frame, text="CPU: 0%")
        self.cpu_label.pack(anchor=tk.W)
        
        self.ram_label = ttk.Label(self.resource_frame, text="RAM: 0%")
        self.ram_label.pack(anchor=tk.W)
        
        self.disk_label = ttk.Label(self.resource_frame, text="Disk: 0%")
        self.disk_label.pack(anchor=tk.W)
        
        # Process list
        self.process_frame = ttk.LabelFrame(self.main_frame, text="High Usage Processes", padding="10")
        self.process_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(self.process_frame, columns=("PID", "Name", "CPU%", "RAM%"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Kill button
        ttk.Button(self.process_frame, text="Kill Process", 
                 command=self.kill_selected_process).pack(side=tk.RIGHT, pady=5)
        
        # Settings button
        ttk.Button(self.main_frame, text="Settings", 
                 command=self.show_settings).pack(side=tk.RIGHT, pady=5)

    def setup_cli(self):
        print("System Monitor running in CLI mode")
        print("Press Ctrl+C to exit")
        print("-" * 40)
        
    def setup_tray_icon(self):
        image = Image.new('RGB', (64, 64), (50, 50, 50))
        self.tray_icon = Icon("System Monitor", image, "System Monitor", 
                            menu=(
                                item('Show', self.show_from_tray),
                                item('Exit', self.quit),
                            ))
        Thread(target=self.tray_icon.run, daemon=True).start()

    def monitor_resources(self):
        while self.running:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            if self.mode == 'gui':
                self.root.after(0, self.update_gui, cpu, ram, disk)
            else:
                self.update_cli(cpu, ram, disk)
                
            self.check_thresholds(cpu, ram, disk)
            time.sleep(self.check_interval)

    def update_gui(self, cpu, ram, disk):
        self.cpu_label.config(text=f"CPU: {cpu:.1f}%")
        self.ram_label.config(text=f"RAM: {ram:.1f}%")
        self.disk_label.config(text=f"Disk: {disk:.1f}%")
        
        for label, value, threshold in [
            (self.cpu_label, cpu, self.cpu_threshold),
            (self.ram_label, ram, self.ram_threshold),
            (self.disk_label, disk, self.disk_threshold)
        ]:
            label.config(foreground='red' if value > threshold else 'black')
        
        if self.root.state() != 'withdrawn':
            self.update_process_list()

    def update_cli(self, cpu, ram, disk):
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        print(textwrap.dedent(f"""
        System Resources:
        CPU:  {cpu:.1f}% {'!!' if cpu > self.cpu_threshold else ''}
        RAM:  {ram:.1f}% {'!!' if ram > self.ram_threshold else ''}
        Disk: {disk:.1f}% {'!!' if disk > self.disk_threshold else ''}
        """))
        
        print("Top Processes:")
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        for i, proc in enumerate(processes[:5], 1):
            print(f"{i}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}% RAM: {proc['memory_percent']:.1f}%")

    def update_process_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        for proc in processes[:20]:
            self.tree.insert("", tk.END, values=(
                proc['pid'], proc['name'], 
                f"{proc['cpu_percent']:.1f}", 
                f"{proc['memory_percent']:.1f}"
            ))

    def kill_selected_process(self):
        if self.mode != 'gui':
            return
            
        selected = self.tree.selection()
        if selected:
            pid = int(self.tree.item(selected[0], 'values')[0])
            try:
                psutil.Process(pid).terminate()
                messagebox.showinfo("Success", f"Process {pid} terminated")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def check_thresholds(self, cpu, ram, disk):
        current_time = time.time()
        alerts = []
        
        for name, value, threshold in [
            ('CPU', cpu, self.cpu_threshold),
            ('RAM', ram, self.ram_threshold),
            ('Disk', disk, self.disk_threshold)
        ]:
            if value > threshold:
                if not self.last_alert_time.get(name) or current_time - self.last_alert_time[name] > self.alert_cooldown:
                    alerts.append(f"{name} threshold exceeded: {value:.1f}%")
                    self.last_alert_time[name] = current_time
        
        if alerts and self.email_enabled:
            self.send_alert("\n".join(alerts))

    def send_alert(self, message):
        if self.mode == 'gui':
            messagebox.showwarning("Alert", message)
        else:
            print(f"ALERT: {message}")

    def show_settings(self):
        if self.mode != 'gui':
            return
            
        window = tk.Toplevel(self.root)
        window.title("Settings")
        
        ttk.Label(window, text="CPU Threshold:").grid(row=0, column=0)
        cpu_entry = ttk.Entry(window)
        cpu_entry.insert(0, str(self.cpu_threshold))
        cpu_entry.grid(row=0, column=1)
        
        ttk.Label(window, text="RAM Threshold:").grid(row=1, column=0)
        ram_entry = ttk.Entry(window)
        ram_entry.insert(0, str(self.ram_threshold))
        ram_entry.grid(row=1, column=1)
        
        ttk.Label(window, text="Check Interval:").grid(row=2, column=0)
        interval_entry = ttk.Entry(window)
        interval_entry.insert(0, str(self.check_interval))
        interval_entry.grid(row=2, column=1)
        
        ttk.Button(window, text="Save", command=lambda: self.save_settings(
            cpu_entry.get(), ram_entry.get(), interval_entry.get()
        )).grid(row=3, columnspan=2)

    def save_settings(self, cpu, ram, interval):
        try:
            self.cpu_threshold = float(cpu)
            self.ram_threshold = float(ram)
            self.check_interval = float(interval)
            if self.mode == 'gui':
                messagebox.showinfo("Success", "Settings saved")
        except ValueError:
            if self.mode == 'gui':
                messagebox.showerror("Error", "Invalid values")

    def switch_to_cli(self):
        if self.mode == 'gui':
            self.quit()
            SystemMonitor(mode='cli')

    def minimize_to_tray(self):
        if hasattr(self, 'root'):
            self.root.withdraw()

    def show_from_tray(self):
        if hasattr(self, 'root'):
            self.root.deiconify()

    def quit(self):
        self.running = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        if hasattr(self, 'root'):
            self.root.destroy()
        if self.mode == 'cli':
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='System Monitor')
    parser.add_argument('--mode', choices=['gui', 'cli'], default='gui',
                      help='Run in GUI or CLI mode')
    args = parser.parse_args()
    
    SystemMonitor(mode=args.mode)
