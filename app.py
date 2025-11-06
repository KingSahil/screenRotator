"""
Screen Rotator Application
Rotates the screen while preserving correct mouse movement by adjusting coordinates
based on the current screen orientation.
"""

import ctypes
from ctypes import wintypes
import time
import threading
import atexit
import msvcrt
import sys

# Constants for display orientation
DMDO_DEFAULT = 0  # 0 degrees
DMDO_90 = 1       # 90 degrees
DMDO_180 = 2      # 180 degrees
DMDO_270 = 3      # 270 degrees

# Mouse hook constants
WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
HC_ACTION = 0

# Keyboard hook constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

# Virtual key codes
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key

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

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.LPVOID)
    ]

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.LPVOID)
    ]

# Windows API functions
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Constants
ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x01
DISP_CHANGE_SUCCESSFUL = 0
DM_DISPLAYORIENTATION = 0x00000080
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000

class MouseRemapper:
    """
    Simpler mouse remapping using input redirection
    This approach transforms mouse sensitivity rather than hooking events
    """
    def __init__(self):
        self.enabled = False
        self.current_orientation = DMDO_DEFAULT
        self.screen_width = 0
        self.screen_height = 0
        self.thread = None
        self.running = False
        
    def set_orientation(self, orientation, width, height):
        """Update the current orientation and screen dimensions"""
        self.current_orientation = orientation
        self.screen_width = width
        self.screen_height = height
        
    def transform_coordinates(self, x, y):
        """Transform coordinates based on screen orientation"""
        if self.current_orientation == DMDO_DEFAULT:  # 0°
            return x, y
        elif self.current_orientation == DMDO_90:  # 90°
            # Rotate coordinates 90° clockwise
            return self.screen_height - y, x
        elif self.current_orientation == DMDO_180:  # 180°
            return self.screen_width - x, self.screen_height - y
        elif self.current_orientation == DMDO_270:  # 270°
            return y, self.screen_width - x
        return x, y
    
    def remap_thread(self):
        """Background thread that monitors and adjusts mouse position"""
        last_pos = POINT()
        user32.GetCursorPos(ctypes.byref(last_pos))
        
        while self.running:
            if self.current_orientation == DMDO_DEFAULT:
                # No remapping needed at 0°
                time.sleep(0.01)
                continue
                
            current_pos = POINT()
            user32.GetCursorPos(ctypes.byref(current_pos))
            
            # Calculate movement delta
            dx = current_pos.x - last_pos.x
            dy = current_pos.y - last_pos.y
            
            if dx != 0 or dy != 0:
                # Transform the delta based on orientation
                if self.current_orientation == DMDO_90:  # 90°
                    new_dx, new_dy = -dy, dx
                elif self.current_orientation == DMDO_180:  # 180°
                    new_dx, new_dy = -dx, -dy
                elif self.current_orientation == DMDO_270:  # 270°
                    new_dx, new_dy = dy, -dx
                else:
                    new_dx, new_dy = dx, dy
                
                # Calculate new position
                new_x = last_pos.x + new_dx
                new_y = last_pos.y + new_dy
                
                # Clamp to screen bounds
                new_x = max(0, min(self.screen_width - 1, new_x))
                new_y = max(0, min(self.screen_height - 1, new_y))
                
                # Set cursor to new position
                user32.SetCursorPos(new_x, new_y)
                
                # Update last position
                last_pos.x = new_x
                last_pos.y = new_y
            
            time.sleep(0.001)  # Poll every 1ms for smooth movement
    
    def start(self):
        """Start the mouse remapping"""
        if self.enabled:
            print("Mouse remapping is already enabled")
            return
        
        self.enabled = True
        self.running = True
        self.thread = threading.Thread(target=self.remap_thread, daemon=True)
        self.thread.start()
        print("✓ Mouse remapping enabled - movements now follow screen rotation")
        if self.current_orientation == DMDO_DEFAULT:
            print("  (Currently at 0° - no transformation needed)")
    
    def stop(self):
        """Stop the mouse remapping"""
        if not self.enabled:
            return
            
        self.running = False
        self.enabled = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None
        print("✓ Mouse remapping disabled")

# Global mouse remapper instance
mouse_remapper = MouseRemapper()

