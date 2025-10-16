from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, make_response
from flask_cors import CORS
import json
import os
import sys
import subprocess
import time
import threading
import logging
import platform
import psutil
import random
import string
from playwright.sync_api import sync_playwright
import re
import urllib.request
import urllib.error

app = Flask(__name__)
CORS(app)

# Configuration
TOKEN_FILE = 'token.json'
CODE_FILE = 'code.json'
TUNNEL_URL = None
tunnel_app = None
tunnel_process = None
tunnel_setup_complete = False

# Ensure token file exists
if not os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, 'w') as f:
        json.dump({}, f)

# Security middleware function
def security_middleware():
    """Check if request is from allowed domains"""
    host = request.headers.get('Host', '')
    origin = request.headers.get('Origin', '')
    referer = request.headers.get('Referer', '')

    allowed_hosts = ['localhost', '127.0.0.1', '::1', 'ducknovis.site']

    is_allowed = any(allowed_host in host for allowed_host in allowed_hosts) or \
                any(allowed_host in origin for allowed_host in allowed_hosts) or \
                any(allowed_host in referer for allowed_host in allowed_hosts)

    if not is_allowed:
        logging.warning(f"Blocked request from: {host} ({origin})")
        return jsonify({"error": "Access denied"}), 403
    return None

@app.before_request
def check_security():
    # Apply security middleware to most routes
    if request.endpoint and not request.endpoint.startswith(('index', 'dashboard')):
        result = security_middleware()
        if result:
            return result

# Rate limiting
rate_limit_data = {
    'total_requests': [],
    'ip_requests': {}
}

def cleanup_rate_limit_data():
    now = time.time()
    one_minute_ago = now - 60

    rate_limit_data['total_requests'] = [
        timestamp for timestamp in rate_limit_data['total_requests']
        if timestamp > one_minute_ago
    ]

    for ip, timestamps in list(rate_limit_data['ip_requests'].items()):
        valid_timestamps = [t for t in timestamps if t > one_minute_ago - 60]
        if valid_timestamps:
            rate_limit_data['ip_requests'][ip] = valid_timestamps
        else:
            del rate_limit_data['ip_requests'][ip]

def check_rate_limit(ip):
    cleanup_rate_limit_data()

    if len(rate_limit_data['total_requests']) >= 15:
        return {'allowed': False, 'reason': 'Rate limit exceeded: too many requests per minute'}

    ip_timestamps = rate_limit_data['ip_requests'].get(ip, [])
    if ip_timestamps:
        last_request = max(ip_timestamps)
        if time.time() - last_request < 60:
            wait_time = int(60 - (time.time() - last_request))
            return {'allowed': False, 'reason': f'Please wait {wait_time} seconds before requesting another code'}

    return {'allowed': True}

def record_request(ip):
    now = time.time()
    rate_limit_data['total_requests'].append(now)

    if ip not in rate_limit_data['ip_requests']:
        rate_limit_data['ip_requests'][ip] = []
    rate_limit_data['ip_requests'][ip].append(now)

