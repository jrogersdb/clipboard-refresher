import sys
import os
import subprocess

def is_running_as_exe():
    """Check if running as a PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def main():
    # Determine the path to the Python interpreter
    python_exe = sys.executable
    
    # Get the path to the main script
    if is_running_as_exe():
        # If running as an executable, use the directory containing the executable
        script_dir = os.path.dirname(sys.executable)
        script_path = os.path.join(script_dir, 'clipboard_refresher', 'main.py')
    else:
        # If running from source, use the source directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'clipboard_refresher', 'main.py')
    
    # Run the script with pythonw.exe to avoid console window
    subprocess.Popen([python_exe, script_path], 
                    creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    main()
