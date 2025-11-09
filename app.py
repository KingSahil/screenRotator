"""
Screen Rotator GUI Application
Features: System tray, keyboard shortcuts, mouse remapping, auto-startup
"""

import ctypes
from ctypes import wintypes
import time
import threading
import sys
import os
import winreg
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"Missing required package: {e}")
    print("\nPlease install required packages:")
    print("pip install pillow pystray")
    sys.exit(1)

# Enable high-resolution timer on Windows for better sleep precision
try:
    winmm = ctypes.windll.winmm
    winmm.timeBeginPeriod(1)  # Request 1ms timer resolution
except:
    pass

# Constants for display orientation
DMDO_DEFAULT = 0  # 0 degrees
DMDO_90 = 1       # 90 degrees
DMDO_180 = 2      # 180 degrees
DMDO_270 = 3      # 270 degrees

# Virtual key codes
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key

# Cursor constants
OCR_NORMAL = 32512
OCR_IBEAM = 32513
OCR_WAIT = 32514
OCR_CROSS = 32515
OCR_UP = 32516
OCR_SIZENWSE = 32642
OCR_SIZENESW = 32643
OCR_SIZEWE = 32644
OCR_SIZENS = 32645
OCR_SIZEALL = 32646
OCR_NO = 32648
OCR_HAND = 32649
OCR_APPSTARTING = 32650

# Windows API structures
class DEVMODE(ctypes.Structure):
    _fields_ = [
        ('dmDeviceName', ctypes.c_wchar * 32),
        ('dmSpecVersion', ctypes.c_ushort),
        ('dmDriverVersion', ctypes.c_ushort),
        ('dmSize', ctypes.c_ushort),
        ('dmDriverExtra', ctypes.c_ushort),
        ('dmFields', ctypes.c_ulong),
        ('dmPosition_x', ctypes.c_long),
        ('dmPosition_y', ctypes.c_long),
        ('dmDisplayOrientation', ctypes.c_ulong),
        ('dmDisplayFixedOutput', ctypes.c_ulong),
        ('dmColor', ctypes.c_short),
        ('dmDuplex', ctypes.c_short),
        ('dmYResolution', ctypes.c_short),
        ('dmTTOption', ctypes.c_short),
        ('dmCollate', ctypes.c_short),
        ('dmFormName', ctypes.c_wchar * 32),
        ('dmLogPixels', ctypes.c_ushort),
        ('dmBitsPerPel', ctypes.c_ulong),
        ('dmPelsWidth', ctypes.c_ulong),
        ('dmPelsHeight', ctypes.c_ulong),
        ('dmDisplayFlags', ctypes.c_ulong),
        ('dmDisplayFrequency', ctypes.c_ulong),
        ('dmICMMethod', ctypes.c_ulong),
        ('dmICMIntent', ctypes.c_ulong),
        ('dmMediaType', ctypes.c_ulong),
        ('dmDitherType', ctypes.c_ulong),
        ('dmReserved1', ctypes.c_ulong),
        ('dmReserved2', ctypes.c_ulong),
        ('dmPanningWidth', ctypes.c_ulong),
        ('dmPanningHeight', ctypes.c_ulong),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP)
    ]

class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),  # Use HANDLE instead of HCURSOR
        ("ptScreenPos", POINT)
    ]

# Windows API functions
user32 = ctypes.windll.user32

# Constants
ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x01
DISP_CHANGE_SUCCESSFUL = 0
DM_DISPLAYORIENTATION = 0x00000080
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000

