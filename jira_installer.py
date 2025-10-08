# jira_installer.py
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os
import urllib.request
import tarfile
import threading
import queue
import sys
import time
import json
import hashlib
import tempfile
import shutil
import platform

# Constants
JDBC_VERSION = "9.4.0"
JDBC_TAR = f"mysql-connector-j-{JDBC_VERSION}.tar.gz"
JDBC_URL = f"https://dev.mysql.com/get/Downloads/Connector-J/{JDBC_TAR}"
JDBC_FOLDER = f"mysql-connector-j-{JDBC_VERSION}"

# Update System Constants
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "tugasky/Xray-Support-DockerJiraInstaller"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_BACKUP_EXT = ".backup"
UPDATE_TEMP_EXT = ".tmp"

# ---------- Update System Functions ----------
def compare_versions(version1, version2):
    """Compare two version strings. Returns -1 if version1 < version2, 0 if equal, 1 if version1 > version2"""
    try:
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # Pad the shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        return 0
    except (ValueError, AttributeError):
        # Fallback to string comparison if version format is unexpected
        if version1 < version2:
            return -1
        elif version1 > version2:
            return 1
        return 0

def check_for_updates():
    """Check if updates are available on GitHub"""
    try:
        log(f"Checking for updates... (current version: {CURRENT_VERSION})")

        # Create request with user agent to avoid GitHub API restrictions
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': 'Jira-Installer/1.0'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest_version = data.get('tag_name', '').lstrip('v')  # Remove 'v' prefix if present

        if not latest_version:
            log("Unable to retrieve latest version information.")
            return None

        log(f"Latest version available: {latest_version}")

        if compare_versions(CURRENT_VERSION, latest_version) < 0:
            log(f"Update available: {CURRENT_VERSION} -> {latest_version}")
            return {
                'version': latest_version,
                'release_data': data
            }
        else:
            log("No updates available. You have the latest version.")
            return None

    except urllib.error.URLError as e:
        log(f"Network error while checking for updates: {e}")
        return None
    except json.JSONDecodeError as e:
        log(f"Error parsing update information: {e}")
        return None
    except Exception as e:
        log(f"Unexpected error checking for updates: {e}")
        return None

