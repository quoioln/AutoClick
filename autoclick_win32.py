"""
Antigravity Auto-Retry (Win32/UIA Mode + GUI Dashboard)
=========================================================
Tự động nhấn nút Retry khi Antigravity gặp lỗi.
Tích hợp giao diện quản lý và thống kê metric trực quan.

Usage:
    python autoclick_win32.py
"""

import sys
import os
import time
import threading
import logging
import winsound
import tkinter as tk
from tkinter import ttk
from datetime import datetime

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    import pyautogui
except ImportError:
    print("Missing pyautogui! Run: pip install pyautogui")
    sys.exit(1)

try:
    from pywinauto import Desktop
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False
    print("Missing pywinauto! Run: pip install pywinauto")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

SCAN_INTERVAL = 3
COOLDOWN_AFTER_CLICK = 10
HOTKEY_TOGGLE = "F6"
HOTKEY_QUIT = "F7"

RETRY_BUTTON_TEXTS = ["Retry", "retry", "Try Again", "try again"]
IDE_PATTERNS = [".*Antigravity.*", ".*Visual Studio Code.*", ".*Cursor.*"]

ERROR_CONTEXT_TEXTS = [
    "terminated",
    "error",
    "failed",
    "high traffic",
    "try again",
    "troubleshooting",
]


