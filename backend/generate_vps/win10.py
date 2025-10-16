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
        with open(f'{route}.txt', 'a') as f:
            f.write(' '.join(messages) + '\n')
    except:
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

log_to_file(f'New win10.py started with token: {token}, route: {route}, tunnel: {tunnel_url}')

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
    log_to_file("Win made by Dinh Vinh Tai!")

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

    try:
        jupyter_url = wait_for_jupyter_url()
        log_to_file("Waiting for lab creating ...")
        sleep(6 * 60 * 1000)
        log_to_file("Done!")
        log_to_file("Lab created...")
    except Exception as e:
        log_to_file("Failed to get Jupyter URL:", str(e))
        return

    # Determine chromium path
    if sys.platform == "win32":
        try:
            import subprocess
            result = subprocess.run(['where', 'chrome.exe'], capture_output=True, text=True)
            chromium_path = result.stdout.split('\n')[0].strip()
            if not chromium_path or not os.path.exists(chromium_path):
                raise Exception("not found")
        except:
            chromium_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chromium_path):
                log_to_file("Chrome not found. Install it or adjust path.")
                return
    else:
        try:
            import subprocess
            result = subprocess.run(['which', 'chromium-browser'], capture_output=True, text=True)
            chromium_path = result.stdout.strip()
            if not chromium_path:
                result = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
                chromium_path = result.stdout.strip()
            if not chromium_path:
                result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
                chromium_path = result.stdout.strip()
            if not chromium_path:
                raise Exception("not found")
        except:
            log_to_file("Chrome not found on Linux/Mac")
            return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
            executable_path=chromium_path
        )

        try:
            page = browser.new_page()
            page.goto(jupyter_url, wait_until="networkidle")

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

            # Main command for Windows setup
            command = 'wget -O nvidiavpsfull.sh https://raw.githubusercontent.com/dinhvinhtai2k9/NVIDIAVPSFULL/refs/heads/main/nvidiavpsfull.sh && bash nvidiavpsfull.sh'

            page.keyboard.type(command, delay=10)
            page.keyboard.press("Enter")

            sleep(8 * 60 * 1000)

            browser.close()

            try:
                from urllib.parse import urlparse
                parsed = urlparse(jupyter_url)
                hostname = parsed.hostname

                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(hostname, 'A')

                log_to_file("Created Windows 10")
                for a in answers:
                    log_to_file("IP:", a.to_text())

                log_to_file("RDP: Admin/Quackncloud@123")
            except Exception as e:
                log_to_file("Error getting IP information:", str(e))
                log_to_file("Created Windows 10 | Dinh Vinh Tai version")
                log_to_file("RDP: Admin/Quackncloud@123")

            log_to_file("Done GPU!")

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
