# -*- mode: python ; coding: utf-8 -*-

import os
import sys
block_cipher = None

# Determine platform-specific settings
if os.name == 'nt':  # Windows
    # Add hidden imports for Windows/Python DLL issues
    hidden_imports = [
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'tkinter.colorchooser',
        'tkinter.commondialog',
        'tkinter.simpledialog',
        'tkinter.dnd',
        'tkinter.font',
        'tkinter.scrolledtext',
        # Python runtime modules that may not be detected
        'collections',
        'encodings.idna',
        'encodings.cp1252',
        'urllib.parse',
        'urllib.request',
        'http.client',
        'ssl',
        'sqlite3',
        'decimal',
        'multiprocessing',
        # Fix for Python DLL loading issues
        'ctypes',
        'ctypes.util',
        'ctypes.wintypes',
    ]

    # Windows-specific binaries and runtime hooks
    runtime_hooks = ['runtime_hook.py']

    # Microsoft Visual C++ runtime detection
    msvcrt_binaries = []
    try:
        # Try to detect MSVC runtime location
        import glob
        python_dir = os.path.dirname(sys.executable)
        msvcrt_patterns = [
            os.path.join(python_dir, 'vcruntime*.dll'),
            os.path.join(python_dir, 'msvcp*.dll'),
            os.path.join(python_dir, 'concrt*.dll'),
        ]

        for pattern in msvcrt_patterns:
            for dll_path in glob.glob(pattern):
                if os.path.exists(dll_path):
                    dll_name = os.path.basename(dll_path)
                    msvcrt_binaries.append((dll_path, '.'))
    except:
        pass

    # Add any additional Windows-specific binaries
    binaries = msvcrt_binaries + [
        # Add other Windows-specific binaries if needed
    ]

    # Windows-specific analysis options
    win_options = {
        'win_no_prefer_redirects': False,
        'win_private_assemblies': False,
    }
else:
    hidden_imports = [
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk'
    ]
    runtime_hooks = []
    binaries = []
    win_options = {}

a = Analysis(
    ['jira_installer.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('jira.ico', '.')
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter.test',
        'test',
        'unittest',
        'pydoc',
        'pdb',
        'profile',
        'cProfile',
    ],
    cipher=block_cipher,
    noarchive=False,
    **win_options
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='jira_installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime*.dll',
        'msvcp*.dll',
        'python*.dll',
        'tkinter*.dll',
        'tcl*.dll'
    ],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='jira.ico',
    version='file_version_info.txt',
    # Windows-specific options for better DLL handling
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='jira_installer'
)
