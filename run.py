import sys
import os
import subprocess
import ctypes

def is_running_as_exe():
    """Check if running as a PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def hide_console():
    """Hide the console window."""
    try:
        if sys.platform == 'win32' and not is_running_as_exe():
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            
            # Get console window handle
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                # Hide the console window
                user32.ShowWindow(console_window, 0)  # 0 = SW_HIDE
    except Exception:
        pass

def main():
    try:
        # Get the base directory of the project
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add the project directory to the Python path
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        # Hide console window if not running as exe
        hide_console()
        
        # Import and run the application
        from clipboard_refresher.main import main as app_main
        app_main()
        
    except Exception as e:
        # Log the error
        error_log = os.path.join(os.path.expanduser('~'), '.clipboard_refresher', 'error.log')
        os.makedirs(os.path.dirname(error_log), exist_ok=True)
        with open(error_log, 'a') as f:
            import traceback
            traceback.print_exc(file=f)
            f.write('\n' + '='*50 + '\n')
        
        # Show error in a message box
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, 
                f"An error occurred. Please check the error log at:\n{error_log}", 
                "Clipboard Refresher Error", 
                0x10  # MB_ICONERROR
            )
        except:
            pass

if __name__ == "__main__":
    main()
