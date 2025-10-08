#!/usr/bin/env python3
"""
Build script for Jira Installer
Automates the PyInstaller build process and version management
"""

import os
import sys
import subprocess
import shutil
import argparse
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

def update_version_in_script(version):
    """Update the CURRENT_VERSION in jira_installer.py"""
    script_path = "jira_installer.py"

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        # Find the current version line (it should be something like CURRENT_VERSION = "x.x.x")
        import re
        version_pattern = r'CURRENT_VERSION = "([^"]+)"'
        match = re.search(version_pattern, content)

        if match:
            current_version_in_file = match.group(1)
            old_line = f'CURRENT_VERSION = "{current_version_in_file}"'
            new_line = f'CURRENT_VERSION = "{version}"'

            content = content.replace(old_line, new_line)
            with open(script_path, 'w') as f:
                f.write(content)
            print(f"✅ Updated version in script from {current_version_in_file} to {version}")
            return True
        else:
            print(f"⚠️  Could not find CURRENT_VERSION line in script")
            return False

    except Exception as e:
        print(f"❌ Failed to update version in script: {e}")
        return False

def build_executable(version):
    """Build the executables using PyInstaller"""
    print(f"Building executable for version {version}...")

    # Update version in script first
    if not update_version_in_script(version):
        return False

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

    # Run PyInstaller
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
        print(f"✅ Executable created: {exe_path} ({exe_size:,}","bytes)")
        return True
    else:
        print("❌ Executable not found at expected location")
        return False

def create_release_structure(version):
    """Create release structure with executable and supporting files"""
    print(f"Creating release structure for version {version}...")

    # Create releases directory if it doesn't exist
    os.makedirs("releases", exist_ok=True)

    # Copy main executable and supporting files
    main_dist_dir = Path("dist/jira_installer")
    updater_dist_dir = Path("dist/updater")

    if main_dist_dir.exists():
        # Create versioned release directory
        release_dir = Path(f"releases/v{version}")
        release_dir.mkdir(exist_ok=True)

        # Copy main executable
        main_exe_src = main_dist_dir / "jira_installer.exe"
        main_exe_dst = release_dir / "jira_installer.exe"
        if main_exe_src.exists():
            shutil.copy2(main_exe_src, main_exe_dst)
            print(f"✅ Copied main executable to {main_exe_dst}")

        # Copy updater executable
        updater_exe_src = updater_dist_dir / "updater.exe"
        updater_exe_dst = release_dir / "updater.exe"
        if updater_exe_src.exists():
            shutil.copy2(updater_exe_src, updater_exe_dst)
            print(f"✅ Copied updater executable to {updater_exe_dst}")
        else:
            print(f"⚠️  Updater executable not found: {updater_exe_src}")

        # Copy icon if needed
        icon_src = Path("jira.ico")
        if icon_src.exists():
            shutil.copy2(icon_src, release_dir / "jira.ico")
            print(f"✅ Copied icon to {release_dir}")

        # Copy updater script (fallback for development)
        updater_script_src = Path("updater.py")
        if updater_script_src.exists():
            shutil.copy2(updater_script_src, release_dir / "updater.py")
            print(f"✅ Copied updater script to {release_dir}")

        print(f"📦 Release created in: {release_dir}")
        return release_dir

    return None

def main():
    """Main build process"""
    parser = argparse.ArgumentParser(description="Build Jira Installer")
    parser.add_argument("--version", default=None, help="Version number (overrides script version)")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning build directories")
    parser.add_argument("--quick", action="store_true", help="Quick build (skip cleaning)")

    args = parser.parse_args()

    print("Jira Installer Build Script")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("jira_installer.py"):
        print("Error: jira_installer.py not found. Please run this script from the project root.")
        sys.exit(1)

    # Determine version to use
    if args.version:
        version = args.version
        print(f"Using specified version: {version}")
    else:
        # Import version from main script
        try:
            sys.path.append('.')
            import jira_installer
            version = jira_installer.CURRENT_VERSION
            print(f"Using version from script: {version}")
        except (ImportError, AttributeError):
            version = "1.0.0"
            print(f"Using fallback version: {version}")

    # Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)

    # Build executable
    if not build_executable(version):
        sys.exit(1)

    # Create release structure
    release_dir = create_release_structure(version)
    if release_dir:
        print(f"\n✅ Release ready in: {release_dir}")
        print("📦 You can now create a GitHub release with the executable.")
    else:
        print("❌ Warning: Release structure creation failed.")

if __name__ == "__main__":
    main()