# ============================================================================
# LOGGER
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("autoclick_win32.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("AutoRetryWin32")


# ============================================================================
# WINDOW DISCOVERY & ERROR VALIDATION
# ============================================================================

def discover_ide_windows():
    desktop = Desktop(backend="uia")
    windows = []
    seen_handles = set()

    for pattern in IDE_PATTERNS:
        try:
            found = desktop.windows(title_re=pattern)
            for w in found:
                handle = w.handle
                if handle not in seen_handles:
                    seen_handles.add(handle)
                    windows.append(w)
        except Exception:
            continue

    return windows


def _has_error_context(button_element):
    try:
        parent = button_element.parent()
        if not parent:
            return False

        try:
            children = parent.children()
            all_text = ""
            for child in children:
                try:
                    text = child.window_text() or ""
                    all_text += " " + text.lower()
                except Exception:
                    continue

            if "dismiss" in all_text:
                return True

            for error_text in ERROR_CONTEXT_TEXTS:
                if error_text in all_text:
                    return True
        except Exception:
            pass

        try:
            grandparent = parent.parent()
            if grandparent:
                all_text = ""
                for child in grandparent.children():
                    try:
                        text = child.window_text() or ""
                        all_text += " " + text.lower()
                        for gc in child.children():
                            try:
                                all_text += " " + (gc.window_text() or "").lower()
                            except Exception:
                                pass
                    except Exception:
                        continue

                if "dismiss" in all_text:
                    return True

                for error_text in ERROR_CONTEXT_TEXTS:
                    if error_text in all_text:
                        return True
        except Exception:
            pass
    except Exception:
        pass
    return False


def _get_window(target):
    try:
        win = target["window"]
        _ = win.window_text()
        return win
    except Exception:
        pass
    try:
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            if w.handle == target["handle"]:
                target["window"] = w
                return w
    except Exception:
        pass
    return None


def find_retry_button_in_windows(target_windows):
    for target in target_windows:
        win = _get_window(target)
        if win is None:
            continue

        try:
            for retry_text in RETRY_BUTTON_TEXTS:
                try:
                    buttons = win.descendants(control_type="Button", title=retry_text)
                    for btn in buttons:
                        if not btn.is_visible() or not btn.is_enabled():
                            continue

                        if not _has_error_context(btn):
                            continue

                        rect = btn.rectangle()
                        cx = (rect.left + rect.right) // 2
                        cy = (rect.top + rect.bottom) // 2
                        win_title = target["title"][:40]
                        logger.info(f"[ERROR DIALOG] '{retry_text}' at ({cx},{cy}) in: {win_title}")
                        return btn, target
                except Exception:
                    continue
        except Exception:
            continue
    return None, None


def click_button(button, target=None):
    """
    Click the Retry button using multiple strategies.
    Electron/Chromium UIs often ignore UIA click_input(),
    so we prioritize coordinate-based clicks after focusing the window.
    """
    rect = None
    cx, cy = 0, 0

    try:
        rect = button.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
    except Exception as e:
        logger.error(f"Cannot get button coordinates: {e}")
        return False

    # Step 1: Bring the target window to foreground
    try:
        if target and target.get("window"):
            win = target["window"]
            try:
                win.set_focus()
                time.sleep(0.3)
            except Exception:
                pass
            # Fallback: use win32 API directly
            try:
                import ctypes
                ctypes.windll.user32.SetForegroundWindow(target["handle"])
                time.sleep(0.3)
            except Exception:
                pass
    except Exception:
        pass

    # Step 2: Try pyautogui coordinate click (most reliable for Electron)
    try:
        logger.info(f"Trying pyautogui click at ({cx}, {cy})...")
        pyautogui.click(cx, cy)
        time.sleep(0.2)
        # Verify button is gone
        try:
            if not button.is_visible() or not button.is_enabled():
                logger.info("pyautogui click succeeded (button disappeared)!")
                return True
        except Exception:
            # Button element may be stale = click worked
            logger.info("pyautogui click succeeded (element stale)!")
            return True
        logger.info("pyautogui click sent, button still visible - trying more...")
    except Exception as e:
        logger.warning(f"pyautogui click failed: {e}")

    # Step 3: Try UIA invoke pattern
    try:
        logger.info("Trying UIA invoke pattern...")
        iface = button.iface_invoke
        if iface:
            iface.Invoke()
            logger.info("UIA invoke succeeded!")
            return True
    except Exception as e:
        logger.debug(f"UIA invoke failed: {e}")

    # Step 4: Try UIA click_input
    try:
        logger.info("Trying UIA click_input...")
        button.click_input()
        logger.info("UIA click_input succeeded!")
        return True
    except Exception as e:
        logger.debug(f"UIA click_input failed: {e}")

    # Step 5: Double-click with pyautogui as last resort
    try:
        logger.info(f"Trying pyautogui double-click at ({cx}, {cy})...")
        pyautogui.click(cx, cy, clicks=2, interval=0.1)
        return True
    except Exception as e:
        logger.error(f"All click methods failed: {e}")
        return False


# ============================================================================
# AUTO RETRY CLICKER ENGINE
# ============================================================================

class AutoRetryWin32:
    def __init__(self, target_windows):
        self.target_windows = target_windows
        self.scanning = False
        self.running = True
        self.retry_count = 0
        self.retry_per_window = {}
        self.session_start = None
        self.last_click_time = None
        self.last_click_window = None
        self._stop_event = threading.Event()
        self._scan_thread = None

    def play_sound(self, sound_type="click"):
        try:
            if sound_type == "click":
                winsound.Beep(1000, 200)
            elif sound_type == "start":
                winsound.Beep(800, 150)
                winsound.Beep(1200, 150)
            elif sound_type == "stop":
                winsound.Beep(1200, 150)
                winsound.Beep(800, 150)
        except Exception:
            pass

    def scan_loop(self):
        n = len(self.target_windows)
        logger.info(f"Scanning {n} window(s) every {SCAN_INTERVAL}s...")

        while not self._stop_event.is_set():
            try:
                button, target = find_retry_button_in_windows(self.target_windows)
                if button and target:
                    win_title = target["title"][:50]
                    logger.info(f"[!] Error dialog detected in: {win_title}")
                    time.sleep(0.5)
                    button2, target2 = find_retry_button_in_windows(self.target_windows)
                    if button2:
                        success = click_button(button2, target2)
                        if success:
                            self.retry_count += 1
                            self.last_click_time = datetime.now()
                            self.last_click_window = target.get("title", "?")

                            key = target.get("title", "unknown")
                            self.retry_per_window[key] = self.retry_per_window.get(key, 0) + 1

                            logger.info(f"[OK] Clicked Retry! (Total: {self.retry_count})")
                            self.play_sound("click")

                            # Save metrics
                            try:
                                timestamp = self.last_click_time.strftime("%Y-%m-%d %H:%M:%S")
                                with open("retry_history.log", "a", encoding="utf-8") as f:
                                    f.write(f"[{timestamp}] CLICKED RETRY | Window: {key}\n")
                                
                                with open("retry_metrics.txt", "w", encoding="utf-8") as f:
                                    f.write(f"=== Antigravity Auto-Retry Metrics ===\n")
                                    f.write(f"Last updated: {timestamp}\n")
                                    f.write(f"Total Retries: {self.retry_count}\n\n")
                                    f.write("--- Per-Window Breakdown ---\n")
                                    sorted_m = sorted(self.retry_per_window.items(), key=lambda x: x[1], reverse=True)
                                    for w, count in sorted_m:
                                        f.write(f"{count:>4}x | {w}\n")
                            except Exception as e:
                                logger.error(f"Failed to save metrics: {e}")

                            logger.info(f"Cooldown {COOLDOWN_AFTER_CLICK}s...")
                            self._stop_event.wait(COOLDOWN_AFTER_CLICK)
            except Exception as e:
                logger.error(f"Scan error: {e}")

            self._stop_event.wait(SCAN_INTERVAL)
        logger.info("Scanning stopped.")

    def start(self):
        if self.scanning: return
        self.scanning = True
        if not self.session_start:
            self.session_start = datetime.now()
        self._stop_event.clear()
        self._scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self._scan_thread.start()
        self.play_sound("start")

    def stop(self):
        if not self.scanning: return
        self.scanning = False
        self._stop_event.set()
        if self._scan_thread:
            self._scan_thread.join(timeout=5)
        self.play_sound("stop")

    def toggle(self):
        if self.scanning: self.stop()
        else: self.start()


# ============================================================================
# GUI APPLICATION
# ============================================================================

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Auto-Retry Dashboard")
        self.root.geometry("600x480")
        self.root.eval('tk::PlaceWindow . center')
        
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')

        self.clicker = None
        self.target_windows = []
        self.checkbox_vars = []
        self.windows_cache = []

        self.selection_frame = ttk.Frame(self.root, padding="15")
        self.dashboard_frame = ttk.Frame(self.root, padding="15")
        
        self.build_selection_view()
        self.selection_frame.pack(fill=tk.BOTH, expand=True)

        # Periodically refresh dashboard
        self.root.after(1000, self.update_dashboard)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_selection_view(self):
        lbl = ttk.Label(self.selection_frame, text="Antigravity Auto-Retry Clicker", font=("Segoe UI", 16, "bold"))
        lbl.pack(pady=(0, 5))
        lbl2 = ttk.Label(self.selection_frame, text="Select the Antigravity windows you want to monitor:", font=("Segoe UI", 10))
        lbl2.pack(pady=(0, 10))
        
        canvas = tk.Canvas(self.selection_frame)
        scrollbar = ttk.Scrollbar(self.selection_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Load windows
        self.windows_cache = discover_ide_windows()
        if not self.windows_cache:
            ttk.Label(self.scrollable_frame, text="No Antigravity/VSCode windows found. Please open your IDE and restart.", foreground="red").pack(pady=10)
        
        self.select_all_var = tk.BooleanVar(value=True)
        def on_select_all_change():
            state = self.select_all_var.get()
            for var in self.checkbox_vars:
                var.set(state)

        if self.windows_cache:
            chk_all = ttk.Checkbutton(self.selection_frame, text="Select / Deselect All", variable=self.select_all_var, command=on_select_all_change)
            chk_all.pack(anchor="w", pady=(0, 5))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for win in self.windows_cache:
            title = win.window_text()
            var = tk.BooleanVar(value=True)
            self.checkbox_vars.append(var)
            display_title = title if len(title) < 80 else title[:77] + "..."
            chk = ttk.Checkbutton(self.scrollable_frame, text=display_title, variable=var)
            chk.pack(anchor="w", pady=2)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        btn_frame = ttk.Frame(self.selection_frame, padding="10 0 0 0")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        if self.windows_cache:
            btn_start = ttk.Button(btn_frame, text="Start Monitoring \u25B6", command=self.do_start_monitoring)
            btn_start.pack(side=tk.RIGHT, padx=5)

        btn_cancel = ttk.Button(btn_frame, text="Exit", command=self.on_close)
        btn_cancel.pack(side=tk.RIGHT)

    def do_start_monitoring(self):
        for i, var in enumerate(self.checkbox_vars):
            if var.get():
                win = self.windows_cache[i]
                self.target_windows.append({"handle": win.handle, "title": win.window_text(), "window": win})
        
        if not self.target_windows:
            return

        self.clicker = AutoRetryWin32(self.target_windows)
        self.clicker.start()

        # Keyboard hotkeys
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY_TOGGLE, self.toggle_from_hotkey)
        except ImportError:
            pass

        self.selection_frame.pack_forget()
        self.build_dashboard_view()
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)

    def toggle_from_hotkey(self):
        if self.clicker:
            self.clicker.toggle()

    def build_dashboard_view(self):
        # Header
        header = ttk.Frame(self.dashboard_frame)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="Dashboard Metrics", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Status: RUNNING")
        self.lbl_status = ttk.Label(header, textvariable=self.status_var, font=("Segoe UI", 10, "bold"), foreground="green")
        self.lbl_status.pack(side=tk.RIGHT)

        # Overview Stats
        stats_frame = ttk.LabelFrame(self.dashboard_frame, text="Overview", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.total_retries_var = tk.StringVar(value="Total Retries: 0")
        self.uptime_var = tk.StringVar(value="Uptime: 00:00:00")
        self.last_sync_var = tk.StringVar(value="Last Click: N/A")

        ttk.Label(stats_frame, textvariable=self.total_retries_var, font=("Segoe UI", 12)).grid(row=0, column=0, sticky='w', pady=2, padx=10)
        ttk.Label(stats_frame, textvariable=self.uptime_var).grid(row=0, column=1, sticky='w', pady=2, padx=20)
        ttk.Label(stats_frame, textvariable=self.last_sync_var).grid(row=1, column=0, columnspan=2, sticky='w', pady=2, padx=10)

        # Per Window Metrics
        metric_frame = ttk.LabelFrame(self.dashboard_frame, text="Per-Window Hits", padding=10)
        metric_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.tree = ttk.Treeview(metric_frame, columns=("Count", "Window"), show="headings", height=8)
        self.tree.heading("Count", text="Hits")
        self.tree.heading("Window", text="Window Title")
        self.tree.column("Count", width=60, anchor="center")
        self.tree.column("Window", width=400)
        
        scrollbar = ttk.Scrollbar(metric_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control Buttons - prominent and clearly visible
        ttk.Separator(self.dashboard_frame, orient="horizontal").pack(fill=tk.X, pady=(5, 10))

        btn_frame = ttk.Frame(self.dashboard_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        # Pause/Resume button (large, left side)
        self.btn_toggle = tk.Button(
            btn_frame, text="\u23F8  Pause Scanning", command=self.ui_toggle,
            font=("Segoe UI", 11, "bold"), bg="#e67e22", fg="white",
            relief="raised", padx=15, pady=6, cursor="hand2"
        )
        self.btn_toggle.pack(side=tk.LEFT, padx=5)

        # Exit button (right side)
        btn_exit = tk.Button(
            btn_frame, text="\u2716  Exit", command=self.on_close,
            font=("Segoe UI", 10), bg="#c0392b", fg="white",
            relief="raised", padx=15, pady=6, cursor="hand2"
        )
        btn_exit.pack(side=tk.RIGHT, padx=5)

        # Hotkey hint
        ttk.Label(btn_frame, text="F6 = Toggle  |  F7 = Quit", foreground="gray").pack(side=tk.RIGHT, padx=10)

    def ui_toggle(self):
        if not self.clicker: return
        self.clicker.toggle()
        if self.clicker.scanning:
            self.btn_toggle.config(text="\u23F8  Pause Scanning", bg="#e67e22")
        else:
            self.btn_toggle.config(text="\u25B6  Resume Scanning", bg="#27ae60")

    def update_dashboard(self):
        if self.clicker:
            # Update Status
            if self.clicker.scanning:
                self.status_var.set("Status: MONITORING")
                self.lbl_status.config(foreground="green")
            else:
                self.status_var.set("Status: PAUSED")
                self.lbl_status.config(foreground="red")

            # Update Overview
            self.total_retries_var.set(f"Total Retries: {self.clicker.retry_count}")
            
            if self.clicker.session_start:
                delta = datetime.now() - self.clicker.session_start
                h, r = divmod(int(delta.total_seconds()), 3600)
                m, s = divmod(r, 60)
                self.uptime_var.set(f"Uptime: {h:02d}:{m:02d}:{s:02d}")

            last_time = self.clicker.last_click_time.strftime("%H:%M:%S") if self.clicker.last_click_time else "N/A"
            last_win = getattr(self.clicker, 'last_click_window', 'N/A') or 'N/A'
            short_win = last_win[:50] + "..." if len(last_win) > 50 else last_win
            self.last_sync_var.set(f"Last Click: {last_time} ({short_win})")

            # Update Treeview Metrics
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            sorted_m = sorted(self.clicker.retry_per_window.items(), key=lambda x: x[1], reverse=True)
            for w, count in sorted_m:
                short_w = w[:70] + "..." if len(w) > 70 else w
                self.tree.insert("", tk.END, values=(f"{count}x", short_w))

        self.root.after(1000, self.update_dashboard)

    def on_close(self):
        if self.clicker:
            self.clicker.stop()
            self.clicker.running = False
        self.root.destroy()
        sys.exit(0)


def main():
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
