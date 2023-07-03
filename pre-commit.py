#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess
import sys

GITLEAKS_VERSION = "8.17.0"

def install_gitleaks():
    system = platform.system()
    machine = platform.machine()
    archive_filename = f"gitleaks_{GITLEAKS_VERSION}_"

    if system == "Linux":
        if machine == "arm64":
            archive_filename += "linux_arm64.tar.gz"
        else:
            archive_filename += "linux_x64.tar.gz"
    elif system == "Darwin":
        if machine == "arm64":
            archive_filename += "darwin_arm64.tar.gz"
        else:
            archive_filename += "darwin_x64.tar.gz"
    elif system == "Windows":
        if machine == "arm64":
            archive_filename += "windows_arm64.zip"
        else: 
            archive_filename += "windows_x64.zip"
    else:
        print(f"Error: Unsupported system {system}. Unable to install gitleaks.")
        sys.exit(1)
    
    download_url = f"https://github.com/gitleaks/gitleaks/releases/download/v{GITLEAKS_VERSION}/{archive_filename}"
    output_filename = "gitleaks"

    if system == "Windows":
        subprocess.run(["curl", "-sfL", download_url, "-o", archive_filename], check=True, shell=True)
        subprocess.run(["tar", "-xf", archive_filename, output_filename], check=True, shell=True)
    else:
        subprocess.run(["curl", "-sfL", download_url, "-o", archive_filename], check=True)
        subprocess.run(["tar", "-xzf", archive_filename, output_filename], check=True)

def enable_gitleaks_hook():
    enable_option = subprocess.run(["git", "config", "--get", "gitleaks.enabled"], capture_output=True, text=True).stdout.strip()
    enable = True
    if enable_option:
        enable = enable_option.lower() != "false"
    if enable:
        hooks_dir = os.path.join(".git", "hooks")
        pre_commit_script = os.path.join(hooks_dir, "pre-commit")
        script_path = os.path.abspath(__file__)
        
        if not os.path.exists(pre_commit_script):
            shutil.copy(script_path, pre_commit_script)
            subprocess.run(["chmod", "+x", pre_commit_script], check=True)
            print("Gitleaks pre-commit hook enabled.")
    else:
        print("Gitleaks pre-commit hook disabled.")


def check_for_secrets():
    try:
        subprocess.run(["./gitleaks", "version"], check=True)
    except FileNotFoundError:
        print("gitleaks not found. Installing...")
        install_gitleaks()

    command = ["./gitleaks", "protect", "--staged", "--source", ".", "--verbose"]
    process = subprocess.run(command, capture_output=True, text=True)

    print(process.stderr)
    print(process.stdout)

    if process.returncode != 0:
        print("Error: Secrets detected. Commit rejected.")
        sys.exit(1)

def main():
    # Check if Gitleaks is already installed
    gitleaks_path = "./gitleaks"
    if os.path.exists(gitleaks_path):
        installed_version = subprocess.run([gitleaks_path, "version"], capture_output=True, text=True).stdout.strip()
        if installed_version == GITLEAKS_VERSION:
            print(f"Gitleaks {GITLEAKS_VERSION} is already installed.")
        else:
            print(f"Existing Gitleaks version {installed_version} is not compatible. Installing Gitleaks {GITLEAKS_VERSION}...")
            install_gitleaks()
    else:
        print("Gitleaks is not installed. Installing...")
        install_gitleaks()

    # Enable gitleaks pre-commit hook
    enable_gitleaks_hook()

    # Check for secrets
    check_for_secrets()

if __name__ == "__main__":
    main()