def perform_nvidia_login(email, password):
    """Perform NVIDIA login using Playwright"""
    try:
        logging.info(f"Starting NVIDIA login for {email}")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = context.new_page()

            try:
                page.goto('https://learn.learn.nvidia.com/login', wait_until='networkidle')

                page.wait_for_selector('#email', timeout=10000)
                page.fill('#email', email)
                page.click('button[type="submit"]')

                page.wait_for_selector('#signinPassword', timeout=40000)
                page.fill('#signinPassword', password)
                page.click('#passwordLoginButton')

                logging.info('Waiting for login completion...')
                time.sleep(30)  # Wait for login to complete

                current_url = page.url
                logging.info('Current URL after password click:', current_url)

                if 'dashboard' not in current_url:
                    logging.info('Not on dashboard, waiting for navigation...')
                    try:
                        page.wait_for_load_state('networkidle', timeout=60000)
                        current_url = page.url
                        logging.info('URL after navigation wait:', current_url)
                    except:
                        current_url = page.url
                        logging.info('Current URL after timeout:', current_url)

                if 'dashboard' not in current_url:
                    logging.info('Still not on dashboard, direct navigation...')
                    page.goto('https://learn.learn.nvidia.com/dashboard', wait_until='networkidle', timeout=15000)

                time.sleep(15)

                cookies = context.cookies()
                logging.info('All cookies found:', len(cookies))

                session_cookie = next((c for c in cookies if c['name'] == 'sessionid'), None)
                logging.info('Session cookie:', session_cookie['value'][:20] + '...' if session_cookie else 'none')

                if session_cookie and len(session_cookie['value']) > 10:
                    logging.info('Authentication successful - saving token')

                    # Read existing tokens
                    try:
                        with open(TOKEN_FILE, 'r') as f:
                            v2 = json.load(f)
                    except:
                        v2 = {}

                    if email not in v2:
                        v2[email] = {}

                    v2[email]['pass'] = password
                    v2[email]['token'] = session_cookie['value']
                    if 'hasDevice' not in v2[email]:
                        v2[email]['hasDevice'] = False

                    with open(TOKEN_FILE, 'w') as f:
                        json.dump(v2, f, indent=2)

                    logging.info(f'Token saved successfully for {email}')
                    return {'success': True, 'message': 'Authentication successful'}
                else:
                    logging.info('Authentication failed - no valid session cookie')
                    return {'success': False, 'message': 'Authentication failed - no session cookie'}

            finally:
                browser.close()
                logging.info('Browser closed successfully')

    except Exception as error:
        logging.error(f'NVIDIA login error for {email}: {str(error)}')
        return {'success': False, 'message': str(error)}

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/dashboard')
def dashboard():
    if not request.cookies.get('token'):
        return redirect('/')

    with open('dashboard.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/generate-code', methods=['POST'])
def generate_code():
    client_ip = request.remote_addr

    rate_limit_check = check_rate_limit(client_ip)
    if not rate_limit_check['allowed']:
        return jsonify({'success': False, 'message': rate_limit_check['reason']})

    record_request(client_ip)

    try:
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(18))

        try:
            with open(CODE_FILE, 'r') as f:
                codes = json.load(f)
        except:
            codes = {}

        codes[code] = {'slot': 2}

        with open(CODE_FILE, 'w') as f:
            json.dump(codes, f, indent=2)

        # Note: Skipping paste.ee API integration for simplicity
        # In real implementation, you'd add this back

        return jsonify({'success': True, 'url': f'https://example.com/code/{code}'})

    except Exception as error:
        logging.error('Error generating code:', str(error))
        return jsonify({'success': False, 'message': 'Failed to generate code'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)
    except:
        v2 = {}

    # Check if account already exists
    if email in v2 and v2[email].get('token'):
        logging.info(f'Existing account found for: {email} - redirecting')
        response = make_response(jsonify({'redirect': True, 'token': v2[email]['token']}))
        response.set_cookie('token', v2[email]['token'], httponly=False, secure=False, max_age=24*60*60*1000)
        return response

    # New account - start authentication process
    logging.info(f'New account - starting authentication for: {email}')

    # Start login process in background
    threading.Thread(target=lambda: perform_nvidia_login_async(email, password)).start()

    return jsonify({'authentication': 'pending', 'loginId': email})

@app.route('/login-status')
def login_status():
    login_id = request.args.get('loginId')

    if not login_id:
        return jsonify({'error': 'loginId parameter required'}), 400

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)
    except:
        v2 = {}

    # Check if account already exists (authentication completed)
    if login_id in v2 and v2[login_id].get('token'):
        try:
            os.unlink(f'login_{login_id}.json')
        except:
            pass

        logging.info(f'Login completed successfully for: {login_id}')

        response = make_response(jsonify({
            'success': True,
            'status': 'completed',
            'redirect': '/dashboard'
        }))
        response.set_cookie('token', v2[login_id]['token'])
        return response

    # Check login status file for pending/completed status
    status_file = f'login_{login_id}.json'
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)

            if status_data['status'] == 'completed':
                if status_data['result'] == 'success':
                    # Check again if token was created
                    if login_id in v2 and v2[login_id].get('token'):
                        os.unlink(status_file)
                        response = make_response(jsonify({
                            'success': True,
                            'status': 'completed',
                            'redirect': '/dashboard'
                        }))
                        response.set_cookie('token', v2[login_id]['token'])
                        return response
                    else:
                        # Token not created yet, still waiting
                        return jsonify({'success': True, 'status': 'pending'})
                else:
                    # Authentication failed
                    os.unlink(status_file)
                    return jsonify({
                        'success': False,
                        'status': 'failed',
                        'error': status_data.get('error', 'Authentication failed')
                    })
            elif status_data['status'] == 'in_progress':
                return jsonify({'success': True, 'status': 'pending'})
        except:
            pass

    # No status file found, assume still pending
    return jsonify({'success': True, 'status': 'pending'})

