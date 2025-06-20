import win32clipboard
import win32process
import win32gui
import win32con
import win32api  # Added missing import
import pywintypes  # For Windows-specific exceptions
import logging
import time
from typing import Optional, Callable, Any
import threading

# List of RDP-related process names to monitor
RDP_PROCESSES = {
    'mstsc.exe',    # Windows Remote Desktop
    'msrdc.exe',    # Microsoft Remote Desktop (newer version)
    'mremoteng.exe', # mRemoteNG
    '1remote.exe',   # 1Remote
    'rdpclip.exe',   # RDP Clipboard Monitor
}

class ClipboardMonitor:
    def __init__(self, on_rdp_clipboard_update: Optional[Callable[[str], None]] = None):
        """
        Initialize the clipboard monitor.
        
        Args:
            on_rdp_clipboard_update: Callback function that will be called when
                                   clipboard content is updated by an RDP process.
        """
        self.logger = logging.getLogger(__name__)
        self.on_rdp_clipboard_update = on_rdp_clipboard_update
        self.last_clipboard_content = ""
        self.running = False
        self.thread = None
        self.enabled = True
        self.clipboard_sequence = 0
        self.last_window = None

    def _get_clipboard_content(self) -> Optional[str]:
        """Get the current clipboard content as text."""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return content if content else None
            return None
        except Exception as e:
            self.logger.error(f"Error getting clipboard content: {e}")
            return None
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

    def _get_process_name(self, hwnd: int) -> Optional[str]:
        """Get the process name from a window handle."""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = win32process.GetModuleFileNameEx(
                win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid),
                None
            )
            return process.split('\\')[-1].lower()
        except Exception as e:
            self.logger.debug(f"Could not get process name: {e}")
            return None

    def _get_foreground_window_process(self) -> Optional[str]:
        """Get the name of the process that owns the foreground window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return self._get_process_name(hwnd)
        except Exception as e:
            self.logger.debug(f"Could not get foreground window process: {e}")
            return None

    def _monitor_clipboard(self):
        """Monitor clipboard for changes in a loop."""
        self.logger.info("Clipboard monitor started")
        last_sequence = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                # Get the current clipboard sequence number with retry logic
                current_sequence = None
                for attempt in range(3):  # Try up to 3 times
                    try:
                        win32clipboard.OpenClipboard()
                        current_sequence = win32clipboard.GetClipboardSequenceNumber()
                        win32clipboard.CloseClipboard()
                        consecutive_errors = 0  # Reset on successful operation
                        break
                    except pywintypes.error as e:
                        if e.winerror == 5:  # Access Denied
                            self.logger.debug("Clipboard is busy, waiting...")
                            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                            if attempt == 2:  # Last attempt
                                raise
                        else:
                            raise
                
                if current_sequence is None:
                    continue  # Skip this iteration if we couldn't get the sequence
                
                # Check if clipboard content has changed
                if current_sequence != last_sequence and self.enabled:
                    last_sequence = current_sequence
                    content = self._get_clipboard_content()
                    
                    if content is not None and content != self.last_clipboard_content:
                        # Get the process that owns the foreground window
                        process_name = self._get_foreground_window_process()
                        
                        if process_name and process_name.lower() in RDP_PROCESSES:
                            self.logger.debug(f"Clipboard updated by RDP process: {process_name}")
                            self.last_clipboard_content = content
                            
                            if self.on_rdp_clipboard_update:
                                try:
                                    self.on_rdp_clipboard_update(content)
                                except Exception as e:
                                    self.logger.error(f"Error in clipboard update callback: {e}")
                        else:
                            self.logger.debug(f"Clipboard updated by non-RDP process: {process_name}")
                            self.last_clipboard_content = content
                    elif content is not None:
                        self.logger.debug("Clipboard content hasn't changed")
                
                # Small delay to prevent high CPU usage
                time.sleep(0.1)
                
            except pywintypes.error as e:
                consecutive_errors += 1
                if e.winerror == 5:  # Access Denied
                    if consecutive_errors % 10 == 0:  # Log every 10th error to avoid log spam
                        self.logger.debug("Clipboard is busy (access denied), will retry...")
                else:
                    self.logger.error(f"Windows error in clipboard monitor: {e}")
                
                if consecutive_errors > max_consecutive_errors:
                    self.logger.warning("Too many consecutive errors, pausing monitor...")
                    time.sleep(5)  # Longer pause if we're having persistent issues
                else:
                    time.sleep(0.5)  # Shorter pause for transient errors
                    
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Unexpected error in clipboard monitor: {e}")
                time.sleep(1)  # Prevent tight loop on error
                
                if consecutive_errors > max_consecutive_errors:
                    self.logger.warning("Too many consecutive errors, pausing monitor...")
                    time.sleep(5)  # Longer pause if we're having persistent issues

    def start(self):
        """Start the clipboard monitoring thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        self.thread.start()
        self.logger.info("Clipboard monitor started")

    def stop(self):
        """Stop the clipboard monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("Clipboard monitor stopped")

    def set_enabled(self, enabled: bool):
        """Enable or disable clipboard monitoring."""
        self.enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"Clipboard monitoring {status}")
