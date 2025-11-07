# Screen Rotator

A Windows application to rotate your screen with mouse remapping and keyboard shortcuts.

## Features

✨ **GUI Interface** - Easy-to-use graphical interface  
🖱️ **Mouse Remapping** - Natural mouse movement when screen is rotated  
⌨️ **Keyboard Shortcuts** - Quick rotation with Ctrl+Alt+Arrow keys  
🔔 **System Tray** - Minimize to system tray for background operation  
🚀 **Auto-Startup** - Start automatically with Windows  
🎯 **Quick Rotation** - One-click rotation to any angle (0°, 90°, 180°, 270°)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the GUI application:
```bash
python app_gui.py
```

**Note:** The application requires administrator privileges to rotate the screen.

## Usage

### GUI Mode

Run the GUI application:
```bash
python app_gui.py
```

#### Features:
- **Quick Rotation Buttons**: Click to rotate to any angle
- **Mouse Remapping**: Enable to make mouse movements feel natural when rotated
- **Keyboard Shortcuts**: Enable to use Ctrl+Alt+Arrow keys for quick rotation
- **Auto-Startup**: Enable to start the app automatically with Windows
- **System Tray**: Minimize to tray and rotate from the tray icon menu

### Console Mode

Run the console application:
```bash
python app.py
```

## Keyboard Shortcuts

When enabled, use these shortcuts from anywhere:

- `Ctrl+Alt+Up` → Rotate to 0° (Default/Normal)
- `Ctrl+Alt+Right` → Rotate to 90° (Clockwise)
- `Ctrl+Alt+Down` → Rotate to 180° (Upside Down)
- `Ctrl+Alt+Left` → Rotate to 270° (Counter-clockwise)

## System Tray

When minimized to tray, you can:
- Right-click the tray icon to access rotation options
- Quickly rotate without opening the main window
- Exit the application

## Auto-Startup

Enable "Start with Windows" to have the app:
- Start automatically when you log in
- Start minimized to system tray
- Run in the background with hotkeys ready

## Requirements

- Windows 10/11
- Python 3.7+
- Administrator privileges (for screen rotation)

## Dependencies

- `pillow` - For system tray icon
- `pystray` - For system tray functionality
- `tkinter` - For GUI (included with Python)

## Troubleshooting

### Screen rotation not working
- Make sure you're running the application as Administrator
- Some displays don't support rotation - check your display settings

### Keyboard shortcuts not working
- Make sure the shortcuts feature is enabled
- Keep the application running in the background

### Mouse remapping feels wrong
- Mouse remapping only works when screen is actually rotated
- At 0°, mouse movements are normal (no transformation needed)

## License

MIT License - Feel free to use and modify!