def perform_nvidia_login_async(email, password):
    """Async wrapper for NVIDIA login"""
    result = perform_nvidia_login(email, password)

    status_file = f'login_{email}.json'
    if result['success']:
        with open(status_file, 'w') as f:
            json.dump({'status': 'completed', 'result': 'success'}, f)
    else:
        with open(status_file, 'w') as f:
            json.dump({'status': 'failed', 'error': result['message']}, f)

@app.route('/logout', methods=['POST'])
def logout():
    response = make_response(redirect('/'))
    response.delete_cookie('token')
    return response

@app.route('/create-linux', methods=['POST'])
def create_linux():
    if not request.cookies.get('token'):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)
    except:
        v2 = {}

    email = None
    for key, value in v2.items():
        if value.get('token') == request.cookies.get('token'):
            email = key
            break

    if not email or 'route' in v2[email]:
        return jsonify({'error': 'Invalid user or device already exists'}), 400

    route = 'quack_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    v2[email]['route'] = route

    with open(TOKEN_FILE, 'w') as f:
        json.dump(v2, f)

    # Start Linux VM process (capture token before thread)
    token_value = request.cookies.get('token')
    threading.Thread(target=lambda: run_linux_vm(token_value, route, TUNNEL_URL)).start()

    return jsonify({'route': route})

@app.route('/create-windows', methods=['POST'])
def create_windows():
    if not request.cookies.get('token'):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)
    except:
        v2 = {}

    email = None
    for key, value in v2.items():
        if value.get('token') == request.cookies.get('token'):
            email = key
            break

    if not email or 'route' in v2[email]:
        return jsonify({'error': 'Invalid user or device already exists'}), 400

    route = 'quack_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    v2[email]['route'] = route

    with open(TOKEN_FILE, 'w') as f:
        json.dump(v2, f)

    # Start Windows VM process (capture token before thread)
    token_value = request.cookies.get('token')
    threading.Thread(target=lambda: run_windows_vm(token_value, route, TUNNEL_URL)).start()

    return jsonify({'route': route})

@app.route('/create-trash', methods=['POST'])
def create_trash():
    if not request.cookies.get('token'):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)
    except:
        v2 = {}

    email = None
    for key, value in v2.items():
        if value.get('token') == request.cookies.get('token'):
            email = key
            break

    if not email or 'route' in v2[email]:
        return jsonify({'error': 'Invalid user or device already exists'}), 400

    route = 'quack_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    v2[email]['route'] = route

    with open(TOKEN_FILE, 'w') as f:
        json.dump(v2, f)

    # Start 2z2 VM process (capture token before thread)
    token_value = request.cookies.get('token')
    threading.Thread(target=lambda: run_2z2_vm(token_value, route)).start()

    return jsonify({'route': route})

# Global variables to store VM processes for cleanup
vm_processes = {}

def run_linux_vm(token, route, tunnel_url):
    """Run Linux VM process"""
    proc = subprocess.Popen([sys.executable, 'linux.py', token, route, tunnel_url or ''])
    vm_processes[route] = proc

def run_windows_vm(token, route, tunnel_url):
    """Run Windows VM process"""
    proc = subprocess.Popen([sys.executable, 'win10.py', token, route, tunnel_url or ''])
    vm_processes[route] = proc

def run_2z2_vm(token, route):
    """Run 2z2 VM process"""
    proc = subprocess.Popen([sys.executable, '2z2.py', token, route])
    vm_processes[route] = proc

@app.route('/cleanup-route', methods=['POST'])
def cleanup_route():
    data = request.get_json()
    route = data.get('route')

    if not route:
        return jsonify({'error': 'Route is required'}), 400

    try:
        with open(TOKEN_FILE, 'r') as f:
            v2 = json.load(f)

        email = None
        for key, value in v2.items():
            if value.get('route') == route:
                email = key
                break

        if email:
            if 'route' in v2[email]:
                del v2[email]['route']
            with open(TOKEN_FILE, 'w') as f:
                json.dump(v2, f, indent=2)
            logging.info(f'Cleaned up route {route} from client request')
            return jsonify({'success': True, 'message': 'Route cleaned up'})
        else:
            return jsonify({'error': 'Route not found'}), 404
    except Exception as error:
        logging.error('Error cleaning up route:', str(error))
        return jsonify({'error': 'Server error'}), 500

