import sys
import os
import logging
import ctypes
import time
from typing import Optional
from .clipboard_monitor import ClipboardMonitor
from .tray_icon import TrayIcon

# Configure logging
def setup_logging():
    """Configure logging to both file and console."""
    try:
        # Get the directory where the executable or script is located
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            log_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            log_dir = os.path.dirname(os.path.abspath(__file__))
            
        log_file = os.path.join(log_dir, 'clipboard_refresher.log')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatters and add it to the handlers
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Get the root logger and add the handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to avoid duplicate messages
        root_logger.handlers = []
        
        # Add the handlers to the logger
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Log a test message
        logging.info("Logging initialized successfully")
        logging.info(f"Log file location: {log_file}")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise

class ClipboardRefresher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clipboard_monitor = None
        self.tray_icon = None
        self.running = False

    def on_clipboard_update(self, content: str):
        """Handle clipboard updates from RDP processes."""
        try:
            self.logger.info(f"Processing RDP clipboard content: {content[:100]}...")
            
            # Log the original content
            self.tray_icon.log(f"RDP clipboard content: {content[:200]}...")
            
            # Re-copy the content back to the clipboard to ensure it's available to clipboard history
            import win32clipboard
            import win32con
            
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(content, win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                self.logger.debug("Successfully updated clipboard with processed content")
            except Exception as e:
                self.logger.error(f"Failed to update clipboard: {e}")
                # Try to close clipboard if it's still open
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error processing clipboard content: {e}")

    def on_toggle_monitoring(self, enabled: bool):
        """Handle monitoring toggle from the tray icon."""
        if self.clipboard_monitor:
            self.clipboard_monitor.set_enabled(enabled)

    def on_quit(self):
        """Handle application quit."""
        self.logger.info("Shutting down...")
        self.running = False
        
        try:
            # Stop the clipboard monitor
            if self.clipboard_monitor:
                self.clipboard_monitor.stop()
                self.clipboard_monitor = None
            
            # Stop the tray icon
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
            
            self.logger.info("Application stopped")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            
        # Use os._exit() instead of sys.exit() to avoid the SystemExit exception
        os._exit(0)

    def run(self):
        """Run the application."""
        self.running = True
        
        try:
            # Setup logging
            setup_logging()
            self.logger.info("Starting Clipboard Refresher")
            
            # Initialize clipboard monitor
            self.clipboard_monitor = ClipboardMonitor(on_rdp_clipboard_update=self.on_clipboard_update)
            
            # Initialize tray icon
            self.tray_icon = TrayIcon(
                on_quit=self.on_quit,
                on_toggle=self.on_toggle_monitoring
            )
            
            # Start tray icon in a separate thread
            import threading
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            self.logger.info("Application started successfully")
            
            # Start clipboard monitoring on the main thread
            self.clipboard_monitor.start()
            
            # Keep the main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested by user (Ctrl+C)")
                self.on_quit()
                
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            if self.tray_icon:
                self.tray_icon.log(f"Fatal error: {e}", level="ERROR")
            self.on_quit()

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """Main entry point for the application."""
    try:
        print("Starting Clipboard Refresher...")
        
        # Skip admin check and run directly
        print("Running without administrator privileges.")
        
        # Create and run the application
        print("Initializing application...")
        app = ClipboardRefresher()
        print("Starting application...")
        app.run()
        
    except Exception as e:
        import traceback
        error_msg = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # Try to log the error to a file
        try:
            log_dir = os.path.join(os.path.expanduser('~'), '.clipboard_refresher')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, 'error.log'), 'w') as f:
                f.write(error_msg)
            print(f"Error details written to: {os.path.join(log_dir, 'error.log')}")
        except Exception as log_err:
            print(f"Could not write error log: {log_err}")
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