def get_executable_path():
    """Get the path to the current executable"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return sys.executable
    else:
        # Running as script
        return os.path.abspath(sys.argv[0])

def create_backup():
    """Create a backup of the current executable/script"""
    try:
        current_path = get_executable_path()
        backup_path = current_path + UPDATE_BACKUP_EXT

        if os.path.exists(backup_path):
            os.remove(backup_path)
            log(f"Removed old backup: {backup_path}")

        shutil.copy2(current_path, backup_path)
        log(f"Created backup: {backup_path}")
        return backup_path

    except Exception as e:
        log(f"Failed to create backup: {e}")
        return None

def restore_backup():
    """Restore from backup if update failed"""
    try:
        current_path = get_executable_path()
        backup_path = current_path + UPDATE_BACKUP_EXT

        if os.path.exists(backup_path):
            if os.path.exists(current_path):
                os.remove(current_path)
            shutil.move(backup_path, current_path)
            log("Restored from backup successfully.")
            return True
        else:
            log("No backup found to restore.")
            return False

    except Exception as e:
        log(f"Failed to restore backup: {e}")
        return False

def download_update(download_url, temp_path):
    """Download update to temporary file"""
    try:
        log(f"Downloading update from: {download_url}")

        # Create request with user agent
        req = urllib.request.Request(
            download_url,
            headers={'User-Agent': 'Jira-Installer/1.0'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))

            with open(temp_path, 'wb') as temp_file:
                downloaded = 0
                block_size = 8192

                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break

                    downloaded += len(buffer)
                    temp_file.write(buffer)

                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        run_on_ui(update_download_progress, progress)

        log(f"Download completed: {temp_path}")
        return True

    except Exception as e:
        log(f"Failed to download update: {e}")
        return False

def update_download_progress(progress):
    """Update download progress bar"""
    try:
        update_progress_bar["value"] = progress
        update_progress_label.config(text=f"Downloading... {progress}%")
    except Exception:
        pass

def show_update_progress():
    """Show update progress UI"""
    try:
        update_progress_frame.pack(fill="x", padx=10, pady=(0, 10))
    except Exception:
        pass

def hide_update_progress():
    """Hide update progress UI"""
    try:
        update_progress_frame.pack_forget()
    except Exception:
        pass

def install_update(temp_path):
    """Install the downloaded update"""
    try:
        current_path = get_executable_path()

        log("Installing update...")

        # Create backup first
        backup_path = create_backup()
        if not backup_path:
            log("Failed to create backup. Update cancelled.")
            return False

        # Replace current file with new one
        if os.path.exists(current_path):
            os.remove(current_path)

        shutil.move(temp_path, current_path)
        log("Update installed successfully.")

        # Clean up backup after successful installation
        try:
            os.remove(backup_path)
            log("Cleaned up backup file.")
        except Exception:
            pass

        return True

    except Exception as e:
        log(f"Failed to install update: {e}")
        return False

def perform_update(update_info):
    """Perform the complete update process"""
    try:
        # Get download URL for the executable
        assets = update_info.get('release_data', {}).get('assets', [])
        download_url = None

        # Look for executable file
        for asset in assets:
            asset_name = asset.get('name', '').lower()
            if asset_name.endswith('.exe') or 'jira-installer' in asset_name:
                download_url = asset.get('browser_download_url')
                break

        if not download_url:
            log("No suitable update file found in release.")
            return False

        # Create temporary file path
        temp_dir = tempfile.gettempdir()
        temp_filename = f"jira_installer_update_{int(time.time())}{UPDATE_TEMP_EXT}"
        temp_path = os.path.join(temp_dir, temp_filename)

        # Download update
        if not download_update(download_url, temp_path):
            return False

        # Install update
        if not install_update(temp_path):
            # Try to restore backup if installation failed
            restore_backup()
            return False

        # Show success message and ask for restart
        log("Update completed successfully!")
        run_on_ui(show_update_success, update_info.get('version'))

        return True

    except Exception as e:
        log(f"Update failed: {e}")
        restore_backup()
        return False

def show_update_success(new_version):
    """Show update success message"""
    messagebox.showinfo(
        "Update Successful",
        f"Application has been updated to version {new_version}.\n\n"
        "Please restart the application to use the new version."
    )

def check_and_prompt_update():
    """Check for updates and prompt user if available"""
    def task():
        update_info = check_for_updates()
        if update_info:
            # Show update available dialog
            if ask_yes_no_on_ui(
                "Update Available",
                f"A new version ({update_info['version']}) is available.\n\n"
                "Current version: {CURRENT_VERSION}\n"
                f"Latest version: {update_info['version']}\n\n"
                "Would you like to update now?\n\n"
                "Note: The application will need to restart after the update."
            ):
                if perform_update(update_info):
                    return
                else:
                    show_error_ui("Update Failed", "Failed to install the update. Please try again later or download manually from GitHub.")
        else:
            messagebox.showinfo("No Updates", "You have the latest version installed.")

    threading.Thread(target=task).start()

# ---------- Helper functions ----------
# UI communication queue (producer from worker threads, consumer on main thread)
ui_queue = queue.Queue()
current_steps = []
step_labels = []
overall_steps_total = 0
overall_steps_done = 0
install_start_time = None
current_step_start_time = None
elapsed_job_id = None
current_step_index = None

def log(msg):
    # Always enqueue log messages; main thread drains and writes to the Text widget
    ui_queue.put(("log", msg))

def run_on_ui(func, *args, **kwargs):
    # If we're on the main thread, call directly; otherwise enqueue
    if threading.current_thread() is threading.main_thread():
        try:
            func(*args, **kwargs)
        except Exception:
            pass
    else:
        ui_queue.put(("call", func, args, kwargs))

def show_error_ui(title, message):
    # If on main thread, show directly; otherwise enqueue
    if threading.current_thread() is threading.main_thread():
        try:
            messagebox.showerror(title, message)
        except Exception:
            pass
    else:
        ui_queue.put(("error", title, message))

def ask_yes_no_on_ui(title, message):
    # If on main thread, ask directly; otherwise enqueue and wait
    if threading.current_thread() is threading.main_thread():
        try:
            return messagebox.askyesno(title, message)
        except Exception:
            return False
    result_container = {}
    done = threading.Event()
    ui_queue.put(("askyesno", title, message, result_container, done))
    done.wait()
    return result_container.get("result", False)

def to_docker_host_path(host_path):
    # Convert a Windows path to a Docker-friendly path with quoting if needed
    abs_path = os.path.abspath(host_path)
    # Do NOT quote; subprocess passes args directly and Docker handles spaces.
    # Quoting here breaks Windows volume parsing (drive colon + container colon).
    return abs_path

def safe_extract_tar(tar: tarfile.TarFile, path: str = "."):
    base = os.path.abspath(path)
    for member in tar.getmembers():
        member_path = os.path.abspath(os.path.join(path, member.name))
        if not member_path.startswith(base + os.sep) and member_path != base:
            raise Exception("Blocked path traversal in tar file")
    tar.extractall(path)

def wait_for_mysql_ready(container_name: str, root_password: str = "root_password", timeout_seconds: int = 120, poll_interval_seconds: float = 2.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # Use mysqladmin ping; --silent returns exit code 0 when alive
            kwargs = {}
            if os.name == 'nt':
                try:
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    kwargs["startupinfo"] = si
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                except Exception:
                    pass
            result = subprocess.run([
                "docker", "exec", container_name, "bash", "-c",
                f"mysqladmin ping -h 127.0.0.1 -uroot -p{root_password} --silent"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
            if result.returncode == 0:
                return True
        except Exception:
            pass
        time.sleep(poll_interval_seconds)
    return False

def clear_logs():
    log_text.delete(1.0, tk.END)

def run_cmd_list(cmd_list, fatal=False):
    try:
        kwargs = {}
        if os.name == 'nt':
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.dwFlags |= subprocess.STARTF_USESTDHANDLES
                kwargs["startupinfo"] = si
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            except Exception:
                pass
        result = subprocess.run(cmd_list, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        msg = e.stderr.decode().strip()
        log(f"Error: {msg}")
        if fatal:
            show_error_ui("Error", f"Command failed:\n{' '.join(cmd_list)}\n\n{msg}")
        return None

def check_docker_installed():
    try:
        kwargs = {}
        if os.name == 'nt':
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                kwargs["startupinfo"] = si
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            except Exception:
                pass
        subprocess.run(["docker", "--version"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_docker_running():
    try:
        kwargs = {}
        if os.name == 'nt':
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                kwargs["startupinfo"] = si
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            except Exception:
                pass
        subprocess.run(["docker", "info"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def ensure_docker_ready(root_window):
    if not check_docker_installed():
        messagebox.showerror(
            "Docker not found",
            "Docker is not installed or not available in PATH.\n\n"
            "Actions you can take:\n"
            "- Install Docker Desktop on Windows/Mac or Docker Engine on Linux.\n"
            "- Ensure the 'docker' command is in your PATH."
        )
        root_window.destroy()
        sys.exit(1)

    if not check_docker_running():
        messagebox.showerror(
            "Docker not running",
            "Docker is installed but the Docker daemon is not running.\n\n"
            "Actions you can take:\n"
            "- Start Docker Desktop (Windows/Mac).\n"
            "- Or start the Docker service: 'sudo systemctl start docker' (Linux).\n"
            "- After starting, reopen this installer."
        )
        root_window.destroy()
        sys.exit(1)

def check_container_exists(name):
    containers = run_cmd_list(["docker", "ps", "-a", "--format", "{{.Names}}"]) or ""
    return name in containers.splitlines()

def check_volume_exists(name):
    volumes = run_cmd_list(["docker", "volume", "ls", "--format", "{{.Name}}"]) or ""
    return name in volumes.splitlines()

def delete_volume(name):
    try:
        run_cmd_list(["docker", "volume", "rm", name], fatal=True)
        log(f"Deleted existing volume '{name}'.")
        return True
    except Exception as e:
        log(f"Failed to delete volume '{name}': {e}")
        return False

def stop_container_using_port(port):
    ports_info = run_cmd_list(["docker", "ps", "--format", "{{.Names}} {{.Ports}}"]) or ""
    for line in ports_info.splitlines():
        if '->' in line:
            name = line.split()[0]
            try:
                p = int(line.split('->')[0].split(':')[-1])
                if p == port:
                    # Ask the user before stopping
                    if ask_yes_no_on_ui("Port in use", f"Container '{name}' is using port {port}. Stop it?"):
                        log(f"Stopping container '{name}' using port {port}...")
                        run_cmd_list(["docker", "stop", name])
                        log(f"Container '{name}' stopped.")
                        return name
                    else:
                        log("User chose not to stop the container. Installation aborted.")
                        return "__CANCELLED__"
            except ValueError:
                continue
    return None

# ---------- Progress helpers ----------
def start_progress(msg):
    progress_label.config(text=msg)
    if setup_toggle_var.get():
        try:
            # Insert progress frame right after steps_frame for better visual flow
            progress_frame.pack(fill="x", padx=10, pady=(0, 10), before=overall_progress_container)
        except Exception:
            progress_frame.pack(fill="x", padx=10, pady=(0, 10))
    progress_bar.start(10)

def stop_progress():
    progress_bar.stop()
    progress_frame.pack_forget()

def check_and_pull_image(image):
    images = run_cmd_list(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"]) or ""
    if image not in images.splitlines():
        log(f"Image '{image}' not found locally. Pulling...")
        run_on_ui(start_progress, f"Pulling {image} ...")
        result = run_cmd_list(["docker", "pull", image], fatal=True)
        run_on_ui(stop_progress)
        if result is None:
            log(f"[FAIL] Failed to pull image {image}. Installation stopped.")
            run_on_ui(finish_steps_timing)
            return False
        log(f"[OK] Image '{image}' pulled successfully.")
    else:
        log(f"Image '{image}' already available locally.")
    return True

# ---------- UI drain loop ----------
def ui_drain():
    try:
        while True:
            item = ui_queue.get_nowait()
            kind = item[0]
            if kind == "log":
                _, msg = item
                try:
                    log_text.insert(tk.END, msg + "\n")
                    if auto_scroll_var.get():
                        log_text.see(tk.END)
                except Exception:
                    pass
            elif kind == "call":
                _, func, args, kwargs = item
                try:
                    func(*args, **kwargs)
                except Exception:
                    pass
            elif kind == "error":
                _, title, message = item
                try:
                    messagebox.showerror(title, message)
                except Exception:
                    pass
            elif kind == "askyesno":
                _, title, message, result_container, done = item
                try:
                    result_container["result"] = messagebox.askyesno(title, message)
                finally:
                    done.set()
            else:
                # Unknown item; ignore
                pass
    except queue.Empty:
        pass
    # Reschedule
    root.after(100, ui_drain)

# ---------- Visual multi-step progress helpers ----------
def init_steps_panel(steps):
    global current_steps, step_labels, overall_steps_total, overall_steps_done, install_start_time, current_step_start_time, current_step_index
    current_steps = steps
    # Clear existing step labels
    for w in steps_frame.winfo_children():
        w.destroy()
    step_labels = []
    for idx, title in enumerate(steps):
        lbl = tk.Label(steps_frame, text=f"[RUNNING] {title}", anchor="w")
        lbl.pack(fill="x", padx=10, pady=1)
        step_labels.append(lbl)
    overall_steps_total = len(steps)
    overall_steps_done = 0
    install_start_time = time.time()
    current_step_start_time = None
    current_step_index = None
    update_overall_progress()
    start_elapsed_updates()

def set_step_running(index):
    global current_step_index
    if 0 <= index < len(step_labels):
        # Reset previous current step styling
        if current_step_index is not None and 0 <= current_step_index < len(step_labels):
            try:
                step_labels[current_step_index].config(bg=root.cget('bg'), font=(None, 9, 'normal'))
            except Exception:
                pass
        title = current_steps[index]
        step_labels[index].config(text=f"[RUNNING] {title}", fg="black", font=(None, 9, 'bold'), bg="#fffbe6")
        current_step_index = index
        start_step_timer()

def set_step_done(index):
    if 0 <= index < len(step_labels):
        title = current_steps[index]
        duration_txt = format_duration(get_and_clear_step_duration())
        suffix = f" ({duration_txt})" if duration_txt else ""
        step_labels[index].config(text=f"[DONE] {title}{suffix}", fg="green", font=(None, 9, 'normal'), bg=root.cget('bg'))
        increment_overall_progress()

def set_step_error(index):
    if 0 <= index < len(step_labels):
        title = current_steps[index]
        step_labels[index].config(text=f"[ERROR] {title}", fg="red", font=(None, 9, 'normal'), bg=root.cget('bg'))
        update_overall_progress()

def start_step_timer():
    global current_step_start_time
    current_step_start_time = time.time()

def get_and_clear_step_duration():
    global current_step_start_time
    if current_step_start_time is None:
        return 0
    elapsed = max(0, int(time.time() - current_step_start_time))
    current_step_start_time = None
    return elapsed

def format_duration(seconds: int) -> str:
    try:
        seconds = int(seconds)
    except Exception:
        return ""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"

def start_elapsed_updates():
    global elapsed_job_id
    if elapsed_job_id is None:
        elapsed_job_id = root.after(1000, update_elapsed_labels)

def stop_elapsed_updates():
    global elapsed_job_id
    if elapsed_job_id is not None:
        try:
            root.after_cancel(elapsed_job_id)
        except Exception:
            pass
        elapsed_job_id = None

def update_elapsed_labels():
    global elapsed_job_id
    try:
        if install_start_time is not None:
            total_elapsed = int(time.time() - install_start_time)
            total_elapsed_label.config(text=f"Total time: {format_duration(total_elapsed)}")
            if current_step_start_time is not None:
                step_elapsed = int(time.time() - current_step_start_time)
                current_step_elapsed_label.config(text=f"Current step: {format_duration(step_elapsed)}")
            else:
                current_step_elapsed_label.config(text="Current step: -")
    finally:
        elapsed_job_id = root.after(1000, update_elapsed_labels)

def finish_steps_timing():
    global install_start_time, current_step_start_time
    install_start_time = None
    current_step_start_time = None
    stop_elapsed_updates()

def increment_overall_progress():
    global overall_steps_done
    overall_steps_done += 1
    update_overall_progress()

def update_overall_progress():
    total = overall_steps_total if overall_steps_total else 1
    percent = int((overall_steps_done / total) * 100)
    overall_progress_bar["value"] = percent
    overall_progress_label.config(text=f"Overall progress: {percent}%")

# ---------- Main functions ----------
def install_jira():
    version = version_entry.get().strip()
    if not version:
        messagebox.showerror("Error", "Please enter a Jira version (e.g., 9.15.0, 10.0.0, 11.0.0).")
        return

    # Get advanced configuration values with fallbacks
    if advanced_toggle_var.get():
        # Use custom port if provided, otherwise use version-based default
        custom_port = port_entry.get().strip()
        if custom_port and custom_port.isdigit():
            port = int(custom_port)
        elif version.startswith("8.") or version.startswith("9."):
            port = 8081
        elif version.startswith("10.") or version.startswith("11."):
            port = 8080
        else:
            messagebox.showerror("Error", "Unsupported Jira version. Only 8.x, 9.x, 10.x, and 11.x are supported.")
            return

        # Use custom container name if provided, otherwise use default
        jira_container_name = jira_container_entry.get().strip() or f"jira{version}"
        network_name = network_entry.get().strip() or "jira_network"

        # MySQL configuration (for Jira 10+)
        if version.startswith("10.") or version.startswith("11."):
            is_mysql = True
            mysql_container_name = mysql_container_entry.get().strip() or f"{version}_mysql"
            mysql_db_name = db_name_entry.get().strip() or f"{version}_db"
            mysql_volume_name = mysql_volume_entry.get().strip() or f"{version}_mysql_data"
            mysql_hostname = mysql_hostname_entry.get().strip() or mysql_container_name

            # MySQL credentials and settings
            mysql_root_password = mysql_root_password_entry.get().strip() or "root_password"
            mysql_user = mysql_user_entry.get().strip() or "jira_user"
            mysql_password = mysql_password_entry.get().strip() or "jira_password"
            mysql_version = mysql_version_entry.get().strip() or "mysql:8.0"
            mysql_port = mysql_port_entry.get().strip() or "3306"
        else:
            is_mysql = False

        # JDBC version
        jdbc_version = jdbc_version_entry.get().strip() or JDBC_VERSION
    else:
        # Use standard defaults when advanced mode is disabled
        if version.startswith("8.") or version.startswith("9."):
            port = 8081
            is_mysql = False
        elif version.startswith("10.") or version.startswith("11."):
            port = 8080
            is_mysql = True
        else:
            messagebox.showerror("Error", "Unsupported Jira version. Only 8.x, 9.x, 10.x, and 11.x are supported.")
            return

        jira_container_name = f"jira{version}"
        network_name = "jira_network"

        if is_mysql:
            mysql_container_name = f"{version}_mysql"
            mysql_db_name = f"{version}_db"
            mysql_volume_name = f"{version}_mysql_data"
            mysql_hostname = mysql_container_name
            mysql_root_password = "root_password"
            mysql_user = "jira_user"
            mysql_password = "jira_password"
            mysql_version = "mysql:8.0"
            mysql_port = "3306"

        jdbc_version = JDBC_VERSION

    # Update JDBC constants to use custom version
    jdbc_tar = f"mysql-connector-j-{jdbc_version}.tar.gz"
    jdbc_url = f"https://dev.mysql.com/get/Downloads/Connector-J/{jdbc_tar}"
    jdbc_folder = f"mysql-connector-j-{jdbc_version}"

    stopped_container = stop_container_using_port(port)
    if stopped_container == "__CANCELLED__":
        # Initialize and immediately mark canceled to reflect in UI
        steps = ["Create/check network", "Pull Jira image", "Start Jira" if not is_mysql else "Pull MySQL image"]
        run_on_ui(init_steps_panel, steps)
        run_on_ui(set_step_error, 0)
        log("Installation cancelled by user.")
        run_on_ui(finish_steps_timing)
        return
    if stopped_container:
        log(f"Port {port} was freed by stopping '{stopped_container}'.")

    def task():
        log(f"Starting installation of Jira {version} on port {port}...")
        # Initialize visual steps for progress
        steps = [
            "Create/check network",
            "Pull Jira image",
        ]
        if is_mysql:
            steps.extend(["Pull MySQL image", "Start MySQL", "Download/extract JDBC", "Start Jira", "Patch JVM args", "Restart Jira", "Finalize"])
        else:
            steps.extend(["Start Jira", "Patch JVM args", "Restart Jira", "Finalize"])
        run_on_ui(init_steps_panel, steps)
        step_index = 0
        run_on_ui(set_step_running, step_index)

        # Ensure network
        networks = run_cmd_list(["docker", "network", "ls", "--format", "{{.Name}}"]) or ""
        if network_name not in networks.splitlines():
            log(f"Creating docker network '{network_name}'...")
            if run_cmd_list(["docker", "network", "create", network_name], fatal=True) is None:
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
        else:
            log(f"'{network_name}' already exists.")
        run_on_ui(set_step_done, step_index)

        # Step: Pull Jira image
        step_index += 1
        run_on_ui(set_step_running, step_index)

        if check_container_exists(jira_container_name):
            log(f"Container '{jira_container_name}' already exists.")
            if ask_yes_no_on_ui("Container exists", f"Container {jira_container_name} exists. Remove it and continue?"):
                run_cmd_list(["docker", "rm", "-f", jira_container_name])
                log(f"Removed existing container {jira_container_name}.")
            else:
                log("Installation cancelled by user.")
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return

        jira_image = f"atlassian/jira-software:{version}"
        if not check_and_pull_image(jira_image):
            run_on_ui(set_step_error, step_index)
            return
        run_on_ui(set_step_done, step_index)

        if not is_mysql:
            # Jira 8/9 with built-in DB
            step_index += 1
            run_on_ui(set_step_running, step_index)
            log(f"Installing Jira {version}...")
            if run_cmd_list([
                "docker", "run", "-d",
                "--name", jira_container_name,
                "--network", network_name,
                "-p", f"{port}:8080",
                jira_image
            ], fatal=True) is None:
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
            run_on_ui(set_step_done, step_index)
        else:
            # Jira 10+ with MySQL
            # Pull MySQL image
            step_index += 1
            run_on_ui(set_step_running, step_index)

            mysql_image = mysql_version
            if not check_and_pull_image(mysql_image):
                run_on_ui(set_step_error, step_index)
                return
            run_on_ui(set_step_done, step_index)

            # Start MySQL
            step_index += 1
            run_on_ui(set_step_running, step_index)

            # Check and delete existing volume before creating container
            if check_volume_exists(mysql_volume_name):
                log(f"Volume '{mysql_volume_name}' already exists. Deleting it...")
                if not delete_volume(mysql_volume_name):
                    log(f"[FAIL] Failed to delete existing volume '{mysql_volume_name}'. Installation stopped.")
                    run_on_ui(set_step_error, step_index)
                    run_on_ui(finish_steps_timing)
                    return
                log(f"[OK] Existing volume '{mysql_volume_name}' deleted successfully.")

            log(f"Installing MySQL container '{mysql_container_name}' with custom credentials...")
            if not check_container_exists(mysql_container_name):
                if run_cmd_list([
                    "docker", "run", "-d",
                    "--name", mysql_container_name,
                    "--network", network_name,
                    "-e", f"MYSQL_ROOT_PASSWORD={mysql_root_password}",
                    "-e", f"MYSQL_DATABASE={mysql_db_name}",
                    "-e", f"MYSQL_USER={mysql_user}",
                    "-e", f"MYSQL_PASSWORD={mysql_password}",
                    "-v", f"{mysql_volume_name}:/var/lib/mysql",
                    mysql_image
                ], fatal=True) is None:
                    run_on_ui(set_step_error, step_index)
                    run_on_ui(finish_steps_timing)
                    return
                log("MySQL container started.")
            else:
                log("MySQL container already running.")
            run_on_ui(set_step_done, step_index)

            # JDBC download/extract
            step_index += 1
            run_on_ui(set_step_running, step_index)
            try:
                if not os.path.exists(jdbc_tar):
                    log(f"Downloading MySQL JDBC Connector {jdbc_version}...")
                    urllib.request.urlretrieve(jdbc_url, jdbc_tar)
                if not os.path.exists(jdbc_folder):
                    with tarfile.open(jdbc_tar) as tar:
                        safe_extract_tar(tar, ".")
            except Exception as e:
                show_error_ui("Download/Extract Error", f"Failed to obtain JDBC driver: {e}")
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
            jar_file = None
            for root, dirs, files in os.walk(jdbc_folder):
                for file in files:
                    if file.endswith(".jar"):
                        jar_file = os.path.join(root, file)
                        break
            if not jar_file:
                show_error_ui("Error", "JDBC jar not found.")
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
            run_on_ui(set_step_done, step_index)

            # Start Jira (after MySQL readiness)
            step_index += 1
            run_on_ui(set_step_running, step_index)
            log("Waiting for MySQL to become ready...")
            if not wait_for_mysql_ready(mysql_container_name, root_password=mysql_root_password, timeout_seconds=120):
                log("MySQL did not become ready in time.")
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
            log("MySQL is ready. Proceeding to start Jira...")
            log(f"Installing Jira {version}...")
            if run_cmd_list([
                "docker", "run", "-d",
                "--name", jira_container_name,
                "--network", network_name,
                "-p", f"{port}:8080",
                "-e", f'ATL_JDBC_URL=jdbc:mysql://{mysql_hostname}:{mysql_port}/{mysql_db_name}?useSSL=false&serverTimezone=UTC',
                "-e", f"ATL_JDBC_USER={mysql_user}",
                "-e", f"ATL_JDBC_PASSWORD={mysql_password}",
                "-v", f"{to_docker_host_path(jar_file)}:/opt/atlassian/jira/lib/{os.path.basename(jar_file)}",
                jira_image
            ], fatal=True) is None:
                run_on_ui(set_step_error, step_index)
                run_on_ui(finish_steps_timing)
                return
            run_on_ui(set_step_done, step_index)

        # Patch JVM args safely (version-specific for Jira 11)
        step_index += 1
        run_on_ui(set_step_running, step_index)

        # Determine JVM arguments based on Jira version
        if version.startswith("11."):
            # Jira 11: include both existing and new JVM arguments
            jvm_args = "-Dupm.plugin.upload.enabled=true -Datlassian.upm.signature.check.disabled=true"
        else:
            # Jira 10 and earlier: use existing JVM argument only
            jvm_args = "-Dupm.plugin.upload.enabled=true"

        sed_cmd = r'sed -i ' \
                  r'"s#^\(:\s*\${JVM_SUPPORT_RECOMMENDED_ARGS[^}]*}\|JVM_SUPPORT_RECOMMENDED_ARGS=.*\)#JVM_SUPPORT_RECOMMENDED_ARGS=\"' + jvm_args + r'\"#"' \
                  r' /opt/atlassian/jira/bin/setenv.sh'
        if run_cmd_list(["docker", "exec", jira_container_name, "bash", "-c", sed_cmd], fatal=True) is None:
            run_on_ui(set_step_error, step_index)
            run_on_ui(finish_steps_timing)
            return
        run_on_ui(set_step_done, step_index)

        # Restart Jira
        step_index += 1
        run_on_ui(set_step_running, step_index)
        if run_cmd_list(["docker", "restart", jira_container_name], fatal=True) is None:
            run_on_ui(set_step_error, step_index)
            run_on_ui(finish_steps_timing)
            return
        run_on_ui(set_step_done, step_index)

        # Final logs
        step_index += 1
        run_on_ui(set_step_running, step_index)
        log(f"[OK] Jira {version} installation complete!")
        if is_mysql:
            log(f"[INFO] MySQL Host: {mysql_container_name}")
            log(f"[INFO] DB: {mysql_db_name}")
            log(f"[INFO] MySQL User: {mysql_user}")
            log(f"[INFO] MySQL Password: {mysql_password}")
        log(f"[INFO] Jira URL: http://localhost:{port}")
        log(f"[INFO] Jira Login: admin/admin")
        log("")
        run_on_ui(set_step_done, step_index)
        run_on_ui(finish_steps_timing)

    threading.Thread(target=task).start()

def view_docker_status():
    def task():
        log("=== Docker Status ===")
        containers = run_cmd_list(["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"]) or ""
        networks = run_cmd_list(["docker", "network", "ls", "--format", "{{.Name}}\t{{.Driver}}"]) or ""
        volumes = run_cmd_list(["docker", "volume", "ls", "--format", "{{.Name}}\t{{.Driver}}"]) or ""

        if containers:
            log("\n-- Running Containers --")
            log(containers)
        else:
            log("\n-- Running Containers --\nNone")

        if networks:
            log("\n-- Networks --")
            log(networks)

        if volumes:
            log("\n-- Volumes --")
            log(volumes)

        log("=======================\n")
    threading.Thread(target=task).start()

# ---------- Helper function for advanced defaults ----------
def set_advanced_defaults():
    """Set default values for advanced configuration fields based on Jira version"""
    version = version_entry.get().strip()
    if version.startswith("8.") or version.startswith("9."):
        port_entry.delete(0, tk.END)
        port_entry.insert(0, "8081")
        mysql_container_entry.delete(0, tk.END)
        mysql_container_entry.insert(0, "")
        db_name_entry.delete(0, tk.END)
        db_name_entry.insert(0, "")
        mysql_volume_entry.delete(0, tk.END)
        mysql_volume_entry.insert(0, "")
        mysql_hostname_entry.delete(0, tk.END)
        mysql_hostname_entry.insert(0, "")
    elif version.startswith("10.") or version.startswith("11."):
        port_entry.delete(0, tk.END)
        port_entry.insert(0, "8080")
        mysql_container_entry.delete(0, tk.END)
        mysql_container_entry.insert(0, f"{version}_mysql")
        db_name_entry.delete(0, tk.END)
        db_name_entry.insert(0, f"{version}_db")
        mysql_volume_entry.delete(0, tk.END)
        mysql_volume_entry.insert(0, f"{version}_mysql_data")
        mysql_hostname_entry.delete(0, tk.END)
        mysql_hostname_entry.insert(0, f"{version}_mysql")

    jira_container_entry.delete(0, tk.END)
    jira_container_entry.insert(0, f"jira{version}")
    network_entry.delete(0, tk.END)
    network_entry.insert(0, "jira_network")

# ---------- GUI ----------
root = tk.Tk()
root.title("Docker Jira One-Click Installer for Xray Support <3")

# Ensure Docker is installed and running before continuing
ensure_docker_ready(root)

# Create main canvas with scrollbar for the entire window
main_canvas = tk.Canvas(root)
main_scrollbar = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
main_canvas.configure(yscrollcommand=main_scrollbar.set)

main_scrollbar.pack(side="right", fill="y")
main_canvas.pack(side="left", fill="both", expand=True)

# Create main frame inside canvas
main_frame = tk.Frame(main_canvas)
main_canvas.create_window((0, 0), window=main_frame, anchor="nw")

# Configure canvas scrolling
def configure_canvas(event):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    # Auto-resize window when content changes
    root.after_idle(resize_window_to_content)

main_frame.bind("<Configure>", configure_canvas)

def mouse_wheel(event):
    main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

main_canvas.bind_all("<MouseWheel>", mouse_wheel)

def resize_window_to_content():
    """Resize window to fit content when possible, otherwise keep scrollable"""
    root.update_idletasks()  # Ensure all widgets are properly sized

    # Get content height
    content_height = main_frame.winfo_reqheight()
    content_width = main_frame.winfo_reqwidth()

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate optimal window size (with some padding)
    window_width = min(content_width + 40, screen_width - 100)  # Leave some space
    window_height = min(content_height + 40, screen_height - 100)  # Leave some space

    # Only resize if content fits within screen limits
    if content_height < screen_height - 100 and content_width < screen_width - 100:
        root.geometry(f"{int(window_width)}x{int(window_height)}")
    # If content is too tall, set a reasonable height and keep scrolling
    elif content_height >= screen_height - 100:
        root.geometry(f"{int(window_width)}x{int(screen_height - 100)}")

tk.Label(main_frame, text="Enter Jira Version (e.g., 8.15.0, 9.15.0, 10.2.6 or 11.0.0):").pack(padx=15, pady=5)
version_entry = tk.Entry(main_frame, width=25)
version_entry.pack(padx=15, pady=5)
version_entry.insert(0, "10.0.0")

# Update advanced configuration fields when version changes
def on_version_change(*args):
    """Update advanced configuration fields when Jira version changes"""
    set_advanced_defaults()

version_entry.bind('<KeyRelease>', on_version_change)



# Buttons horizontal with improved alignment and spacing
button_frame = tk.Frame(main_frame)
button_frame.pack(padx=15, pady=10, fill="x")
tk.Button(button_frame, text="Install Jira", command=install_jira).pack(side=tk.LEFT, padx=10, pady=5)
tk.Button(button_frame, text="View Docker Status", command=view_docker_status).pack(side=tk.LEFT, padx=10, pady=5)
tk.Button(button_frame, text="Clear Logs", command=clear_logs).pack(side=tk.LEFT, padx=10, pady=5)
tk.Button(button_frame, text="Check for Updates", command=check_and_prompt_update).pack(side=tk.LEFT, padx=10, pady=5)

# Main content area with logs and advanced options side by side
main_content = tk.Frame(main_frame)
main_content.pack(fill="both", expand=True, padx=15, pady=10)
# Configure column weights for proper expansion
main_content.columnconfigure(0, weight=1)  # Left column (logs)
main_content.columnconfigure(1, weight=1)  # Right column (advanced)

# Left side - Logs
logs_container = tk.Frame(main_content)
logs_container.pack(side=tk.LEFT, fill="both", expand=True)
logs_header = tk.Frame(logs_container)
logs_header.pack(fill="x")
logs_toggle_var = tk.BooleanVar(value=True)
def toggle_logs():
    if logs_toggle_var.get():
        log_text.pack(padx=10, pady=(0,10))
    else:
        log_text.pack_forget()
    root.after_idle(resize_window_to_content)
tk.Checkbutton(logs_header, text="Show logs", variable=logs_toggle_var, command=toggle_logs).pack(side=tk.LEFT, padx=10)
auto_scroll_var = tk.BooleanVar(value=True)
tk.Checkbutton(logs_header, text="Auto-scroll", variable=auto_scroll_var).pack(side=tk.LEFT, padx=10)

# Advanced mode toggle in logs header
advanced_toggle_var = tk.BooleanVar(value=False)
def toggle_advanced():
    if advanced_toggle_var.get():
        # Populate fields with current defaults when enabling advanced mode
        set_advanced_defaults()
        advanced_container.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
    else:
        advanced_container.pack_forget()
    root.after_idle(resize_window_to_content)
tk.Checkbutton(logs_header, text="Advanced Mode", variable=advanced_toggle_var, command=toggle_advanced).pack(side=tk.LEFT, padx=10)

logs_container.pack(side=tk.LEFT, fill="both", expand=True)

log_text = tk.Text(logs_container, height=18, width=35)
log_text.pack(padx=10, pady=(0,10), fill="both", expand=True)

# Right side - Advanced configuration
advanced_container = tk.Frame(main_content)
advanced_frame = tk.Frame(advanced_container)

# Configure grid weights for proper column alignment
advanced_frame.columnconfigure(1, weight=1)  # Make entry column expandable
advanced_frame.columnconfigure(0, minsize=140)  # Set minimum label column width

# ========== JIRA CONFIGURATION ==========
tk.Label(advanced_frame, text="[JIRA] CONFIGURATION", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))

tk.Label(advanced_frame, text="Port:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
port_entry = tk.Entry(advanced_frame, width=20)
port_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

tk.Label(advanced_frame, text="Jira Container Name:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
jira_container_entry = tk.Entry(advanced_frame, width=20)
jira_container_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

tk.Label(advanced_frame, text="Network Name:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
network_entry = tk.Entry(advanced_frame, width=20)
network_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

# ========== MYSQL CONFIGURATION (Jira 10+) ==========
tk.Label(advanced_frame, text="[MYSQL] CONFIGURATION", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))

tk.Label(advanced_frame, text="MySQL Container Name:").grid(row=5, column=0, sticky="w", padx=5, pady=2)
mysql_container_entry = tk.Entry(advanced_frame, width=20)
mysql_container_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=2)

tk.Label(advanced_frame, text="Database Name:").grid(row=6, column=0, sticky="w", padx=5, pady=2)
db_name_entry = tk.Entry(advanced_frame, width=20)
db_name_entry.grid(row=6, column=1, sticky="ew", padx=5, pady=2)

tk.Label(advanced_frame, text="MySQL Volume Name:").grid(row=7, column=0, sticky="w", padx=5, pady=2)
mysql_volume_entry = tk.Entry(advanced_frame, width=20)
mysql_volume_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=2)

tk.Label(advanced_frame, text="MySQL Hostname:").grid(row=8, column=0, sticky="w", padx=5, pady=2)
mysql_hostname_entry = tk.Entry(advanced_frame, width=20)
mysql_hostname_entry.grid(row=8, column=1, sticky="ew", padx=5, pady=2)

# ========== MYSQL CREDENTIALS ==========
tk.Label(advanced_frame, text="[CREDS] MYSQL CREDENTIALS", font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))

tk.Label(advanced_frame, text="MySQL Root Password:").grid(row=10, column=0, sticky="w", padx=5, pady=2)
mysql_root_password_entry = tk.Entry(advanced_frame, width=20)
mysql_root_password_entry.grid(row=10, column=1, sticky="ew", padx=5, pady=2)
mysql_root_password_entry.insert(0, "root_password")

tk.Label(advanced_frame, text="MySQL Username:").grid(row=11, column=0, sticky="w", padx=5, pady=2)
mysql_user_entry = tk.Entry(advanced_frame, width=20)
mysql_user_entry.grid(row=11, column=1, sticky="ew", padx=5, pady=2)
mysql_user_entry.insert(0, "jira_user")

tk.Label(advanced_frame, text="MySQL Password:").grid(row=12, column=0, sticky="w", padx=5, pady=2)
mysql_password_entry = tk.Entry(advanced_frame, width=20)
mysql_password_entry.grid(row=12, column=1, sticky="ew", padx=5, pady=2)
mysql_password_entry.insert(0, "jira_password")

# ========== MYSQL SETTINGS ==========
tk.Label(advanced_frame, text="[SETTINGS] MYSQL SETTINGS", font=("Arial", 10, "bold")).grid(row=13, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))

tk.Label(advanced_frame, text="MySQL Version:").grid(row=14, column=0, sticky="w", padx=5, pady=2)
mysql_version_entry = tk.Entry(advanced_frame, width=20)
mysql_version_entry.grid(row=14, column=1, sticky="ew", padx=5, pady=2)
mysql_version_entry.insert(0, "mysql:8.0")

tk.Label(advanced_frame, text="MySQL Port:").grid(row=15, column=0, sticky="w", padx=5, pady=2)
mysql_port_entry = tk.Entry(advanced_frame, width=20)
mysql_port_entry.grid(row=15, column=1, sticky="ew", padx=5, pady=2)
mysql_port_entry.insert(0, "3306")

# ========== JDBC CONFIGURATION ==========
tk.Label(advanced_frame, text="[JDBC] CONFIGURATION", font=("Arial", 10, "bold")).grid(row=16, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))

tk.Label(advanced_frame, text="JDBC Version:").grid(row=17, column=0, sticky="w", padx=5, pady=2)
jdbc_version_entry = tk.Entry(advanced_frame, width=20)
jdbc_version_entry.grid(row=17, column=1, sticky="ew", padx=5, pady=2)
jdbc_version_entry.insert(0, JDBC_VERSION)

advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)
# Advanced panel is visible by default for real-time configuration

# Steps panel for multi-step visual progress
steps_container = tk.Frame(main_frame)
# Header with collapsible toggle
steps_header = tk.Frame(steps_container)
steps_header.pack(fill="x")
setup_toggle_var = tk.BooleanVar(value=True)
def toggle_setup():
    if setup_toggle_var.get():
        steps_frame.pack(fill="x", padx=10, pady=(0, 10))
        # progress_frame is only shown during pulling
        overall_progress_container.pack(fill="x")
        elapsed_container.pack(fill="x")
    else:
        steps_frame.pack_forget()
        progress_frame.pack_forget()
        overall_progress_container.pack_forget()
        elapsed_container.pack_forget()
    root.after_idle(resize_window_to_content)
tk.Checkbutton(steps_header, text="Show setup progress", variable=setup_toggle_var, command=toggle_setup).pack(side=tk.LEFT, padx=10)
steps_frame = tk.Frame(steps_container)
steps_frame.pack(fill="x", padx=10, pady=(0, 10))
steps_container.pack(fill="x")

# Progress bar UI (integrated with setup progress section)
progress_frame = tk.Frame(steps_container)
progress_label = tk.Label(progress_frame, text="Pulling image...")
progress_label.pack(anchor="w", padx=10, pady=(0, 5))
progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=300)
progress_bar.pack(fill="x", padx=10, pady=(0, 10))
progress_frame.pack_forget()

# Update progress UI (for update downloads)
update_progress_frame = tk.Frame(steps_container)
update_progress_label = tk.Label(update_progress_frame, text="Checking for updates...")
update_progress_label.pack(anchor="w", padx=10, pady=(0, 5))
update_progress_bar = ttk.Progressbar(update_progress_frame, mode="determinate", length=300, maximum=100)
update_progress_bar.pack(fill="x", padx=10, pady=(0, 10))
update_progress_frame.pack_forget()

# Overall progress bar inside steps container
overall_progress_container = tk.Frame(steps_container)
overall_progress_label = tk.Label(overall_progress_container, text="Overall progress: 0%")
overall_progress_label.pack(anchor="w", padx=10)
overall_progress_bar = ttk.Progressbar(overall_progress_container, mode="determinate", length=300, maximum=100)
overall_progress_bar.pack(padx=10, pady=(0, 10), fill="x")
overall_progress_container.pack(fill="x")

# Elapsed time labels inside steps container
elapsed_container = tk.Frame(steps_container)
current_step_elapsed_label = tk.Label(elapsed_container, text="Current step: -")
current_step_elapsed_label.pack(anchor="w", padx=10)
total_elapsed_label = tk.Label(elapsed_container, text="Total time: 0s")
total_elapsed_label.pack(anchor="w", padx=10)
elapsed_container.pack(fill="x")

tk.Label(main_frame, text="Credits: João Silva (joao.silva@sembi.com)").pack(padx=10, pady=5)
tk.Label(main_frame, text="Contact the author if you have any doubts.").pack(padx=10, pady=5)

# Start UI drain loop and enter mainloop
root.after(100, ui_drain)
root.mainloop()
