#!/usr/bin/env python3
"""
NCloud Server Runner - Checks dependencies and runs the server
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'playwright',
        'requests',
        'psutil',
        'dns',
        'pytz',
        'stringcase'  # Not actually used but in requirements
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('_', ''))  # Handle flask_cors -> flaskcors
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} packages. Running installation...")
        try:
            subprocess.check_call([sys.executable, 'check_and_install.py'])
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run 'python check_and_install.py' manually.")
            return False
        except FileNotFoundError:
            print("❌ check_and_install.py not found.")
            return False

    return True

def run_server():
    """Run the Flask server"""
    print("🚀 Starting NCloud Python Server...")
    try:
        # Run server.py
        subprocess.check_call([sys.executable, 'server.py'])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed with error code {e.returncode}")
        return False

    return True

def main():
    """Main runner function"""
    print("🔍 NCloud Python Server Launcher\n")

    # Check if we're in the right directory
    if not os.path.exists('server.py') or not os.path.exists('check_and_install.py'):
        print("❌ Error: server.py or check_and_install.py not found.")
        print("Make sure you're running this from the python directory.")
        return False

    # Check dependencies
    if not check_dependencies():
        return False

    print("\n✨ Starting server...")
    # Run the server
    return run_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