class KeyboardMonitor:
    """Monitors keyboard for hotkey combinations using polling"""
    def __init__(self, rotator):
        self.rotator = rotator
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
            # Check if Ctrl and Alt are pressed
            ctrl = self.is_key_pressed(VK_CONTROL)
            alt = self.is_key_pressed(VK_MENU)
            
            if ctrl and alt:
                current_time = time.time()
                
                # Check arrow keys
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
                
                # Execute action if combo changed and debounce (0.3s)
                if combo and (combo != last_combo or current_time - combo_time > 0.3):
                    if combo == 'UP':
                        print("\n[Hotkey] Ctrl+Alt+Up - Rotating to 0° (Default)")
                        self.rotator.rotate_screen(DMDO_DEFAULT)
                    elif combo == 'DOWN':
                        print("\n[Hotkey] Ctrl+Alt+Down - Rotating to 180°")
                        self.rotator.rotate_screen(DMDO_180)
                    elif combo == 'LEFT':
                        print("\n[Hotkey] Ctrl+Alt+Left - Rotating to 270°")
                        self.rotator.rotate_screen(DMDO_270)
                    elif combo == 'RIGHT':
                        print("\n[Hotkey] Ctrl+Alt+Right - Rotating to 90°")
                        self.rotator.rotate_screen(DMDO_90)
                    
                    last_combo = combo
                    combo_time = current_time
            else:
                last_combo = None
            
            time.sleep(0.05)  # Check every 50ms
    
    def start(self):
        """Start the keyboard monitor"""
        if self.enabled:
            print("Keyboard shortcuts are already enabled")
            return True
        
        self.enabled = True
        self.running = True
        self.thread = threading.Thread(target=self.monitor_thread, daemon=True)
        self.thread.start()
        print("✓ Keyboard shortcuts enabled:")
        print("  Ctrl+Alt+Up    → Rotate to 0° (Default)")
        print("  Ctrl+Alt+Right → Rotate to 90°")
        print("  Ctrl+Alt+Down  → Rotate to 180°")
        print("  Ctrl+Alt+Left  → Rotate to 270°")
        return True
    
    def stop(self):
        """Stop the keyboard monitor"""
        if not self.enabled:
            return
        
        self.running = False
        self.enabled = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None
        print("✓ Keyboard shortcuts disabled")

# Global keyboard monitor instance (will be initialized in main)
keyboard_monitor = None

class ScreenRotator:
    def __init__(self):
        self.current_orientation = self.get_current_orientation()
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        # Update mouse remapper with current orientation
        mouse_remapper.set_orientation(self.current_orientation, self.screen_width, self.screen_height)
        
    def get_current_orientation(self):
        """Get the current screen orientation"""
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        
        if user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            return devmode.dmDisplayOrientation
        return DMDO_DEFAULT
    
    def rotate_screen(self, orientation):
        """
        Rotate the screen to the specified orientation
        orientation: 0 (0°), 1 (90°), 2 (180°), 3 (270°)
        """
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        
        if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            print("Failed to get current display settings")
            return False
        
        # Get the native (non-rotated) dimensions
        # If currently rotated 90° or 270°, width/height are already swapped
        current_orientation = devmode.dmDisplayOrientation
        current_width = devmode.dmPelsWidth
        current_height = devmode.dmPelsHeight
        
        # Determine native dimensions (as if at 0°)
        if current_orientation in (DMDO_90, DMDO_270):
            native_width = current_height
            native_height = current_width
        else:
            native_width = current_width
            native_height = current_height
        
        # Set the orientation
        devmode.dmDisplayOrientation = orientation
        
        # Set width and height based on target orientation
        if orientation in (DMDO_90, DMDO_270):
            devmode.dmPelsWidth = native_height
            devmode.dmPelsHeight = native_width
        else:
            devmode.dmPelsWidth = native_width
            devmode.dmPelsHeight = native_height
        
        # Set flags to indicate which fields are being changed
        devmode.dmFields = DM_DISPLAYORIENTATION | DM_PELSWIDTH | DM_PELSHEIGHT
        
        # Apply the changes
        result = user32.ChangeDisplaySettingsW(ctypes.byref(devmode), CDS_UPDATEREGISTRY)
        
        if result == DISP_CHANGE_SUCCESSFUL:
            print(f"✓ Screen rotated successfully to {orientation * 90}°")
            self.current_orientation = orientation
            # Update screen dimensions
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
            print(f"  New resolution: {self.screen_width}x{self.screen_height}")
            # Update mouse remapper
            mouse_remapper.set_orientation(orientation, self.screen_width, self.screen_height)
            return True
        else:
            error_messages = {
                -1: "DISP_CHANGE_RESTART - Restart required",
                -2: "DISP_CHANGE_BADMODE - Invalid display mode",
                -3: "DISP_CHANGE_FAILED - Display driver failed",
                -4: "DISP_CHANGE_BADPARAM - Invalid parameter",
                -5: "DISP_CHANGE_BADFLAGS - Invalid flags"
            }
            error_msg = error_messages.get(result, f"Unknown error ({result})")
            print(f"✗ Failed to rotate screen: {error_msg}")
            print(f"  Attempted: {devmode.dmPelsWidth}x{devmode.dmPelsHeight} @ {orientation * 90}°")
            return False
    
    def rotate_clockwise(self):
        """Rotate the screen 90 degrees clockwise"""
        new_orientation = (self.current_orientation + 1) % 4
        return self.rotate_screen(new_orientation)
    
    def rotate_counterclockwise(self):
        """Rotate the screen 90 degrees counterclockwise"""
        new_orientation = (self.current_orientation - 1) % 4
        return self.rotate_screen(new_orientation)
    
    def rotate_to_default(self):
        """Rotate the screen to default (0°) orientation"""
        return self.rotate_screen(DMDO_DEFAULT)
    
    def get_orientation_string(self):
        """Get a string representation of the current orientation"""
        orientations = {
            DMDO_DEFAULT: "0° (Default)",
            DMDO_90: "90° (Clockwise)",
            DMDO_180: "180° (Upside Down)",
            DMDO_270: "270° (Counter-clockwise)"
        }
        return orientations.get(self.current_orientation, "Unknown")
    
    def get_screen_info(self):
        """Get current screen information"""
        return {
            'width': self.screen_width,
            'height': self.screen_height,
            'orientation': self.current_orientation,
            'orientation_degrees': self.current_orientation * 90,
            'orientation_string': self.get_orientation_string()
        }


