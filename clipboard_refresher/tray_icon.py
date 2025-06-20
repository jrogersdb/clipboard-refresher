import pystray
from PIL import Image, ImageDraw
import logging
import threading
import io
import sys
import tkinter as tk
from tkinter import scrolledtext
from typing import Optional, Callable, Any

class TrayIcon:
    def __init__(self, on_quit: Callable[[], None], on_toggle: Callable[[bool], None]):
        """
        Initialize the system tray icon.
        
        Args:
            on_quit: Callback function to call when the user selects Exit
            on_toggle: Callback function to call when the user toggles monitoring
        """
        self.logger = logging.getLogger(__name__)
        self.on_quit = on_quit
        self.on_toggle = on_toggle
        self.enabled = True
        self.log_messages = []
        self.max_log_entries = 100
        self.icon = None
        self.menu = None
        self.log_lock = threading.Lock()
        self._create_menu()

    def _create_menu(self):
        """Create the system tray menu."""
        # Create a toggle item that will update its text based on state
        self.toggle_item = pystray.MenuItem(
            'Disable Monitoring',
            self._toggle_monitoring
        )
        
        self.menu = pystray.Menu(
            self.toggle_item,
            pystray.MenuItem('Show Log', self._show_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self._on_quit)
        )

    def _create_image(self, width=64, height=64, color1='#4CAF50', color2='#45a049'):
        """Create a simple icon for the system tray."""
        # Generate an image with a colored square and a clipboard icon
        image = Image.new('RGB', (width, height), '#ffffff00')
        dc = ImageDraw.Draw(image)
        
        # Draw a clipboard shape
        # Main clipboard body
        dc.rectangle([width//4, height//8, 3*width//4, 7*height//8], fill=color1, outline='black', width=2)
        # Clipboard top
        dc.rectangle([width//3, height//16, 2*width//3, height//8], fill=color2, outline='black', width=2)
        
        return image

    def _create_menu(self):
        """Create the system tray menu."""
        # Create a toggle item with the current state
        toggle_text = 'Disable Monitoring' if self.enabled else 'Enable Monitoring'
        self.toggle_item = pystray.MenuItem(
            toggle_text,
            self._toggle_monitoring
        )
        
        self.menu = pystray.Menu(
            self.toggle_item,
            pystray.MenuItem('Show Log', self._show_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self._on_quit)
        )
        
        # Update the icon menu if it exists
        if hasattr(self, 'icon') and self.icon is not None:
            self.icon.menu = self.menu

    def _toggle_monitoring(self, icon, item):
        """Toggle monitoring state."""
        self.enabled = not self.enabled
        self.on_toggle(self.enabled)
        
        # Recreate the menu with the updated toggle text
        self._create_menu()
        
        # Update the icon to reflect the state
        if self.icon is not None:
            self.icon.update_menu()
        
        self.log(f"Monitoring {'enabled' if self.enabled else 'disabled'}")

    def _show_log(self, icon, item):
        """Display the log messages in a simple dialog."""
        
        # Create the window if it doesn't exist or is closed
        if not hasattr(self, '_log_window') or not self._log_window.winfo_exists():
            self._log_window = tk.Toplevel()
            self._log_window.title("Clipboard Refresher - Debug Log")
            self._log_window.geometry("700x500")
            
            # Create a frame for the buttons
            button_frame = tk.Frame(self._log_window)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Add a refresh button
            refresh_btn = tk.Button(button_frame, text="Refresh", command=self._update_log_window)
            refresh_btn.pack(side=tk.LEFT, padx=5)
            
            # Add a clear button
            clear_btn = tk.Button(button_frame, text="Clear", command=self._clear_logs)
            clear_btn.pack(side=tk.LEFT, padx=5)
            
            # Add a close button
            close_btn = tk.Button(button_frame, text="Close", command=self._close_log_window)
            close_btn.pack(side=tk.RIGHT, padx=5)
            
            # Create a scrolled text widget
            self._log_text_area = scrolledtext.ScrolledText(
                self._log_window, 
                wrap=tk.WORD, 
                width=80, 
                height=25,
                font=('Consolas', 9)  # Use a monospace font for better alignment
            )
            self._log_text_area.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
            
            # Configure tags for different log levels
            self._log_text_area.tag_configure('normal', font=('Consolas', 9))
            self._log_text_area.tag_configure('error', foreground='red')
            self._log_text_area.tag_configure('warning', foreground='orange')
            
            # Handle window close
            self._log_window.protocol("WM_DELETE_WINDOW", self._close_log_window)
            
            # Initial update of the log content
            self._update_log_window()
        else:
            # If window exists, bring it to front
            self._log_window.lift()
            self._log_window.focus_force()
    
    def _close_log_window(self):
        """Safely close the log window."""
        if hasattr(self, '_log_window') and self._log_window.winfo_exists():
            self._log_window.destroy()
            # Don't destroy the root window here, as we need it for future log windows
    
    def _clear_logs(self):
        """Clear all log messages."""
        with self.log_lock:
            self.log_messages = []
        self._update_log_window()

    def _on_quit(self, icon, item):
        """Handle quit action from the menu."""
        self.log("Exiting application...")
        if self.icon is not None:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()

    def log(self, message: str, level: str = "INFO"):
        """Add a message to the log."""
        # Format the timestamp for the log message
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (timestamp, level, message)
        
        with self.log_lock:
            self.log_messages.append(log_entry)
            # Keep only the most recent log messages
            if len(self.log_messages) > self.max_log_entries:
                self.log_messages = self.log_messages[-self.max_log_entries:]
        
        # Also log to the console
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Print to console for debugging
        print(f"[{timestamp}] [{level}] {message}")
        
        # Update the log window if it's open
        self._update_log_window()
        
    def _update_log_window(self):
        """Update the log window with current messages."""
        if hasattr(self, '_log_window') and self._log_window.winfo_exists():
            try:
                text_area = self._log_text_area
                text_area.config(state=tk.NORMAL)
                text_area.delete(1.0, tk.END)
                
                with self.log_lock:
                    for timestamp, level, message in self.log_messages:
                        if level == "ERROR":
                            text_area.tag_config('error', foreground='red')
                            text_area.insert(tk.END, f"[{timestamp}] ", 'normal')
                            text_area.insert(tk.END, f"[{level}] ", 'error')
                            text_area.insert(tk.END, f"{message}\n", 'normal')
                        elif level == "WARNING":
                            text_area.tag_config('warning', foreground='orange')
                            text_area.insert(tk.END, f"[{timestamp}] ", 'normal')
                            text_area.insert(tk.END, f"[{level}] ", 'warning')
                            text_area.insert(tk.END, f"{message}\n", 'normal')
                        else:
                            text_area.insert(tk.END, f"[{timestamp}] [{level}] {message}\n", 'normal')
                
                text_area.see(tk.END)
                text_area.config(state=tk.DISABLED)
            except Exception as e:
                self.logger.error(f"Error updating log window: {e}")

    def run(self):
        """Start the system tray icon."""
        # Create an image for the icon
        image = self._create_image()
        
        # Create the icon
        self.icon = pystray.Icon(
            "clipboard_refresher",
            image,
            "Clipboard Refresher",
            menu=self.menu
        )
        
        # Start the icon in a separate thread
        import threading
        def run_icon():
            self.icon.run()
        
        icon_thread = threading.Thread(target=run_icon, daemon=True)
        icon_thread.start()
        
        self.log("Application started")
        
        # Start the Tkinter main loop in the main thread
        self._root = tk.Tk()
        self._root.withdraw()  # Hide the root window
        self._root.mainloop()

    def stop(self):
        """Stop the system tray icon and clean up resources."""
        self.log("Stopping tray icon...")
        
        try:
            # Clean up Tkinter windows first
            if hasattr(self, '_log_window') and hasattr(self._log_window, 'winfo_exists') and self._log_window.winfo_exists():
                try:
                    self._log_window.destroy()
                except Exception as e:
                    self.logger.error(f"Error destroying log window: {e}")
            
            # Clean up the root window if it exists
            if hasattr(self, '_root') and self._root:
                try:
                    self._root.quit()
                    self._root.destroy()
                except Exception as e:
                    self.logger.error(f"Error cleaning up Tkinter root: {e}")
            
            # Stop the icon last
            if self.icon is not None:
                try:
                    self.icon.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping system tray icon: {e}")
                finally:
                    self.icon = None
                    
            self.log("Tray icon stopped")
            
        except Exception as e:
            self.logger.error(f"Error during tray icon shutdown: {e}")
        finally:
            # Ensure we clear any remaining references
            if hasattr(self, '_root'):
                del self._root
            if hasattr(self, '_log_window'):
                del self._log_window
