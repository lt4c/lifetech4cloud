#!/usr/bin/env python3
"""
Check and install dependencies for NCloud Python server
"""

import os
import sys
import subprocess
import importlib.util

def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False, result.stdout, result.stderr
        return True, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return False, "", str(e)

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Need Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False

def install_package(package_name, version=None):
    """Install a Python package"""
    pkg = f"{package_name}=={version}" if version else package_name
    print(f"Installing {pkg}...")
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install {pkg}")
    if success:
        print("✅")
    else:
        print(f"❌ Failed to install {pkg}")
        print(stderr)
    return success

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    print("\nChecking Playwright browsers...")

    # Check chromium
    success, stdout, stderr = run_command("playwright install chromium --dry-run", check=False)
    if "chromium" in stdout or success:
        print("✅ Chromium browser")
        return True
    else:
        print("❌ Chromium browser - NOT INSTALLED")
        print("Installing Chromium...")
        success, stdout, stderr = run_command("playwright install chromium")
        if success:
            print("✅ Chromium installed")
            return True
        else:
            print("❌ Failed to install Chromium")
            return False

def check_system_dependencies():
    """Check system dependencies and install Chrome if needed"""
    print("\nChecking system dependencies...")

    chrome_found = False

    # Check if Chrome/Chromium is available
    if sys.platform == "win32":
        # Windows
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]

        # Check PATH first
        success, stdout, stderr = run_command('where chrome.exe 2>nul', check=False)
        if success and stdout.strip():
            chrome_found = True
            print("✅ Chrome found in PATH")
        else:
            # Check common installation paths
            for path in possible_paths:
                if os.path.exists(path):
                    chrome_found = True
                    print("✅ Chrome found in common location")
                    # Add to PATH for current session
                    os.environ['PATH'] += os.pathsep + os.path.dirname(path)
                    break

        if not chrome_found:
            print("❌ Chrome not found, attempting installation...")
            try:
                success, stdout, stderr = run_command('choco --version', check=False)
                if success:
                    success, stdout, stderr = run_command('choco install googlechrome -y', check=False)
                    if success:
                        print("✅ Chrome installed via Chocolatey")
                        chrome_found = True
                    else:
                        print("❌ Failed to install Chrome via Chocolatey")
                else:
                    print("❌ Chocolatey not found. Please install Chrome manually from: https://www.google.com/chrome/")
            except Exception as e:
                print(f"❌ Error installing Chrome: {e}")

    else:
        # Linux/Mac
        commands = ['google-chrome', 'chromium-browser', 'chromium']
        for cmd in commands:
            success, stdout, stderr = run_command(f'which {cmd} 2>/dev/null', check=False)
            if success and stdout.strip():
                chrome_found = True
                print(f"✅ {cmd} found")
                break

        # Check common paths
        if not chrome_found:
            linux_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/google-chrome",
            ]
            for path in linux_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chrome_found = True
                    print("✅ Chrome/Chromium found in common location")
                    break

        if not chrome_found:
            print("❌ Chrome not found, attempting installation...")
            try:
                # Try to install Chrome based on OS
                if os.path.exists("/etc/debian_version"):
                    print("Installing Chrome on Ubuntu/Debian...")
                    success, stdout, stderr = run_command('wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && apt-get update && apt-get install -y google-chrome-stable', check=False)
                elif os.path.exists("/etc/redhat-release"):
                    print("Installing Chrome on CentOS/RHEL/Fedora...")
                    success, stdout, stderr = run_command('wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm && yum localinstall -y google-chrome-stable_current_x86_64.rpm', check=False)
                else:
                    success, stdout, stderr = run_command('curl -fsSL https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm -o chrome.rpm && yum localinstall -y chrome.rpm', check=False)

                if success:
                    print("✅ Chrome installation completed")
                    chrome_found = True
                else:
                    print("❌ Failed to install Chrome automatically")

            except Exception as e:
                print(f"❌ Error installing Chrome: {e}")

    if not chrome_found:
        print("⚠️  Warning: Chrome/Chromium not available. VM creation may fail.")
        print("Please install Google Chrome or Chromium to enable VM creation.")
        return False
    else:
        return True

def main():
    """Main check and install function"""
    print("🔍 Checking NCloud Python dependencies...\n")

    # Check Python version
    if not check_python_version():
        return False

    # Required packages
    packages = [
        ('Flask', 'flask', '3.0.0'),
        ('Flask-CORS', 'flask_cors', '4.0.0'),
        ('playwright', None, '1.40.0'),
        ('requests', None, '2.31.0'),
        ('psutil', None, '5.9.6'),
        ('dnspython', 'dns', '2.8.0'),

        ('pytz', None, '2023.3'),
        ('stringcase', None, '1.2.0'),
    ]

    # Check packages
    missing_packages = []
    print("\nChecking Python packages...")
    for package, import_name, version in packages:
        if not check_package(package, import_name):
            missing_packages.append((package, import_name, version))

    # Install missing packages
    if missing_packages:
        print(f"\n📦 Installing {len(missing_packages)} missing packages...")
        for package, import_name, version in missing_packages:
            if not install_package(package, version):
                return False

        # Re-check after installation
        print("\nRe-checking packages after installation...")
        for package, import_name, version in missing_packages:
            if not check_package(package, import_name):
                print(f"❌ {package} still not available after installation")
                return False
    else:
        print("\n✅ All Python packages are installed!")

    # Check Playwright browsers
    check_playwright_browsers()

    # Check system dependencies
    check_system_dependencies()

    print("\n🎉 Dependency check completed!")
    print("Run 'python server.py' to start the server.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
