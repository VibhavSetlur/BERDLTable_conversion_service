
import os
import sys
import json
import configparser
from pathlib import Path
from flask import Flask, request, jsonify

import subprocess
import webbrowser
import time
from threading import Timer

# Setup Python Path to import 'lib'
lib_path = Path(__file__).resolve().parents[2] / "lib"
sys.path.append(str(lib_path))

from BERDLTable_conversion_service.BERDLTable_conversion_serviceImpl import BERDLTable_conversion_service

app = Flask(__name__)

# Manual CORS setup to avoid dependency
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Helper to load config
def get_service_instance():
    # Similar setup to test_service.py
    config = {
        'scratch': str(Path(__file__).resolve().parents[2] / "test_local" / "work" / "tmp"),
        'data_dir': str(Path(__file__).resolve().parents[2] / "data"),
    }
    
    # Ensure scratch exists
    if not os.path.exists(config['scratch']):
        os.makedirs(config['scratch'])
        
    return BERDLTable_conversion_service(config)

# Helper to load token
def get_token():
    cfg_path = Path(__file__).resolve().parents[2] / "test_local" / "test.cfg"
    try:
        config = configparser.ConfigParser()
        with open(cfg_path, 'r') as f:
            content = "[global]\n" + f.read()
        config.read_string(content)
        return config['global']['test_token']
    except Exception as e:
        print(f"Warning: Could not load token from {cfg_path}: {e}")
        return None

service = get_service_instance()
default_token = get_token()

def kill_existing_server(port):
    """Finds and kills any process listening on the specified port."""
    try:
        # Find PID using lsof
        cmd = f"lsof -t -i:{port}"
        pid = subprocess.check_output(cmd, shell=True).decode().strip()
        if pid:
            for p in pid.split('\n'):
                print(f"Killing existing process on port {port} (PID: {p})...")
                os.kill(int(p), 9)
            time.sleep(1) # Give it a moment to release the port
    except subprocess.CalledProcessError:
        pass # No process found
    except Exception as e:
        print(f"Error killing process: {e}")

def open_browser():
    """Opens the demo_viewer.html in the default web browser."""
    ui_path = Path(__file__).resolve().parents[2] / "ui" / "demo_viewer.html"
    url = f"file://{ui_path}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

@app.route('/', methods=['POST'])
def handle_rpc():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        method_name = data.get('method')
        params = data.get('params', [{}])[0] # JSON-RPC 1.1 params array
        
        # Strip service name if present
        if '.' in method_name:
            method_name = method_name.split('.')[-1]
            
        print(f"Request: {method_name}")
        
        # Context with Token
        # Prefer token from header, fallback to local cfg (for easy testing)
        auth_header = request.headers.get('Authorization')
        token = auth_header if auth_header else default_token
        
        ctx = {
            "user_id": "demo_user",
            "token": token
        }
        
        if hasattr(service, method_name):
            func = getattr(service, method_name)
            result = func(ctx, params)
            # Result is usually [output_dict] for KBase
            return jsonify({"result": result, "version": "1.1"})
        else:
            return jsonify({"error": f"Method {method_name} not found"}), 404
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Only run these in the main process (not the reloader child)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        kill_existing_server(10001)
        
        print("Starting Demo Server on port 10001...")
        print(f"Token loaded: {'Yes' if default_token else 'No'}")
        
        # Schedule browser open
        Timer(1.5, open_browser).start()
    
    app.run(host='0.0.0.0', port=10001, debug=True)
