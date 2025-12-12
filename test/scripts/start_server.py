#!/usr/bin/env python3
import http.server
import socketserver
import json
import sys
import os
from pathlib import Path

# Add lib to path
lib_path = Path(__file__).resolve().parents[2] / "lib"
sys.path.append(str(lib_path))

from BERDLTable_conversion_service.BERDLTable_conversion_serviceImpl import BERDLTable_conversion_service

# Initialize service
config = {'scratch': '/tmp/berdl_test'}
os.makedirs(config['scratch'], exist_ok=True)
service = BERDLTable_conversion_service(config)

class JSONRPCHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"Request: {json.dumps(data)}")
            
            method_name = data['method'].replace('BERDLTable_conversion_service.', '')
            params = data['params']
            
            response = {}
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                # KBase params are passed as a list, first element is the dict
                param_dict = params[0] if params else {}
                
                # Call method
                result = method({}, param_dict)
                response = {'result': result, 'id': data.get('id'), 'version': '1.1'}
            else:
                response = {'error': f"Method {method_name} not found", 'id': data.get('id')}
            
            response_bytes = json.dumps(response).encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        # Silence default logging
        return

if __name__ == "__main__":
    PORT = 5000
    # Enable address reuse to avoid "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    
    print(f"Starting BERDLTable Test Server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), JSONRPCHandler) as httpd:
        httpd.serve_forever()