class CursorRotator:
    """
    Handles cursor rotation to match screen orientation
    
    Note: Windows API limitations mean we can only change cursor style, not truly rotate it.
    This implementation changes cursor appearance based on orientation:
    - 0°: Normal arrow cursor
    - 90°: Cross cursor (sideways indicator)
    - 180°: Up arrow cursor (inverted indicator)
    - 270°: Cross cursor (sideways indicator)
    """
    def __init__(self):
        self.current_orientation = DMDO_DEFAULT
        self.enabled = False
        self.running = False
        self.thread = None
        self.target_cursor = None
        
    def monitor_cursor_thread(self):
        """Background thread to maintain cursor style"""
        while self.running:
            if self.enabled and self.target_cursor:
                try:
                    # Get current cursor info
                    cursor_info = CURSORINFO()
                    cursor_info.cbSize = ctypes.sizeof(CURSORINFO)
                    
                    if user32.GetCursorInfo(ctypes.byref(cursor_info)):
                        # Only set if cursor is visible and different
                        if cursor_info.flags == 1:  # CURSOR_SHOWING
                            current = user32.GetCursor()
                            if current != self.target_cursor:
                                user32.SetCursor(self.target_cursor)
                except:
                    pass
                    
            time.sleep(0.05)  # Check every 50ms
    
    def start(self):
        """Start cursor monitoring thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitor_cursor_thread, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop cursor monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def rotate_cursors(self, orientation):
        """Change cursor style to match orientation"""
        self.current_orientation = orientation
        
        try:
            if orientation == DMDO_DEFAULT:
                # Normal arrow cursor
                self.target_cursor = user32.LoadCursorW(None, OCR_NORMAL)
                self.enabled = False
                
            elif orientation == DMDO_90 or orientation == DMDO_270:
                # Use CROSS cursor for 90° and 270° (indicates rotation)
                self.target_cursor = user32.LoadCursorW(None, OCR_CROSS)
                self.enabled = True
                    
            elif orientation == DMDO_180:
                # Use UP arrow for 180° (inverted indicator)  
                self.target_cursor = user32.LoadCursorW(None, OCR_UP)
                self.enabled = True
            
            # Set the cursor immediately
            if self.target_cursor:
                user32.SetCursor(self.target_cursor)
            
            # Start monitoring if not already running
            if self.enabled and not self.running:
                self.start()
                    
        except Exception as e:
            print(f"Error rotating cursor: {e}")
    
    def restore_cursors(self):
        """Restore original system cursors"""
        try:
            self.enabled = False
            self.target_cursor = user32.LoadCursorW(None, OCR_NORMAL)
            if self.target_cursor:
                user32.SetCursor(self.target_cursor)
        except Exception as e:
            print(f"Error restoring cursors: {e}")

class MouseRemapper:
    """Optimized mouse remapping for near-native feel"""
    def __init__(self):
        self.enabled = False
        self.current_orientation = DMDO_DEFAULT
        self.screen_width = 0
        self.screen_height = 0
        self.thread = None
        self.running = False
        
        # High-performance tracking
        self.last_physical_x = 0
        self.last_physical_y = 0
        self.ignore_next_read = False
        
        # Pre-allocate POINT structure for better performance
        self.point_struct = POINT()
        
    def set_orientation(self, orientation, width, height):
        """Update the current orientation and screen dimensions"""
        self.current_orientation = orientation
        self.screen_width = width
        self.screen_height = height
        
        # Reset tracking when orientation changes
        user32.GetCursorPos(ctypes.byref(self.point_struct))
        self.last_physical_x = self.point_struct.x
        self.last_physical_y = self.point_struct.y
        self.ignore_next_read = False
    
    def remap_thread(self):
        """Optimized background thread for mouse remapping with minimal latency"""
        # Initialize with current position
        user32.GetCursorPos(ctypes.byref(self.point_struct))
        self.last_physical_x = self.point_struct.x
        self.last_physical_y = self.point_struct.y
        
        # Pre-calculate constants outside loop
        orientation = self.current_orientation
        
        while self.running:
            # Skip processing if not enabled or at default orientation
            if not self.enabled or self.current_orientation == DMDO_DEFAULT:
                time.sleep(0.005)
                # Update orientation reference
                orientation = self.current_orientation
                continue
            
            # Check if orientation changed
            if orientation != self.current_orientation:
                orientation = self.current_orientation
                user32.GetCursorPos(ctypes.byref(self.point_struct))
                self.last_physical_x = self.point_struct.x
                self.last_physical_y = self.point_struct.y
                self.ignore_next_read = False
                continue
            
            # Skip this read if we just moved the cursor
            if self.ignore_next_read:
                user32.GetCursorPos(ctypes.byref(self.point_struct))
                self.last_physical_x = self.point_struct.x
                self.last_physical_y = self.point_struct.y
                self.ignore_next_read = False
                time.sleep(0.0005)  # Minimal sleep after our move
                continue
            
            # Get current cursor position (fast)
            user32.GetCursorPos(ctypes.byref(self.point_struct))
            current_x = self.point_struct.x
            current_y = self.point_struct.y
            
            # Calculate delta (physical mouse movement)
            dx = current_x - self.last_physical_x
            dy = current_y - self.last_physical_y
            
            # Only process if there's actual movement
            if dx != 0 or dy != 0:
                # Transform delta based on orientation (pre-calculated in if-elif chain)
                if orientation == DMDO_90:  # 90° CW
                    transformed_dx = -dy
                    transformed_dy = dx
                elif orientation == DMDO_180:  # 180°
                    transformed_dx = -dx
                    transformed_dy = -dy
                elif orientation == DMDO_270:  # 270° CW (90° CCW)
                    transformed_dx = dy
                    transformed_dy = -dx
                else:
                    transformed_dx = dx
                    transformed_dy = dy
                
                # Calculate new position from last known position
                new_x = self.last_physical_x + transformed_dx
                new_y = self.last_physical_y + transformed_dy
                
                # Clamp to screen bounds (fast min/max)
                if new_x < 0:
                    new_x = 0
                elif new_x >= self.screen_width:
                    new_x = self.screen_width - 1
                    
                if new_y < 0:
                    new_y = 0
                elif new_y >= self.screen_height:
                    new_y = self.screen_height - 1
                
                # Move cursor to new position
                user32.SetCursorPos(new_x, new_y)
                
                # Update last known position to where we moved it
                self.last_physical_x = new_x
                self.last_physical_y = new_y
                
                # Flag to ignore the next read (our own movement)
                self.ignore_next_read = True
            else:
                # No movement detected, minimal sleep
                time.sleep(0.0005)  # 0.5ms sleep when idle
    
    def start(self):
        """Start the mouse remapping with high priority"""
        if self.enabled:
            return
        
        self.enabled = True
        self.running = True
        self.thread = threading.Thread(target=self.remap_thread, daemon=True)
        self.thread.start()
        
        # Boost thread priority for better responsiveness
        try:
            import win32api
            import win32process
            import win32con
            
            # Get thread handle and boost priority
            thread_id = self.thread.ident
            if thread_id:
                # Set to highest non-realtime priority
                handle = win32api.OpenThread(win32con.THREAD_SET_INFORMATION, False, thread_id)
                win32process.SetThreadPriority(handle, win32process.THREAD_PRIORITY_HIGHEST)
                win32api.CloseHandle(handle)
        except ImportError:
            # win32api not available, use ctypes alternative
            try:
                kernel32 = ctypes.windll.kernel32
                thread_handle = kernel32.OpenThread(0x0020, False, self.thread.ident)  # THREAD_SET_INFORMATION
                if thread_handle:
                    # THREAD_PRIORITY_HIGHEST = 2
                    kernel32.SetThreadPriority(thread_handle, 2)
                    kernel32.CloseHandle(thread_handle)
            except:
                pass  # If priority boost fails, continue without it
    
    def stop(self):
        """Stop the mouse remapping"""
        if not self.enabled:
            return
            
        self.running = False
        self.enabled = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None

class KeyboardMonitor:
    """Monitors keyboard for hotkey combinations using polling"""
    def __init__(self, callback):
        self.callback = callback
        self.enabled = False
        self.thread = None
        self.running = False
        
    def is_key_pressed(self, vk_code):
        """Check if a virtual key is currently pressed"""
        return user32.GetAsyncKeyState(vk_code) & 0x8000 != 0
    
    def monitor_thread(self):
        """Background thread that monitors for hotkey combinations"""
        last_combo = None
        combo_time = 0
        
        while self.running:
            ctrl = self.is_key_pressed(VK_CONTROL)
            alt = self.is_key_pressed(VK_MENU)
            
            if ctrl and alt:
                current_time = time.time()
                
                if self.is_key_pressed(VK_UP):
                    combo = 'UP'
                elif self.is_key_pressed(VK_DOWN):
                    combo = 'DOWN'
                elif self.is_key_pressed(VK_LEFT):
                    combo = 'LEFT'
                elif self.is_key_pressed(VK_RIGHT):
                    combo = 'RIGHT'
                else:
                    combo = None
                
                if combo and (combo != last_combo or current_time - combo_time > 0.3):
                    self.callback(combo)
                    last_combo = combo
                    combo_time = current_time
            else:
                last_combo = None
            
            time.sleep(0.05)
    
    def start(self):
        """Start the keyboard monitor"""
        if self.enabled:
            return
        
        self.enabled = True
        self.running = True
        self.thread = threading.Thread(target=self.monitor_thread, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the keyboard monitor"""
        if not self.enabled:
            return
        
        self.running = False
        self.enabled = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None