@app.route('/logs/<route>')
def get_logs(route):
    log_file = f'{route}.txt'
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return f.read()
    return 'Logs not found', 404

@app.route('/get-route')
def get_route():
    if request.cookies.get('token'):
        try:
            with open(TOKEN_FILE, 'r') as f:
                v2 = json.load(f)
        except:
            v2 = {}

        for key, value in v2.items():
            if value.get('token') == request.cookies.get('token'):
                if 'route' in value:
                    return jsonify({'success': True, 'route': value['route']})
                break

    return jsonify({'success': False})

@app.route('/server-stats')
def server_stats():
    try:
        mem = psutil.virtual_memory()
        ram_percent = int(mem.percent)

        if platform.system() == 'Windows':
            cpu_percent = int(psutil.cpu_percent(interval=1))
        else:
            cpu_percent = int(psutil.cpu_percent())

        return jsonify({'ram': ram_percent, 'cpu': cpu_percent})
    except:
        return jsonify({'ram': 0, 'cpu': 0})

@app.route('/execute-command', methods=['POST'])
def execute_command():
    data = request.get_json()
    route = data.get('route')
    command = data.get('command')

    if not route or not command:
        return jsonify({'error': 'Route and command are required'}), 400

    log_file = f'{route}.txt'

    try:
        if command == 'stop':
            # Kill VM processes and cleanup
            try:
                with open(TOKEN_FILE, 'r') as f:
                    v2 = json.load(f)
            except:
                v2 = {}

            email = None
            for key, value in v2.items():
                if value.get('route') == route:
                    email = key
                    break

            if email and 'route' in v2[email]:
                del v2[email]['route']
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(v2, f)

            # Kill processes
            if platform.system() == 'Windows':
                try:
                    subprocess.run(['taskkill', '/f', '/im', 'python.exe', '/fi', f'WINDOWTITLE eq *{route}*'],
                                 capture_output=True)
                except:
                    pass
            else:
                try:
                    subprocess.run(['pkill', '-f', route], capture_output=True)
                except:
                    pass

            log_entry = f'quackuser@{route}:~$ {command}\nVM creation stopped and route deleted.\n'

        elif command == 'clear':
            open(log_file, 'w').close()
            return jsonify({'success': True})

        elif command.startswith('clear '):
            try:
                parts = command.split(' ')
                lines_to_clear = int(parts[1])
                if lines_to_clear > 0 and os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                    lines = content.split('\n')
                    remaining_lines = lines[:max(0, len(lines) - lines_to_clear - 1)]
                    with open(log_file, 'w') as f:
                        f.write('\n'.join(remaining_lines) + ('\n' if remaining_lines else ''))
            except:
                pass
            return jsonify({'success': True})

        else:
            log_entry = f'quackuser@{route}:~$ {command}\n'

            if command == 'cmd':
                log_entry += 'Available commands:\n'
                log_entry += '  echo <text>    - print text\n'
                log_entry += '  stop           - stop vps creation or vps created\n'
                log_entry += '  cmd            - Show this help\n\n'
            elif command.startswith('echo '):
                content = command[5:]
                log_entry += content + '\n'
            else:
                first_word = command.split(' ')[0]
                log_entry += f'{first_word}: command not found\n'

        with open(log_file, 'a') as f:
            f.write(log_entry)

        return jsonify({'success': True})

    except Exception as error:
        logging.error('Error executing command:', str(error))
        return jsonify({'error': 'Failed to execute command'}), 500

@app.route('/redeem-code', methods=['POST'])
def redeem_code():
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({'success': False})

    try:
        with open(CODE_FILE, 'r') as f:
            codes = json.load(f)
    except:
        codes = {}

    if code in codes and codes[code].get('slot', 0) > 0:
        codes[code]['slot'] -= 1
        with open(CODE_FILE, 'w') as f:
            json.dump(codes, f, indent=2)
        return jsonify({'success': True})

    return jsonify({'success': False})

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../public/js', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../public/css', filename)

@app.route('/background.png')
def background():
    return send_from_directory('.', 'background.png')

