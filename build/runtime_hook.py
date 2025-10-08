"""
Runtime hook for PyInstaller to fix Python DLL loading issues on Windows
"""

import os
import sys
import ctypes

def fix_python_dll_path():
    """Fix Python DLL path issues on Windows"""
    try:
        if os.name == 'nt':  # Windows only
            # Get the current executable directory
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle
                app_path = os.path.dirname(sys.executable)
            else:
                # Running as script
                app_path = os.path.dirname(os.path.abspath(__file__))

            # Add the app directory to DLL search paths
            if os.path.exists(app_path):
                # Add to PATH if not already there
                if app_path not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = app_path + os.pathsep + os.environ.get('PATH', '')

                # Try to load python.dll explicitly if it fails to load
                python_dll = os.path.join(app_path, 'python.dll')
                if os.path.exists(python_dll):
                    try:
                        ctypes.windll.LoadLibrary(python_dll)
                    except:
                        pass  # Ignore if we can't load it explicitly

    except Exception:
        # Silently ignore errors in runtime hooks
        pass

# Run the fix when this module is imported
fix_python_dll_path()