class ScreenRotator:
    def __init__(self, update_callback=None):
        self.current_orientation = self.get_current_orientation()
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        self.update_callback = update_callback
        self.cursor_rotator = CursorRotator()
        self.cursor_rotation_enabled = True  # Default enabled
        
    def get_current_orientation(self):
        """Get the current screen orientation"""
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        
        if user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            return devmode.dmDisplayOrientation
        return DMDO_DEFAULT
    
    def rotate_screen(self, orientation):
        """Rotate the screen to the specified orientation"""
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        
        if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            return False, "Failed to get current display settings"
        
        current_orientation = devmode.dmDisplayOrientation
        current_width = devmode.dmPelsWidth
        current_height = devmode.dmPelsHeight
        
        if current_orientation in (DMDO_90, DMDO_270):
            native_width = current_height
            native_height = current_width
        else:
            native_width = current_width
            native_height = current_height
        
        devmode.dmDisplayOrientation = orientation
        
        if orientation in (DMDO_90, DMDO_270):
            devmode.dmPelsWidth = native_height
            devmode.dmPelsHeight = native_width
        else:
            devmode.dmPelsWidth = native_width
            devmode.dmPelsHeight = native_height
        
        devmode.dmFields = DM_DISPLAYORIENTATION | DM_PELSWIDTH | DM_PELSHEIGHT
        
        result = user32.ChangeDisplaySettingsW(ctypes.byref(devmode), CDS_UPDATEREGISTRY)
        
        if result == DISP_CHANGE_SUCCESSFUL:
            self.current_orientation = orientation
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
            
            # Rotate cursor to match screen orientation if enabled
            if self.cursor_rotation_enabled:
                self.cursor_rotator.rotate_cursors(orientation)
            
            if self.update_callback:
                self.update_callback()
            
            return True, f"Rotated to {orientation * 90}°"
        else:
            return False, f"Failed to rotate (error {result})"
    
    def get_orientation_string(self):
        """Get a string representation of the current orientation"""
        orientations = {
            DMDO_DEFAULT: "0° (Default)",
            DMDO_90: "90° (Clockwise)",
            DMDO_180: "180° (Upside Down)",
            DMDO_270: "270° (Counter-clockwise)"
        }
        return orientations.get(self.current_orientation, "Unknown")