def print_menu():
    """Display the menu options"""
    mouse_status = "ENABLED ✓" if mouse_remapper.enabled else "DISABLED ✗"
    hotkey_status = "ENABLED ✓" if keyboard_monitor and keyboard_monitor.enabled else "DISABLED ✗"
    print("\n" + "="*50)
    print("Screen Rotator - With Mouse Remapping & Hotkeys")
    print("="*50)
    print(f"Mouse Remapping: {mouse_status}")
    print(f"Keyboard Hotkeys: {hotkey_status}")
    print("="*50)
    print("1. Rotate Clockwise (90°)")
    print("2. Rotate Counter-clockwise (90°)")
    print("3. Rotate to 0° (Default)")
    print("4. Rotate to 90°")
    print("5. Rotate to 180°")
    print("6. Rotate to 270°")
    print("7. Show Current Screen Info")
    print("8. Toggle Mouse Remapping")
    print("9. Toggle Keyboard Shortcuts")
    print("0. Exit")
    print("="*50)


def main():
    """Main function to run the screen rotator application"""
    global keyboard_monitor
    
    print("Initializing Screen Rotator...")
    
    # Register cleanup on exit
    def cleanup():
        mouse_remapper.stop()
        if keyboard_monitor:
            keyboard_monitor.stop()
    
    atexit.register(cleanup)
    
    try:
        rotator = ScreenRotator()
        keyboard_monitor = KeyboardMonitor(rotator)
        
        print(f"Current orientation: {rotator.get_orientation_string()}")
        print(f"Screen resolution: {rotator.screen_width}x{rotator.screen_height}")
        print("\nTips:")
        print("• Enable mouse remapping (option 8) to make mouse movements")
        print("  feel natural when the screen is rotated!")
        print("• Enable keyboard shortcuts (option 9) for quick rotation with")
        print("  Ctrl+Alt+Arrow keys!")
        
        while True:
            print_menu()
            choice = input("\nEnter your choice (0-9): ").strip()
            
            if choice == '1':
                print("\nRotating clockwise...")
                rotator.rotate_clockwise()
                
            elif choice == '2':
                print("\nRotating counter-clockwise...")
                rotator.rotate_counterclockwise()
                
            elif choice == '3':
                print("\nRotating to default (0°)...")
                rotator.rotate_to_default()
                
            elif choice == '4':
                print("\nRotating to 90°...")
                rotator.rotate_screen(DMDO_90)
                
            elif choice == '5':
                print("\nRotating to 180°...")
                rotator.rotate_screen(DMDO_180)
                
            elif choice == '6':
                print("\nRotating to 270°...")
                rotator.rotate_screen(DMDO_270)
                
            elif choice == '7':
                info = rotator.get_screen_info()
                print("\n" + "-"*50)
                print("Current Screen Information:")
                print("-"*50)
                print(f"Width: {info['width']}px")
                print(f"Height: {info['height']}px")
                print(f"Orientation: {info['orientation_string']}")
                print(f"Orientation Value: {info['orientation']}")
                print(f"Degrees: {info['orientation_degrees']}°")
                print(f"Mouse Remapping: {'ENABLED' if mouse_remapper.enabled else 'DISABLED'}")
                print(f"Keyboard Shortcuts: {'ENABLED' if keyboard_monitor.enabled else 'DISABLED'}")
                print("-"*50)
                
            elif choice == '8':
                if mouse_remapper.enabled:
                    mouse_remapper.stop()
                else:
                    mouse_remapper.start()
                    if mouse_remapper.enabled:
                        print("\nNote: Mouse remapping works best when screen is rotated.")
                        print("      At 0°, movements are unchanged.")
                
            elif choice == '9':
                if keyboard_monitor.enabled:
                    keyboard_monitor.stop()
                else:
                    keyboard_monitor.start()
                    
            elif choice == '0':
                print("\nExiting Screen Rotator. Goodbye!")
                cleanup()
                break
                
            else:
                print("\nInvalid choice. Please enter a number between 0 and 9.")
            
            time.sleep(0.3)  # Small delay for better user experience
    
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting...")
        cleanup()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        cleanup()


if __name__ == "__main__":
    print("Note: This application requires administrator privileges to rotate the screen.")
    print("Please run this script as administrator.\n")
    main()
