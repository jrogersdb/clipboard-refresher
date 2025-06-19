# Clipboard Refresher

A Windows system tray application that monitors clipboard activity from Remote Desktop (RDP) sessions and performs custom actions when clipboard updates are detected from RDP processes.

## Features

- Runs in the system tray for easy access
- Monitors clipboard activity from RDP-related processes
- Logs all detected clipboard activity
- Toggle monitoring on/off from the system tray menu
- View debug logs from the system tray
- Lightweight and runs in the background

## Installation

1. Ensure you have Python 3.7 or higher installed
2. Clone this repository or download the source code
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application with administrator privileges (required for clipboard access):

```bash
python -m clipboard_refresher.main
```

The application will start and appear in your system tray. Right-click the icon to access the menu.

### System Tray Menu Options

- **Enable/Disable Monitoring**: Toggle clipboard monitoring on or off
- **Show Log**: View the debug log in a separate window
- **Exit**: Close the application

## Configuration

The application logs to `%USERPROFILE%\.clipboard_refresher\clipboard_refresher.log`.

## Supported RDP Processes

The application monitors clipboard activity from the following processes:

- `mstsc.exe` (Windows Remote Desktop)
- `msrdc.exe` (Microsoft Remote Desktop - newer version)
- `mremoteng.exe` (mRemoteNG)
- `1remote.exe` (1Remote)
- `rdpclip.exe` (RDP Clipboard Monitor)

## Customization

You can modify the `on_clipboard_update` method in `main.py` to add custom processing for clipboard content from RDP sessions.

## Requirements

- Windows 7 or later
- Python 3.7+
- See `requirements.txt` for Python package dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