class AutoStartupManager:
    """Manages Windows auto-startup registry entry"""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "ScreenRotator"
    
    @staticmethod
    def is_enabled():
        """Check if auto-startup is enabled"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutoStartupManager.REG_PATH, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, AutoStartupManager.APP_NAME)
                winreg.CloseKey(key)
                return True
            except WindowsError:
                winreg.CloseKey(key)
                return False
        except WindowsError:
            return False
    
    @staticmethod
    def enable():
        """Enable auto-startup"""
        try:
            # Get the path to the current script
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys.executable
            else:
                # Running as script
                app_path = f'pythonw.exe "{os.path.abspath(__file__)}"'
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutoStartupManager.REG_PATH, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, AutoStartupManager.APP_NAME, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            return True, "Auto-startup enabled"
        except Exception as e:
            return False, f"Failed to enable auto-startup: {e}"
    
    @staticmethod
    def disable():
        """Disable auto-startup"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutoStartupManager.REG_PATH, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, AutoStartupManager.APP_NAME)
            except WindowsError:
                pass
            winreg.CloseKey(key)
            return True, "Auto-startup disabled"
        except Exception as e:
            return False, f"Failed to disable auto-startup: {e}"

class ScreenRotatorGUI:
    def __init__(self, start_minimized=False):
        self.root = tk.Tk()
        self.root.title("Screen Rotator")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        
        # Initialize components
        self.rotator = ScreenRotator(update_callback=self.update_display)
        self.mouse_remapper = MouseRemapper()
        self.keyboard_monitor = KeyboardMonitor(callback=self.handle_hotkey)
        
        self.mouse_remapper.set_orientation(
            self.rotator.current_orientation,
            self.rotator.screen_width,
            self.rotator.screen_height
        )
        
        # System tray icon
        self.tray_icon = None
        
        # Create GUI
        self.create_widgets()
        self.update_display()
        
        # Start all features by default
        self.mouse_remapper.start()
        self.keyboard_monitor.start()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        if start_minimized:
            self.root.after(100, self.minimize_to_tray)
    
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create a simple icon
        def create_image():
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), (255, 255, 255))
            dc = ImageDraw.Draw(image)
            dc.rectangle([10, 10, 54, 54], fill=(50, 150, 250), outline=(0, 0, 0))
            dc.line([20, 32, 44, 32], fill=(255, 255, 255), width=3)
            dc.line([32, 20, 32, 44], fill=(255, 255, 255), width=3)
            return image
        
        menu = pystray.Menu(
            item('Show', self.show_window),
            item('Rotate 0°', lambda: self.rotate_from_tray(DMDO_DEFAULT)),
            item('Rotate 90°', lambda: self.rotate_from_tray(DMDO_90)),
            item('Rotate 180°', lambda: self.rotate_from_tray(DMDO_180)),
            item('Rotate 270°', lambda: self.rotate_from_tray(DMDO_270)),
            pystray.Menu.SEPARATOR,
            item('Exit', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("ScreenRotator", create_image(), "Screen Rotator", menu)
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', pady=10)
        title_frame.pack(fill='x')
        
        title_label = tk.Label(
            title_frame,
            text="Screen Rotator",
            font=('Segoe UI', 16, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack()
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="Status", font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        status_frame.pack(padx=10, pady=10, fill='x')
        
        self.orientation_label = tk.Label(status_frame, text="", font=('Segoe UI', 10))
        self.orientation_label.pack(anchor='w')
        
        self.resolution_label = tk.Label(status_frame, text="", font=('Segoe UI', 10))
        self.resolution_label.pack(anchor='w')
        
        # Rotation Buttons
        rotation_frame = tk.LabelFrame(self.root, text="Quick Rotation", font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        rotation_frame.pack(padx=10, pady=10, fill='x')
        
        btn_frame1 = tk.Frame(rotation_frame)
        btn_frame1.pack(pady=5)
        
        btn_0 = tk.Button(btn_frame1, text="0° Default", width=15, height=2, 
                         command=lambda: self.rotate(DMDO_DEFAULT), font=('Segoe UI', 9))
        btn_0.pack(side='left', padx=5)
        
        btn_90 = tk.Button(btn_frame1, text="90° Clockwise", width=15, height=2,
                          command=lambda: self.rotate(DMDO_90), font=('Segoe UI', 9))
        btn_90.pack(side='left', padx=5)
        
        btn_frame2 = tk.Frame(rotation_frame)
        btn_frame2.pack(pady=5)
        
        btn_180 = tk.Button(btn_frame2, text="180° Upside Down", width=15, height=2,
                           command=lambda: self.rotate(DMDO_180), font=('Segoe UI', 9))
        btn_180.pack(side='left', padx=5)
        
        btn_270 = tk.Button(btn_frame2, text="270° Counter-CW", width=15, height=2,
                           command=lambda: self.rotate(DMDO_270), font=('Segoe UI', 9))
        btn_270.pack(side='left', padx=5)
        
        # Features Frame
        features_frame = tk.LabelFrame(self.root, text="Features", font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        features_frame.pack(padx=10, pady=10, fill='x')
        
        self.mouse_var = tk.BooleanVar(value=True)  # Enabled by default
        mouse_check = tk.Checkbutton(
            features_frame,
            text="Enable Mouse Remapping (natural mouse movement when rotated)",
            variable=self.mouse_var,
            command=self.toggle_mouse_remapping,
            font=('Segoe UI', 9)
        )
        mouse_check.pack(anchor='w', pady=5)
        
        self.hotkey_var = tk.BooleanVar(value=True)  # Enabled by default
        hotkey_check = tk.Checkbutton(
            features_frame,
            text="Enable Keyboard Shortcuts (Ctrl+Alt+Arrow Keys)",
            variable=self.hotkey_var,
            command=self.toggle_keyboard_shortcuts,
            font=('Segoe UI', 9)
        )
        hotkey_check.pack(anchor='w', pady=5)
        
        self.cursor_var = tk.BooleanVar(value=True)  # Already enabled by default
        cursor_check = tk.Checkbutton(
            features_frame,
            text="Rotate Cursor Icon (match cursor to screen orientation)",
            variable=self.cursor_var,
            font=('Segoe UI', 9)
        )
        cursor_check.pack(anchor='w', pady=5)
        
        self.startup_var = tk.BooleanVar(value=AutoStartupManager.is_enabled())
        startup_check = tk.Checkbutton(
            features_frame,
            text="Start with Windows (Auto-startup)",
            variable=self.startup_var,
            command=self.toggle_auto_startup,
            font=('Segoe UI', 9)
        )
        startup_check.pack(anchor='w', pady=5)
        
        # Hotkeys Info
        info_frame = tk.LabelFrame(self.root, text="Keyboard Shortcuts", font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        info_frame.pack(padx=10, pady=10, fill='x')
        
        shortcuts = [
            "Ctrl+Alt+Up    → Rotate to 0°",
            "Ctrl+Alt+Right → Rotate to 90°",
            "Ctrl+Alt+Down  → Rotate to 180°",
            "Ctrl+Alt+Left  → Rotate to 270°"
        ]
        
        for shortcut in shortcuts:
            lbl = tk.Label(info_frame, text=shortcut, font=('Consolas', 9), anchor='w')
            lbl.pack(anchor='w')
        
        # Bottom Buttons
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(padx=10, pady=10, fill='x')
        
        minimize_btn = tk.Button(
            bottom_frame,
            text="Minimize to Tray",
            command=self.minimize_to_tray,
            font=('Segoe UI', 9),
            width=20
        )
        minimize_btn.pack(side='left', padx=5)
        
        exit_btn = tk.Button(
            bottom_frame,
            text="Exit",
            command=self.quit_app,
            font=('Segoe UI', 9),
            width=20
        )
        exit_btn.pack(side='right', padx=5)
    
    def update_display(self):
        """Update the status display"""
        self.orientation_label.config(
            text=f"Current Orientation: {self.rotator.get_orientation_string()}"
        )
        self.resolution_label.config(
            text=f"Screen Resolution: {self.rotator.screen_width}x{self.rotator.screen_height}"
        )
        
        # Update mouse remapper with new dimensions
        self.mouse_remapper.set_orientation(
            self.rotator.current_orientation,
            self.rotator.screen_width,
            self.rotator.screen_height
        )
    
    def rotate(self, orientation):
        """Rotate the screen"""
        # Sync cursor rotation setting
        self.rotator.cursor_rotation_enabled = self.cursor_var.get()
        
        success, message = self.rotator.rotate_screen(orientation)
        if not success:
            messagebox.showerror("Error", message)
    
    def handle_hotkey(self, combo):
        """Handle keyboard hotkey"""
        combo_map = {
            'UP': DMDO_DEFAULT,
            'RIGHT': DMDO_90,
            'DOWN': DMDO_180,
            'LEFT': DMDO_270
        }
        
        if combo in combo_map:
            self.rotator.rotate_screen(combo_map[combo])
    
    def toggle_mouse_remapping(self):
        """Toggle mouse remapping"""
        if self.mouse_var.get():
            self.mouse_remapper.start()
        else:
            self.mouse_remapper.stop()
    
    def toggle_keyboard_shortcuts(self):
        """Toggle keyboard shortcuts"""
        if self.hotkey_var.get():
            self.keyboard_monitor.start()
        else:
            self.keyboard_monitor.stop()
    
    def toggle_auto_startup(self):
        """Toggle auto-startup"""
        if self.startup_var.get():
            success, message = AutoStartupManager.enable()
        else:
            success, message = AutoStartupManager.disable()
        
        if not success:
            messagebox.showerror("Error", message)
            self.startup_var.set(AutoStartupManager.is_enabled())
    
    def minimize_to_tray(self):
        """Minimize window to system tray"""
        self.root.withdraw()
        
        if not self.tray_icon:
            self.create_tray_icon()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def rotate_from_tray(self, orientation):
        """Rotate screen from tray menu"""
        self.rotator.rotate_screen(orientation)
    
    def quit_app(self):
        """Quit the application"""
        self.mouse_remapper.stop()
        self.keyboard_monitor.stop()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    # Check for command line arguments
    start_minimized = '--minimized' in sys.argv or '--startup' in sys.argv
    
    app = ScreenRotatorGUI(start_minimized=start_minimized)
    app.run()

if __name__ == "__main__":
    main()
