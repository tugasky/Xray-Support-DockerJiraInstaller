#!/usr/bin/env python3
"""
Build script for Jira Installer
Automates the PyInstaller build process and version management
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Import version from main script
try:
    sys.path.append('.')
    import jira_installer
    CURRENT_VERSION = jira_installer.CURRENT_VERSION
except (ImportError, AttributeError):
    # Fallback version if import fails
    CURRENT_VERSION = "1.0.0"

def run_command(cmd, shell=False):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd if shell else cmd,
            shell=shell,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.stderr, 0
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        stdout, stderr, code = run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
        if code != 0:
            print(f"Failed to install PyInstaller: {stderr}")
            return False
        return True

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")

    # Clean previous builds more thoroughly
    for dir_name in ["dist", "build", "__pycache__"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned: {dir_name}")

    # Also clean any .pyc files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))

    # Run PyInstaller (debugging options not valid with .spec files)
    print("Running PyInstaller...")
    stdout, stderr, code = run_command(["pyinstaller", "--clean", "pyinstaller.spec"])

    if code != 0:
        print(f"Build failed with code {code}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

    print("Build completed successfully!")

    # Verify the executable was created
    exe_path = "dist/jira_installer/jira_installer.exe"
    if os.path.exists(exe_path):
        exe_size = os.path.getsize(exe_path)
        print(f"Executable created: {exe_path} ({exe_size:,}","bytes)")
        return True
    else:
        print("Warning: Executable not found at expected location")
        return False

def create_release_structure():
    """Create release structure with executable and supporting files"""
    print("Creating release structure...")

    # Create releases directory if it doesn't exist
    os.makedirs("releases", exist_ok=True)

    # Copy executable and supporting files
    dist_dir = Path("dist/jira_installer")
    if dist_dir.exists():
        # Create versioned release directory
        release_dir = Path(f"releases/v{CURRENT_VERSION}")
        release_dir.mkdir(exist_ok=True)

        # Copy executable
        exe_src = dist_dir / "jira_installer.exe"
        exe_dst = release_dir / "jira_installer.exe"
        if exe_src.exists():
            shutil.copy2(exe_src, exe_dst)
            print(f"Copied executable to {exe_dst}")

        # Copy icon if needed
        icon_src = Path("jira.ico")
        if icon_src.exists():
            shutil.copy2(icon_src, release_dir / "jira.ico")

        print(f"Release created in: {release_dir}")
        return release_dir

    return None

def main():
    """Main build process"""
    print("Jira Installer Build Script")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("jira_installer.py"):
        print("Error: jira_installer.py not found. Please run this script from the project root.")
        sys.exit(1)

    # Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)

    # Build executable
    if not build_executable():
        sys.exit(1)

    # Create release structure
    release_dir = create_release_structure()
    if release_dir:
        print(f"\nRelease ready in: {release_dir}")
        print("You can now create a GitHub release with the executable.")
    else:
        print("Warning: Release structure creation failed.")

if __name__ == "__main__":
    main()