def download_cloudflared():
    """Download cloudflared binary if not available"""
    import tempfile
    import stat

    is_windows = platform.system() == 'Windows'
    download_url = 'https://github.com/cloudflare/cloudflared/releases/download/2025.9.1/cloudflared-windows-amd64.exe' if is_windows else 'https://github.com/cloudflare/cloudflared/releases/download/2025.9.1/cloudflared-linux-amd64'
    file_name = 'cloudflared.exe' if is_windows else 'cloudflared'
    file_path = os.path.join('.', file_name)

    if os.path.exists(file_path):
        print(f'Cloudflared already exists at: {file_path}')
        return file_path

    print(f'Downloading cloudflared from: {download_url}')

    try:
        with urllib.request.urlopen(download_url) as response:
            with open(file_path, 'wb') as f:
                f.write(response.read())

        if not is_windows:
            os.chmod(file_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            # Verify it's executable
            if not os.access(file_path, os.X_OK):
                print('Warning: cloudflared is not executable')

        print(f'Cloudflared downloaded to: {file_path}')
        return file_path
    except Exception as e:
        print(f'Error downloading cloudflared: {e}')
        if os.path.exists(file_path):
            os.unlink(file_path)
        return None

def setup_cloudflare_tunnel():
    """Setup Cloudflare tunnel for SSHX callbacks"""
    global TUNNEL_URL, tunnel_app, tunnel_process

    print("Setting up Cloudflare tunnel...")

    # Check for existing cloudflared
    is_windows = platform.system() == 'Windows'
    cloudflared_paths = ['cloudflared.exe', './cloudflared.exe', 'C:\\cloudflared\\cloudflared.exe'] if is_windows else ['cloudflared', './cloudflared', '/usr/local/bin/cloudflared']

    cloudflared_path = None
    for path in cloudflared_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                cloudflared_path = path
                print(f'Found cloudflared at: {path}')
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            continue

    # Download if not found
    if not cloudflared_path:
        print('Cloudflared not found, downloading...')
        cloudflared_path = download_cloudflared()
        if not cloudflared_path:
            print('Failed to download cloudflared, skipping tunnel setup')
            return

    # Import Flask here to avoid import issues
    from flask import Flask as TunnelFlask

    # Create tunnel app
    tunnel_app = TunnelFlask(__name__)

    @tunnel_app.route('/sshx', methods=['POST'])
    def sshx_callback():
        print(f"🔗 SSHx POST received. Content-Type: {request.content_type}")
        print(f"🔗 Request data: {request.get_data()}")
        print(f"🔗 Request JSON: {request.get_json(force=True, silent=True)}")
        try:
            data = request.get_json(force=True)
            sshx = data.get('sshx')
            route = data.get('route')

            print(f"🔗 SSHx callback data: sshx={sshx}, route={route}")
            print(f"🔗 Processing callback...")

            if sshx and route:
                log_file = f'{route}.txt'
                try:
                    with open(log_file, 'a') as f:
                        f.write(f'Sshx link: {sshx}\n')
                    print(f'✅ SSHX link received for route {route}: {sshx}')

                    # Create escaped response to prevent parsing errors
                    response_data = {'success': True, 'link': sshx, 'route': route}
                    response_json = json.dumps(response_data, separators=(',', ':'))

                    print(f"🔗 Sending escaped response: {response_json}")

                    # Return with proper headers and escaped content
                    response = app.response_class(
                        response=response_json,
                        status=200,
                        mimetype='application/json'
                    )
                    return response

                except Exception as e:
                    print(f'❌ Error writing SSHX link to log: {e}')
                    error_response = {'success': False, 'error': f'Failed to write log: {str(e)}'}
                    error_json = json.dumps(error_response, separators=(',', ':'))
                    print(f"🔗 Sending error response: {error_json}")
                    return app.response_class(error_json, status=500, mimetype='application/json')
            else:
                print(f"❌ Missing data: sshx={sshx}, route={route}")
                error_response = {'success': False, 'error': 'Missing sshx or route'}
                error_json = json.dumps(error_response, separators=(',', ':'))
                print(f"🔗 Sending missing data response: {error_json}")
                return app.response_class(error_json, status=400, mimetype='application/json')
        except Exception as e:
            print(f'❌ Error processing SSHX callback: {e}')
            import traceback
            print(f"🔗 Full traceback: {traceback.format_exc()}")
            error_response = {'success': False, 'error': str(e)}
            error_json = json.dumps(error_response, separators=(',', ':'))
            print(f"🔗 Sending exception response: {error_json}")
            return app.response_class(error_json, status=500, mimetype='application/json')

    def run_tunnel_server():
        """Run the tunnel server on port 3001"""
        try:
            print('SSHx receiver server starting on port 3001...')
            print(f'Flask tunnel app will listen on 0.0.0.0:3001 and handle /sshx POST requests')

            @tunnel_app.route('/health', methods=['GET'])
            def health_check():
                return {'status': 'ok', 'tunnel_url': TUNNEL_URL}

            tunnel_app.run(host='0.0.0.0', port=3001, debug=False, use_reloader=False, threaded=True)
        except Exception as e:
            print(f'Error starting tunnel server: {e}')

    # Start tunnel server in separate thread
    tunnel_thread = threading.Thread(target=run_tunnel_server, daemon=True)
    tunnel_thread.start()

    # Give server time to start
    time.sleep(2)

    print('Launching cloudflared tunnel...')

    # Launch cloudflared tunnel
    try:
        print(f"🏁 Starting cloudflared process: {' '.join([cloudflared_path, 'tunnel', '--url', 'http://localhost:3001'])}")
        tunnel_process = subprocess.Popen(
            [cloudflared_path, 'tunnel', '--url', 'http://localhost:3001'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        print(f"✅ Cloudflared process started with PID: {tunnel_process.pid}")

        # Monitor output for tunnel URL
        def monitor_output():
            print(f"🔧 Monitor thread started for PID: {tunnel_process.pid}")
            global TUNNEL_URL
            print("🔍 Starting tunnel URL monitoring...")

            start_time = time.time()

            # Try to import fcntl for non-blocking I/O (Linux/Mac only)
            try:
                import fcntl
                import os
                use_nonblock = True
            except ImportError:
                # Windows doesn't have fcntl
                use_nonblock = False

            print("Using blocking mode (Windows)")
            while time.time() - start_time < 120:  # Monitor for 120 seconds
                current_time = time.time()
                elapsed = current_time - start_time
                print(f"⏱️  Checking tunnel process at {elapsed:.1f}s...")

                if tunnel_process.poll() is not None:
                    print(f"⚠️  Tunnel process terminated (exit code: {tunnel_process.returncode})")
                    # Read any remaining output
                    try:
                        remaining_stdout = tunnel_process.stdout.read()
                        remaining_stderr = tunnel_process.stderr.read()
                        if remaining_stdout:
                            print(f"📝 Remaining stdout: {remaining_stdout.strip()}")
                        if remaining_stderr:
                            print(f"📝 Remaining stderr: {remaining_stderr.strip()}")
                    except:
                        pass
                    break

                try:
                    if use_nonblock and hasattr(tunnel_process.stdout, 'fileno'):
                        # Non-blocking mode for Linux/Mac
                        stdout_fd = tunnel_process.stdout.fileno()
                        stderr_fd = tunnel_process.stderr.fileno()

                        # Set non-blocking mode
                        flags = fcntl.fcntl(stdout_fd, fcntl.F_GETFL)
                        fcntl.fcntl(stdout_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                        flags = fcntl.fcntl(stderr_fd, fcntl.F_GETFL)
                        fcntl.fcntl(stderr_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                        # Read line by line non-blocking
                        try:
                            line = tunnel_process.stdout.readline()
                            if line:
                                line = line.strip()
                                print(f'[CLOUDFLARE STDOUT] {line}')  # Log ALL stdout

                                if 'trycloudflare.com' in line or 'cloudflaretunnel.com' in line:
                                    import re
                                    urls = re.findall(r'https://[^\s]+', line)
                                    for url in urls:
                                        if 'trycloudflare.com' in url or 'cloudflaretunnel.com' in url:
                                            TUNNEL_URL = url.rstrip('.').strip()
                                            print(f'✅ Cloudflare tunnel established: {TUNNEL_URL}')
                                            return
                        except (OSError, IOError):
                            # Non-blocking read, no data available
                            pass

                        try:
                            line = tunnel_process.stderr.readline()
                            if line:
                                line = line.strip()
                                print(f'[CLOUDFLARE STDERR] {line}')  # Log ALL stderr

                                if 'trycloudflare.com' in line or 'cloudflaretunnel.com' in line:
                                    import re
                                    urls = re.findall(r'https://[^\s]+', line)
                                    for url in urls:
                                        if 'trycloudflare.com' in url or 'cloudflaretunnel.com' in url:
                                            TUNNEL_URL = url.rstrip('.').strip()
                                            print(f'✅ Cloudflare tunnel established: {TUNNEL_URL}')
                                            return
                        except (OSError, IOError):
                            # Non-blocking read, no data available
                            pass

                    else:
                        # Blocking mode for Windows - use timeout to prevent indefinite blocking
                        import threading
                        import queue

                        output_queue = queue.Queue()

                        def read_with_timeout(pipe, prefix, timeout_seconds=1.0):
                            """Read from pipe with timeout using separate thread"""
                            def read_thread():
                                try:
                                    while True:
                                        line = pipe.readline()
                                        if not line:  # EOF reached
                                            break
                                        if line.strip():  # Only queue non-empty lines
                                            output_queue.put((prefix, line.strip()))
                                except Exception as e:
                                    output_queue.put(('ERROR', f"Error reading {prefix}: {e}"))

                            thread = threading.Thread(target=read_thread, daemon=True)
                            thread.start()
                            thread.join(timeout=timeout_seconds)
                            return not thread.is_alive()  # Return False if thread completed

                        # Try to read from both pipes with timeout
                        stdout_done = read_with_timeout(tunnel_process.stdout, 'STDOUT')
                        stderr_done = read_with_timeout(tunnel_process.stderr, 'STDERR')

                        # Process any lines that were captured
                        while not output_queue.empty():
                            type_prefix, line = output_queue.get_nowait()
                            if type_prefix == 'ERROR':
                                print(f"[READ ERROR] {line}")
                            else:
                                print(f'[CLOUDFLARE {type_prefix}] {line}')

                                if 'trycloudflare.com' in line or 'cloudflaretunnel.com' in line:
                                    import re
                                    urls = re.findall(r'https://[^\s]+', line)
                                    for url in urls:
                                        if 'trycloudflare.com' in url or 'cloudflaretunnel.com' in url:
                                            TUNNEL_URL = url.rstrip('.').strip()
                                            print(f'✅ Cloudflare tunnel established: {TUNNEL_URL}')
                                            return

                        # If both pipes are done (EOF), process has no more output
                        if stdout_done and stderr_done:
                            print("📏 Both output pipes reached EOF")

                except Exception as e:
                    print(f"General error in monitoring: {e}")
                    break

                time.sleep(use_nonblock and 0.5 or 1.0)  # Shorter sleep for non-blocking

            print("🕐 Tunnel monitoring completed")

        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()

        # Wait longer for tunnel URL - Cloudflare can take time to assign URL
        start_wait = time.time()
        while time.time() - start_wait < 120:  # Wait up to 2 minutes for tunnel URL
            if TUNNEL_URL:
                break
            time.sleep(1.0)  # Check once per second

            # Give progress update every 10 seconds
            if int(time.time() - start_wait) % 10 == 0 and not TUNNEL_URL:
                print(f"⏳ Still waiting for tunnel URL... ({int(time.time() - start_wait)}s)")

        if TUNNEL_URL:
            print(f'Successfully established tunnel: {TUNNEL_URL}')
        else:
            print('Warning: Cloudflare tunnel URL not detected within timeout, but process continues...')

    except Exception as e:
        print(f'Error starting cloudflared tunnel: {e}')

if __name__ == '__main__':
    # Setup logging - disable werkzeug INFO logs
    logging.basicConfig(level=logging.INFO)
    # Disable werkzeug INFO logging (HTTP request logs)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Setup Cloudflare tunnel - only in main process, not reloader
    tunnel_pid_file = 'tunnel_pid.txt'

    # Check if tunnel is already running from another process
    tunnel_already_running = False
    if os.path.exists(tunnel_pid_file):
        try:
            with open(tunnel_pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                tunnel_already_running = True
                print(f"✅ Tunnel already running (PID: {pid})")
            except OSError:
                # Process doesn't exist, remove stale PID file
                os.unlink(tunnel_pid_file)
        except:
            if os.path.exists(tunnel_pid_file):
                os.unlink(tunnel_pid_file)

    if not tunnel_already_running:
        print("🚀 Starting Cloudflare tunnel setup...")
        setup_cloudflare_tunnel()

        # Write our PID to file
        with open(tunnel_pid_file, 'w') as f:
            f.write(str(os.getpid()))

    # Start server WITHOUT reloader to prevent duplicate tunnel setups
    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
